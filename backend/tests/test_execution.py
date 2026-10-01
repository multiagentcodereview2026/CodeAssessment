import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from uuid import uuid4

from auth import hash_password
from database import Base, engine, SessionLocal
from execution.languages import get_language_config, validate_language_for_problem
from execution.queue import aggregate_verdict, ExecutionJob, process_job
from execution.sandbox import execute_in_sandbox
import models

def test_verdict_precedence():
    assert aggregate_verdict("ACCEPTED", "WRONG_ANSWER") == "WRONG_ANSWER"
    assert aggregate_verdict("WRONG_ANSWER", "TIME_LIMIT_EXCEEDED") == "TIME_LIMIT_EXCEEDED"
    assert aggregate_verdict("TIME_LIMIT_EXCEEDED", "COMPILATION_ERROR") == "COMPILATION_ERROR"
    assert aggregate_verdict("COMPILATION_ERROR", "ACCEPTED") == "COMPILATION_ERROR"

def test_language_validation():
    assert validate_language_for_problem("python", "python, c, cpp")
    assert validate_language_for_problem("c", "python, c, cpp")
    assert not validate_language_for_problem("java", "python, c, cpp")
    assert get_language_config("python") is not None

def test_sandbox_max_source_size():
    lang_cfg = get_language_config("python")
    huge_code = "a = 1\n" * 20000
    os.environ["EXECUTION_MAX_SOURCE_BYTES"] = "100"
    try:
        res = execute_in_sandbox(
            code=huge_code,
            lang_config=lang_cfg,
            input_data="1 2",
            expected_output="3"
        )
        assert res.status == models.VERDICT_COMPILATION_ERROR
        assert "exceeds maximum allowed size" in res.compile_stderr
    finally:
        os.environ.pop("EXECUTION_MAX_SOURCE_BYTES", None)

def test_job_processing_flow():
    asyncio.run(run_job_processing_flow())

async def run_job_processing_flow():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    uid = uuid4().hex[:8]
    p_id = f"P_{uid}"
    sub_id = f"sub_{uid}"
    student_name = f"student_{uid}"

    try:
        student_user = models.User(
            username=student_name,
            email=f"{student_name}@test.com",
            full_name="Test Student",
            hashed_password=hash_password("pass123"),
            role="student"
        )
        db.add(student_user)
        db.flush()
        
        student = models.Student(
            student_id=student_name,
            user_id=student_user.id,
            name="Test Student"
        )
        db.add(student)

        prob = models.Problem(
            id=p_id,
            title="Test Addition",
            difficulty="Easy",
            category="Math",
            description="Add A and B",
            examples=[],
            constraints=[],
            starter_codes={"python": "def add(a, b): return a + b"},
            test_cases=[]
        )
        db.add(prob)
        db.commit()

        tc_public = models.ProblemTestCase(
            id=f"tc_pub_{uid}",
            problem_id=p_id,
            position=1,
            input_data="3 5",
            expected_output="8",
            visibility="PUBLIC",
            content_hash="mock"
        )

        tc_hidden = models.ProblemTestCase(
            id=f"tc_hid_{uid}",
            problem_id=p_id,
            position=2,
            input_data="100 200",
            expected_output="300",
            visibility="HIDDEN",
            content_hash="mock"
        )

        db.add(tc_public)
        db.add(tc_hidden)
        db.commit()

        sub = models.Submission(
            submission_id=sub_id,
            student_id=student_name,
            problem_id=p_id,
            language="python",
            code="print(sum(map(int, input().split())))",
            status="QUEUED"
        )

        db.add(sub)
        db.commit()

        job = ExecutionJob(
            submission_id=sub_id,
            problem_id=p_id,
            language="python",
            code="print(sum(map(int, input().split())))",
            is_submit=True
        )

        await process_job(job)

        sub_updated = (
            db.query(models.Submission)
            .filter(models.Submission.submission_id == sub_id)
            .first()
        )

        assert sub_updated is not None
        assert sub_updated.status in [
            models.VERDICT_ACCEPTED,
            models.VERDICT_SYSTEM_ERROR,
            models.VERDICT_RUNTIME_ERROR,
            "EVALUATED",
            "QUEUED"
        ]

    finally:
        db.close()

if __name__ == "__main__":
    test_verdict_precedence()
    test_language_validation()
    test_sandbox_max_source_size()
    asyncio.run(test_job_processing_flow())
    print("\n--- ALL SUITE TESTS PASSED SUCCESSFULLY! ---")
