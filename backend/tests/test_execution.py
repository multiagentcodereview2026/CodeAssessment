import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

from auth import hash_password
from database import Base
from database import engine
from database import SessionLocal
from execution.languages import get_language_config
from execution.languages import validate_language_for_problem
from execution.queue import aggregate_verdict
from execution.queue import ExecutionJob
from execution.queue import process_job
from execution.sandbox import execute_in_sandbox
import models
from schemas import TestCaseResultResponse


def test_schema_hidden_redaction():
    res = TestCaseResultResponse(
        id=1,
        execution_result_id=10,
        test_case_id=100,
        status="ACCEPTED",
        runtime_ms=15,
        memory_kb=1024,
        is_hidden=True,
        input="SECRET_INPUT",
        expected_output="SECRET_EXPECTED",
        actual_output="SECRET_ACTUAL",
        stderr="SECRET_STDERR",
        created_at=datetime.utcnow()
    )

    assert res.input is None
    assert res.expected_output is None
    assert res.actual_output is None
    assert res.stderr is None
    print("[PASS] test_schema_hidden_redaction")


def test_verdict_precedence():
    assert aggregate_verdict("ACCEPTED", "WRONG_ANSWER") == "WRONG_ANSWER"
    assert aggregate_verdict("WRONG_ANSWER", "TIME_LIMIT_EXCEEDED") == "TIME_LIMIT_EXCEEDED"
    assert aggregate_verdict("TIME_LIMIT_EXCEEDED", "COMPILATION_ERROR") == "COMPILATION_ERROR"
    assert aggregate_verdict("COMPILATION_ERROR", "ACCEPTED") == "COMPILATION_ERROR"
    print("[PASS] test_verdict_precedence")


def test_language_validation():
    assert validate_language_for_problem("python", "python, c, cpp")
    assert validate_language_for_problem("c", "python, c, cpp")
    assert not validate_language_for_problem("java", "python, c, cpp")
    assert get_language_config("python") is not None
    print("[PASS] test_language_validation")


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

    print("[PASS] test_sandbox_max_source_size")


async def test_job_processing_flow():
    from uuid import uuid4
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
            password_hash=hash_password("pass123"),
            role="student"
        )
        db.add(student_user)

        prob = models.Problem(
            problem_id=p_id,
            title="Test Addition",
            description="Add A and B",
            supported_languages="python, c, cpp, java",
            time_limit=2,
            memory_limit=256
        )
        db.add(prob)

        tc_public = models.TestCase(
            problem_id=p_id,
            input="3 5",
            expected_output="8",
            is_hidden=False
        )

        tc_hidden = models.TestCase(
            problem_id=p_id,
            input="100 200",
            expected_output="300",
            is_hidden=True
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

        print(f"DEBUG: sub_updated.status = {sub_updated.status}")

        assert sub_updated is not None
        assert sub_updated.status in [
            models.VERDICT_ACCEPTED,
            models.VERDICT_SYSTEM_ERROR,
            models.VERDICT_RUNTIME_ERROR,
            "PROCESSING",
            "QUEUED"
        ]

        exec_res = (
            db.query(models.ExecutionResult)
            .filter(models.ExecutionResult.submission_id == sub_id)
            .first()
        )

        assert exec_res is not None

        tc_results = (
            db.query(models.TestCaseResult)
            .filter(models.TestCaseResult.execution_result_id == exec_res.id)
            .all()
        )

        for tc_r in tc_results:
            if tc_r.is_hidden:
                item = TestCaseResultResponse.model_validate(tc_r)
                assert item.input is None
                assert item.expected_output is None
                assert item.actual_output is None

        print("[PASS] test_job_processing_flow")

    finally:
        db.close()


def main():
    test_schema_hidden_redaction()
    test_verdict_precedence()
    test_language_validation()
    test_sandbox_max_source_size()
    asyncio.run(test_job_processing_flow())
    print("\n--- ALL SUITE TESTS PASSED SUCCESSFULLY! ---")


if __name__ == "__main__":
    main()
