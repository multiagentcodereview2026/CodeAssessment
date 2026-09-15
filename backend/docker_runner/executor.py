import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from typing import Any, Dict, List
import requests

logger = logging.getLogger(__name__)

DOCKER_ENGINE_URL = os.getenv("DOCKER_ENGINE_URL", "http://localhost:8001/execute")
DOCKER_ENGINE_REQUEST_TIMEOUT_SECONDS = int(os.getenv("DOCKER_ENGINE_REQUEST_TIMEOUT_SECONDS", "120"))


def wrap_python_leetcode(code: str) -> str:
    """Wraps user's Solution class or standalone function with a smart CLI test harness."""
    # Normalized Newfacade problems require a complete stdin/stdout program.
    # Do not append the legacy method-call harness when a student has supplied
    # a normal Python entry point.
    if "input(" in code or "sys.stdin" in code or "def main(" in code or "__name__" in code:
        return code

    harness = f"""import sys, json, ast

{code}

def _run_harness():
    raw = sys.stdin.read().strip()
    if not raw:
        return

    target_func = None
    if 'Solution' in globals():
        sol = Solution()
        methods = [m for m in dir(sol) if not m.startswith('_') and callable(getattr(sol, m))]
        if methods:
            target_func = getattr(sol, methods[0])

    if not target_func:
        user_funcs = [v for k, v in globals().items() if callable(v) and not k.startswith('_') and k != '_run_harness']
        if user_funcs:
            target_func = user_funcs[-1]

    if not target_func:
        return

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    args = []
    for line in lines:
        try:
            val = ast.literal_eval(line)
            args.append(val)
        except Exception:
            parts = line.split()
            if len(parts) > 1:
                args.append([int(p) if (p.isdigit() or (p.startswith('-') and p[1:].isdigit())) else p for p in parts])
            elif parts and (parts[0].isdigit() or (parts[0].startswith('-') and parts[0][1:].isdigit())):
                args.append(int(parts[0]))
            else:
                args.append(line)
    try:
        res = target_func(*args)
        if isinstance(res, bool):
            print('true' if res else 'false')
        elif isinstance(res, (list, dict, tuple)):
            print(json.dumps(res))
        else:
            print(res)
    except TypeError:
        try:
            res = target_func(args)
            if isinstance(res, bool):
                print('true' if res else 'false')
            elif isinstance(res, (list, dict, tuple)):
                print(json.dumps(res))
            else:
                print(res)
        except Exception as err:
            print('Runtime Error: ' + str(err), file=sys.stderr)
            sys.exit(1)
    except Exception as err:
        print('Runtime Error: ' + str(err), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    _run_harness()
"""
    return harness


def normalize_output(value: str) -> str:
    """Ignore only non-semantic output formatting differences.
    Leading whitespace and whitespace *inside* a line can be meaningful.  The
    judge accepts trailing spaces/tabs on each line and an optional final
    newline, but it does not collapse arbitrary whitespace.
    """
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.rstrip("\n")
    return "\n".join(line.rstrip(" \t") for line in text.split("\n"))


def compare_outputs(actual: str, expected: str) -> bool:
    """Compare stdout while preserving meaningful content."""
    act = normalize_output(actual)
    exp = normalize_output(expected)

    if act == exp:
        return True

    try:
        if json.loads(act) == json.loads(exp):
            return True
    except Exception:
        pass

    return False


VERDICT_REASONS = {
    "WRONG_ANSWER": "Your output did not match the expected output.",
    "RUNTIME_ERROR": "Your program ended with a runtime error.",
    "TIME_LIMIT_EXCEEDED": "Your program exceeded the time limit.",
    "MEMORY_LIMIT_EXCEEDED": "Your program exceeded the memory limit.",
    "OUTPUT_LIMIT_EXCEEDED": "Your program produced too much output.",
    "SYSTEM_ERROR": "The test could not be evaluated because of a system error.",
}


