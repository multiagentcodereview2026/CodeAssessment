"""Merge saved APPS batches into one canonical, exact-deduplicated dataset."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from datasets import Dataset, load_from_disk


FIELDS = ["id", "question", "solutions", "input_output", "difficulty", "url", "starter_code"]


def normalized(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def duplicate_key(row: dict) -> str:
    # Statement plus source URL avoids merging different problems that happen
    # to share a short/common title.
    payload = f"{normalized(row['url'])}\n{normalized(row['question'])}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_row(row: dict) -> dict:
    raw_id = row.get("id", row.get("problem_id"))
    if raw_id is None:
        raise ValueError("Dataset row has neither id nor problem_id")
    return {
        "id": int(raw_id),
        "question": str(row.get("question") or ""),
        "solutions": str(row.get("solutions") or ""),
        "input_output": str(row.get("input_output") or ""),
        "difficulty": str(row.get("difficulty") or ""),
        "url": str(row.get("url") or ""),
        "starter_code": str(row.get("starter_code") or ""),
    }


def merge(input_root: str, output_path: str) -> None:
    root = Path(input_root)
    batch_paths = sorted(
        path for path in root.iterdir()
        if path.is_dir() and path.name.startswith("apps-") and path.name != Path(output_path).name
    )
    if not batch_paths:
        raise ValueError("No saved APPS batches found")

    seen, records, source_counts = set(), [], {}
    for batch_path in batch_paths:
        batch = load_from_disk(str(batch_path))
        source_counts[batch_path.name] = len(batch)
        for row in batch:
            record = canonical_row(row)
            key = duplicate_key(record)
            if key in seen:
                continue
            seen.add(key)
            records.append(record)

    records.sort(key=lambda row: row["id"])
    merged = Dataset.from_list(records)
    merged.save_to_disk(output_path)
    report = {
        "source_batches": source_counts,
        "input_rows": sum(source_counts.values()),
        "unique_rows": len(records),
        "duplicates_removed": sum(source_counts.values()) - len(records),
        "fields": FIELDS,
    }
    Path(output_path, "merge_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--output-path", required=True)
    args = parser.parse_args()
    merge(args.input_root, args.output_path)
