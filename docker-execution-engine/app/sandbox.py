import os
import shutil
import subprocess
import tempfile
import threading
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


def run_container_command(
    cmd_list: list[str],
    container_name: str,
    timeout_seconds: int,
    input_str: str | None = None,
    max_output_bytes: int = 1048576
) -> tuple[int, str, str, bool, bool]:
    process = None
    stdout_data = bytearray()
    stderr_data = bytearray()
    timed_out = False
    output_limited = threading.Event()
    output_lock = threading.Lock()
    output_bytes = 0

    def drain(stream, destination: bytearray) -> None:
        nonlocal output_bytes
        while True:
            chunk = stream.read(8192)
            if not chunk:
                return
            with output_lock:
                remaining = max(0, max_output_bytes - output_bytes)
                if remaining:
                    destination.extend(chunk[:remaining])
                output_bytes += len(chunk)
                if output_bytes > max_output_bytes:
                    output_limited.set()

    try:
        process = subprocess.Popen(
            cmd_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
        )
        stdout_reader = threading.Thread(target=drain, args=(process.stdout, stdout_data), daemon=True)
        stderr_reader = threading.Thread(target=drain, args=(process.stderr, stderr_data), daemon=True)
        stdout_reader.start()
        stderr_reader.start()

        try:
            if input_str is not None:
                process.stdin.write(input_str.encode("utf-8"))
                process.stdin.flush()
            process.stdin.close()
        except (BrokenPipeError, OSError):
            pass

        deadline = time.monotonic() + timeout_seconds
        while process.poll() is None:
            if output_limited.is_set():
                break
            remaining_seconds = deadline - time.monotonic()
            if remaining_seconds <= 0:
                timed_out = True
                break
            time.sleep(min(0.02, remaining_seconds))

        if timed_out or output_limited.is_set():
            try:
                subprocess.run(
                    ["docker", "kill", container_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                    check=False,
                )
            except Exception:
                pass
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)

        stdout_reader.join(timeout=2)
        stderr_reader.join(timeout=2)
    except Exception as exc:
        if process and process.poll() is None:
            process.kill()
        return 1, "", str(exc), False, False

    return (
        process.returncode if process else 1,
        stdout_data.decode("utf-8", errors="replace"),
        stderr_data.decode("utf-8", errors="replace"),
        timed_out,
        output_limited.is_set(),
    )


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
    # The program's timeout must stay equal to the judge limit. Allow extra
    # time only around the outer Docker command for scheduling and startup.
    scheduling_grace_sec = int(
        get_env_limit("EXECUTION_DOCKER_SCHEDULING_GRACE_SECONDS", "3")
    )
    timeout_kill_grace_sec = 1

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
    if not use_docker:
        return SandboxRunResult(
            status=VERDICT_SYSTEM_ERROR,
            runtime_ms=0,
            memory_kb=0,
            compile_success=False,
            compile_stderr="Docker execution sandbox is unavailable; student code was not run.",
            actual_output=None,
            stderr="Docker execution sandbox is unavailable; student code was not run."
        )
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

                returncode, stdout_data, stderr_data, timed_out, output_limited = run_container_command(
                    cmd_list=compile_cmd,
                    container_name=compile_name,
                    timeout_seconds=15,
                    input_str=None,
                    max_output_bytes=max_output_bytes
                )

                if output_limited:
                    return SandboxRunResult(
                        status=VERDICT_OUTPUT_LIMIT_EXCEEDED,
                        runtime_ms=0,
                        memory_kb=0,
                        compile_success=False,
                        compile_stderr="Compiler produced too much output.",
                        actual_output=None,
                        stderr=stderr_data,
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
                "--signal=TERM",
                f"--kill-after={timeout_kill_grace_sec}s",
                f"{timeout_sec}s",
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

            returncode, stdout_data, stderr_data, timed_out, output_limited = run_container_command(
                cmd_list=run_cmd,
                container_name=run_name,
                timeout_seconds=(
                    timeout_sec
                    + timeout_kill_grace_sec
                    + scheduling_grace_sec
                    + int(get_env_limit("EXECUTION_DOCKER_STARTUP_GRACE_SECONDS", "5"))
                ),
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

        if output_limited:
            return SandboxRunResult(
                status=VERDICT_OUTPUT_LIMIT_EXCEEDED,
                runtime_ms=elapsed_ms,
                memory_kb=0,
                compile_success=True,
                compile_stderr=None,
                actual_output=stdout_data,
                stderr=clean_stderr or "Program produced too much output",
            )

        if timed_out or returncode == 124:
            return SandboxRunResult(
                status=VERDICT_TIME_LIMIT_EXCEEDED,
                runtime_ms=timeout_sec * 1000,
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
