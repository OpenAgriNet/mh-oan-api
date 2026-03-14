"""
Collect valid synthetic conversations and prepare a Hugging Face dataset.

Reads all JSONL files from the synthetic data directory, filters out errored
conversations, converts pydantic-ai message histories into OpenAI chat
completions format (with an added `thinking` field), and saves as a HF Dataset.

Usage:
    python -m synthetic.prepare_dataset [--data-dir data/synthetic] [--output-dir data/hf_dataset]
"""

import argparse
import json
from pathlib import Path

from datasets import Dataset, Features, Value


DATA_DIR = Path("data/synthetic")
OUTPUT_DIR = Path("data/hf_dataset")
HF_REPO = "kenpath/mh-synthetic-v1"


# ── OpenAI chat completions format conversion ───────────────────────────


def _flush_assistant(tool_calls_buf: list[dict], messages: list[dict]):
    """Emit a pending assistant message from buffered tool_calls, then clear buffer."""
    if not tool_calls_buf:
        return
    msg: dict = {"role": "assistant", "tool_calls": list(tool_calls_buf)}
    messages.append(msg)
    tool_calls_buf.clear()


def _extract_messages(raw_messages_json: str) -> list[dict]:
    """Convert pydantic-ai message history JSON into OpenAI chat completions format.

    Produces messages with standard OpenAI roles (developer, user, assistant, tool).
    Thinking/chain-of-thought parts are stripped entirely.

    Grouping logic:
      - Consecutive tool-call parts are collected into one `tool_calls` array.
      - A tool-return or text part flushes the pending assistant buffer first.

    Filters out: retry-prompt, thinking, empty text parts.
    """
    raw_messages = json.loads(raw_messages_json)
    messages: list[dict] = []
    tool_calls_buf: list[dict] = []

    for msg in raw_messages:
        for part in msg.get("parts", []):
            kind = part.get("part_kind", "")

            if kind in ("retry-prompt", "system-prompt", "thinking"):
                continue

            if kind == "user-prompt":
                _flush_assistant(tool_calls_buf, messages)
                content = str(part.get("content", "")).strip()
                if content:
                    messages.append({"role": "user", "content": content})

            elif kind == "tool-call":
                tool_name = part.get("tool_name", "")
                tool_call_id = part.get("tool_call_id", "")
                args = part.get("args", {})
                args_str = args if isinstance(args, str) else json.dumps(args, ensure_ascii=False)
                tool_calls_buf.append({
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": args_str,
                    },
                })

            elif kind == "tool-return":
                _flush_assistant(tool_calls_buf, messages)
                tool_name = part.get("tool_name", "")
                tool_call_id = part.get("tool_call_id", "")
                content = str(part.get("content", ""))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": content,
                })

            elif kind == "text":
                content = str(part.get("content", "")).strip()
                if content:
                    tool_calls_buf.clear()
                    messages.append({"role": "assistant", "content": content})

    # Flush any remaining buffered tool_calls
    _flush_assistant(tool_calls_buf, messages)

    return messages


def load_records(data_dir: Path) -> list[dict]:
    """Load all valid (non-error, turn_count > 0) records from JSONL files."""
    records: list[dict] = []
    total = 0
    skipped = 0

    for jsonl_file in sorted(data_dir.glob("*.jsonl")):
        with open(jsonl_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total += 1
                rec = json.loads(line)

                # Skip errored or empty conversations
                if rec.get("error") or rec.get("turn_count", 0) == 0:
                    skipped += 1
                    continue

                records.append(rec)

    print(f"Loaded {len(records)} valid records from {total} total ({skipped} skipped)")
    return records


def record_to_row(rec: dict) -> dict:
    """Transform a raw conversation record into a flat dataset row."""
    env = rec.get("env", {})
    profile = rec.get("profile", {})
    scenario = profile.get("scenario", {})

    messages = _extract_messages(rec.get("agrinet_messages_json", "[]"))

    return {
        "session_id": rec["session_id"],
        "agent_type": "agrinet",
        "scenario_id": scenario.get("id", ""),
        "scenario_category": scenario.get("category", ""),
        "target_language": env.get("target_language", ""),
        "today_date": str(env.get("today_date", ""))[:10],
        "turn_count": rec.get("turn_count", 0),
        "completed": rec.get("completed", False),
        "messages": json.dumps(messages, ensure_ascii=False),
    }


def build_dataset(rows: list[dict]) -> Dataset:
    """Build a HF Dataset from processed rows."""
    features = Features({
        "session_id": Value("string"),
        "agent_type": Value("string"),
        "scenario_id": Value("string"),
        "scenario_category": Value("string"),
        "target_language": Value("string"),
        "today_date": Value("string"),
        "turn_count": Value("int32"),
        "completed": Value("bool"),
        "messages": Value("large_string"),
    })

    columns: dict[str, list] = {k: [] for k in features}
    for row in rows:
        for k in features:
            columns[k].append(row[k])

    return Dataset.from_dict(columns, features=features)


def main():
    parser = argparse.ArgumentParser(description="Prepare HF dataset from synthetic conversations.")
    parser.add_argument("--data-dir", type=str, default=str(DATA_DIR), help="Input JSONL directory")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR), help="Output dataset directory")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)

    # Load and filter
    records = load_records(data_dir)
    if not records:
        print("No valid records found. Exiting.")
        return

    # Transform
    print("Transforming records...")
    rows = [record_to_row(r) for r in records]

    # Build dataset
    print("Building HF Dataset...")
    ds = build_dataset(rows)
    print(ds)

    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    ds.save_to_disk(str(output_dir))
    print(f"\nDataset saved to {output_dir}")

    # Also save as parquet for easy sharing
    parquet_path = output_dir / "data.parquet"
    ds.to_parquet(str(parquet_path))
    print(f"Parquet saved to {parquet_path}")

    # Push to Hugging Face Hub
    print(f"\nPushing to HF Hub: {HF_REPO} ...")
    ds.push_to_hub(HF_REPO)
    print(f"Pushed to https://huggingface.co/datasets/{HF_REPO}")


if __name__ == "__main__":
    main()
