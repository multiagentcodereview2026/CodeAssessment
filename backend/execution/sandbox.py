import os
import shutil
import subprocess
import tempfile
import time
import uuid

from dataclasses import dataclass

from execution.languages import LanguageConfig
from models import VERDICT_ACCEPTED
from models import VERDICT_COMPILATION_ERROR
from models import VERDICT_MEMORY_LIMIT_EXCEEDED
from models import VERDICT_OUTPUT_LIMIT_EXCEEDED
from models import VERDICT_RUNTIME_ERROR
from models import VERDICT_SYSTEM_ERROR
from models import VERDICT_TIME_LIMIT_EXCEEDED
from models import VERDICT_WRONG_ANSWER


@dataclass
class SandboxRunResult:

    status: str
    runtime_ms: int
    memory_kb: int
    compile_success: bool
    compile_stderr: str | None
    actual_output: str | None
    stderr: str | None


def get_env_limit(key: str, default_val: str) -> str:
    return os.getenv(key, default_val)


def run_container_command(
    cmd_list: list[str],
    container_name: str,
    timeout_seconds: int,
    input_str: str | None = None,
    max_output_bytes: int = 1048576
) -> tuple[int, str, str, bool]:

    process = None
    stdout_data = ""
    stderr_data = ""
    timed_out = False

    try:
        process = subprocess.Popen(
            cmd_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout_data, stderr_data = process.communicate(
                input=input_str,
                timeout=timeout_seconds
            )
        except subprocess.TimeoutExpired:
            timed_out = True

            try:
                subprocess.run(
                    [
                        "docker",
                        "kill",
                        container_name
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
            except Exception:
                pass

            try:
                stdout_data, stderr_data = process.communicate(
                    timeout=2
                )
            except Exception:
                process.kill()

    except Exception as exc:
        return 1, "", str(exc), False

    if len(stdout_data) > max_output_bytes:
        stdout_data = stdout_data[:max_output_bytes]

    if len(stderr_data) > max_output_bytes:
        stderr_data = stderr_data[:max_output_bytes]

    return process.returncode if process else 1, stdout_data, stderr_data, timed_out


def execute_in_sandbox(
    code: str,
    lang_config: LanguageConfig,
    input_data: str,
    expected_output: str,
    time_limit: int | None = None,
    memory_limit: int | None = None
) -> SandboxRunResult:

    max_source_bytes = int(
        get_env_limit(
            "EXECUTION_MAX_SOURCE_BYTES",
            "65536"
        )
    )

    if len(code.encode("utf-8")) > max_source_bytes:
        return SandboxRunResult(
            status=VERDICT_COMPILATION_ERROR,
            runtime_ms=0,
            memory_kb=0,
            compile_success=False,
            compile_stderr=f"Source code exceeds maximum allowed size of {max_source_bytes} bytes",
            actual_output=None,
            stderr=None
        )

    cpu_limit = get_env_limit(
        "EXECUTION_CPU_LIMIT",
        "1.0"
    )

    mem_limit_str = (
        f"{memory_limit}m"
        if memory_limit
        else get_env_limit("EXECUTION_MEMORY_LIMIT", "256m")
    )

    timeout_sec = (
        time_limit
        if time_limit
        else int(get_env_limit("EXECUTION_TIMEOUT_SECONDS", "5"))
    )

    pids_limit = get_env_limit(
        "EXECUTION_MAX_PROCESSES",
        "64"
    )

    max_output_bytes = int(
        get_env_limit(
            "EXECUTION_MAX_OUTPUT_BYTES",
            "1048576"
        )
    )

    temp_dir = tempfile.mkdtemp(
        prefix="sandbox_"
    )

    try:
        source_path = os.path.join(
            temp_dir,
            lang_config.source_filename
        )

        with open(source_path, "w", encoding="utf-8") as f:
            f.write(code)

        if lang_config.compile_cmd:
            compile_container_name = f"compile_{uuid.uuid4().hex[:8]}"

            compile_cmd_list = [
                "docker",
                "run",
                "--name",
                compile_container_name,
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--tmpfs",
                "/tmp",
                "--pids-limit",
                pids_limit,
                "--memory",
                mem_limit_str,
                "--cpus",
                cpu_limit,
                "--user",
                "1000:1000",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "-v",
                f"{temp_dir}:/code",
                "-w",
                "/code",
                lang_config.docker_image
            ] + lang_config.compile_cmd

            returncode, stdout_data, stderr_data, timed_out = run_container_command(
                cmd_list=compile_cmd_list,
                container_name=compile_container_name,
                timeout_seconds=15,
                input_str=None,
                max_output_bytes=max_output_bytes
            )

            if timed_out:
                return SandboxRunResult(
                    status=VERDICT_TIME_LIMIT_EXCEEDED,
                    runtime_ms=15000,
                    memory_kb=0,
                    compile_success=False,
                    compile_stderr="Compilation timed out",
                    actual_output=None,
                    stderr=stderr_data
                )

            if returncode != 0:
                return SandboxRunResult(
                    status=VERDICT_COMPILATION_ERROR,
                    runtime_ms=0,
                    memory_kb=0,
                    compile_success=False,
                    compile_stderr=stderr_data or stdout_data or "Compilation failed",
                    actual_output=None,
                    stderr=stderr_data
                )

        run_container_name = f"run_{uuid.uuid4().hex[:8]}"

        run_cmd_list = [
            "docker",
            "run",
            "--name",
            run_container_name,
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--pids-limit",
            pids_limit,
            "--memory",
            mem_limit_str,
            "--cpus",
            cpu_limit,
            "--user",
            "1000:1000",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "-v",
            f"{temp_dir}:/code:ro",
            "-w",
            "/code",
            lang_config.docker_image
        ] + lang_config.run_cmd

        start_time = time.time()

        returncode, stdout_data, stderr_data, timed_out = run_container_command(
            cmd_list=run_cmd_list,
            container_name=run_container_name,
            timeout_seconds=timeout_sec,
            input_str=input_data,
            max_output_bytes=max_output_bytes
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        if timed_out:
            return SandboxRunResult(
                status=VERDICT_TIME_LIMIT_EXCEEDED,
                runtime_ms=timeout_sec * 1000,
                memory_kb=0,
                compile_success=True,
                compile_stderr=None,
                actual_output=stdout_data,
                stderr=stderr_data
            )

        if returncode == 137:
            return SandboxRunResult(
                status=VERDICT_MEMORY_LIMIT_EXCEEDED,
                runtime_ms=elapsed_ms,
                memory_kb=0,
                compile_success=True,
                compile_stderr=None,
                actual_output=stdout_data,
                stderr=stderr_data
            )

        if len(stdout_data) >= max_output_bytes:
            return SandboxRunResult(
                status=VERDICT_OUTPUT_LIMIT_EXCEEDED,
                runtime_ms=elapsed_ms,
                memory_kb=0,
                compile_success=True,
                compile_stderr=None,
                actual_output=stdout_data,
                stderr=stderr_data
            )

        if returncode != 0:
            return SandboxRunResult(
                status=VERDICT_RUNTIME_ERROR,
                runtime_ms=elapsed_ms,
                memory_kb=0,
                compile_success=True,
                compile_stderr=None,
                actual_output=stdout_data,
                stderr=stderr_data or f"Exit code {returncode}"
            )

        normalized_actual = stdout_data.strip().replace("\r\n", "\n")
        normalized_expected = expected_output.strip().replace("\r\n", "\n")

        if normalized_actual == normalized_expected:
            status = VERDICT_ACCEPTED
        else:
            status = VERDICT_WRONG_ANSWER

        return SandboxRunResult(
            status=status,
            runtime_ms=elapsed_ms,
            memory_kb=0,
            compile_success=True,
            compile_stderr=None,
            actual_output=stdout_data,
            stderr=stderr_data
        )

    except Exception as exc:
        return SandboxRunResult(
            status=VERDICT_SYSTEM_ERROR,
            runtime_ms=0,
            memory_kb=0,
            compile_success=False,
            compile_stderr=None,
            actual_output=None,
            stderr=str(exc)
        )

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )
