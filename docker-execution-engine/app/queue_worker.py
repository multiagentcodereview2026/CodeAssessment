import asyncio
import os
import time

from app.languages import get_language_config
from app.models import SandboxRunResult
from app.models import VERDICT_ACCEPTED
from app.models import VERDICT_COMPILATION_ERROR
from app.models import VERDICT_MEMORY_LIMIT_EXCEEDED
from app.models import VERDICT_OUTPUT_LIMIT_EXCEEDED
from app.models import VERDICT_RUNTIME_ERROR
from app.models import VERDICT_SYSTEM_ERROR
from app.models import VERDICT_TIME_LIMIT_EXCEEDED
from app.models import VERDICT_WRONG_ANSWER
from app.sandbox import execute_in_sandbox
from app.sandbox import prepare_submission_workspace
from app.sandbox import cleanup_submission_workspace
from app.schemas import ExecuteRequest
from app.schemas import ExecutionResultResponse
from app.schemas import FailedTestCaseSummaryResponse
from app.schemas import TestCaseResultResponse


VERDICT_PRECEDENCE = [
    VERDICT_SYSTEM_ERROR,
    VERDICT_COMPILATION_ERROR,
    VERDICT_TIME_LIMIT_EXCEEDED,
    VERDICT_MEMORY_LIMIT_EXCEEDED,
    VERDICT_OUTPUT_LIMIT_EXCEEDED,
    VERDICT_RUNTIME_ERROR,
    VERDICT_WRONG_ANSWER,
    VERDICT_ACCEPTED
]


VERDICT_REASONS = {
    VERDICT_WRONG_ANSWER: "Your output did not match the expected output.",
    VERDICT_RUNTIME_ERROR: "Your program ended with a runtime error.",
    VERDICT_TIME_LIMIT_EXCEEDED: "Your program exceeded the time limit.",
    VERDICT_MEMORY_LIMIT_EXCEEDED: "Your program exceeded the memory limit.",
    VERDICT_OUTPUT_LIMIT_EXCEEDED: "Your program produced too much output.",
    VERDICT_SYSTEM_ERROR: "The test could not be evaluated because of a system error.",
}


def failure_reason(status: str) -> str:
    """Return a fixed, student-safe explanation for a failed verdict."""
    return VERDICT_REASONS.get(status, "This test did not pass.")


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


