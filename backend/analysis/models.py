from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComplexityAnalysis:
    time_complexity: str | None = None
    space_complexity: str | None = None
    confidence: float = 0.0
    method: str = "unknown"
    status: str = "REVIEW_REQUIRED"
    signals: list[str] = field(default_factory=list)
    dynamic_measurements: list[dict[str, Any]] = field(default_factory=list)
    explanation: str = ""


@dataclass
class ComplexityEvidence:
    static: ComplexityAnalysis | None = None
    dynamic: ComplexityAnalysis | None = None
    final: ComplexityAnalysis | None = None