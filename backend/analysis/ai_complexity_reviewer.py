"""Experimental AI complexity review layer.

This module is deliberately not imported by the production workflow.  It
provides a strict contract for comparing an LLM opinion with the deterministic
AST result before any future integration is considered.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field


class AIComplexityReview(BaseModel):
    time_complexity: str | None = None
    space_complexity: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = ""
    evidence: list[str] = Field(default_factory=list)
    status: str = "NEEDS_REVIEW"


@dataclass(frozen=True)
class ComplexityReview:
    time_complexity: str | None
    space_complexity: str | None
    confidence: float
    status: str
    evidence: list[str]


def build_review_payload(
    source_code: str,
    language: str,
    ast_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """Create a target-free prompt payload using AST evidence."""
    ast_result = ast_result or {}
    return {
        "instruction": (
            "Analyze only the submitted code. Do not infer the problem's optimal "
            "solution. Return valid JSON with time_complexity, space_complexity, "
            "confidence, reasoning, evidence, and status. Use NEEDS_REVIEW when "
            "the code does not provide enough evidence."
        ),
        "language": language,
        "source_code": source_code,
        "ast_evidence": {
            "time_complexity": ast_result.get("time_complexity"),
            "space_complexity": ast_result.get("space_complexity"),
            "confidence": ast_result.get("confidence", 0.0),
            "signals": list(ast_result.get("signals") or []),
            "explanation": ast_result.get("explanation", ""),
        },
    }


def _canonical(value: str | None) -> str | None:
    if not value:
        return None
    text = value.lower().replace(" ", "").replace("×", "*")
    return text.replace("\\log", "log")


def resolve_review(
    ast_result: dict[str, Any] | None,
    ai_result: AIComplexityReview | dict[str, Any] | None,
    *,
    minimum_confidence: float = 0.70,
) -> ComplexityReview:
    """Resolve agreement conservatively; never let weak AI override strong AST."""
    ast = ast_result or {}
    ai = AIComplexityReview.model_validate(ai_result or {})
    ast_time = ast.get("time_complexity")
    ast_space = ast.get("space_complexity")
    time_agrees = ast_time and ai.time_complexity and _canonical(ast_time) == _canonical(ai.time_complexity)
    space_agrees = ast_space and ai.space_complexity and _canonical(ast_space) == _canonical(ai.space_complexity)
    ast_confidence = float(ast.get("confidence") or 0.0)
    ai_confidence = float(ai.confidence)
    evidence = list(ai.evidence)
    if ai.reasoning:
        evidence.append(ai.reasoning)

    if time_agrees and space_agrees:
        return ComplexityReview(
            ast_time,
            ast_space,
            round(min(1.0, max(ast_confidence, ai_confidence) + 0.10), 3),
            "AGREEMENT",
            evidence + ["AST and AI complexity results agree."],
        )

    if ast_confidence >= minimum_confidence and ai_confidence < minimum_confidence:
        return ComplexityReview(ast_time, ast_space, round(ast_confidence, 3), "AST_PRIMARY", evidence)

    if ai_confidence >= minimum_confidence and ast_confidence < minimum_confidence:
        return ComplexityReview(
            ai.time_complexity,
            ai.space_complexity,
            round(ai_confidence, 3),
            "AI_PROVISIONAL",
            evidence + ["AI result is provisional because AST confidence is low."],
        )

    return ComplexityReview(
        ast_time if time_agrees else None,
        ast_space if space_agrees else None,
        round(min(ast_confidence, ai_confidence), 3),
        "NEEDS_REVIEW",
        evidence + ["AST and AI evidence conflict or is incomplete."],
    )


async def review_complexity(
    source_code: str,
    language: str,
    ast_result: dict[str, Any] | None,
    invoke: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]] | None = None,
) -> ComplexityReview:
    """Run an injected AI reviewer; no network call occurs without ``invoke``."""
    if invoke is None:
        return ComplexityReview(
            ast_result.get("time_complexity") if ast_result else None,
            ast_result.get("space_complexity") if ast_result else None,
            float((ast_result or {}).get("confidence") or 0.0),
            "AI_UNAVAILABLE",
            ["No AI reviewer was configured; AST result was preserved."],
        )
    try:
        ai_result = await invoke(build_review_payload(source_code, language, ast_result))
        return resolve_review(ast_result, ai_result)
    except Exception as exc:  # AI is optional and must not break AST scoring.
        return ComplexityReview(
            ast_result.get("time_complexity") if ast_result else None,
            ast_result.get("space_complexity") if ast_result else None,
            float((ast_result or {}).get("confidence") or 0.0),
            "AI_ERROR",
            [f"AI reviewer unavailable: {type(exc).__name__}"],
        )
