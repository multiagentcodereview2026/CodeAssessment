from dataclasses import dataclass

# Standardized Verdict Strings
VERDICT_ACCEPTED = "ACCEPTED"
VERDICT_WRONG_ANSWER = "WRONG_ANSWER"
VERDICT_COMPILATION_ERROR = "COMPILATION_ERROR"
VERDICT_RUNTIME_ERROR = "RUNTIME_ERROR"
VERDICT_TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
VERDICT_MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
VERDICT_OUTPUT_LIMIT_EXCEEDED = "OUTPUT_LIMIT_EXCEEDED"
VERDICT_SYSTEM_ERROR = "SYSTEM_ERROR"


@dataclass
class SandboxRunResult:

    status: str
    runtime_ms: int
    memory_kb: int
    compile_success: bool
    compile_stderr: str | None
    actual_output: str | None
    stderr: str | None