from typing import Optional

from pydantic import BaseModel, Field


class ComplexityResult(BaseModel):
    time_complexity: str
    space_complexity: str
    explanation: str
    confidence: float = Field(ge=0, le=1)


class CorrectnessResult(BaseModel):
    passed_tests: int = Field(ge=0)
    total_tests: int = Field(ge=0)

    correctness_score: float = Field(
        ge=0,
        le=100
    )

    is_correct: bool

    issues: list[str]

    coverage_warning: str = ""

    explanation: str

    confidence: float = Field(
        ge=0,
        le=1
    )


class StyleResult(BaseModel):
    overall_score: float = Field(
        ge=0,
        le=100
    )

    readability_score: float = Field(
        ge=0,
        le=100
    )

    naming_score: float = Field(
        ge=0,
        le=100
    )

    maintainability_score: float = Field(
        ge=0,
        le=100
    )

    documentation_score: float = Field(
        ge=0,
        le=100
    )

    issues: list[str]

    suggestions: list[str]

    explanation: str

    confidence: float = Field(
        ge=0,
        le=1
    )


class TestCase(BaseModel):
    id: str
    input: str
    expected_output: str
    weight: float = Field(default=1.0, gt=0)
    is_hidden: bool = False


class Problem(BaseModel):
    problem_id: str
    title: str
    description: str
    language: str
    expected_time_complexity: str
    expected_space_complexity: str
    test_cases: list[TestCase]


class TestResult(BaseModel):
    test_case_id: str

    input: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None

    passed: bool

    runtime_ms: int = 0
    memory_kb: int = 0

    error: str = ""

    is_hidden: bool = False


class ExecutionResult(BaseModel):
    status: str = "ACCEPTED"

    passed_tests: int = Field(ge=0)
    failed_tests: int = Field(ge=0)
    total_tests: int = Field(ge=0)

    test_results: list[TestResult]

    stdout: str = ""
    stderr: str = ""

    runtime_ms: int = 0
    memory_kb: int = 0

    timed_out: bool = False
    runtime_error: bool = False
    compilation_error: bool = False

    exit_code: Optional[int] = None