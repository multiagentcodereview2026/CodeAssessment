import subprocess
import tempfile
import os
import time


def execute_python_code(
    code: str,
    input_data: str,
    timeout: int = 2
):
    """
    Execute untrusted Python code inside a Docker container.

    The container:
    - has no network access
    - has limited memory
    - has limited CPU
    - is automatically removed
    - runs with no privileges
    """

    temp_dir = tempfile.mkdtemp()

    try:
        code_file = os.path.join(temp_dir, "solution.py")

        with open(
            code_file,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(code)

        command = [
            "docker",
            "run",
            "--rm",
            # Keep stdin open
            "-i",

            # No network access
            "--network", "none",

            # Prevent privilege escalation
            "--security-opt", "no-new-privileges",

            # Drop Linux capabilities
            "--cap-drop", "ALL",

            # Memory limit
            "--memory", "128m",

            # CPU limit
            "--cpus", "0.5",

            # Process limit
            "--pids-limit", "64",

            # Read-only container filesystem
            "--read-only",

            # Temporary writable filesystem
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",

            # Mount only the source file
            "--mount",
            f"type=bind,source={code_file},target=/app/solution.py,readonly",

            "python:3.11-slim",

            "python",
            "/app/solution.py"
        ]

        start_time = time.perf_counter()

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
        return {
            "status": "TIMEOUT",
            "stdout": "",
            "stderr": "Execution timed out",
            "execution_time": timeout,
            "exit_code": -1
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "stdout": "",
            "stderr": str(e),
            "execution_time": 0,
            "exit_code": -1
        }

    finally:
        try:
            os.remove(code_file)
            os.rmdir(temp_dir)
        except Exception:
            pass