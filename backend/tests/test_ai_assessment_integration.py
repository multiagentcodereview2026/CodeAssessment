import asyncio

from agents import aggregation
from agents.complexity import extract_expected_complexities
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


def test_complexity_requirements_are_read_from_constraints():
    expected = extract_expected_complexities(
        {"constraints": ["O(n) time required", "O(1) space complexity"]}
    )

    assert expected == ("O(n)", "O(1)")


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
