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
from app.sandbox import execute_in_sandbox


def test_python_addition():
    print("Testing Python Code Execution...")
    python_code = """
a, b = map(int, input().split())
print(a + b)
"""
    lang_cfg = get_language_config("python")

    # Test Case 1: Correct Output (3 + 5 = 8)
    res1 = execute_in_sandbox(
        code=python_code,
        lang_config=lang_cfg,
        input_data="3 5",
        expected_output="8"
    )
    print(f"Test Case 1 (Expected ACCEPTED): Status = {res1.status}, Output = {res1.actual_output.strip() if res1.actual_output else None}")

    # Test Case 2: Wrong Answer (10 + 20 != 50)
    res2 = execute_in_sandbox(
        code=python_code,
        lang_config=lang_cfg,
        input_data="10 20",
        expected_output="50"
    )
    print(f"Test Case 2 (Expected WRONG_ANSWER): Status = {res2.status}, Output = {res2.actual_output.strip() if res2.actual_output else None}")


if __name__ == "__main__":
    test_python_addition()
