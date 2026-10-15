from main import redact_hidden_execution


def test_student_view_reveals_only_one_failed_hidden_learning_case():
    execution = {
        "compile_status": "success",
        "results": [
            {"status": "accepted", "is_hidden": False, "input": "2", "expected_output": "2"},
            {"status": "wrong_answer", "is_hidden": True, "input": "10", "expected_output": "false", "actual_output": "true"},
            {"status": "wrong_answer", "is_hidden": True, "input": "100", "expected_output": "false", "actual_output": "true"},
        ],
    }

    safe = redact_hidden_execution(redact_hidden_execution(execution), student_view=True)

    assert safe["results"] == [
        {"status": "accepted", "is_hidden": False, "input": "2", "expected_output": "2"}
    ]
    assert safe["revealed_feedback_case"] == {
        "status": "WRONG_ANSWER",
        "reason": "Your output did not match the expected output.",
        "input": "10",
        "expected_output": "false",
        "actual_output": "true",
    }
    assert "100" not in str(safe)
