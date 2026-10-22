import asyncio

from agents import revision


def test_guided_revision_never_returns_a_complete_replacement(monkeypatch):
    async def fake_invoke(prompt, payload, schema, fallback):
        return {
            "stage": "ALGORITHM",
            "title": "Generalize the approach",
            "next_goal": "Replace fixed-output branches with state that represents the current window.",
            "guided_steps": ["Track the state needed by one candidate window."],
            "algorithm_outline": ["Expand one boundary.", "Repair the window when it becomes invalid."],
            "starter_fragment": "repeat while the window is invalid: move its left boundary",
            "change_summary": "Move from example-specific output to a general invariant.",
            "improvement_explanation": "Submit your own changed attempt before asking for another step.",
            "analysis_source": "groq",
            # A provider must not be able to bypass the policy by adding this.
            "improved_code": "int main() { return 0; }",
        }

    monkeypatch.setattr(revision, "invoke_agent", fake_invoke)
    result = asyncio.run(revision.guided_revision_node({
        "problem": {"title": "Window problem", "statement": "..."},
        "submission": {"source_code": "int main() {}", "language": "cpp"},
        "execution_result": {"results": []},
    }, "ALGORITHM"))["improved_code"]

    assert result["improved_code"] == ""
    assert result["starter_fragment"] == ""
    assert result["verification"]["status"] == "guided_step"
    assert result["revision_source"] == "ai"


def test_guided_no_change_is_explicit_and_has_no_code():
    result = revision.guided_revision_fallback("NO_CHANGE", {
        "problem": {"title": "Already optimal"},
        "submission": {"source_code": "", "language": "cpp"},
    })

    assert result["starter_fragment"] == ""
    assert result["guided_steps"] == []