async def process_execution_request(req: ExecuteRequest) -> ExecutionResultResponse:
    request_started_at = time.monotonic()
    lang_config = get_language_config(req.language)

    if not lang_config:
        return ExecutionResultResponse(
            status=VERDICT_SYSTEM_ERROR,
            runtime_ms=0,
            memory_kb=0,
            compile_success=False,
            compile_stderr=f"Unsupported language: {req.language}",
            tests_total=len(req.test_cases),
            tests_passed=0,
            tests_failed=len(req.test_cases),
            results=[]
        )

    overall_status = VERDICT_ACCEPTED
    total_runtime_ms = 0
    max_memory_kb = 0
    compile_success = True
    compile_stderr = None
    tests_passed = 0
    tests_failed = 0
    results_list = []
    last_failed_case = None

    # Every test keeps its own disposable, network-isolated runner container.
    # Bounded parallelism prevents a 60–200 case submission from waiting for
    # every container serially, without allowing one request to exhaust the host.
    max_parallel = max(1, int(os.getenv("EXECUTION_MAX_CONCURRENT_JOBS", "4")))
    semaphore = asyncio.Semaphore(max_parallel)

    workspace = prepare_submission_workspace(req.code, lang_config) if lang_config.compile_cmd else None

    async def run_case(tc, should_compile: bool = True):
        tc_time_limit = (
            tc.time_limit
            if tc.time_limit
            else req.time_limit
        )

        tc_memory_limit = (
            tc.memory_limit
            if tc.memory_limit
            else req.memory_limit
        )

        async with semaphore:
            res: SandboxRunResult = await asyncio.to_thread(
                execute_in_sandbox,
                code=req.code,
                lang_config=lang_config,
                input_data=tc.input,
                expected_output=tc.expected_output,
                time_limit=tc_time_limit,
                memory_limit=tc_memory_limit,
                workspace=workspace,
                should_compile=should_compile
            )

            # Docker Desktop can occasionally schedule a newly-created runner
            # late under parallel load. Retry one isolated timeout so a tiny,
            # otherwise-correct program is not rejected by host contention.
            # A real slow/infinite solution times out again and remains TLE.
            if res.status == VERDICT_TIME_LIMIT_EXCEEDED:
                res = await asyncio.to_thread(
                    execute_in_sandbox,
                    code=req.code,
                    lang_config=lang_config,
                    input_data=tc.input,
                    expected_output=tc.expected_output,
                    time_limit=tc_time_limit,
                    memory_limit=tc_memory_limit,
                    workspace=workspace,
                    should_compile=False
                )
        return tc, res

    try:
        if workspace:
            # Compile the source exactly once, then reuse the binary for the
            # remaining isolated runners in this submission.
            first_tc = req.test_cases[0]
            first_completed = await run_case(first_tc, should_compile=True)
            if first_completed[1].compile_success and not (req.stop_on_first_failure and first_completed[1].status != VERDICT_ACCEPTED):
                remaining_tasks = [asyncio.create_task(run_case(tc, should_compile=False)) for tc in req.test_cases[1:]]
                completed_cases = [first_completed]
                for task in asyncio.as_completed(remaining_tasks):
                    completed = await task
                    completed_cases.append(completed)
                    if req.stop_on_first_failure and completed[1].status != VERDICT_ACCEPTED:
                        for pending in remaining_tasks:
                            if not pending.done():
                                pending.cancel()
                        break
            else:
                completed_cases = [first_completed]
        else:
            tasks = [asyncio.create_task(run_case(tc)) for tc in req.test_cases]
            completed_cases = []
            for task in asyncio.as_completed(tasks):
                completed = await task
                completed_cases.append(completed)
                if req.stop_on_first_failure and completed[1].status != VERDICT_ACCEPTED:
                    for pending in tasks:
                        if not pending.done():
                            pending.cancel()
                    break
    finally:
        cleanup_submission_workspace(workspace)

    # Tasks finish in timing-dependent order. Return them in the problem's
    # stored order so the first failed case is deterministic in the UI.
    case_positions = {id(tc): position for position, tc in enumerate(req.test_cases)}
    completed_cases.sort(key=lambda completed: case_positions.get(id(completed[0]), len(case_positions)))

    for tc, res in completed_cases:
        case_ordinal = case_positions.get(id(tc), len(case_positions)) + 1

        if not res.compile_success:
            compile_success = False
            compile_stderr = res.compile_stderr
            overall_status = res.status

            results_list.append(
                TestCaseResultResponse(
                    test_case_id=tc.id,
                    status=res.status,
                    runtime_ms=res.runtime_ms,
                    memory_kb=res.memory_kb,
                    is_hidden=tc.is_hidden,
                    input=None if tc.is_hidden else tc.input,
                    expected_output=None if tc.is_hidden else tc.expected_output,
                    actual_output=None,
                    stderr=None if tc.is_hidden else res.stderr
                )
            )

            tests_failed += 1
            continue

        total_runtime_ms += res.runtime_ms
        max_memory_kb = max(max_memory_kb, res.memory_kb)
        overall_status = aggregate_verdict(overall_status, res.status)

        if res.status == VERDICT_ACCEPTED:
            tests_passed += 1
        else:
            tests_failed += 1
            # This summary contains no source test data, so it is safe for
            # public API responses even when the failed test is hidden.
            # Keep overwriting it while iterating in stored order so it is
            # always the last failed test, not the last runner to finish.
            last_failed_case = FailedTestCaseSummaryResponse(
                ordinal=case_ordinal,
                status=res.status,
                reason=failure_reason(res.status),
                is_hidden=tc.is_hidden,
            )

        results_list.append(
            TestCaseResultResponse(
                test_case_id=tc.id,
                status=res.status,
                runtime_ms=res.runtime_ms,
                memory_kb=res.memory_kb,
                is_hidden=tc.is_hidden,
                input=None if tc.is_hidden else tc.input,
                expected_output=None if tc.is_hidden else tc.expected_output,
                actual_output=None if tc.is_hidden else res.actual_output,
                stderr=None if tc.is_hidden else res.stderr
            )
        )

    return ExecutionResultResponse(
        status=overall_status,
        # Individual cases run concurrently. Summing their elapsed times is
        # not a duration and can misleadingly show several minutes. Report
        # the student's real end-to-end judge elapsed time instead.
        runtime_ms=int((time.monotonic() - request_started_at) * 1000),
        memory_kb=max_memory_kb,
        compile_success=compile_success,
        compile_stderr=compile_stderr,
        tests_total=len(req.test_cases),
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        results=results_list,
        last_failed_case=last_failed_case,
    )
