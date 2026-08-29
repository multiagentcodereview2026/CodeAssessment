from services.executor import execute_code


def normalize_output(output: str) -> str:
    """
    Normalize output before comparison.

    Removes leading/trailing whitespace and
    normalizes line endings.
    """
    if output is None:
        return ""

    return output.strip().replace("\r\n", "\n")


def evaluate_submission(
    code: str,
    test_cases: list,
    language: str = "python",
    timeout: int = 2
):
    """
    Run submitted code against all test cases.

    The selected language determines which Docker
    executor is used.
    """

    results = []

    passed = 0
    failed = 0

    for test_case in test_cases:

        # ----------------------------------------------------
        # Execute submitted code
        # ----------------------------------------------------

        execution = execute_code(
            language=language,
            code=code,
            input_data=test_case.input_data,
            timeout=timeout
        )

        # ----------------------------------------------------
        # Normalize outputs
        # ----------------------------------------------------

        actual_output = normalize_output(
            execution["stdout"]
        )

        expected_output = normalize_output(
            test_case.expected_output
        )

        # ----------------------------------------------------
        # Determine test result
        # ----------------------------------------------------

        if execution["status"] != "SUCCESS":

            test_status = execution["status"]
            failed += 1

        elif actual_output == expected_output:

            test_status = "PASS"
            passed += 1

        else:

            test_status = "FAIL"
            failed += 1

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        results.append({
            "test_case_id": test_case.id,
            "status": test_status,
            "input": test_case.input_data,
            "expected_output": expected_output,
            "actual_output": actual_output,
            "execution_time": execution["execution_time"],
            "stderr": execution["stderr"],
        })

    # --------------------------------------------------------
    # Overall result
    # --------------------------------------------------------

    total = len(test_cases)

    if total == 0:

        overall_status = "NO_TEST_CASES"

    elif failed == 0:

        overall_status = "PASSED"

    else:

        overall_status = "FAILED"

    return {
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": failed,
        "status": overall_status,
        "test_results": results
    }