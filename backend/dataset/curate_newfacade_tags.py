"""Create a non-destructive Newfacade copy with reviewed missing topic tags.

The normalized source corpus is preserved exactly.  This script only fills the
eight records that arrived without tags and writes a separate curated JSONL
file.  Test cases, descriptions, schemas, and source provenance are copied
unchanged.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


# Reviewed from each problem statement.  These are topics for discovery and
# analytics, not a replacement for the per-problem TC/SC target metadata.
TAG_OVERRIDES = {
    "leetcode-3253": ["String", "Dynamic Programming"],
    "leetcode-3469": ["Array", "Dynamic Programming"],
    "leetcode-3496": ["Array", "Greedy"],
    "leetcode-3498": ["String", "Simulation"],
    "leetcode-3499": ["String", "Greedy"],
    "leetcode-3502": ["Array", "Prefix Minimum"],
    "leetcode-3503": ["String", "Dynamic Programming"],
    "leetcode-3504": ["String", "Dynamic Programming"],
}


def curate(source_path: Path, output_path: Path) -> dict[str, int]:
    if not source_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {source_path}")
    if source_path.resolve() == output_path.resolve():
        raise ValueError("Use a new output file; never overwrite the source corpus.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {"problems": 0, "tags_filled": 0, "existing_tags": 0, "unexpected_missing_tags": 0}
    seen_overrides: set[str] = set()

    with source_path.open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as destination:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            problem_id = str(row["problem_id"])
            tags = [str(tag).strip() for tag in row.get("tags") or [] if str(tag).strip()]
            if tags:
                report["existing_tags"] += 1
            elif problem_id in TAG_OVERRIDES:
                row["tags"] = TAG_OVERRIDES[problem_id]
                seen_overrides.add(problem_id)
                report["tags_filled"] += 1
            else:
                report["unexpected_missing_tags"] += 1
            destination.write(json.dumps(row, ensure_ascii=False) + "\n")
            report["problems"] += 1

    missing_overrides = set(TAG_OVERRIDES) - seen_overrides
    if missing_overrides:
        raise ValueError(f"Expected problem IDs not found in source: {sorted(missing_overrides)}")
    if report["unexpected_missing_tags"]:
        raise ValueError(f"Unexpected untagged rows: {report['unexpected_missing_tags']}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fill the reviewed missing Newfacade topic tags into a new JSONL file.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(curate(Path(args.source), Path(args.output)), indent=2))
