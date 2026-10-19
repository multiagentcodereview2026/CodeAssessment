import asyncio

import pytest

from docker_runner import executor


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

    assert calls == 2
    assert result["compile_status"] == "unavailable"
    assert result["execution_status"] == "system_error"
    assert "temporarily unavailable" in result["compile_error"]

