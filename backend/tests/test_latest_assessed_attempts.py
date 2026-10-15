from datetime import datetime, timedelta
from types import SimpleNamespace

from main import latest_assessed_attempts


def attempt(identifier, score, created_at):
    return SimpleNamespace(
        id=identifier,
        assignment_id=11,
        student_id="student-01",
        problem_id="maximum-two-subarrays",
        status="EVALUATED",
        overall_score=score,
        created_at=created_at,
    )


def test_latest_attempt_replaces_the_previous_score_for_the_same_assignment_problem():
    start = datetime(2026, 10, 13, 10, 0, 0)
    older = attempt(1, 83.3, start)
    newer = attempt(2, 93.3, start + timedelta(minutes=5))

    latest = latest_assessed_attempts([older, newer])

    assert len(latest) == 1
    assert latest[0].overall_score == 93.3
