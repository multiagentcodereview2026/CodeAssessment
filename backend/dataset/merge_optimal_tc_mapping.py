"""Merge a reviewed TC mapping CSV into a separate problem-bank JSONL file.

The mapping may use exact multi-variable expressions such as ``O(m * n)`` or
``O(log(min(m, n)))``.  They are retained verbatim in candidate fields.  The
platform's final target fields are deliberately not overwritten: its current
scoring validator uses a small one-variable bucket vocabulary and must not
silently collapse an exact expression into a different claim.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = {"problem_no", "title", "optimal_tc", "current_space_tc"}


def read_mapping(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"TC mapping CSV not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Mapping CSV lacks columns: {sorted(missing)}")
        mapping: dict[str, dict[str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            problem_id = str(row.get("problem_no") or "").strip()
            title = str(row.get("title") or "").strip()
            time_value = str(row.get("optimal_tc") or "").strip()
            space_value = str(row.get("current_space_tc") or "").strip()
            if not problem_id or not title or not time_value or not space_value:
                raise ValueError(f"Mapping row {line_number} has a blank required value.")
            if problem_id in mapping:
                raise ValueError(f"Mapping contains duplicate problem id: {problem_id}")
            mapping[problem_id] = {
                "title": title,
                "optimal_tc": time_value,
                "current_space_tc": space_value,
            }
    return mapping


def merge(bank_path: Path, mapping_path: Path, output_path: Path) -> dict[str, Any]:
    if not bank_path.is_file():
        raise FileNotFoundError(f"Problem bank not found: {bank_path}")
    if bank_path.resolve() == output_path.resolve():
        raise ValueError("Use a new output path; never overwrite the source bank.")

    mapping = read_mapping(mapping_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report: Counter[str] = Counter()
    seen: set[str] = set()

    with bank_path.open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as destination:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            problem_id = str(row.get("problem_id") or "")
            report["problems"] += 1
            current_time = (row.get("reference_solution_complexity") or {}).get("observed_time_complexity")
            current_space = (row.get("reference_solution_complexity") or {}).get("observed_space_complexity")
            supplied = mapping.get(problem_id)

            if supplied:
                seen.add(problem_id)
                if supplied["title"] != str(row.get("title") or ""):
                    raise ValueError(f"Title mismatch for {problem_id}: mapping does not match bank title.")
                if current_time:
                    raise ValueError(f"{problem_id} already has observed TC; mapping must only fill pending rows.")
                if supplied["current_space_tc"] != current_space:
                    raise ValueError(f"Space mismatch for {problem_id}: mapping does not match bank evidence.")
                row["candidate_time_complexity"] = supplied["optimal_tc"]
                row["candidate_space_complexity"] = supplied["current_space_tc"]
                row["candidate_complexity_source"] = "optimal_tc_mapping_tmp.csv"
                row["candidate_complexity_status"] = "exact-expression-pending-canonical-target-review"
                report["mapped_pending_time_rows"] += 1
            else:
                row["candidate_time_complexity"] = current_time
                row["candidate_space_complexity"] = current_space
                row["candidate_complexity_source"] = "local-reference-solution-evidence"
                row["candidate_complexity_status"] = "reference-evidence-pending-optimal-target-review"
                report["retained_reference_rows"] += 1

            # Keep final target fields untouched.  They remain the gate used
            # by import_newfacade.py and the assessment scoring pipeline.
            destination.write(json.dumps(row, ensure_ascii=False) + "\n")

    unmapped = sorted(set(mapping) - seen)
    if unmapped:
        raise ValueError(f"Mapping problem IDs were not found in bank: {unmapped[:20]}")
    report["mapped_rows"] = len(seen)
    report["candidate_time_available"] = report["problems"]
    report["candidate_space_available"] = report["problems"]
    report["output_path"] = str(output_path)
    return dict(report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge a validated optimal-TC mapping into a new problem bank.")
    parser.add_argument("--bank", required=True)
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(merge(Path(args.bank), Path(args.mapping), Path(args.output)), indent=2, ensure_ascii=False))
