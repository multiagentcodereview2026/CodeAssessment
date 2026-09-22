import asyncio

from agents import aggregation
from agents import complexity
from agents.complexity import public_problem_context, score_complexity_analysis
from agents.correctness import (
    calculate_correctness_score,
    sanitize_execution_for_llm,
)


def test_correctness_uses_observed_test_results():
    execution = {
        "compile_status": "success",
        "results": [
            {"status": "accepted"},
            {"status": "wrong_answer"},
        ],
    }

    assert calculate_correctness_score(execution) == 50.0


def test_correctness_supports_summary_only_execution_results():
    execution = {
        "compile_status": "success",
        "passed_cases": 3,
        "failed_cases": 1,
    }

    assert calculate_correctness_score(execution) == 75.0


def test_hidden_execution_details_are_not_sent_to_the_llm():
    safe_execution = sanitize_execution_for_llm(
        {
            "results": [
                {
                    "is_hidden": True,
                    "status": "wrong_answer",
                    "input": "private input",
                    "expected_output": "private output",
                    "actual_output": "student output",
                    "stderr": "private diagnostic",
                    "error_message": "private error",
                }
            ]
        }
    )

    assert safe_execution["results"] == [
        {"is_hidden": True, "status": "wrong_answer"}
    ]


def test_complexity_ai_payload_excludes_private_target_data():
    public = public_problem_context(
        {
            "title": "Two Sum",
            "statement": "Find two values.",
            "constraints": ["2 <= n <= 10^4"],
            "target_time_complexity": "O(n)",
            "target_space_complexity": "O(n)",
        }
    )

    assert "target_time_complexity" not in public
    assert "target_space_complexity" not in public


def test_groq_complexity_call_never_receives_private_target_data(monkeypatch):
    captured = {}

    async def inspect_payload(_prompt, payload, _schema, _fallback):
        captured.update(payload)
        return {
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
            "bottlenecks": [],
            "optimization_suggestion": "Keep the single traversal.",
            "reasoning": "One pass over the input.",
        }

    monkeypatch.setattr(complexity, "invoke_agent", inspect_payload)
    asyncio.run(
        complexity.analyze_student_complexity(
            {
                "title": "Two Sum",
                "statement": "Find two values.",
                "target_time_complexity": "O(n)",
                "target_space_complexity": "O(n)",
            },
            "print('student code')",
            "python",
        )
    )

    encoded_payload = str(captured)
    assert "target_time_complexity" not in encoded_payload
    assert "target_space_complexity" not in encoded_payload
    assert "O(n)" not in encoded_payload


def test_complexity_response_excludes_private_target_data():
    scored = score_complexity_analysis(
        {
            "time_complexity": "O(n log n)",
            "space_complexity": "O(n)",
            "bottlenecks": ["Sorting dominates the runtime."],
            "optimization_suggestion": "Use a hash map.",
            "reasoning": "The code sorts the input.",
        },
        {"time": "O(n)", "space": "O(n)"},
    )

    details = scored["complexity_details"]
    assert scored["complexity_score"] == 93.75
    assert details["time_score"] == 21.875
    assert details["space_score"] == 25.0
    assert "target_time_complexity" not in details
    assert "expected_time_complexity" not in details
    assert "optimal" not in details
    assert scored["assessment_flags"] == {"benchmark_review_required": False}


def test_aggregation_does_not_replace_a_zero_score_with_a_default(monkeypatch):
    async def use_deterministic_fallback(_prompt, _payload, _schema, fallback):
        return fallback

    monkeypatch.setattr(aggregation, "invoke_agent", use_deterministic_fallback)

    result = asyncio.run(
        aggregation.aggregation_node(
            {
                "correctness_score": 0.0,
                "complexity_score": None,
                "style_score": 90.0,
                "similarity_score": 20.0,
                "execution_result": {"compile_status": "error"},
            }
        )
    )

    assert result["overall_score"] == 32.5
