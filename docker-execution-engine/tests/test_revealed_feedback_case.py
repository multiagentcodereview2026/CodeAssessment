from app.schemas import ExecutionResultResponse, RevealedFeedbackCaseResponse


def test_revealed_feedback_case_keeps_only_the_deliberately_released_values():
    result = ExecutionResultResponse(
        status="WRONG_ANSWER",
        runtime_ms=10,
        memory_kb=0,
        compile_success=True,
        compile_stderr=None,
        tests_total=2,
        tests_passed=1,
        tests_failed=1,
        revealed_feedback_case=RevealedFeedbackCaseResponse(
            status="WRONG_ANSWER",
            reason="Your output did not match the expected output.",
            input="10",
            expected_output="false",
            actual_output="true",
        ),
    )

    assert result.revealed_feedback_case.model_dump() == {
        "status": "WRONG_ANSWER",
        "reason": "Your output did not match the expected output.",
        "input": "10",
        "expected_output": "false",
        "actual_output": "true",
    }
