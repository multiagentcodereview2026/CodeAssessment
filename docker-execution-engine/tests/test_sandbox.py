import os
import subprocess
import sys
import pytest

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from app.languages import get_language_config
from app.languages import LANGUAGES
from app.models import VERDICT_ACCEPTED
from app.models import VERDICT_COMPILATION_ERROR
from app.models import VERDICT_OUTPUT_LIMIT_EXCEEDED
from app.models import VERDICT_SYSTEM_ERROR
from app.models import VERDICT_WRONG_ANSWER
from app.queue_worker import aggregate_verdict
from app import sandbox
from app.schemas import TestCaseResultResponse as CaseResultResponse


def test_schema_hidden_redaction():

    res = CaseResultResponse(
        test_case_id="tc_101",
        status="ACCEPTED",
        runtime_ms=12,
        memory_kb=512,
        is_hidden=True,
        input="SECRET_INPUT",
        expected_output="SECRET_EXPECTED",
        actual_output="SECRET_ACTUAL",
        stderr="SECRET_STDERR"
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


def test_language_config():

    assert get_language_config("python") is not None
    assert get_language_config("c") is not None
    assert get_language_config("cpp") is not None
    assert get_language_config("java") is not None
    assert get_language_config("javascript") is not None
    assert set(LANGUAGES) == {"python", "c", "cpp", "java", "javascript"}
    assert get_language_config("unknown") is None
    print("[PASS] test_language_config")


def test_output_capture_is_bounded(monkeypatch):
    monkeypatch.setattr(sandbox.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0))
    result = sandbox.run_container_command(
        [sys.executable, "-c", "import sys; sys.stdout.write('x' * 2000000)"],
        "test-container",
        timeout_seconds=5,
        max_output_bytes=1024,
    )
    code, stdout, stderr, timed_out, output_limited = result
    assert output_limited is True
    assert len(stdout.encode()) + len(stderr.encode()) <= 1024
    assert timed_out is False


def test_execution_fails_closed_when_docker_is_unavailable(monkeypatch):
    monkeypatch.setattr(sandbox, "is_docker_available", lambda: False)
    monkeypatch.setattr(sandbox.tempfile, "mkdtemp", lambda **kwargs: pytest.fail("workspace must not be created"))
    result = sandbox.execute_in_sandbox("print('should not run')", get_language_config("python"), "", "")
    assert result.status == VERDICT_SYSTEM_ERROR
    assert result.actual_output is None
    assert "was not run" in result.stderr


def test_sandbox_commands_apply_isolation_and_read_only_runner_mount(monkeypatch):
    commands = []

    def fake_run_container_command(cmd_list, **kwargs):
        commands.append(cmd_list)
        return 0, "", "", False, False

    monkeypatch.setattr(sandbox, "is_docker_available", lambda: True)
    monkeypatch.setattr(sandbox, "run_container_command", fake_run_container_command)
    result = sandbox.execute_in_sandbox(
        "int main(){return 0;}", get_language_config("cpp"), "", "", time_limit=2
    )
    assert result.status == VERDICT_ACCEPTED
    assert len(commands) == 2
    runner = commands[1]
    timeout_index = runner.index("timeout")
    assert runner[timeout_index + 1:timeout_index + 4] == [
        "--signal=TERM", "--kill-after=1s", "2s"
    ]
    for option in ("--network", "none", "--read-only", "--pids-limit", "--memory", "--cpus", "--cap-drop", "ALL", "--security-opt", "no-new-privileges"):
        assert option in runner
    mount_index = runner.index("-v") + 1
    assert runner[mount_index].endswith(":ro")


def main():

    test_schema_hidden_redaction()
    test_verdict_precedence()
    test_language_config()
    print("\n--- ALL STANDALONE UNIT TESTS PASSED SUCCESSFULLY! ---")


if __name__ == "__main__":

    main()
