from services.executor import execute_code


def normalize_output(output: str) -> str:
    """
    Normalize program output before comparison.
    """

    return output.strip().replace("\r\n", "\n")


def evaluate_submission(
    code: str,
    test_cases: list,
    language: str,
    timeout: int = 2
):
    """
    Execute submitted code against all test cases
    and calculate the functional score.
    """

    results = []

    passed = 0
    failed = 0

    for test_case in test_cases:

        # --------------------------------------------------
        # Execute submitted code
        # --------------------------------------------------

        execution = execute_code(
            language=language,
            code=code,
            input_data=test_case.input_data,
            timeout=timeout
        )

        # --------------------------------------------------
        # Normalize outputs
        # --------------------------------------------------

        actual_output = normalize_output(
            execution["stdout"]
        )

        expected_output = normalize_output(
            test_case.expected_output
        )

        # --------------------------------------------------
        # Determine test result
        # --------------------------------------------------

        if execution["status"] != "SUCCESS":

            test_status = execution["status"]
            failed += 1

        elif actual_output == expected_output:

            test_status = "PASS"
            passed += 1

        else:

            test_status = "FAIL"
            failed += 1

        # --------------------------------------------------
        # Store test result
        # --------------------------------------------------

        results.append({
            "test_case_id": test_case.id,
            "status": test_status,
            "input": test_case.input_data,
            "expected_output": expected_output,
            "actual_output": actual_output,
            "execution_time": execution["execution_time"],
            "stderr": execution["stderr"],
        })

    # ------------------------------------------------------
    # Calculate totals
    # ------------------------------------------------------

    total = len(test_cases)

    # ------------------------------------------------------
    # Calculate functional score
    # ------------------------------------------------------

    if total == 0:

        overall_status = "NO_TEST_CASES"
        score = 0.0

    elif failed == 0:

        overall_status = "PASSED"
        score = 100.0

    else:

        overall_status = "FAILED"
        score = round(
            (passed / total) * 100,
            2
        )

    # ------------------------------------------------------
    # Return evaluation result
    # ------------------------------------------------------

    return {
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": failed,
        "score": score,
        "status": overall_status,
        "test_results": results
    }