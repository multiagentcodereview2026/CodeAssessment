import asyncio
from workflow.graph import evaluation_graph
from workflow.state import EvaluationState

async def test_langgraph_pipeline_dry_run():
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
        "similarity_score": None,
        "similarity_details": None,
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

    # Execute workflow graph
    result = await evaluation_graph.ainvoke(initial_state)

    assert result["status"] == "complete", f"Expected complete, got {result['status']}"
    assert result["overall_score"] is not None
    assert 0 <= result["overall_score"] <= 100
    assert result["feedback"] is not None
    assert "strengths" in result["feedback"]
    assert result["improved_code"] is not None
    assert result["projected_score"] is not None
    print("\n==========================================")
    print(" [SUCCESS] LangGraph Multi-Agent Pipeline Passed!")
    print("==========================================")
    print(f"Overall Score   : {result['overall_score']}")
    print(f"Correctness     : {result['correctness_score']}")
    print(f"Complexity      : {result['complexity_score']}")
    print(f"Style           : {result['style_score']}")
    print(f"Originality     : {100.0 - result['similarity_score']}")
    print(f"Projected Score : {result['projected_score']['projected_score']}")
    print(f"Strengths       : {result['feedback']['strengths']}")
    print(f"Insight         : {result['feedback']['key_insight']}")
    print("==========================================\n")

if __name__ == "__main__":
    asyncio.run(test_langgraph_pipeline_dry_run())
