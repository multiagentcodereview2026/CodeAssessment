import pytest
from workflow.graph import evaluation_graph
from workflow.state import EvaluationState

@pytest.mark.asyncio
@pytest.mark.parametrize("analysis_available", [False, True])
async def test_langgraph_pipeline_dry_run(monkeypatch, analysis_available):
    # Keep this graph test deterministic and offline even when a developer has
    # a provider key in their local environment.
    import agents.base as agent_base

    monkeypatch.setattr(agent_base, "llm", None)
    monkeypatch.setattr(agent_base.settings, "GROQ_API_KEY", "")
    initial_state: EvaluationState = {
        "user": {"student_id": "24BD1A058Z", "name": "Vignesh"},
        "problem": {
            "title": "Two Sum",
            "statement": "Find two indices that sum to target.",
            "constraints": "O(N) time required"
        },
        "submission": {
            "source_code": "def twoSum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n    return []",
            "language": "python"
        },
        "execution_result": {
            "compile_status": "success",
            "compile_error": None,
            "execution_status": "completed",
            "exit_code": 0,
            "stdout": "[0, 1]",
            "stderr": "",
            "runtime_ms": 14,
            "memory_kb": 4200,
            "passed_cases": 3,
            "failed_cases": 0
        },
        "validation_result": None,
        "correctness_score": None,
        "correctness_details": None,
        "complexity_score": None,
        "complexity_details": None,
        "style_score": None,
        "style_details": None,
        "overall_score": None,
        "score_breakdown": None,
        "confidence": None,
        "feedback": None,
        "recommendations": None,
        "improved_code": None,
        "learning_analytics": None,
        "projected_score": None,
        "status": "running",
        "errors": []
    }

    # These fixtures test orchestration, not analyzer accuracy. Supply known
    # evidence for the complete path; leave it unavailable for the other path.
    initial_state["precomputed_complexity_analysis"] = {
        "time_complexity": "O(n)" if analysis_available else None,
        "space_complexity": "O(n)" if analysis_available else None,
        "status": "ANALYZED" if analysis_available else "ANALYSIS_FAILED",
        "confidence": 1.0 if analysis_available else 0.0,
        "method": "test-fixture",
    }
    initial_state["complexity_target"] = {"time": "O(n)", "space": "O(n)"}

    # Execute workflow graph
    result = await evaluation_graph.ainvoke(initial_state)

    assert result["status"] == "complete", f"Expected complete, got {result['status']}"
    assert result["correctness_score"] == 100
    assert result["score_breakdown"]["rubric"]["version"] == "complexity-focused-v2"
    if analysis_available:
        assert result["score_breakdown"]["assessment"]["status"] == "complete"
        assert result["overall_score"] == round(90 + result["style_score"] * .10, 1)
        assert 0 <= result["overall_score"] <= 100
    else:
        assert result["overall_score"] is None
        assessment = result["score_breakdown"]["assessment"]
        assert assessment["status"] == "incomplete"
        assert set(assessment["missing_components"]) == {"time", "space"}
        assert assessment["score_upper_bound"] - assessment["score_lower_bound"] == pytest.approx(60)
    assert result["feedback"] is not None
    assert "strengths" in result["feedback"]
    # Revision is requested separately after a saved submission; the scoring
    # graph must not fabricate a replacement code draft in its offline path.
    assert result["improved_code"] is None
    assert result["projected_score"] is not None
    print("\n==========================================")
    print(" [SUCCESS] LangGraph Multi-Agent Pipeline Passed!")
    print("==========================================")
    print(f"Overall Score   : {result['overall_score']}")
    print(f"Correctness     : {result['correctness_score']}")
    print(f"Complexity      : {result['complexity_score']}")
    print(f"Style           : {result['style_score']}")
    print(f"Projected Score : {result['projected_score']['projected_score']}")
    print(f"Strengths       : {result['feedback']['strengths']}")
    print(f"Insight         : {result['feedback']['key_insight']}")
    print("==========================================\n")
