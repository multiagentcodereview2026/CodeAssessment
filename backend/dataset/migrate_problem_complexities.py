"""Apply target TC/SC metadata from an enriched corpus without replacing data.

This migration preserves students, submissions, problems, and hidden test
cases. It only updates per-problem complexity metadata after human/LLM review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import models
from database import SessionLocal, ensure_problem_complexity_columns


FIELDS = (
    "target_time_complexity",
    "target_space_complexity",
    "complexity_source",
    "complexity_confidence",
    "complexity_reasoning",
)

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


def migrate(dataset_path: str, dry_run: bool = False, batch_size: int = 100) -> None:
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    ensure_problem_complexity_columns()
    db = SessionLocal()
    report = {"updated": 0, "unchanged": 0, "missing": 0, "needs_review": 0}
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                time_target = row.get("target_time_complexity")
                space_target = row.get("target_space_complexity")
                if (
                    row.get("complexity_needs_review")
                    or time_target not in ALLOWED_COMPLEXITIES
                    or space_target not in ALLOWED_COMPLEXITIES
                ):
                    report["needs_review"] += 1
                    continue
                problem = db.get(models.Problem, str(row["problem_id"]))
                if problem is None:
                    report["missing"] += 1
                    continue

                changed = False
                for field in FIELDS:
                    value = row.get(field)
                    if getattr(problem, field) != value:
                        setattr(problem, field, value)
                        changed = True
                report["updated" if changed else "unchanged"] += 1
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
    parser = argparse.ArgumentParser(description="Apply reviewed complexity metadata to PostgreSQL problems.")
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()
    migrate(args.dataset_path, dry_run=args.dry_run, batch_size=args.batch_size)
