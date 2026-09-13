"""Import the validated CodeContests JSONL corpus into PostgreSQL.

The JSONL file stays outside the web application image.  This one-shot tool
reads it line-by-line, stores only up to three source-provided public examples,
and stores every source-provided private/generated case as HIDDEN.
"""
import argparse
import hashlib
import json
from pathlib import Path

import models
from database import Base, SessionLocal, engine


def digest(*values: str) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def difficulty(value) -> str:
    """CodeContests exposes numeric difficulty buckets; keep a UI-safe label."""
    try:
        bucket = int(value)
    except (TypeError, ValueError):
        return "Medium"
    if bucket <= 6:
        return "Easy"
    if bucket <= 12:
        return "Medium"
    return "Hard"


def numeric_limit(value, fallback: int) -> int:
    """CodeContests may store a limit as a scalar or per-language mapping."""
    if isinstance(value, dict):
        value = next((item for item in value.values() if item is not None), None)
    if isinstance(value, (list, tuple)):
        value = next((item for item in value if item is not None), None)
    try:
        result = int(float(value))
        return result if result > 0 else fallback
    except (TypeError, ValueError):
        return fallback


def import_dataset(dataset_path: str, batch_size: int = 25) -> None:
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    imported = skipped = hidden_count = public_count = 0
    try:
        with path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                problem_id = str(row.get("problem_id") or "")
                statement = str(row.get("description") or "").strip()
                hidden_tests = row.get("hidden_tests") or []
                if not problem_id or not statement or not hidden_tests:
                    skipped += 1
                    continue

                # A cancelled Docker session can be resumed safely: committed
                # problems are immutable for this import and are not rewritten.
                if db.get(models.Problem, problem_id) is not None:
                    skipped += 1
                    continue

                tags = [str(tag) for tag in (row.get("tags") or []) if str(tag).strip()]
                public_tests = (row.get("public_tests") or [])[:3]
                problem = db.get(models.Problem, problem_id)
                if problem is None:
                    problem = models.Problem(id=problem_id)
                    db.add(problem)

                examples = [
                    {"input": str(case.get("input") or ""), "output": str(case.get("output") or ""), "explanation": ""}
                    for case in public_tests
                    if case.get("input") is not None and case.get("output") is not None
                ]
                problem.title = str(row.get("title") or problem_id)
                problem.difficulty = difficulty(row.get("difficulty"))
                problem.category = tags[0] if tags else "CodeContests"
                problem.description = statement
                problem.examples = examples
                problem.constraints = []
                problem.starter_codes = {}
                problem.test_cases = []  # Relational records below are authoritative.
                problem.source_url = row.get("source_url")
                problem.source_license = "CodeContests source dataset; review source terms before production use"
                # The extraction step already removes duplicate test inputs. Keep
                # a source-key component here so distinct original problems with
                # similar statements do not violate the database unique index.
                problem.content_hash = digest(problem_id, statement)

                db.query(models.ProblemTestCase).filter(
                    models.ProblemTestCase.problem_id == problem_id
                ).delete(synchronize_session=False)

                position = 1
                for visibility, cases in (("PUBLIC", public_tests), ("HIDDEN", hidden_tests)):
                    for case in cases:
                        test_input, expected = case.get("input"), case.get("output")
                        if not isinstance(test_input, str) or not isinstance(expected, str):
                            continue
                        db.add(models.ProblemTestCase(
                            id=f"{problem_id}-tc-{position}",
                            problem_id=problem_id,
                            position=position,
                            visibility=visibility,
                            input_data=test_input,
                            expected_output=expected,
                            time_limit_seconds=numeric_limit(row.get("time_limit"), 2),
                            memory_limit_mb=max(1, numeric_limit(row.get("memory_limit"), 256 * 1024 * 1024) // (1024 * 1024)),
                            content_hash=digest(test_input, expected),
                        ))
                        position += 1
                        if visibility == "PUBLIC":
                            public_count += 1
                        else:
                            hidden_count += 1
                imported += 1
                if imported % batch_size == 0:
                    db.commit()
                    print(json.dumps({"imported": imported, "line": line_number}), flush=True)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(json.dumps({"imported": imported, "skipped": skipped, "public_cases": public_count, "hidden_cases": hidden_count}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--batch-size", type=int, default=25)
    arguments = parser.parse_args()
    import_dataset(arguments.dataset_path, arguments.batch_size)
