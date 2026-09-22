import asyncio
import ast
import inspect
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List

import requests


logger = logging.getLogger(__name__)

DOCKER_ENGINE_URL = os.getenv(
    "DOCKER_ENGINE_URL",
    "http://localhost:8001/execute"
)

DOCKER_ENGINE_REQUEST_TIMEOUT_SECONDS = int(
    os.getenv(
        "DOCKER_ENGINE_REQUEST_TIMEOUT_SECONDS",
        "120"
    )
)


def wrap_python_leetcode(code: str) -> str:
    """
    Wrap a LeetCode-style Python Solution class or standalone function
    with a CLI test harness.
    """

    # Do not wrap programs that already handle stdin/stdout.
    if (
        "input(" in code
        or "sys.stdin" in code
        or "def main(" in code
        or "__name__" in code
    ):
        return code

    # Use a normal string instead of an f-string.
    # This prevents braces and nested docstrings in the generated
    # harness from breaking the Python source.
    harness = """
import sys
import json
import ast
import inspect

__USER_CODE__


def _parse_scalar(value):
    value = value.strip()

    try:
        return ast.literal_eval(value)
    except Exception:
        pass

    try:
        return int(value)
    except Exception:
        pass

    try:
        return float(value)
    except Exception:
        pass

    return value


def _parse_assignment_input(raw, parameter_count):
    values = []

    for line in raw.splitlines():
        line = line.strip()

        if not line or "=" not in line:
            continue

        _, value = line.split("=", 1)
        values.append(_parse_scalar(value.strip()))

    if len(values) >= parameter_count:
        return values[:parameter_count]

    return None


def _parse_length_prefixed_input(raw, parameter_count):
    lines = [
        line.strip()
        for line in raw.splitlines()
        if line.strip()
    ]

    if not lines:
        return []

    args = []
    i = 0

    while i < len(lines) and len(args) < parameter_count:

        current = lines[i]
        parts = current.split()

        # Length-prefixed list.
        #
        # Example:
        #
        # 3
        # 1 2 8
        # 8
        #
        # becomes:
        #
        # [1, 2, 8], 8

        if (
            len(parts) == 1
            and parts[0].lstrip("-").isdigit()
        ):

            length = int(parts[0])

            # Empty list:
            #
            # 0
            #
            # becomes:
            #
            # []

            if length == 0:
                args.append([])
                i += 1
                continue

            # Non-empty list.
            if i + 1 < len(lines):

                next_parts = lines[i + 1].split()

                if len(next_parts) == length:

                    values = [
                        _parse_scalar(item)
                        for item in next_parts
                    ]

                    args.append(values)
                    i += 2
                    continue

        # Normal scalar or Python literal.
        args.append(_parse_scalar(current))
        i += 1

    return args[:parameter_count]


def _parse_whitespace_input(raw, parameter_count):
    tokens = raw.split()

    if not tokens:
        return []

    values = [
        _parse_scalar(token)
        for token in tokens
    ]

    return values[:parameter_count]


def _parse_input(raw, parameter_count):

    # 1. Assignment-style input.
    assignment_args = _parse_assignment_input(
        raw,
        parameter_count
    )

    if assignment_args is not None:
        return assignment_args

    # 2. Length-prefixed platform input.
    length_args = _parse_length_prefixed_input(
        raw,
        parameter_count
    )

    if len(length_args) == parameter_count:
        return length_args

    # 3. Python literals on separate lines.
    lines = [
        line.strip()
        for line in raw.splitlines()
        if line.strip()
    ]

    literal_args = []

    for line in lines:

        try:
            literal_args.append(
                ast.literal_eval(line)
            )

        except Exception:
            literal_args = []
            break

    if len(literal_args) == parameter_count:
        return literal_args

    # 4. Whitespace fallback.
    return _parse_whitespace_input(
        raw,
        parameter_count
    )


def _serialize_result(result):

    if isinstance(result, bool):
        return "true" if result else "false"

    if isinstance(result, (list, dict, tuple)):
        return json.dumps(result)

    if result is None:
        return ""

    return str(result)


def _find_target_function():

    target_func = None

    # Look for Solution class.
    if "Solution" in globals():

        sol = Solution()

        methods = [
            name
            for name in dir(sol)
            if not name.startswith("_")
            and callable(getattr(sol, name))
        ]

        if methods:
            target_func = getattr(
                sol,
                methods[0]
            )

    # Standalone function fallback.
    if target_func is None:

        ignored = {
            "_run_harness",
            "_parse_scalar",
            "_parse_assignment_input",
            "_parse_length_prefixed_input",
            "_parse_whitespace_input",
            "_parse_input",
            "_serialize_result",
            "_find_target_function",
        }

        user_functions = [
            value
            for name, value in globals().items()
            if callable(value)
            and not name.startswith("_")
            and name not in ignored
        ]

        if user_functions:
            target_func = user_functions[-1]

    return target_func


def _run_harness():

    raw = sys.stdin.read().strip()

    if not raw:
        return

    target_func = _find_target_function()

    if target_func is None:

        print(
            "Runtime Error: No callable Solution method or function found.",
            file=sys.stderr
        )

        sys.exit(1)

    try:

        # For a bound Solution method, self is not included.
        parameter_count = len(
            inspect.signature(target_func).parameters
        )

        args = _parse_input(
            raw,
            parameter_count
        )

        if len(args) != parameter_count:

            try:

                whole_value = ast.literal_eval(raw)

                if isinstance(
                    whole_value,
                    (list, tuple)
                ):

                    if len(whole_value) == parameter_count:
                        args = list(whole_value)

            except Exception:
                pass

        if len(args) != parameter_count:

            raise TypeError(
                "Expected "
                + str(parameter_count)
                + " argument(s), but parsed "
                + str(len(args))
                + " argument(s) from input."
            )

        result = target_func(*args)

        print(
            _serialize_result(result)
        )

    except Exception as err:

        print(
            "Runtime Error: " + str(err),
            file=sys.stderr
        )

        sys.exit(1)


if __name__ == "__main__":
    _run_harness()
"""

    # Insert the student's code without using an f-string.
    return harness.replace(
        "__USER_CODE__",
        code
    )


def normalize_output(value: str) -> str:
    """
    Ignore only non-semantic output formatting differences.

    Leading whitespace and whitespace inside a line can be meaningful.
    The judge accepts trailing spaces/tabs on each line and an optional
    final newline, but it does not collapse arbitrary whitespace.
    """

    text = (
        (value or "")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    text = text.rstrip("\n")

    return "\n".join(
        line.rstrip(" \t")
        for line in text.split("\n")
    )


def compare_outputs(actual: str, expected: str) -> bool:
    """
    Compare program output with expected output.

    Supports equivalent representations such as:

        [0, 1]
        0 1

    while still preserving meaningful output differences.
    """

    act = normalize_output(actual)
    exp = normalize_output(expected)

    # Exact match first.
    if act == exp:
        return True

    # ---------------------------------------------------------
    # Try JSON comparison.
    #
    # Example:
    # [0, 1]
    # [0,1]
    # ---------------------------------------------------------
    try:
        act_json = json.loads(act)

        try:
            exp_json = json.loads(exp)

            if act_json == exp_json:
                return True

        except Exception:
            pass

        # -----------------------------------------------------
        # JSON list vs whitespace-separated expected output.
        #
        # Example:
        # actual   = "[0, 1]"
        # expected = "0 1"
        # -----------------------------------------------------
        if isinstance(act_json, list):

            expected_tokens = exp.split()

            converted_expected = []

            for token in expected_tokens:

                try:
                    converted_expected.append(
                        int(token)
                    )
                    continue
                except Exception:
                    pass

                try:
                    converted_expected.append(
                        float(token)
                    )
                    continue
                except Exception:
                    pass

                converted_expected.append(token)

            if act_json == converted_expected:
                return True

    except Exception:
        pass

    # ---------------------------------------------------------
    # Whitespace-separated output vs JSON list.
    #
    # Example:
    # actual   = "0 1"
    # expected = "[0, 1]"
    # ---------------------------------------------------------
    try:
        exp_json = json.loads(exp)

        if isinstance(exp_json, list):

            actual_tokens = act.split()

            converted_actual = []

            for token in actual_tokens:

                try:
                    converted_actual.append(
                        int(token)
                    )
                    continue
                except Exception:
                    pass

                try:
                    converted_actual.append(
                        float(token)
                    )
                    continue
                except Exception:
                    pass

                converted_actual.append(token)

            if converted_actual == exp_json:
                return True

    except Exception:
        pass

    return False


def _sync_request_docker(
    payload: Dict[str, Any]
) -> Dict[str, Any] | None:

    try:

        response = requests.post(
            DOCKER_ENGINE_URL,
            json=payload,
            timeout=DOCKER_ENGINE_REQUEST_TIMEOUT_SECONDS
        )

        if response.status_code == 200:

            data = response.json()

            for result in data.get(
                "results",
                []
            ):

                err = str(
                    result.get(
                        "stderr",
                        ""
                    )
                    or ""
                )

                if (
                    "failed to connect to the docker API"
                    in err
                    or "daemon is running"
                    in err
                    or "dockerDesktopLinuxEngine"
                    in err
                ):
                    return None

            return data

    except Exception:
        pass

    return None


def execute_locally(
    source_code: str,
    language: str,
    test_cases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Fallback execution for Python, C, C++, and Java
    stdin/stdout programs.
    """

    lang = language.lower()

    temp_dir = tempfile.mkdtemp()

    try:

        # ---------------------------------------------------------
        # Python
        # ---------------------------------------------------------
        if lang in [
            "python",
            "python3",
            "py"
        ]:

            python_code = wrap_python_leetcode(
                source_code
            )

            runner_cmd = [
                sys.executable,
                "-c",
                python_code
            ]

        # ---------------------------------------------------------
        # C / C++
        # ---------------------------------------------------------
        elif lang in [
            "cpp",
            "c++",
            "c"
        ]:

            compiler = (
                "g++"
                if "cpp" in lang or "c++" in lang
                else "gcc"
            )

            ext = (
                ".cpp"
                if "cpp" in lang or "c++" in lang
                else ".c"
            )

            src_path = os.path.join(
                temp_dir,
                f"solution{ext}"
            )

            bin_path = os.path.join(
                temp_dir,
                "solution.exe"
                if os.name == "nt"
                else "solution"
            )

            with open(
                src_path,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(source_code)

            comp_proc = subprocess.run(
                [
                    compiler,
                    "-O2",
                    src_path,
                    "-o",
                    bin_path
                ],
                capture_output=True,
                text=True
            )

            if comp_proc.returncode != 0:

                return {
                    "compile_status": "error",
                    "compile_error": (
                        comp_proc.stderr
                        or "Compilation failed."
                    ),
                    "execution_status": "compilation_error",
                    "exit_code": comp_proc.returncode,
                    "stdout": "",
                    "stderr": (
                        comp_proc.stderr
                        or "Compilation failed."
                    ),
                    "runtime_ms": 0,
                    "memory_kb": 0,
                    "passed_cases": 0,
                    "failed_cases": len(test_cases),
                    "total_cases": len(test_cases),
                    "results": []
                }

            runner_cmd = [
                bin_path
            ]

        # ---------------------------------------------------------
        # Java
        # ---------------------------------------------------------
        elif lang in ["java"]:

            src_path = os.path.join(
                temp_dir,
                "Main.java"
            )

            with open(
                src_path,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(source_code)

            comp_proc = subprocess.run(
                [
                    "javac",
                    src_path
                ],
                capture_output=True,
                text=True
            )

            if comp_proc.returncode != 0:

                return {
                    "compile_status": "error",
                    "compile_error": (
                        comp_proc.stderr
                        or "Compilation failed."
                    ),
                    "execution_status": "compilation_error",
                    "exit_code": comp_proc.returncode,
                    "stdout": "",
                    "stderr": (
                        comp_proc.stderr
                        or "Compilation failed."
                    ),
                    "runtime_ms": 0,
                    "memory_kb": 0,
                    "passed_cases": 0,
                    "failed_cases": len(test_cases),
                    "total_cases": len(test_cases),
                    "results": []
                }

            runner_cmd = [
                "java",
                "-cp",
                temp_dir,
                "Main"
            ]

        # ---------------------------------------------------------
        # Unknown language
        # ---------------------------------------------------------
        else:

            runner_cmd = [
                sys.executable,
                "-c",
                source_code
            ]

    except Exception as e:

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        return {
            "compile_status": "error",
            "compile_error": str(e),
            "execution_status": "compilation_error",
            "exit_code": 1,
            "stdout": "",
            "stderr": str(e),
            "runtime_ms": 0,
            "memory_kb": 0,
            "passed_cases": 0,
            "failed_cases": len(test_cases),
            "total_cases": len(test_cases),
            "results": []
        }

    passed_count = 0
    failed_count = 0

    results = []

    total_runtime_ms = 0

    first_stdout = ""

    for tc in test_cases:

        tc_id = str(
            tc.get(
                "id",
                "1"
            )
        )

        tc_input = str(
            tc.get(
                "input",
                ""
            )
        )

        expected_output = str(
            tc.get(
                "expected_output",
                tc.get(
                    "output",
                    ""
                )
            )
        )

        is_hidden = bool(
            tc.get(
                "is_hidden",
                tc.get(
                    "isHidden",
                    False
                )
            )
        )

        start = time.time()

        try:

            proc = subprocess.Popen(
                runner_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            out, err = proc.communicate(
                input=tc_input,
                timeout=2.5
            )

            elapsed_ms = max(
                1,
                int(
                    (time.time() - start) * 1000
                )
            )

            total_runtime_ms += elapsed_ms

            actual_out = out

            if not first_stdout and actual_out:
                first_stdout = actual_out

            # -----------------------------------------------------
            # Runtime error
            # -----------------------------------------------------
            if proc.returncode != 0:

                failed_count += 1

                results.append({
                    "test_case_id": tc_id,
                    "status": "runtime_error",
                    "runtime_ms": elapsed_ms,
                    "actual_output": actual_out,
                    "expected_output": expected_output,
                    "is_hidden": is_hidden,
                    "error_message": (
                        err.strip()
                        or f"Exit code {proc.returncode}"
                    )
                })

            # -----------------------------------------------------
            # Accepted
            # -----------------------------------------------------
            elif compare_outputs(
                actual_out,
                expected_output
            ):

                passed_count += 1

                results.append({
                    "test_case_id": tc_id,
                    "status": "accepted",
                    "runtime_ms": elapsed_ms,
                    "actual_output": actual_out,
                    "expected_output": expected_output,
                    "is_hidden": is_hidden,
                    "error_message": None
                })

            # -----------------------------------------------------
            # Wrong answer
            # -----------------------------------------------------
            else:

                failed_count += 1

                results.append({
                    "test_case_id": tc_id,
                    "status": "wrong_answer",
                    "runtime_ms": elapsed_ms,
                    "actual_output": actual_out,
                    "expected_output": expected_output,
                    "is_hidden": is_hidden,
                    "error_message": None
                })

        except subprocess.TimeoutExpired:

            failed_count += 1

            proc.kill()

            results.append({
                "test_case_id": tc_id,
                "status": "time_limit_exceeded",
                "runtime_ms": 2500,
                "actual_output": "",
                "expected_output": expected_output,
                "is_hidden": is_hidden,
                "error_message": (
                    "Execution timed out (2.5s)"
                )
            })

        except Exception as e:

            failed_count += 1

            results.append({
                "test_case_id": tc_id,
                "status": "system_error",
                "runtime_ms": 0,
                "actual_output": "",
                "expected_output": expected_output,
                "is_hidden": is_hidden,
                "error_message": str(e)
            })

    status_str = (
        "completed"
        if failed_count == 0
        else next(
            (
                str(result["status"])
                for result in results
                if result["status"] != "accepted"
            ),
            "wrong_answer"
        )
    )

    shutil.rmtree(
        temp_dir,
        ignore_errors=True
    )

    return {
        "compile_status": "success",
        "compile_error": None,
        "execution_status": status_str,
        "exit_code": (
            0
            if failed_count == 0
            else 1
        ),
        "stdout": (
            first_stdout
            or "Execution completed."
        ),
        "stderr": "",
        "runtime_ms": (
            total_runtime_ms
            // max(
                1,
                len(test_cases)
            )
        ),
        "memory_kb": 4096,
        "passed_cases": passed_count,
        "failed_cases": failed_count,
        "total_cases": len(test_cases),
        "results": results
    }


async def execute_code_sandboxed(
    source_code: str,
    language: str = "python",
    test_cases: List[Dict[str, Any]] = None,
    stop_on_first_failure: bool = False
) -> Dict[str, Any]:
    """
    Execute code in the Docker execution microservice.

    If the Docker microservice cannot be reached,
    fall back to local execution.
    """

    if isinstance(
        test_cases,
        str
    ):

        try:

            test_cases = json.loads(
                test_cases
            )

        except Exception:

            test_cases = []

    formatted_cases = []

    if test_cases:

        for idx, tc in enumerate(
            test_cases,
            start=1
        ):

            if isinstance(
                tc,
                str
            ):
                continue

            formatted_cases.append({
                "id": str(
                    tc.get(
                        "id",
                        idx
                    )
                ),
                "input": str(
                    tc.get(
                        "input",
                        ""
                    )
                ),
                "expected_output": str(
                    tc.get(
                        "expected_output",
                        tc.get(
                            "output",
                            ""
                        )
                    )
                ),
                "is_hidden": bool(
                    tc.get(
                        "is_hidden",
                        tc.get(
                            "isHidden",
                            False
                        )
                    )
                ),
                "time_limit": tc.get(
                    "time_limit",
                    2
                ),
                "memory_limit": tc.get(
                    "memory_limit",
                    256
                )
            })

    else:

        formatted_cases = [
            {
                "id": "1",
                "input": "2 7 11 15\n9",
                "expected_output": "[0, 1]",
                "is_hidden": False
            }
        ]

    # -------------------------------------------------------------
    # Python LeetCode-style submissions need the wrapper.
    #
    # C/C++/Java submissions are sent unchanged because they are
    # expected to be complete programs.
    # -------------------------------------------------------------
    execution_code = source_code

    if language.lower() in [
        "python",
        "python3",
        "py"
    ]:

        execution_code = wrap_python_leetcode(
            source_code
        )

    payload = {
        "code": execution_code,
        "language": language.lower(),
        "test_cases": formatted_cases,
        "time_limit": 2,
        "memory_limit": 256,
        "stop_on_first_failure": stop_on_first_failure
    }

    # -------------------------------------------------------------
    # 1. Try Docker execution microservice
    # -------------------------------------------------------------
    data = await asyncio.to_thread(
        _sync_request_docker,
        payload
    )

    if data and "results" in data:

        compile_status = (
            "success"
            if data.get(
                "compile_success",
                True
            )
            else "error"
        )

        compile_error = data.get(
            "compile_stderr"
        )

        # ---------------------------------------------------------
        # Compilation failure
        # ---------------------------------------------------------
        if compile_status == "error":

            return {
                "compile_status": "error",
                "compile_error": (
                    compile_error
                    or "Compilation failed."
                ),
                "execution_status": "compilation_error",
                "exit_code": 1,
                "stdout": "",
                "stderr": (
                    compile_error
                    or "Compilation failed."
                ),
                "runtime_ms": data.get(
                    "runtime_ms",
                    0
                ),
                "memory_kb": data.get(
                    "memory_kb",
                    0
                ),
                "passed_cases": 0,
                "failed_cases": 0,
                "total_cases": data.get(
                    "tests_total",
                    len(formatted_cases)
                ),
                "results": []
            }

        stdout_str = ""

        passed_count = 0
        failed_count = 0

        normalized_results = []

        for r in data.get(
            "results",
            []
        ):

            act = str(
                r.get(
                    "actual_output",
                    ""
                )
                or ""
            )

            exp = str(
                r.get(
                    "expected_output",
                    ""
                )
                or ""
            )

            if not stdout_str and act:
                stdout_str = act

            is_match = compare_outputs(
                act,
                exp
            )

            engine_status = str(
                r.get(
                    "status",
                    ""
                )
                or ""
            ).lower()

            if (
                is_match
                and engine_status in [
                    "accepted",
                    "completed",
                    ""
                ]
            ):

                passed_count += 1

                r["status"] = "accepted"

            else:

                failed_count += 1

                if engine_status == "accepted":
                    r["status"] = "wrong_answer"

            normalized_results.append(r)

        status_str = (
            "completed"
            if failed_count == 0
            else next(
                (
                    str(
                        result.get(
                            "status"
                        )
                    )
                    for result in normalized_results
                    if result.get(
                        "status"
                    ) != "accepted"
                ),
                "wrong_answer"
            )
        )

        return {
            "compile_status": compile_status,
            "compile_error": compile_error,
            "execution_status": status_str,
            "exit_code": (
                0
                if (
                    compile_status == "success"
                    and failed_count == 0
                )
                else 1
            ),
            "stdout": (
                stdout_str
                or "Execution completed."
            ),
            "stderr": (
                data.get(
                    "compile_stderr"
                )
                or ""
            ),
            "runtime_ms": data.get(
                "runtime_ms",
                15
            ),
            "memory_kb": data.get(
                "memory_kb",
                5240
            ),
            "passed_cases": passed_count,
            "failed_cases": failed_count,
            "total_cases": data.get(
                "tests_total",
                len(formatted_cases)
            ),
            "results": normalized_results
        }

    # -------------------------------------------------------------
    # 2. Local execution fallback
    # -------------------------------------------------------------
    local_res = await asyncio.to_thread(
        execute_locally,
        source_code,
        language,
        formatted_cases
    )

    return local_res