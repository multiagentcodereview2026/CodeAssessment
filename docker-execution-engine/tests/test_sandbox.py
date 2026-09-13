import os
import sys

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from app.languages import get_language_config
from app.models import VERDICT_ACCEPTED
from app.models import VERDICT_COMPILATION_ERROR
from app.models import VERDICT_WRONG_ANSWER
from app.queue_worker import aggregate_verdict
from app.schemas import TestCaseResultResponse


def test_schema_hidden_redaction():

    res = TestCaseResultResponse(
        test_case_id="tc_101",
        status="ACCEPTED",
        runtime_ms=12,
        memory_kb=512,
        is_hidden=True,
        input="SECRET_INPUT",
        expected_output="SECRET_EXPECTED",
        actual_output="SECRET_ACTUAL",
        stderr="SECRET_STDERR"
    )

    assert res.input is None
    assert res.expected_output is None
    assert res.actual_output is None
    assert res.stderr is None
    print("[PASS] test_schema_hidden_redaction")


def test_verdict_precedence():

    assert aggregate_verdict("ACCEPTED", "WRONG_ANSWER") == "WRONG_ANSWER"
    assert aggregate_verdict("WRONG_ANSWER", "TIME_LIMIT_EXCEEDED") == "TIME_LIMIT_EXCEEDED"
    assert aggregate_verdict("TIME_LIMIT_EXCEEDED", "COMPILATION_ERROR") == "COMPILATION_ERROR"
    assert aggregate_verdict("COMPILATION_ERROR", "ACCEPTED") == "COMPILATION_ERROR"
    print("[PASS] test_verdict_precedence")


def test_language_config():

    assert get_language_config("python") is not None
    assert get_language_config("c") is not None
    assert get_language_config("cpp") is not None
    assert get_language_config("java") is not None
    assert get_language_config("unknown") is None
    print("[PASS] test_language_config")


def main():

    test_schema_hidden_redaction()
    test_verdict_precedence()
    test_language_config()
    print("\n--- ALL STANDALONE UNIT TESTS PASSED SUCCESSFULLY! ---")


if __name__ == "__main__":

    main()
