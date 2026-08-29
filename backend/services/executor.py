import subprocess
import tempfile
import os
import time


# ============================================================
# Common Docker security settings
# ============================================================

def build_docker_security_options():
    """
    Common security restrictions used for every submitted program.
    """

    return [
        "--rm",
        "-i",

        # No network access
        "--network", "none",

        # Prevent privilege escalation
        "--security-opt", "no-new-privileges",

        # Drop all Linux capabilities
        "--cap-drop", "ALL",

        # Memory limit
        "--memory", "128m",

        # CPU limit
        "--cpus", "0.5",

        # Process limit
        "--pids-limit", "64",

        # Read-only container filesystem
        "--read-only",

        # Writable temporary filesystem
        # exec is disabled here for security.
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=64m",

        # Writable + executable workspace.
        # Required for compiled C++/Java programs.
        "--tmpfs",
        "/app/work:rw,exec,nosuid,size=64m",
    ]


# ============================================================
# Generic Docker execution helper
# ============================================================

def run_docker_command(
    command,
    input_data: str,
    timeout: int = 2
):
    """
    Run a Docker command with resource and security restrictions.
    """

    start_time = time.perf_counter()

    try:

        process = subprocess.run(
            command,
            input=input_data,
            text=True,
            capture_output=True,
            timeout=timeout
        )

        execution_time = time.perf_counter() - start_time

        if process.returncode == 0:
            status = "SUCCESS"
        else:
            status = "RUNTIME_ERROR"

        return {
            "status": status,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "execution_time": round(execution_time, 4),
            "exit_code": process.returncode
        }

    except subprocess.TimeoutExpired:

        execution_time = time.perf_counter() - start_time

        return {
            "status": "TIMEOUT",
            "stdout": "",
            "stderr": "Execution timed out",
            "execution_time": round(execution_time, 4),
            "exit_code": -1
        }

    except Exception as e:

        execution_time = time.perf_counter() - start_time

        return {
            "status": "ERROR",
            "stdout": "",
            "stderr": str(e),
            "execution_time": round(execution_time, 4),
            "exit_code": -1
        }


# ============================================================
# Python
# ============================================================

def execute_python_code(
    code: str,
    input_data: str,
    timeout: int = 2
):
    """
    Execute untrusted Python code inside Docker.
    """

    temp_dir = tempfile.mkdtemp()

    code_file = os.path.join(
        temp_dir,
        "solution.py"
    )

    try:

        with open(
            code_file,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(code)

        command = [
            "docker",
            "run"
        ]

        command.extend(
            build_docker_security_options()
        )

        command.extend([
            "--mount",
            f"type=bind,source={code_file},target=/app/solution.py,readonly",

            "python:3.11-slim",

            "python",
            "/app/solution.py"
        ])

        return run_docker_command(
            command=command,
            input_data=input_data,
            timeout=timeout
        )

    finally:

        try:
            os.remove(code_file)
        except Exception:
            pass

        try:
            os.rmdir(temp_dir)
        except Exception:
            pass


# ============================================================
# C++
# ============================================================

def execute_cpp_code(
    code: str,
    input_data: str,
    timeout: int = 2
):
    """
    Compile and execute untrusted C++ code inside Docker.

    Compilation happens inside the container.
    The generated executable is stored in /app/work.
    """

    temp_dir = tempfile.mkdtemp()

    code_file = os.path.join(
        temp_dir,
        "solution.cpp"
    )

    try:

        with open(
            code_file,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(code)

        security_options = build_docker_security_options()

        command = [
            "docker",
            "run"
        ]

        command.extend(security_options)

        command.extend([
            "--mount",
            f"type=bind,source={code_file},target=/app/solution.cpp,readonly",

            "gcc:13",

            "sh",
            "-c",

            (
                "g++ /app/solution.cpp "
                "-std=c++17 "
                "-O2 "
                "-o /app/work/solution "
                "&& "
                "/app/work/solution"
            )
        ])

        return run_docker_command(
            command=command,
            input_data=input_data,
            timeout=timeout
        )

    finally:

        try:
            os.remove(code_file)
        except Exception:
            pass

        try:
            os.rmdir(temp_dir)
        except Exception:
            pass


# ============================================================
# Java
# ============================================================

def execute_java_code(
    code: str,
    input_data: str,
    timeout: int = 2
):
    """
    Compile and execute untrusted Java code inside Docker.

    The submitted Java program must contain:

        public class Main

    Compilation output is stored inside /app/work.
    """

    temp_dir = tempfile.mkdtemp()

    code_file = os.path.join(
        temp_dir,
        "Main.java"
    )

    try:

        with open(
            code_file,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(code)

        security_options = build_docker_security_options()

        command = [
            "docker",
            "run"
        ]

        command.extend(security_options)

        command.extend([
            "--mount",
            f"type=bind,source={code_file},target=/app/Main.java,readonly",

            "eclipse-temurin:17-jdk",

            "sh",
            "-c",

            (
                "javac "
                "-d /app/work "
                "/app/Main.java "
                "&& "
                "java "
                "-cp /app/work "
                "Main"
            )
        ])

        return run_docker_command(
            command=command,
            input_data=input_data,
            timeout=timeout
        )

    finally:

        try:
            os.remove(code_file)
        except Exception:
            pass

        try:
            os.rmdir(temp_dir)
        except Exception:
            pass


# ============================================================
# Multi-language executor
# ============================================================

def execute_code(
    language: str,
    code: str,
    input_data: str,
    timeout: int = 2
):
    """
    Execute code according to the selected programming language.

    Supported languages:
        - Python
        - C++
        - Java
    """

    if not language:
        return {
            "status": "ERROR",
            "stdout": "",
            "stderr": "Programming language is required",
            "execution_time": 0,
            "exit_code": -1
        }

    language_normalized = language.lower().strip()

    # --------------------------------------------------------
    # Python
    # --------------------------------------------------------

    if language_normalized in (
        "python",
        "python3",
        "py"
    ):
        return execute_python_code(
            code=code,
            input_data=input_data,
            timeout=timeout
        )

    # --------------------------------------------------------
    # C++
    # --------------------------------------------------------

    if language_normalized in (
        "cpp",
        "c++",
        "cxx"
    ):
        return execute_cpp_code(
            code=code,
            input_data=input_data,
            timeout=timeout
        )

    # --------------------------------------------------------
    # Java
    # --------------------------------------------------------

    if language_normalized in (
        "java"
    ):
        return execute_java_code(
            code=code,
            input_data=input_data,
            timeout=timeout
        )

    # --------------------------------------------------------
    # Unsupported language
    # --------------------------------------------------------

    return {
        "status": "ERROR",
        "stdout": "",
        "stderr": f"Unsupported language: {language}",
        "execution_time": 0,
        "exit_code": -1
    }