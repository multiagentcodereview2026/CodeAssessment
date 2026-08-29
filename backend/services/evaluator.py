from services.executor import execute_python_code


def normalize_output(output: str) -> str:
    """
    Normalize output before comparison.

    Removes leading/trailing whitespace,
    normalizes line endings, and removes
    whitespace differences inside the output.
    """
    return "".join(output.strip().split())


def evaluate_submission(
    code: str,
    test_cases: list,
    timeout: int = 2
):
    """
    Run submitted code against all test cases.

    Each test case is executed separately inside Docker.
    The actual output is compared with the expected output.
    """

    results = []

    passed = 0
    failed = 0

    for test_case in test_cases:

        # -------------------------------------------------
        # Execute submitted code
        # -------------------------------------------------

        execution = execute_python_code(
            code=code,
            input_data=test_case.input_data,
            timeout=timeout
        )

        # -------------------------------------------------
        # Normalize outputs
        # -------------------------------------------------

        actual_output = normalize_output(
            execution["stdout"]
        )

        expected_output = normalize_output(
            test_case.expected_output
        )

        # -------------------------------------------------
        # Determine test result
        # -------------------------------------------------

        if execution["status"] != "SUCCESS":

            test_status = execution["status"]
            failed += 1

        elif actual_output == expected_output:

            test_status = "PASS"
            passed += 1

        else:

            test_status = "FAIL"
            failed += 1

        # -------------------------------------------------
        # Store test result
        # -------------------------------------------------

        results.append({
            "test_case_id": test_case.id,
            "status": test_status,
            "input": test_case.input_data,
            "expected_output": expected_output,
            "actual_output": actual_output,
            "execution_time": execution["execution_time"],
            "stderr": execution["stderr"]
        })

    # -----------------------------------------------------
    # Overall result
    # -----------------------------------------------------

    total = len(test_cases)

    if total == 0:

        overall_status = "NO_TEST_CASES"

    elif failed == 0:

        overall_status = "PASSED"

    else:

        overall_status = "FAILED"

    # -----------------------------------------------------
    # Return evaluation
    # -----------------------------------------------------

    return {
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": failed,
        "status": overall_status,
        "test_results": results
    }