import os
import shutil
import subprocess
import tempfile
import time
import uuid

from app.languages import LanguageConfig
from app.models import SandboxRunResult
from app.models import VERDICT_ACCEPTED
from app.models import VERDICT_COMPILATION_ERROR
from app.models import VERDICT_MEMORY_LIMIT_EXCEEDED
from app.models import VERDICT_OUTPUT_LIMIT_EXCEEDED
from app.models import VERDICT_RUNTIME_ERROR
from app.models import VERDICT_SYSTEM_ERROR
from app.models import VERDICT_TIME_LIMIT_EXCEEDED
from app.models import VERDICT_WRONG_ANSWER


def normalize_output(value: str) -> str:
    """Allow only trailing whitespace and final-newline differences."""
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.rstrip("\n")
    return "\n".join(line.rstrip(" \t") for line in text.split("\n"))


def get_env_limit(key: str, default_val: str) -> str:
    return os.getenv(key, default_val)


def is_docker_available() -> bool:
    try:
        res = subprocess.run(
            ["docker", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.5
        )
        return res.returncode == 0
    except Exception:
        return False


def run_local_process_command(
    cmd_list: list[str],
    cwd: str,
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
            cwd=cwd,
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
            process.kill()
            try:
                stdout_data, stderr_data = process.communicate(timeout=1)
            except Exception:
                pass
    except Exception as exc:
        return 1, "", str(exc), False

    if len(stdout_data) > max_output_bytes:
        stdout_data = stdout_data[:max_output_bytes]
    if len(stderr_data) > max_output_bytes:
        stderr_data = stderr_data[:max_output_bytes]

    return process.returncode if process else 1, stdout_data, stderr_data, timed_out


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


def prepare_submission_workspace(code: str, lang_config: LanguageConfig) -> dict | None:
    """Create one disposable workspace for a whole submission.

    Compiled languages use this workspace to compile once and let every
    isolated test runner read the resulting binary.
    """
    if not is_docker_available():
        return None

    sandbox_volume = os.getenv("SANDBOX_VOLUME", "").strip()
    if sandbox_volume:
        workspace_root = os.getenv("SANDBOX_WORKSPACE_ROOT", "/sandbox")
        os.makedirs(workspace_root, exist_ok=True)
        temp_dir = os.path.join(workspace_root, f"sandbox_{uuid.uuid4().hex}")
        os.makedirs(temp_dir, exist_ok=False)
        docker_mount = f"{sandbox_volume}:/code"
        docker_workdir = f"/code/{os.path.basename(temp_dir)}"
    else:
        temp_dir = tempfile.mkdtemp(prefix="sandbox_")
        docker_mount = f"{temp_dir}:/code"
        docker_workdir = "/code"

    os.chmod(temp_dir, 0o777)
    with open(os.path.join(temp_dir, lang_config.source_filename), "w", encoding="utf-8") as source_file:
        source_file.write(code)
    return {"temp_dir": temp_dir, "docker_mount": docker_mount, "docker_workdir": docker_workdir}


def cleanup_submission_workspace(workspace: dict | None) -> None:
    if workspace and os.path.exists(workspace["temp_dir"]):
        shutil.rmtree(workspace["temp_dir"], ignore_errors=True)


def execute_in_sandbox(
    code: str,
    lang_config: LanguageConfig,
    input_data: str,
    expected_output: str,
    time_limit: int | None = None,
    memory_limit: int | None = None,
    workspace: dict | None = None,
    should_compile: bool = True
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
            compile_stderr=f"Source code exceeds limit of {max_source_bytes} bytes",
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
    # Docker Desktop may briefly delay an otherwise-ready process under
    # concurrent runner creation. Keep the judge bounded, while giving that
    # platform scheduling delay a small allowance.
    runner_timeout_sec = timeout_sec + int(
        get_env_limit("EXECUTION_DOCKER_SCHEDULING_GRACE_SECONDS", "3")
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

    # A Docker daemon cannot bind-mount a path that exists only inside this
    # service container. When the engine runs in Compose, use a named volume
    # shared with the short-lived runner containers instead.
    use_docker = is_docker_available()
    owns_workspace = workspace is None
    sandbox_volume = os.getenv("SANDBOX_VOLUME", "").strip()
    if workspace:
        temp_dir = workspace["temp_dir"]
        docker_mount = workspace["docker_mount"]
        docker_workdir = workspace["docker_workdir"]
    elif use_docker and sandbox_volume:
        workspace_root = os.getenv("SANDBOX_WORKSPACE_ROOT", "/sandbox")
        os.makedirs(workspace_root, exist_ok=True)
        temp_dir = os.path.join(workspace_root, f"sandbox_{uuid.uuid4().hex}")
        os.makedirs(temp_dir, exist_ok=False)
        docker_mount = f"{sandbox_volume}:/code"
        docker_workdir = f"/code/{os.path.basename(temp_dir)}"
    else:
        temp_dir = tempfile.mkdtemp(prefix="sandbox_")
        docker_mount = f"{temp_dir}:/code"
        docker_workdir = "/code"

    # Runner containers execute as UID 1000. They must be able to read the
    # submission and, for compiled languages, write the resulting binary.
    # This is confined to the disposable per-run workspace.
    if use_docker:
        os.chmod(temp_dir, 0o777)

    try:
        if owns_workspace:
            source_path = os.path.join(temp_dir, lang_config.source_filename)
            with open(source_path, "w", encoding="utf-8") as f:
                f.write(code)

        if use_docker:
            if should_compile and lang_config.compile_cmd:
                compile_name = f"compile_{uuid.uuid4().hex[:8]}"

                compile_cmd = [
                    "docker",
                    "run",
                    "--name",
                    compile_name,
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
                    docker_mount,
                    "-w",
                    docker_workdir,
                    lang_config.docker_image
                ] + lang_config.compile_cmd

                returncode, stdout_data, stderr_data, timed_out = run_container_command(
                    cmd_list=compile_cmd,
                    container_name=compile_name,
                    timeout_seconds=15,
                    input_str=None,
                    max_output_bytes=max_output_bytes
                )

                if timed_out or returncode != 0:
                    return SandboxRunResult(
                        status=VERDICT_COMPILATION_ERROR,
                        runtime_ms=0,
                        memory_kb=0,
                        compile_success=False,
                        compile_stderr=stderr_data or stdout_data or "Compilation failed",
                        actual_output=None,
                        stderr=stderr_data
                    )

            run_name = f"run_{uuid.uuid4().hex[:8]}"
            # The outer command includes Docker startup/cleanup, which must not
            # be charged to the student's algorithm. `timeout` runs inside the
            # disposable runner container and enforces the real judge limit.
            runner_cmd = [
                "timeout",
                "--signal=KILL",
                f"{runner_timeout_sec}s",
            ] + lang_config.run_cmd

            run_cmd = [
                "docker",
                "run",
                "-i",
                "--name",
                run_name,
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
                f"{docker_mount}:ro",
                "-w",
                docker_workdir,
                lang_config.docker_image
            ] + runner_cmd

            # A wall-clock adjustment can make a short runner appear to have
            # a negative duration.  Monotonic time is stable for measurement.
            start_time = time.monotonic()
            formatted_input = (
                input_data
                if input_data.endswith("\n")
                else f"{input_data}\n"
            )

            returncode, stdout_data, stderr_data, timed_out = run_container_command(
                cmd_list=run_cmd,
                container_name=run_name,
                timeout_seconds=runner_timeout_sec + int(get_env_limit("EXECUTION_DOCKER_STARTUP_GRACE_SECONDS", "5")),
                input_str=formatted_input,
                max_output_bytes=max_output_bytes
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
        else:
            # Local Sandboxed Fallback
            if lang_config.compile_cmd:
                local_compile = list(lang_config.compile_cmd)
                if shutil.which(local_compile[0]):
                    returncode, stdout_data, stderr_data, timed_out = run_local_process_command(
                        cmd_list=local_compile,
                        cwd=temp_dir,
                        timeout_seconds=15,
                        input_str=None,
                        max_output_bytes=max_output_bytes
                    )
                    if timed_out or returncode != 0:
                        return SandboxRunResult(
                            status=VERDICT_COMPILATION_ERROR,
                            runtime_ms=0,
                            memory_kb=0,
                            compile_success=False,
                            compile_stderr=stderr_data or stdout_data or "Local compilation failed",
                            actual_output=None,
                            stderr=stderr_data
                        )

            local_run = list(lang_config.run_cmd)
            # Normalize python command on Windows if python3 is not in PATH
            if local_run and local_run[0] == "python3" and not shutil.which("python3"):
                import sys
                local_run[0] = sys.executable

            start_time = time.monotonic()
            formatted_input = (
                input_data
                if input_data.endswith("\n")
                else f"{input_data}\n"
            )

            returncode, stdout_data, stderr_data, timed_out = run_local_process_command(
                cmd_list=local_run,
                cwd=temp_dir,
                timeout_seconds=timeout_sec,
                input_str=formatted_input,
                max_output_bytes=max_output_bytes
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)

        clean_stderr = ""
        if stderr_data:
            lines = [
                line
                for line in stderr_data.splitlines()
                if not line.startswith("Unable to find image")
                and not line.startswith("Status: Downloaded")
                and not line.startswith("Digest: sha256")
                and "Pulling" not in line
            ]
            clean_stderr = "\n".join(lines).strip()

        if timed_out or returncode == 124:
            return SandboxRunResult(
                status=VERDICT_TIME_LIMIT_EXCEEDED,
                runtime_ms=runner_timeout_sec * 1000,
                memory_kb=0,
                compile_success=True,
                compile_stderr=None,
                actual_output=stdout_data,
                stderr=clean_stderr or "Execution timed out"
            )

        if returncode == 137:
            return SandboxRunResult(
                status=VERDICT_MEMORY_LIMIT_EXCEEDED,
                runtime_ms=elapsed_ms,
                memory_kb=0,
                compile_success=True,
                compile_stderr=None,
                actual_output=stdout_data,
                stderr=clean_stderr
            )

        if returncode != 0:
            return SandboxRunResult(
                status=VERDICT_RUNTIME_ERROR,
                runtime_ms=elapsed_ms,
                memory_kb=0,
                compile_success=True,
                compile_stderr=None,
                actual_output=stdout_data,
                stderr=clean_stderr or f"Exit code {returncode}"
            )

        normalized_actual = normalize_output(stdout_data)
        normalized_expected = normalize_output(expected_output)

        is_accepted = normalized_actual == normalized_expected
        if not is_accepted:
            try:
                import json
                if json.loads(normalized_actual) == json.loads(normalized_expected):
                    is_accepted = True
            except Exception:
                pass
        status = (
            VERDICT_ACCEPTED
            if is_accepted
            else VERDICT_WRONG_ANSWER
        )

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
        if owns_workspace and os.path.exists(temp_dir):
            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )
