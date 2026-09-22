"""Apply a regenerated Newfacade stdin/stdout corpus without deleting history.

The original import encoded every string as ``byte_length`` plus a raw line.
This migration updates only existing problem metadata and testcase payloads
from a regenerated corpus where strings are raw lines.  It intentionally does
not recreate tables or delete submissions, students, or problem IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import models
from database import SessionLocal, ensure_problem_complexity_columns


def digest(*values: str) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def migrate(dataset_path: str, dry_run: bool = False, batch_size: int = 50) -> None:
    source_path = Path(dataset_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {source_path}")

    ensure_problem_complexity_columns()
    db = SessionLocal()
    report = {"updated": 0, "unchanged": 0, "missing": 0, "case_count_mismatch": 0}
    try:
        with source_path.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                row = json.loads(line)
                problem_id = str(row["problem_id"])
                problem = db.get(models.Problem, problem_id)
                if problem is None:
                    report["missing"] += 1
                    continue

                desired_cases = [
                    (visibility, case)
                    for visibility, cases in (("PUBLIC", row.get("public_tests") or []), ("HIDDEN", row.get("hidden_tests") or []))
                    for case in cases
                ]
                stored_cases = (
                    db.query(models.ProblemTestCase)
                    .filter(models.ProblemTestCase.problem_id == problem_id)
                    .order_by(models.ProblemTestCase.position)
                    .all()
                )
                if len(desired_cases) != len(stored_cases):
                    report["case_count_mismatch"] += 1
                    continue

                changed = False
                for stored, (visibility, desired) in zip(stored_cases, desired_cases):
                    input_data = str(desired["input"])
                    expected_output = str(desired["output"])
                    if (
                        stored.visibility != visibility
                        or stored.input_data != input_data
                        or stored.expected_output != expected_output
                    ):
                        changed = True
                        stored.visibility = visibility
                        stored.input_data = input_data
                        stored.expected_output = expected_output
                        stored.content_hash = digest(input_data, expected_output)

                description = str(row.get("description") or "")
                examples = list(row.get("examples") or [])
                starter_codes = dict(row.get("starter_codes") or {})
                if problem.description != description:
                    changed = True
                    problem.description = description
                if problem.examples != examples:
                    changed = True
                    problem.examples = examples
                if problem.starter_codes != starter_codes:
                    changed = True
                    problem.starter_codes = starter_codes

                complexity_values = {
                    "target_time_complexity": row.get("target_time_complexity"),
                    "target_space_complexity": row.get("target_space_complexity"),
                    "complexity_source": row.get("complexity_source"),
                    "complexity_confidence": row.get("complexity_confidence"),
                    "complexity_reasoning": row.get("complexity_reasoning"),
                }
                for field, value in complexity_values.items():
                    if getattr(problem, field) != value:
                        changed = True
                        setattr(problem, field, value)
                if changed:
                    problem.content_hash = str(row.get("content_hash") or digest(problem_id, description))
                    report["updated"] += 1
                else:
                    report["unchanged"] += 1

                if not dry_run and (report["updated"] + report["unchanged"]) % batch_size == 0:
                    db.commit()

        if dry_run:
            db.rollback()
        else:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()
    migrate(args.dataset_path, dry_run=args.dry_run, batch_size=args.batch_size)
