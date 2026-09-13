import asyncio
from dataclasses import dataclass

from database import SessionLocal
from execution.languages import get_language_config
from execution.sandbox import execute_in_sandbox
import models


@dataclass
class ExecutionJob:

    submission_id: str
    problem_id: str
    language: str
    code: str
    is_submit: bool


execution_queue: asyncio.Queue[ExecutionJob] = asyncio.Queue()


VERDICT_PRECEDENCE = [
    models.VERDICT_SYSTEM_ERROR,
    models.VERDICT_COMPILATION_ERROR,
    models.VERDICT_TIME_LIMIT_EXCEEDED,
    models.VERDICT_MEMORY_LIMIT_EXCEEDED,
    models.VERDICT_OUTPUT_LIMIT_EXCEEDED,
    models.VERDICT_RUNTIME_ERROR,
    models.VERDICT_WRONG_ANSWER,
    models.VERDICT_ACCEPTED
]


def aggregate_verdict(current_status: str, new_status: str) -> str:
    current_idx = (
        VERDICT_PRECEDENCE.index(current_status)
        if current_status in VERDICT_PRECEDENCE
        else len(VERDICT_PRECEDENCE)
    )

    new_idx = (
        VERDICT_PRECEDENCE.index(new_status)
        if new_status in VERDICT_PRECEDENCE
        else len(VERDICT_PRECEDENCE)
    )

    return (
        current_status
        if current_idx <= new_idx
        else new_status
    )


async def process_job(job: ExecutionJob) -> None:
    db = SessionLocal()

    try:
        submission = (
            db.query(models.Submission)
            .filter(
                models.Submission.submission_id == job.submission_id
            )
            .first()
        )

        if not submission:
            return

        submission.status = "PROCESSING"
        db.commit()

        problem = (
            db.query(models.Problem)
            .filter(
                models.Problem.problem_id == job.problem_id
            )
            .first()
        )

        query = db.query(models.TestCase).filter(
            models.TestCase.problem_id == job.problem_id
        )

        if not job.is_submit:
            query = query.filter(
                models.TestCase.is_hidden == False
            )

        test_cases = query.all()

        lang_config = get_language_config(job.language)

        if not lang_config:
            submission.status = models.VERDICT_SYSTEM_ERROR
            db.commit()
            return

        problem_time_limit = problem.time_limit if problem else None
        problem_memory_limit = problem.memory_limit if problem else None

        overall_status = models.VERDICT_ACCEPTED
        total_runtime_ms = 0
        max_memory_kb = 0
        compile_success = True
        compile_stderr = None
        tests_passed = 0
        tests_failed = 0

        execution_result = models.ExecutionResult(
            submission_id=job.submission_id,
            status="PROCESSING",
            runtime_ms=0,
            memory_kb=0,
            compile_success=True,
            compile_stderr=None,
            tests_total=len(test_cases),
            tests_passed=0,
            tests_failed=0
        )

        db.add(execution_result)
        db.commit()
        db.refresh(execution_result)

        if not test_cases:
            submission.status = models.VERDICT_ACCEPTED
            execution_result.status = models.VERDICT_ACCEPTED
            db.commit()
            return

        for tc in test_cases:
            tc_time_limit = tc.time_limit if tc.time_limit else problem_time_limit
            tc_memory_limit = tc.memory_limit if tc.memory_limit else problem_memory_limit

            res = await asyncio.to_thread(
                execute_in_sandbox,
                code=job.code,
                lang_config=lang_config,
                input_data=tc.input,
                expected_output=tc.expected_output,
                time_limit=tc_time_limit,
                memory_limit=tc_memory_limit
            )

            if not res.compile_success:
                compile_success = False
                compile_stderr = res.compile_stderr
                overall_status = res.status

                tc_res = models.TestCaseResult(
                    execution_result_id=execution_result.id,
                    test_case_id=tc.id,
                    status=res.status,
                    runtime_ms=res.runtime_ms,
                    memory_kb=res.memory_kb,
                    is_hidden=tc.is_hidden,
                    input=tc.input if not tc.is_hidden else None,
                    expected_output=tc.expected_output if not tc.is_hidden else None,
                    actual_output=None,
                    stderr=res.stderr
                )
                db.add(tc_res)
                tests_failed += 1
                break

            total_runtime_ms += res.runtime_ms
            max_memory_kb = max(max_memory_kb, res.memory_kb)
            overall_status = aggregate_verdict(overall_status, res.status)

            if res.status == models.VERDICT_ACCEPTED:
                tests_passed += 1
            else:
                tests_failed += 1

            tc_res = models.TestCaseResult(
                execution_result_id=execution_result.id,
                test_case_id=tc.id,
                status=res.status,
                runtime_ms=res.runtime_ms,
                memory_kb=res.memory_kb,
                is_hidden=tc.is_hidden,
                input=tc.input if not tc.is_hidden else None,
                expected_output=tc.expected_output if not tc.is_hidden else None,
                actual_output=res.actual_output if not tc.is_hidden else None,
                stderr=res.stderr if not tc.is_hidden else None
            )
            db.add(tc_res)

        execution_result.status = overall_status
        execution_result.runtime_ms = total_runtime_ms
        execution_result.memory_kb = max_memory_kb
        execution_result.compile_success = compile_success
        execution_result.compile_stderr = compile_stderr
        execution_result.tests_passed = tests_passed
        execution_result.tests_failed = tests_failed

        submission.status = overall_status

        db.commit()

    except Exception as exc:
        db.rollback()
        try:
            submission = (
                db.query(models.Submission)
                .filter(
                    models.Submission.submission_id == job.submission_id
                )
                .first()
            )
            if submission:
                submission.status = models.VERDICT_SYSTEM_ERROR
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


async def execution_worker() -> None:
    while True:
        try:
            job = await execution_queue.get()
            await process_job(job)
            execution_queue.task_done()
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(1)
