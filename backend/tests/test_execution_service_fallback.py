import asyncio

import pytest

from docker_runner import executor


def test_engine_sandbox_unavailable_response_is_retryable(monkeypatch):
    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {
                "status": "SYSTEM_ERROR",
                "compile_success": False,
                "compile_stderr": "Docker execution sandbox is unavailable; student code was not run.",
                "results": [],
            }

    monkeypatch.setattr(executor.requests, "post", lambda *_args, **_kwargs: Response())

    assert executor._sync_request_docker({"code": "int main() {}"}) is None


def test_backend_output_comparison_accepts_nested_rows_as_whitespace_tokens():
    assert executor.compare_outputs("1 2\n3 10\n12 16\n", "1 2 3 10 12 16")
    assert not executor.compare_outputs("1 2\n3 10\n12 16", "1 2 3 10 12 17")


@pytest.mark.parametrize("language", ["python", "cpp", "java"])
def test_runner_outage_never_executes_student_code_on_backend(monkeypatch, language):
    calls = 0

    def unavailable_engine(_payload):
        nonlocal calls
        calls += 1
        return None

    original_sleep = executor.asyncio.sleep

    async def no_wait(_seconds):
        await original_sleep(0)

    monkeypatch.setattr(executor, "_sync_request_docker", unavailable_engine)
    monkeypatch.setattr(executor.asyncio, "sleep", no_wait)

    result = asyncio.run(executor.execute_code_sandboxed(
        source_code="print(1)" if language == "python" else "int main() { return 0; }",
        language=language,
        test_cases=[{"input": "", "expected_output": "1"}],
    ))

    assert calls == 3
    assert result["compile_status"] == "unavailable"
    assert result["execution_status"] == "system_error"
    assert "temporarily unavailable" in result["compile_error"]


def test_temporary_engine_sandbox_result_retries_before_scoring(monkeypatch):
    calls = 0

    def transient_then_accepted(_payload):
        nonlocal calls
        calls += 1
        if calls == 1:
            return None
        return {
            "status": "ACCEPTED",
            "runtime_ms": 1,
            "memory_kb": 0,
            "compile_success": True,
            "compile_stderr": None,
            "tests_total": 1,
            "tests_passed": 1,
            "tests_failed": 0,
            "results": [{
                "status": "ACCEPTED",
                "actual_output": "1\\n",
                "expected_output": "1\\n",
                "stderr": "",
            }],
        }

    original_sleep = executor.asyncio.sleep

    async def no_wait(_seconds):
        await original_sleep(0)

    monkeypatch.setattr(executor, "_sync_request_docker", transient_then_accepted)
    monkeypatch.setattr(executor.asyncio, "sleep", no_wait)

    result = asyncio.run(executor.execute_code_sandboxed(
        source_code="int main() { return 0; }",
        language="cpp",
        test_cases=[{"input": "", "expected_output": "1"}],
    ))

    assert calls == 2
    assert result["compile_status"] == "success"
    assert result["execution_status"] == "completed"

