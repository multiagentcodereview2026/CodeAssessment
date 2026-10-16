import asyncio

from docker_runner import executor


def test_cpp_runner_outage_is_not_reported_as_missing_local_compiler(monkeypatch):
    calls = 0

    def unavailable_engine(_payload):
        nonlocal calls
        calls += 1
        return None

    def local_fallback_must_not_run(*_args, **_kwargs):
        raise AssertionError("C++ must not use the backend local fallback")

    original_sleep = executor.asyncio.sleep

    async def no_wait(_seconds):
        await original_sleep(0)

    monkeypatch.setattr(executor, "_sync_request_docker", unavailable_engine)
    monkeypatch.setattr(executor, "execute_locally", local_fallback_must_not_run)
    monkeypatch.setattr(executor.asyncio, "sleep", no_wait)

    result = asyncio.run(executor.execute_code_sandboxed(
        source_code="#include <iostream>\nint main() { std::cout << 1; }",
        language="cpp",
        test_cases=[{"input": "", "expected_output": "1"}],
    ))

    assert calls == 2
    assert result["compile_status"] == "unavailable"
    assert result["execution_status"] == "system_error"
    assert "g++" not in result["compile_error"]

