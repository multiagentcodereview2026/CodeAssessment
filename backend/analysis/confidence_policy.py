"""Phase-N confidence calibration and safe review handoff helpers."""

from __future__ import annotations

from typing import Any

from .models import ComplexityAnalysis


# Results below this threshold must not be treated as a deterministic answer.
# The AST engine normally emits 0.85-0.98; this threshold is for fallback or
# incomplete evidence only.
REVIEW_THRESHOLD = 0.70


def apply_confidence_policy(result: ComplexityAnalysis | None) -> ComplexityAnalysis | None:
    """Mark weak or incomplete evidence for review without changing its guess."""
    if result is None:
        return None

    signals = list(result.signals or [])
    missing_result = not result.time_complexity or not result.space_complexity
    weak = result.confidence < REVIEW_THRESHOLD or missing_result
    if result.status != "ANALYZED" or weak:
        if "llm-handoff-required" not in signals:
            signals.append("llm-handoff-required")
        reason = result.explanation or "Complexity evidence is incomplete."
        if "review" not in reason.lower():
            reason += " Manual or LLM review is required before scoring."
        return ComplexityAnalysis(
            time_complexity=result.time_complexity,
            space_complexity=result.space_complexity,
            confidence=round(max(0.0, min(1.0, result.confidence)), 3),
            method=result.method,
            status="REVIEW_REQUIRED",
            signals=signals,
            dynamic_measurements=list(result.dynamic_measurements or []),
            explanation=reason,
        )

    return result


def build_llm_handoff(
    source_code: str,
    language: str,
    result: ComplexityAnalysis | None,
) -> dict[str, Any]:
    """Build an explicit, target-free review request for an optional LLM.

    The private optimal benchmark is intentionally absent.  This payload can
    be queued for Groq/another reviewer without leaking the answer key.
    """
    return {
        "language": language,
        "source_code": source_code,
        "detected_time_complexity": result.time_complexity if result else None,
        "detected_space_complexity": result.space_complexity if result else None,
        "confidence": result.confidence if result else 0.0,
        "signals": list(result.signals or []) if result else [],
        "reason": result.explanation if result else "No static complexity result is available.",
        "instruction": (
            "Review only the submitted code. Return tight Big-O time and space "
            "complexities with a short structural explanation. Do not infer or "
            "request the private optimal benchmark."
        ),
    }
