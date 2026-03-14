"""
Generate synthetic suggestions data from existing agrinet conversations.

Picks random conversations, extracts random windows of QA pairs, and runs the
suggestions agent to produce follow-up question suggestions.

Usage:
    python -m synthetic.generate_suggestions -n 100 --max-parallel 10
"""

import argparse
import asyncio
import json
import random
import traceback
from pathlib import Path
from uuid import uuid4

from synthetic.deps import FarmerContext, build_suggestions_input, load_conversation
from synthetic.suggestions_agent import suggestions_agent
from synthetic.utils import walk_dir


DATA_DIR = Path("data/synthetic")
OUTPUT_DIR = Path("data/suggestions")


def _get_conversation_ids() -> list[str]:
    """Get all conversation IDs from the synthetic data directory."""
    files = walk_dir(str(DATA_DIR), extension="jsonl")
    return [Path(f).stem for f in files]


def _random_history_window(agrinet_history: list, window: int = 3) -> list:
    """Truncate history at a random point to get a window of QA pairs.

    get_message_pairs walks backwards from the end, so by truncating
    at a random point we effectively get a random window.
    """
    if len(agrinet_history) <= 2:
        return agrinet_history

    # Find all indices where a text part exists (assistant responses)
    text_indices = []
    for i, msg in enumerate(agrinet_history):
        for part in msg.parts:
            if getattr(part, "part_kind", "") == "text":
                text_indices.append(i)
                break

    if len(text_indices) <= window:
        return agrinet_history

    # Pick a random end point — at least `window` assistant responses in
    min_end = text_indices[window - 1]
    end_idx = random.choice(text_indices[window - 1:])

    # Return history up to and including this point
    return agrinet_history[: end_idx + 1]


async def generate_one(convo_id: str) -> dict:
    """Generate suggestions for a random window of one conversation."""
    record = load_conversation(convo_id)
    profile = record["profile"]
    env = record["env"]
    agrinet_history = record["agrinet_history"]

    # Pick a random window
    windowed_history = _random_history_window(agrinet_history, window=3)

    farmer_ctx = FarmerContext(
        query="",
        lang_code=env["target_language"],
        session_id=env["session_id"],
        today_date=env["today_date"],
        farmer_id=profile.get("farmer_id") if profile.get("has_agristack") else None,
        farmer_name=profile.get("name"),
        farmer_phone=profile.get("phone"),
        farmer_state=profile.get("state"),
        farmer_district=profile.get("district"),
        farmer_taluka=profile.get("taluka"),
        farmer_village=profile.get("village"),
        farmer_village_code=profile.get("village_code"),
        farmer_crops=profile.get("crops"),
        farmer_land_acres=profile.get("land_acres"),
        farmer_gender=profile.get("gender"),
        farmer_caste_category=profile.get("caste_category"),
        farmer_latitude=profile.get("latitude"),
        farmer_longitude=profile.get("longitude"),
        farmer_is_pocra=profile.get("is_pocra"),
    )

    suggestions_input = build_suggestions_input(windowed_history, limit=3)
    if not suggestions_input:
        return None

    result = await suggestions_agent.run(suggestions_input, deps=farmer_ctx)

    return {
        "id": str(uuid4()),
        "source_session_id": convo_id,
        "target_language": env["target_language"],
        "suggestions_input": suggestions_input,
        "suggestions": result.output,
    }


async def generate_batch(
    n: int,
    max_parallel: int = 10,
    output_dir: str = str(OUTPUT_DIR),
) -> Path:
    """Generate n suggestions records and write to JSONL."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    convo_ids = _get_conversation_ids()
    if not convo_ids:
        print("No conversations found in data/synthetic/")
        return output_path

    semaphore = asyncio.Semaphore(max_parallel)
    count = 0
    errors = 0

    async def _run_one(index: int) -> None:
        nonlocal count, errors
        async with semaphore:
            convo_id = random.choice(convo_ids)
            try:
                record = await generate_one(convo_id)
                if record:
                    out_file = output_path / f"{record['id']}.jsonl"
                    with open(out_file, "w") as f:
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
                    print(
                        f"[{index + 1}/{n}] source={convo_id} "
                        f"lang={record['target_language']} "
                        f"suggestions={len(record['suggestions'])}"
                    )
                else:
                    print(f"[{index + 1}/{n}] source={convo_id} SKIPPED (empty history)")
            except Exception:
                errors += 1
                print(f"[{index + 1}/{n}] source={convo_id} ERROR")
                traceback.print_exc()

    tasks = [asyncio.create_task(_run_one(i)) for i in range(n)]
    await asyncio.gather(*tasks)

    print(f"\nWrote {count} suggestions to {output_path}/ ({errors} errors)")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate suggestions from existing synthetic conversations.",
    )
    parser.add_argument("-n", type=int, default=50, help="Number of suggestions to generate (default: 50)")
    parser.add_argument("--max-parallel", type=int, default=10, help="Max concurrent requests (default: 10)")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    asyncio.run(
        generate_batch(
            n=args.n,
            max_parallel=args.max_parallel,
            output_dir=args.output_dir,
        )
    )


if __name__ == "__main__":
    main()
