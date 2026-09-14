from pydantic import BaseModel, Field

from schemas import (
    CorrectnessResult,
    ComplexityResult,
    StyleResult,
)


class AssessmentScores(BaseModel):
    correctness: float = Field(ge=0, le=100)
    complexity: float = Field(ge=0, le=100)
    style: float = Field(ge=0, le=100)

    similarity: float | None = Field(
        default=None,
        ge=0,
        le=100
    )

    originality: float | None = Field(
        default=None,
        ge=0,
        le=100
    )

    final: float = Field(ge=0, le=100)


class AssessmentResult(BaseModel):
    correctness: CorrectnessResult
    complexity: ComplexityResult
    style: StyleResult
    scores: AssessmentScores
    similarity_status: str