import asyncio

from agents import revision
from agents.explainability import build_evidence_feedback


def test_revision_fallback_never_offers_a_different_problem_solution():
    state = {
        "problem": {"title": "Longest Substring Without Repeating Characters"},
        "submission": {"language": "cpp", "source_code": "int longestUnique() { return 0; }"},
    }

    fallback = revision.unavailable_revision(state)

    assert fallback["improved_code"] == ""
    assert "Longest Substring" in fallback["change_summary"]
    assert "twoSum" not in fallback["improved_code"]


def test_revision_node_rejects_the_known_unrelated_two_sum_template(monkeypatch):
    captured = {}

    async def return_unrelated_solution(_prompt, payload, _schema, _fallback):
        captured.update(payload)
        return {
            "improved_code": "vector<int> twoSum(vector<int> nums, int target) { return {}; }",
            "changes": [],
            "change_summary": "Rewritten solution.",
            "improvement_explanation": "Improved.",
        }

    monkeypatch.setattr(revision, "invoke_agent", return_unrelated_solution)
    state = {
        "problem": {"title": "Longest Substring Without Repeating Characters", "description": "Find the longest unique substring."},
        "submission": {"language": "cpp", "source_code": "int longestUnique() { return 0; }"},
        "execution_result": {"results": [{"status": "wrong_answer", "is_hidden": False}, {"status": "wrong_answer", "is_hidden": True, "error_message": "private detail"}]},
    }

    result = asyncio.run(revision.revision_node(state))["improved_code"]

    assert result["improved_code"] == ""
    assert result["revision_source"] == "fallback"
    assert captured["problem"]["title"] == state["problem"]["title"]
    assert len(captured["public_execution_results"]) == 1
    assert "private detail" not in str(captured)


def test_offline_feedback_is_specific_and_uses_only_public_results():
    feedback = build_evidence_feedback({
        "problem": {"title": "Palindrome Number"},
        "submission": {"language": "python"},
        "execution_result": {
            "compile_status": "success",
            "results": [
                {"status": "accepted", "is_hidden": False},
                {"status": "wrong_answer", "is_hidden": False},
                {"status": "wrong_answer", "is_hidden": True, "error_message": "private expected value"},
            ],
        },
    })

    assert "Palindrome Number" in feedback["mentor_feedback"]
    assert "1/2 public examples" in feedback["mentor_feedback"]
    assert any("public test case 2" in step for step in feedback["improvement_steps"])
    assert "private expected value" not in str(feedback)
