"""Verify normalized stdin/stdout cases against Newfacade's original oracle data.

This does not run arbitrary ``completion`` code from the dataset.  Instead it
recreates the portable cases from the original, authoritative ``input_output``
records and compares every input, expected output, and schema with the
normalized corpus.  It is therefore safe to run locally and detects accidental
test-case corruption after curation/enrichment.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from dataset.normalize_newfacade import normalize_row


COMPARED_FIELDS = ("public_tests", "hidden_tests", "parameter_schema", "return_schema", "method")


def load_recreated_oracles(source_paths: list[Path]) -> tuple[dict[str, dict[str, Any]], Counter[str]]:
    expected: dict[str, dict[str, Any]] = {}
    skipped: Counter[str] = Counter()
    for path in source_paths:
        if not path.is_file():
            raise FileNotFoundError(f"Raw dataset not found: {path}")
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                normalized, reason = normalize_row(json.loads(line))
                if normalized is None:
                    skipped[reason] += 1
                elif normalized["problem_id"] in expected:
                    skipped["duplicate_question_id"] += 1
                else:
                    expected[normalized["problem_id"]] = normalized
    return expected, skipped


def verify(source_paths: list[Path], normalized_path: Path) -> dict[str, Any]:
    if not normalized_path.is_file():
        raise FileNotFoundError(f"Normalized dataset not found: {normalized_path}")
    expected, skipped = load_recreated_oracles(source_paths)
    actual = {
        str(row["problem_id"]): row
        for row in (
            json.loads(line)
            for line in normalized_path.open("r", encoding="utf-8")
            if line.strip()
        )
    }
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    mismatches = {
        problem_id: [field for field in COMPARED_FIELDS if expected[problem_id].get(field) != actual[problem_id].get(field)]
        for problem_id in sorted(set(expected) & set(actual))
        if any(expected[problem_id].get(field) != actual[problem_id].get(field) for field in COMPARED_FIELDS)
    }
    report = {
        "raw_oracle_problems": len(expected),
        "normalized_problems": len(actual),
        "verified_test_cases": sum(len(row["public_tests"]) + len(row["hidden_tests"]) for row in expected.values()),
        "missing_problem_ids": missing,
        "unexpected_problem_ids": unexpected,
        "field_mismatches": mismatches,
        "raw_rows_skipped_by_portable_normalizer": dict(skipped),
        "passed": not missing and not unexpected and not mismatches,
    }
    if not report["passed"]:
        raise ValueError(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare normalized cases with Newfacade's original test oracles.")
    parser.add_argument("--raw-source", required=True, nargs="+", help="Raw Newfacade train/test JSONL files")
    parser.add_argument("--normalized", required=True)
    args = parser.parse_args()
    print(json.dumps(verify([Path(path) for path in args.raw_source], Path(args.normalized)), indent=2))
