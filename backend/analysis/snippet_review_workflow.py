"""Create and apply independent snippet-complexity reviews."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _rows(path: str) -> list[dict[str, Any]]:
    file = Path(path)
    if not file.is_file():
        raise IsADirectoryError(f"Dataset must be a JSONL file: {file}")
    return [json.loads(line) for line in file.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def build_queue(dataset: str, output: str) -> dict[str, int]:
    rows = _rows(dataset)
    target = Path(output)
    with target.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({
                "problem_id": row.get("problem_id"),
                "solution_id": row.get("solution_id"),
                "language": row.get("language"),
                "approach": row.get("approach"),
                "source": row.get("source") or row.get("reference_source") or "",
                "current_time": row.get("snippet_time_complexity"),
                "current_space": row.get("snippet_space_complexity"),
                "corrected_time": None,
                "corrected_space": None,
                "review_status": "pending",
                "reviewer": None,
                "review_notes": None,
            }) + "\n")
    return {"rows": len(rows), "output": output}


def apply_review(queue: str, original: str, output: str) -> dict[str, int]:
    review_rows = _rows(queue)
    original_rows = _rows(original)
    reviews = {str(row.get("solution_id")): row for row in review_rows}
    missing = []
    corrected = 0
    result = []
    for row in original_rows:
        key = str(row.get("solution_id"))
        review = reviews.get(key)
        if not review or review.get("review_status") != "reviewed":
            missing.append(key)
            continue
        time_value = review.get("corrected_time")
        space_value = review.get("corrected_space")
        if not time_value or not space_value or not review.get("reviewer"):
            missing.append(key)
            continue
        updated = dict(row)
        updated["snippet_time_complexity"] = time_value
        updated["snippet_space_complexity"] = space_value
        updated["ground_truth_source"] = "independent_snippet_review"
        updated["review_status"] = "reviewed"
        updated["reviewer"] = review["reviewer"]
        updated["review_notes"] = review.get("review_notes")
        result.append(updated)
        corrected += 1
    if missing:
        raise ValueError(f"Unreviewed or incomplete rows: {len(missing)}")
    Path(output).write_text("\n".join(json.dumps(row) for row in result) + "\n", encoding="utf-8")
    return {"rows": len(result), "corrected": corrected, "output": output}


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    queue = sub.add_parser("build-queue")
    queue.add_argument("--dataset", required=True)
    queue.add_argument("--output", required=True)
    apply = sub.add_parser("apply")
    apply.add_argument("--queue", required=True)
    apply.add_argument("--original", required=True)
    apply.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "build-queue":
        result = build_queue(args.dataset, args.output)
    else:
        result = apply_review(args.queue, args.original, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

