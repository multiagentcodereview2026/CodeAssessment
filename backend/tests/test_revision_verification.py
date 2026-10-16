import asyncio

from agents import revision_verification_node
from agents.revision_verification import summarize_revision_verification, unverified_revision


def test_verified_revision_summary_exposes_only_safe_counts():
    result = summarize_revision_verification({
        "compile_status": "success",
        "passed_cases": 5,
        "total_cases": 5,
        "results": [{"input": "private", "expected_output": "secret"}],
    })

    assert result["status"] == "verified_passed"
    assert result["passed_cases"] == 5
    assert "private" not in str(result)
    assert "secret" not in str(result)


def test_failed_revision_is_not_presented_as_verified_solution():
    result = summarize_revision_verification({
        "compile_status": "success",
        "passed_cases": 3,
        "total_cases": 5,
    })

    assert result["status"] == "verification_failed"
    assert result["passed_cases"] == 3


def test_unavailable_revision_verification_is_explicit():
    result = unverified_revision("Judge unavailable.")

    assert result["status"] == "verification_unavailable"
    assert result["verified"] is False


def test_revision_node_judges_ai_code_without_leaking_case_values(monkeypatch):
    captured = {}

    async def fake_execute(**kwargs):
        captured.update(kwargs)
        return {"compile_status": "success", "passed_cases": 2, "total_cases": 2}

    monkeypatch.setattr(revision_verification_node, "execute_code_sandboxed", fake_execute)
    result = asyncio.run(revision_verification_node.revision_verification_node({
        "submission": {"language": "python"},
        "improved_code": {"revision_source": "ai", "improved_code": "print(1)"},
        "revision_test_cases": [{"input": "secret", "expected_output": "1", "is_hidden": True}],
    }))

    assert result["improved_code"]["verification"]["status"] == "verified_passed"
    assert captured["test_cases"][0]["input"] == "secret"
    assert "secret" not in str(result)
