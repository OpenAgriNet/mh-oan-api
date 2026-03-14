"""
Prepare suggestions data for the HF dataset.

Reads suggestions JSONL, formats into the same schema as the main dataset,
and appends to the existing HF repo.

Usage:
    python -m synthetic.prepare_suggestions_dataset [--data-dir data/suggestions] [--push]
"""

import argparse
import json
from pathlib import Path

from datasets import Dataset, Features, Value, concatenate_datasets, load_from_disk


SUGGESTIONS_DIR = Path("data/suggestions")
MAIN_DATASET_DIR = Path("data/hf_dataset")
HF_REPO = "kenpath/mh-synthetic-v1"

FEATURES = Features({
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


def load_suggestions(data_dir: Path) -> list[dict]:
    """Load suggestions records from JSONL files."""
    records = []
    for jsonl_file in sorted(data_dir.glob("*.jsonl")):
        with open(jsonl_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    print(f"Loaded {len(records)} suggestions records")
    return records


def suggestion_to_row(rec: dict) -> dict:
    """Convert a suggestions record into the common dataset row format."""
    # Build simple messages: user (the conversation context) -> assistant (suggestions list)
    messages = [
        {"role": "user", "content": rec["suggestions_input"]},
        {"role": "assistant", "content": json.dumps(rec["suggestions"], ensure_ascii=False)},
    ]

    return {
        "session_id": rec["id"],
        "agent_type": "suggestions",
        "scenario_id": "",
        "scenario_category": "",
        "target_language": rec.get("target_language", ""),
        "today_date": "",
        "turn_count": 1,
        "completed": True,
        "messages": json.dumps(messages, ensure_ascii=False),
    }


def build_dataset(rows: list[dict]) -> Dataset:
    """Build a HF Dataset from rows."""
    columns: dict[str, list] = {k: [] for k in FEATURES}
    for row in rows:
        for k in FEATURES:
            columns[k].append(row[k])
    return Dataset.from_dict(columns, features=FEATURES)


def main():
    parser = argparse.ArgumentParser(description="Prepare suggestions for HF dataset.")
    parser.add_argument("--data-dir", type=str, default=str(SUGGESTIONS_DIR))
    parser.add_argument("--push", action="store_true", help="Push combined dataset to HF Hub")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    records = load_suggestions(data_dir)
    if not records:
        print("No suggestions records found.")
        return

    print("Transforming records...")
    rows = [suggestion_to_row(r) for r in records]

    print("Building suggestions dataset...")
    suggestions_ds = build_dataset(rows)
    print(f"Suggestions: {suggestions_ds}")

    # Load existing main dataset and combine
    if MAIN_DATASET_DIR.exists():
        print(f"\nLoading existing dataset from {MAIN_DATASET_DIR}...")
        main_ds = load_from_disk(str(MAIN_DATASET_DIR))
        # Filter out old suggestions rows before appending
        main_ds = main_ds.filter(lambda x: x["agent_type"] != "suggestions")
        combined = concatenate_datasets([main_ds, suggestions_ds])
        print(f"Combined: {combined}")
    else:
        combined = suggestions_ds

    # Save (use temp dir to avoid overwrite-self error)
    import shutil
    tmp_dir = MAIN_DATASET_DIR.with_name("hf_dataset_tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    combined.save_to_disk(str(tmp_dir))
    if MAIN_DATASET_DIR.exists():
        shutil.rmtree(MAIN_DATASET_DIR)
    tmp_dir.rename(MAIN_DATASET_DIR)
    print(f"\nDataset saved to {MAIN_DATASET_DIR}")

    parquet_path = MAIN_DATASET_DIR / "data.parquet"
    combined.to_parquet(str(parquet_path))
    print(f"Parquet saved to {parquet_path}")

    if args.push:
        print(f"\nPushing to HF Hub: {HF_REPO} ...")
        combined.push_to_hub(HF_REPO)
        print(f"Pushed to https://huggingface.co/datasets/{HF_REPO}")
    else:
        print("\nSkipping HF push (use --push to upload)")


if __name__ == "__main__":
    main()
