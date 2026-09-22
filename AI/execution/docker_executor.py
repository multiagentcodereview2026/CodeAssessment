import subprocess
import tempfile
import os


def execute_python(code: str, timeout: int = 10):

    with tempfile.TemporaryDirectory() as temp_dir:

        code_file = os.path.join(temp_dir, "main.py")

        with open(code_file, "w", encoding="utf-8") as file:
            file.write(code)

        command = [
            "docker",
            "run",
            "--rm",

            # Disable network access
            "--network", "none",

            # Limit memory
            "--memory", "128m",

            # Limit CPU
            "--cpus", "0.5",

            # Read-only container filesystem
            "--read-only",

            # Prevent privilege escalation
            "--security-opt", "no-new-privileges",

            # Mount only the submitted code
            "-v",
            f"{code_file}:/app/main.py:ro",

            "python:3.12-slim",

            "python",
            "/app/main.py"
        ]

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "timed_out": False
            }

        except subprocess.TimeoutExpired:

            return {
                "stdout": "",
                "stderr": "Execution timed out.",
                "exit_code": -1,
                "timed_out": True
            }