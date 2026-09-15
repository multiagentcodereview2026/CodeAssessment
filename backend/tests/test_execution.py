import asyncio
import pytest
from docker_runner import executor


def test_local_python_and_wrong_answer():
    cases = [{'input': '3', 'expected_output': '3'}]
    assert executor.execute_locally('print(input())', 'python', cases)['passed_cases'] == 1
    assert executor.execute_locally('print(4)', 'python', cases)['failed_cases'] == 1


def test_hidden_fallback_redaction():
    result = executor.execute_locally('print(input())', 'python', [{'input': 'private123', 'expected_output': 'private123', 'is_hidden': True}])
    assert result['passed_cases'] == 1
    assert 'private123' not in str(result)


def test_local_fallback_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setattr(executor, '_sync_request_docker', lambda payload: None)
    monkeypatch.delenv('ALLOW_LOCAL_EXECUTION', raising=False)
    with pytest.raises(RuntimeError):
        asyncio.run(executor.execute_code_sandboxed('print(1)', 'python', [{'input': '', 'expected_output': '1'}]))


def test_output_comparison_preserves_meaningful_whitespace():
    assert executor.compare_outputs('1 2  \n', '1 2')
    assert not executor.compare_outputs('12', '1 2')