def _failed_case_summary(ordinal: int, status: Any, is_hidden: bool) -> Dict[str, Any] | None:
    """Create student-safe failure metadata without any test data."""
    normalized_status = str(status or "SYSTEM_ERROR").strip().upper()
    if normalized_status in {"ACCEPTED", "COMPLETED"}:
        return None

    return {
        "ordinal": max(1, int(ordinal)),
        "status": normalized_status,
        "reason": VERDICT_REASONS.get(normalized_status, "This test did not pass."),
        "is_hidden": bool(is_hidden),
    }


def _last_failed_case_summary(
    results: List[Dict[str, Any]],
    test_cases: List[Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Find the last failure in stored testcase order, not runner finish order."""
    ordinal_by_id = {
        str(case.get("id", index)): index
        for index, case in enumerate(test_cases, start=1)
    }
    last_failure = None

    for fallback_ordinal, result in enumerate(results, start=1):
        if not isinstance(result, dict):
            continue
        ordinal = ordinal_by_id.get(
            str(result.get("test_case_id", "")),
            fallback_ordinal,
        )
        summary = _failed_case_summary(
            ordinal=ordinal,
            status=result.get("status"),
            is_hidden=bool(result.get("is_hidden")),
        )
        if summary is not None:
            last_failure = summary

    return last_failure


def _sanitize_engine_failed_case_summary(value: Any) -> Dict[str, Any] | None:
    """Keep only the fixed, safe fields from the execution-service summary."""
    if not isinstance(value, dict):
        return None
    try:
        ordinal = int(value.get("ordinal"))
    except (TypeError, ValueError):
        return None
    return _failed_case_summary(
        ordinal=ordinal,
        status=value.get("status"),
        is_hidden=bool(value.get("is_hidden")),
    )


def _redact_hidden_case_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Remove raw judge diagnostics from a hidden testcase result."""
    safe_result = dict(result)
    if safe_result.get("is_hidden"):
        for field in (
            "input",
            "expected_output",
            "actual_output",
            "stderr",
            "error_message",
        ):
            safe_result.pop(field, None)
    return safe_result


def _sync_request_docker(payload: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        response = requests.post(
            DOCKER_ENGINE_URL,
            json=payload,
            timeout=DOCKER_ENGINE_REQUEST_TIMEOUT_SECONDS
        )
        if response.status_code == 200:
            data = response.json()
            for r in data.get("results", []):
                err = str(r.get("stderr", "") or "")
                if "failed to connect to the docker API" in err or "daemon is running" in err or "dockerDesktopLinuxEngine" in err:
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
    """Fallback execution for Python, C, C++, and Java stdin/stdout programs."""
    lang = language.lower()
    temp_dir = tempfile.mkdtemp()
    
    try:
        if lang in ["python", "python3", "py"]:
            runner_cmd = [sys.executable, "-c", source_code]
        elif lang in ["cpp", "c++", "c"]:
            compiler = "g++" if "cpp" in lang or "c++" in lang else "gcc"
            ext = ".cpp" if "cpp" in lang or "c++" in lang else ".c"
            src_path = os.path.join(temp_dir, f"solution{ext}")
            bin_path = os.path.join(temp_dir, "solution.exe" if os.name == "nt" else "solution")
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(source_code)
            
            comp_proc = subprocess.run([compiler, "-O2", src_path, "-o", bin_path], capture_output=True, text=True)
            if comp_proc.returncode != 0:
                return {
                    "compile_status": "error",
                    "compile_error": comp_proc.stderr or "Compilation failed.",
                    "execution_status": "compilation_error",
                    "exit_code": comp_proc.returncode,
                    "stdout": "",
                    "stderr": comp_proc.stderr or "Compilation failed.",
                    "runtime_ms": 0,
                    "memory_kb": 0,
                    "passed_cases": 0,
                    "failed_cases": len(test_cases),
                    "total_cases": len(test_cases),
                    "results": []
                }
            runner_cmd = [bin_path]
        elif lang in ["java"]:
            src_path = os.path.join(temp_dir, "Main.java")
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(source_code)
            comp_proc = subprocess.run(["javac", src_path], capture_output=True, text=True)
            if comp_proc.returncode != 0:
                return {
                    "compile_status": "error",
                    "compile_error": comp_proc.stderr or "Compilation failed.",
                    "execution_status": "compilation_error",
                    "exit_code": comp_proc.returncode,
                    "stdout": "",
                    "stderr": comp_proc.stderr or "Compilation failed.",
                    "runtime_ms": 0,
                    "memory_kb": 0,
                    "passed_cases": 0,
                    "failed_cases": len(test_cases),
                    "total_cases": len(test_cases),
                    "results": []
                }
            runner_cmd = ["java", "-cp", temp_dir, "Main"]
        else:
            runner_cmd = [sys.executable, "-c", source_code]
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
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
        tc_id = str(tc.get("id", "1"))
        tc_input = str(tc.get("input", ""))
        expected_output = str(tc.get("expected_output", tc.get("output", "")))
        is_hidden = bool(tc.get("is_hidden", tc.get("isHidden", False)))

        start = time.time()
        try:
            proc = subprocess.Popen(
                runner_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            out, err = proc.communicate(input=tc_input, timeout=2.5)
            elapsed_ms = max(1, int((time.time() - start) * 1000))
            total_runtime_ms += elapsed_ms

            actual_out = out
            # A top-level stdout preview must never accidentally contain the
            # output of a hidden test in the local fallback path.
            if not is_hidden and not first_stdout and actual_out:
                first_stdout = actual_out

            if proc.returncode != 0:
                failed_count += 1
                results.append({
                    "test_case_id": tc_id,
                    "status": "runtime_error",
                    "runtime_ms": elapsed_ms,
                    "actual_output": None if is_hidden else actual_out,
                    "expected_output": None if is_hidden else expected_output,
                    "is_hidden": is_hidden,
                    "error_message": None if is_hidden else (err.strip() or f"Exit code {proc.returncode}")
                })
            elif compare_outputs(actual_out, expected_output):
                passed_count += 1
                results.append({
                    "test_case_id": tc_id,
                    "status": "accepted",
                    "runtime_ms": elapsed_ms,
                    "actual_output": None if is_hidden else actual_out,
                    "expected_output": None if is_hidden else expected_output,
                    "is_hidden": is_hidden,
                    "error_message": None
                })
            else:
                failed_count += 1
                results.append({
                    "test_case_id": tc_id,
                    "status": "wrong_answer",
                    "runtime_ms": elapsed_ms,
                    "actual_output": None if is_hidden else actual_out,
                    "expected_output": None if is_hidden else expected_output,
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
                "actual_output": None if is_hidden else "",
                "expected_output": None if is_hidden else expected_output,
                "is_hidden": is_hidden,
                "error_message": None if is_hidden else "Execution timed out (2.5s)"
            })
        except Exception as e:
            failed_count += 1
            results.append({
                "test_case_id": tc_id,
                "status": "system_error",
                "runtime_ms": 0,
                "actual_output": None if is_hidden else "",
                "expected_output": None if is_hidden else expected_output,
                "is_hidden": is_hidden,
                "error_message": None if is_hidden else str(e)
            })

    status_str = "completed" if failed_count == 0 else next(
        (str(result["status"]) for result in results if result["status"] != "accepted"),
        "wrong_answer"
    )

    shutil.rmtree(temp_dir, ignore_errors=True)
    return {
        "compile_status": "success",
        "compile_error": None,
        "execution_status": status_str,
        "exit_code": 0 if failed_count == 0 else 1,
        "stdout": first_stdout or "Execution completed.",
        "stderr": "",
        "runtime_ms": total_runtime_ms // max(1, len(test_cases)),
        "memory_kb": 4096,
        "passed_cases": passed_count,
        "failed_cases": failed_count,
        "total_cases": len(test_cases),
        "results": results,
        "last_failed_case": _last_failed_case_summary(results, test_cases),
    }


async def execute_code_sandboxed(
    source_code: str,
    language: str = "python",
    test_cases: List[Dict[str, Any]] = None,
    stop_on_first_failure: bool = False
) -> Dict[str, Any]:
    """
    Executes code in isolated sandbox (Docker microservice or local containerized harness).
    """
    if isinstance(test_cases, str):
        try:
            test_cases = json.loads(test_cases)
        except Exception:
            test_cases = []

    formatted_cases = []
    if test_cases:
        for idx, tc in enumerate(test_cases, start=1):
            if isinstance(tc, str):
                continue
            formatted_cases.append({
                "id": str(tc.get("id", idx)),
                "input": str(tc.get("input", "")),
                "expected_output": str(tc.get("expected_output", tc.get("output", ""))),
                "is_hidden": bool(tc.get("is_hidden", tc.get("isHidden", False))),
                "time_limit": tc.get("time_limit", 2),
                "memory_limit": tc.get("memory_limit", 256)
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

    payload = {
        # All languages receive the complete program the student typed.  No
        # method-name or LeetCode Solution-class harness is injected.
        "code": source_code,
        "language": language.lower(),
        "test_cases": formatted_cases,
        "time_limit": 2,
        "memory_limit": 256,
        "stop_on_first_failure": stop_on_first_failure
    }

    # 1. Try Docker microservice asynchronously
    data = await asyncio.to_thread(_sync_request_docker, payload)

    if data and "results" in data:
        compile_status = "success" if data.get("compile_success", True) else "error"
        compile_error = data.get("compile_stderr")

        # A compiler failure happens before a program exists to run.  Do not
        # present the compiler's placeholder first case as a failed test: no
        # public or hidden input was executed.
        if compile_status == "error":
            return {
                "compile_status": "error",
                "compile_error": compile_error or "Compilation failed.",
                "execution_status": "compilation_error",
                "exit_code": 1,
                "stdout": "",
                "stderr": compile_error or "Compilation failed.",
                "runtime_ms": data.get("runtime_ms", 0),
                "memory_kb": data.get("memory_kb", 0),
                "passed_cases": 0,
                "failed_cases": 0,
                "total_cases": data.get("tests_total", len(formatted_cases)),
                "results": [],
                "last_failed_case": None,
            }

        stdout_str = ""
        passed_count = 0
        failed_count = 0
        normalized_results = []

        for raw_result in data.get("results", []):
            r = _redact_hidden_case_result(raw_result)
            act = str(r.get("actual_output") or "")
            exp = str(r.get("expected_output") or "")
            if not bool(r.get("is_hidden")) and not stdout_str and act:
                stdout_str = act

            is_match = compare_outputs(act, exp)
            engine_status = str(r.get("status") or "").lower()
            if is_match and engine_status in ["accepted", "completed", ""]:
                passed_count += 1
                r["status"] = "accepted"
            else:
                failed_count += 1
                if engine_status == "accepted":
                    r["status"] = "wrong_answer"
            normalized_results.append(r)

        status_str = "completed" if failed_count == 0 else next(
            (str(result.get("status")) for result in normalized_results if result.get("status") != "accepted"),
            "wrong_answer"
        )

        return {
            "compile_status": compile_status,
            "compile_error": compile_error,
            "execution_status": status_str,
            "exit_code": 0 if compile_status == "success" and failed_count == 0 else 1,
            "stdout": stdout_str or "Execution completed.",
            "stderr": data.get("compile_stderr") or "",
            "runtime_ms": data.get("runtime_ms", 15),
            "memory_kb": data.get("memory_kb", 5240),
            "passed_cases": passed_count,
            "failed_cases": failed_count,
            "total_cases": data.get("tests_total", len(formatted_cases)),
            "results": normalized_results,
            "last_failed_case": (
                _sanitize_engine_failed_case_summary(data.get("last_failed_case"))
                or _last_failed_case_summary(normalized_results, formatted_cases)
            ),
        }

    # 2. Local execution fallback
    local_res = await asyncio.to_thread(execute_locally, source_code, language, formatted_cases)
    return local_res
