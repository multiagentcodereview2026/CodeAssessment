"""Read-only validator for problem-bank TC/SC benchmark targets.

Usage (from the backend container or with backend on PYTHONPATH)::

    python dataset/validate_complexity_catalog.py PATH/TO/problem-bank.jsonl \
        --start 0 --count 60

The validator never runs code, creates submissions, imports data, or reads a
test case.  It only verifies that the stored target strings can be projected
into the platform's fixed ten-level complexity ladder.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scoring.complexity import TIME_COMPLEXITY_LEVELS, normalize_complexity


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on line {line_number}: {error.msg}") from error
            if not isinstance(record, dict):
                raise ValueError(f"Line {line_number} is not a JSON object")
            rows.append(record)
    return rows


def validate_record(record: dict[str, Any]) -> tuple[str, str, str, str, str]:
    raw_time = record.get("target_time_complexity") or ""
    raw_space = record.get("target_space_complexity") or ""
    time_bucket = normalize_complexity(raw_time)
    space_bucket = normalize_complexity(raw_space)
    status = (
        "SCORABLE"
        if time_bucket in TIME_COMPLEXITY_LEVELS and space_bucket in TIME_COMPLEXITY_LEVELS
        else "REVIEW_REQUIRED"
    )
    return (
        str(record.get("problem_id") or ""),
        str(record.get("title") or ""),
        str(time_bucket or ""),
        str(space_bucket or ""),
        status,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bank", type=Path, help="Path to the JSONL problem bank")
    parser.add_argument("--start", type=int, default=0, help="Zero-based first record")
    parser.add_argument("--count", type=int, default=60, help="Number of records to validate")
    arguments = parser.parse_args()

    if arguments.start < 0 or arguments.count <= 0:
        parser.error("--start must be non-negative and --count must be positive")

    batch = load_rows(arguments.bank)[arguments.start : arguments.start + arguments.count]
    print("problem_id\ttitle\ttime_bucket\tspace_bucket\tstatus")
    scorable = 0
    for record in batch:
        row = validate_record(record)
        print("\t".join(row))
        scorable += row[-1] == "SCORABLE"

    print(f"SUMMARY\t{scorable}/{len(batch)} scorable\t{len(batch) - scorable} review-required")
    return 0 if scorable == len(batch) else 2


if __name__ == "__main__":
    raise SystemExit(main())
