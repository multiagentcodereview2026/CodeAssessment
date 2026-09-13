"""Import the validated portable Newfacade corpus into PostgreSQL.

The normalizer is the source of truth.  Do not import upstream Newfacade JSONL
directly: it contains Python method-call tests, while this application judges
complete stdin/stdout programs in multiple languages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import models
from database import Base, SessionLocal, engine


def digest(*values: str) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def replace_problem_bank(db) -> None:
    """Remove every old problem and its dependent, now-invalid submissions."""
    # Submissions reference problem IDs.  They must be removed before the old
    # problem bank; otherwise PostgreSQL correctly rejects the replacement.
    db.query(models.Submission).delete(synchronize_session=False)
    db.query(models.ProblemTestCase).delete(synchronize_session=False)
    db.query(models.Problem).delete(synchronize_session=False)
    db.commit()


def import_dataset(dataset_path: str, replace: bool, batch_size: int, limit: int | None = None) -> None:
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    imported = public = hidden = skipped = 0
    try:
        if replace:
            replace_problem_bank(db)

        with path.open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                row = json.loads(line)
                problem_id = str(row.get("problem_id") or "")
                if not problem_id or db.get(models.Problem, problem_id):
                    skipped += 1
                    continue

                tags = [str(tag) for tag in row.get("tags") or [] if str(tag).strip()]
                public_tests = list(row.get("public_tests") or [])[:3]
                hidden_tests = list(row.get("hidden_tests") or [])
                if not public_tests or not hidden_tests:
                    skipped += 1
                    continue

                problem = models.Problem(
                    id=problem_id,
                    title=str(row.get("title") or problem_id),
                    difficulty=str(row.get("difficulty") or "Medium"),
                    category=tags[0] if tags else "Algorithms",
                    description=str(row.get("description") or ""),
                    examples=list(row.get("examples") or []),
                    constraints=list(row.get("constraints") or []),
                    starter_codes=dict(row.get("starter_codes") or {}),
                    test_cases=[],
                    source_url=row.get("source_url"),
                    source_license=str(row.get("source_license") or "Newfacade LeetCodeDataset (Apache-2.0)"),
                    content_hash=str(row.get("content_hash") or digest(problem_id, str(row.get("description") or ""))),
                )
                db.add(problem)

                position = 1
                for visibility, cases in (("PUBLIC", public_tests), ("HIDDEN", hidden_tests)):
                    for case in cases:
                        test_input = case.get("input")
                        expected_output = case.get("output")
                        if not isinstance(test_input, str) or not isinstance(expected_output, str):
                            continue
                        db.add(models.ProblemTestCase(
                            id=f"{problem_id}-tc-{position}",
                            problem_id=problem_id,
                            position=position,
                            visibility=visibility,
                            input_data=test_input,
                            expected_output=expected_output,
                            time_limit_seconds=2,
                            memory_limit_mb=256,
                            content_hash=digest(test_input, expected_output),
                        ))
                        position += 1
                        if visibility == "PUBLIC":
                            public += 1
                        else:
                            hidden += 1
                imported += 1
                if imported % batch_size == 0:
                    db.commit()
                    print(json.dumps({"imported": imported, "hidden_cases": hidden}), flush=True)
                if limit is not None and imported >= limit:
                    break
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(json.dumps({"imported": imported, "skipped": skipped, "public_cases": public, "hidden_cases": hidden}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--replace", action="store_true", help="Delete old submissions, cases and problems first.")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--limit", type=int, help="Import only this many rows; useful for isolated validation.")
    args = parser.parse_args()
    import_dataset(args.dataset_path, args.replace, args.batch_size, args.limit)
