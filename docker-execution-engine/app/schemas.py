from pydantic import BaseModel
from pydantic import model_validator


class TestCaseInput(BaseModel):

    id: int | str
    input: str
    expected_output: str
    is_hidden: bool = False
    time_limit: int | None = None
    memory_limit: int | None = None


class ExecuteRequest(BaseModel):

    code: str
    language: str
    test_cases: list[TestCaseInput]
    time_limit: int | None = 2
    memory_limit: int | None = 256
    stop_on_first_failure: bool = False


class TestCaseResultResponse(BaseModel):

    test_case_id: int | str
    status: str
    runtime_ms: int
    memory_kb: int
    is_hidden: bool
    input: str | None = None
    expected_output: str | None = None
    actual_output: str | None = None
    stderr: str | None = None

    @model_validator(mode="after")
    def redact_hidden(self):
        if self.is_hidden:
            self.input = None
            self.expected_output = None
            self.actual_output = None
            self.stderr = None
        return self


class FailedTestCaseSummaryResponse(BaseModel):
    """Safe metadata for the last test that did not pass.

    Hidden test inputs, outputs, and stderr must never leave the execution
    service.  This deliberately contains only the one-based position in the
    submitted test list and a fixed verdict description that is safe to show
    to a student.
    """

    ordinal: int
    status: str
    reason: str
    is_hidden: bool


class ExecutionResultResponse(BaseModel):

    status: str
    runtime_ms: int
    memory_kb: int
    compile_success: bool
    compile_stderr: str | None
    tests_total: int
    tests_passed: int
    tests_failed: int
    results: list[TestCaseResultResponse] = []
    last_failed_case: FailedTestCaseSummaryResponse | None = None
