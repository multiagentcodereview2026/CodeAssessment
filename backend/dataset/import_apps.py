"""Normalize and import a local APPS dataset snapshot into the judge database."""
import argparse
import hashlib
import json
import re

from datasets import load_from_disk

import models
from database import Base, SessionLocal, engine


def digest(*values: str) -> str:
    value = "\n".join(values).strip().lower()
    value = re.sub(r"\s+", " ", value)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_json(value: str, fallback):
    try:
        return json.loads(value) if value else fallback
    except (TypeError, json.JSONDecodeError):
        return fallback


def normalize_record(row, public_test_count: int):
    raw_id = row.get("id", row.get("problem_id"))
    if raw_id is None:
        return None
    io_data = parse_json(row["input_output"], {})
    inputs, outputs = io_data.get("inputs", []), io_data.get("outputs", [])
    if not isinstance(inputs, list) or not isinstance(outputs, list) or len(inputs) != len(outputs):
        return None

    tests = []
    for position, (test_input, expected_output) in enumerate(zip(inputs, outputs), start=1):
        if test_input is None or expected_output is None:
            continue
        case_hash = digest(str(test_input), str(expected_output))
        tests.append({
            "id": f"apps-{raw_id}-tc-{position}",
            "position": position,
            "visibility": "PUBLIC" if position <= public_test_count else "HIDDEN",
            "input_data": str(test_input),
            "expected_output": str(expected_output),
            "content_hash": case_hash,
        })
    if not tests:
        return None

    description = str(row["question"]).strip()
    problem_id = f"apps-{raw_id}"
    return {
        "id": problem_id,
        "title": f"APPS Problem {raw_id}",
        "difficulty": str(row.get("difficulty") or "Unrated").title(),
        "category": "Imported APPS",
        "description": description,
        "examples": [{"input": tests[0]["input_data"], "output": tests[0]["expected_output"], "explanation": ""}],
        "constraints": [],
        "starter_codes": {"python": str(row.get("starter_code") or "")},
        "test_cases": [],
        "source_url": str(row.get("url") or ""),
        "source_license": "REVIEW_REQUIRED",
        "content_hash": digest(description),
        "tests": tests,
    }


def import_dataset(dataset_path: str, limit: int, public_test_count: int) -> None:
    dataset = load_from_disk(dataset_path)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    imported = skipped = duplicates = 0
    try:
        for row in dataset.select(range(min(limit, len(dataset)))):
            item = normalize_record(row, public_test_count)
            if not item:
                skipped += 1
                continue
            duplicate = db.query(models.Problem).filter(models.Problem.content_hash == item["content_hash"]).first()
            if duplicate and duplicate.id != item["id"]:
                duplicates += 1
                continue
            problem = db.get(models.Problem, item["id"])
            if not problem:
                problem = models.Problem(id=item["id"])
                db.add(problem)
            for field in ("title", "difficulty", "category", "description", "examples", "constraints", "starter_codes", "test_cases", "source_url", "source_license", "content_hash"):
                setattr(problem, field, item[field])
            db.query(models.ProblemTestCase).filter(models.ProblemTestCase.problem_id == item["id"]).delete()
            for test in item["tests"]:
                db.add(models.ProblemTestCase(problem_id=item["id"], time_limit_seconds=2, memory_limit_mb=256, **test))
            imported += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(json.dumps({"imported": imported, "skipped": skipped, "duplicates": duplicates}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--public-test-count", type=int, default=3)
    args = parser.parse_args()
    import_dataset(args.dataset_path, args.limit, args.public_test_count)
