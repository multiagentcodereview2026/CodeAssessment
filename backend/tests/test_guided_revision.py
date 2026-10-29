import asyncio

from agents import revision


def test_guided_revision_never_returns_a_complete_program(monkeypatch):
    async def fake_invoke(prompt, payload, schema, fallback, **_kwargs):
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
            "improved_code": "int main() { return 0; }",
            "changes": [{"line_original": "if (x ≠ y)", "line_improved": "if (x ≠ y)"}],
        }

    monkeypatch.setattr(revision, "invoke_agent", fake_invoke)
    result = asyncio.run(revision.guided_revision_node({
        "problem": {"title": "Window problem", "statement": "..."},
        "submission": {"source_code": "int main() {}", "language": "cpp"},
        "execution_result": {"results": []},
    }, "ALGORITHM"))["improved_code"]

    assert result["improved_code"] == ""
    assert result["changes"] == []
    assert result["starter_fragment"] == ""
    assert result["verification"]["status"] == "guided_step"
    assert result["stage"] == "ALGORITHM"
    assert result["revision_source"] == "ai"


def test_guided_no_change_is_explicit_and_has_no_code():
    result = revision.guided_revision_fallback("NO_CHANGE", {
        "problem": {"title": "Already optimal"},
        "submission": {"source_code": "", "language": "cpp"},
    })

    assert result["starter_fragment"] == ""
    assert result["guided_steps"] == []


def test_guided_revision_passes_previous_stage_for_comparison(monkeypatch):
    captured = {}

    async def fake_invoke(_prompt, payload, _schema, _fallback, **_kwargs):
        captured.update(payload)
        return {
            "stage": "OPTIMIZE",
            "title": "Remove repeated work",
            "next_goal": "Keep the prior correction and address the measured bottleneck.",
            "guided_steps": ["Replace only the repeated operation."],
            "algorithm_outline": [],
            "improved_code": "int main() { return 0; }",
            "changes": [],
            "change_summary": "A second stage.",
            "improvement_explanation": "The earlier stage is preserved.",
            "analysis_source": "groq",
        }

    monkeypatch.setattr(revision, "invoke_agent", fake_invoke)
    asyncio.run(revision.guided_revision_node({
        "problem": {"title": "Practice", "statement": "..."},
        "submission": {"source_code": "int main() { return 1; }", "language": "cpp"},
        "execution_result": {"results": []},
        "previous_revision": {
            "stage": "ALGORITHM",
            "student_source_code": "int main() { return 0; }",
            "guided_code": "int main() { return 0; }",
        },
    }, "OPTIMIZE"))

    assert captured["previous_revision"]["stage"] == "ALGORITHM"


def test_manual_work_stage_has_an_ordered_future_plan():
    assert revision.guided_future_plan("OPTIMIZE_MANUAL_WORK") == [
        "OPTIMIZE_DATA_STRUCTURE: after this smaller improvement is assessed, remove repeated whole-collection ordering with a structure suited to selecting the next two values.",
        "REFINEMENT: once the measured performance bottleneck is resolved, improve naming, formatting, and edge-case clarity.",
    ]


def test_local_optimization_future_plan_defers_algorithm_change():
    plan = revision.guided_future_plan("OPTIMIZE_LOCAL")
    assert plan[0].startswith("OPTIMIZE_DATA_STRUCTURE")
    assert plan[1].startswith("REFINEMENT")


def test_manual_work_fallback_is_specific_without_an_ai_provider():
    result = revision.guided_revision_fallback("OPTIMIZE_MANUAL_WORK", {
        "problem": {"title": "Last Stone Weight"},
    })

    assert result["title"] == "Remove repeated manual ordering"
    assert len(result["guided_steps"]) == 3
    assert result["future_plan"][0].startswith("OPTIMIZE_DATA_STRUCTURE")


def test_private_stage_revision_receives_the_same_bounded_stage(monkeypatch):
    captured = {}

    async def fake_invoke(_prompt, payload, _schema, _fallback, **_kwargs):
        captured.update(payload)
        return {"improved_code": "int main() { return 0; }", "analysis_source": "groq"}

    monkeypatch.setattr(revision, "invoke_agent", fake_invoke)
    result = asyncio.run(revision.private_stage_revision_node({
        "problem": {"title": "Practice", "statement": "..."},
        "submission": {"source_code": "int main() { return 1; }", "language": "cpp"},
    }, "OPTIMIZE_LOCAL"))["private_revision"]

    assert captured["stage"] == "OPTIMIZE_LOCAL"
    assert result["revision_source"] == "ai"


def test_private_stage_accepts_text_change_metadata(monkeypatch):
    async def fake_invoke(_prompt, _payload, _schema, _fallback, **_kwargs):
        return {
            "improved_code": "int main() { return 0; }",
            "changes": ["Replace the repeated loop."],
            "analysis_source": "groq",
        }

    monkeypatch.setattr(revision, "invoke_agent", fake_invoke)
    result = asyncio.run(revision.private_stage_revision_node({
        "problem": {"title": "Practice"},
        "submission": {"source_code": "int main() {}", "language": "cpp"},
    }, "OPTIMIZE_LOCAL"))["private_revision"]

    assert result["revision_source"] == "ai"
    assert result["improved_code"]
