"""Validate that a curated problem bank is complete enough to become main data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_COMPLEXITIES = {
    "O(1)",
    "O(log n)",
    "O(n)",
    "O(n log n)",
    "O(n^2)",
    "O(n^3)",
    "O(2^n)",
    "O(n!)",
}


def validate(dataset_path: Path) -> dict[str, Any]:
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    problems = incomplete = invalid = review_required = 0
    examples: list[dict[str, str]] = []
    with dataset_path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            problems += 1
            time_value = row.get("target_time_complexity")
            space_value = row.get("target_space_complexity")
            issue = None
            if row.get("complexity_needs_review"):
                review_required += 1
                issue = "needs_review"
            elif not time_value or not space_value:
                incomplete += 1
                issue = "missing_target"
            elif time_value not in ALLOWED_COMPLEXITIES or space_value not in ALLOWED_COMPLEXITIES:
                invalid += 1
                issue = "unsupported_target"
            if issue and len(examples) < 25:
                examples.append({"problem_id": str(row.get("problem_id")), "issue": issue})
    report = {
        "problems": problems,
        "complete_reviewed_targets": problems - incomplete - invalid - review_required,
        "missing_targets": incomplete,
        "invalid_targets": invalid,
        "needs_review": review_required,
        "examples": examples,
        "passed": problems > 0 and not incomplete and not invalid and not review_required,
    }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify that every main-bank problem has reviewed optimal TC/SC.")
    parser.add_argument("--dataset-path", required=True)
    args = parser.parse_args()
    report = validate(Path(args.dataset_path))
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit("TC/SC dataset is incomplete; it cannot become the main problem bank yet.")
