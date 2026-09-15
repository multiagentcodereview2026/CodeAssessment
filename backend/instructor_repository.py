"""Persistent copies of the built-in instructor assignments.

Definitions are seeded only when an assignment is absent. Existing assignments,
their judge data and submissions are never replaced during an application restart.
"""

import copy
import hashlib
import json

from sqlalchemy.orm import Session

import models
from instructor_definitions import INSTRUCTOR_PROBLEMS


ASSIGNMENTS = {definition["id"]: definition for definition in INSTRUCTOR_PROBLEMS}
INSTRUCTOR_PROBLEM_IDS = tuple(ASSIGNMENTS)
LEGACY_INSTRUCTOR_ALIASES = {
    definition["slug"]: definition["id"] for definition in INSTRUCTOR_PROBLEMS
}


def canonical_problem_id(problem_id: str) -> str:
    return LEGACY_INSTRUCTOR_ALIASES.get(problem_id, problem_id)


def assignment_metadata(problem_id: str, db: Session | None = None) -> dict:
    definition = ASSIGNMENTS.get(problem_id)
    if definition is not None:
        return {
            "is_instructor_assigned": True,
            "course_code": definition["course_code"],
            "due_date": definition["due_date"],
        }
    assignment = db.get(models.InstructorAssignment, problem_id) if db else None
    if assignment is None:
        return {}
    return {
        "is_instructor_assigned": True,
        "course_code": assignment.course_code,
        "due_date": assignment.due_date,
    }


def provision_instructor_problems(db: Session) -> int:
    """Insert missing assignments and cases atomically; return the number created."""
    created = 0
    for problem_id, definition in ASSIGNMENTS.items():
        if db.get(models.Problem, problem_id) is not None:
            continue

        cases = definition["test_cases"]
        problem = models.Problem(
            id=problem_id,
            title=definition["title"],
            difficulty=definition["difficulty"],
            category=definition["category"],
            description=definition["description"],
            examples=copy.deepcopy(definition["examples"]),
            constraints=copy.deepcopy(definition["constraints"]),
            starter_codes=copy.deepcopy(definition["starter_codes"]),
            # The normalized table below is the authoritative judge data.
            test_cases=copy.deepcopy([case for case in cases if not case["is_hidden"]][:3]),
            source_url=definition.get("source_url"),
            source_license=definition.get("source_license"),
            content_hash=hashlib.sha256(f"instructor-assignment:{problem_id}".encode()).hexdigest(),
        )
        db.add(problem)
        db.flush()
        for position, case in enumerate(cases, start=1):
            case_hash = hashlib.sha256(json.dumps(
                [case["input"], case["expected_output"]], ensure_ascii=False
            ).encode()).hexdigest()
            db.add(models.ProblemTestCase(
                id=f"{problem_id}-case-{position}",
                problem_id=problem_id,
                position=position,
                visibility="HIDDEN" if case["is_hidden"] else "PUBLIC",
                input_data=case["input"],
                expected_output=case["expected_output"],
                time_limit_seconds=case.get("time_limit", 2),
                memory_limit_mb=case.get("memory_limit", 256),
                content_hash=case_hash,
            ))
        created += 1
    db.commit()
    return created


def load_problem_cases(db: Session, problem: models.Problem, *, public_only: bool = False) -> list:
    """Load canonical server-side tests, retaining support for older JSON records."""
    query = db.query(models.ProblemTestCase).filter(
        models.ProblemTestCase.problem_id == problem.id
    )
    if public_only:
        query = query.filter(models.ProblemTestCase.visibility == "PUBLIC")
    query = query.order_by(models.ProblemTestCase.position)
    if public_only:
        query = query.limit(3)
    records = query.all()
    if records:
        return [{
            "id": case.id,
            "input": case.input_data,
            "expected_output": case.expected_output,
            "is_hidden": case.visibility == "HIDDEN",
            "time_limit": case.time_limit_seconds,
            "memory_limit": case.memory_limit_mb,
        } for case in records]

    cases = problem.test_cases
    if isinstance(cases, str):
        try:
            cases = json.loads(cases)
        except (TypeError, ValueError):
            return []
    if not isinstance(cases, list):
        return []
    cases = [case for case in cases if isinstance(case, dict)
             and "input" in case and "expected_output" in case]
    if public_only:
        return [case for case in cases if not case.get("is_hidden", False)][:3]
    return cases
