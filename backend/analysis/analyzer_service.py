from .evidence_merger import merge_evidence
from .confidence_policy import apply_confidence_policy, build_llm_handoff
from .models import ComplexityAnalysis, ComplexityEvidence
from .static_analyzer import analyze_source


async def analyze_submission_complexity(
    source_code: str,
    language: str,
    dynamic_result: ComplexityAnalysis | None = None,
) -> ComplexityEvidence:
    static_result = analyze_source(
        source=source_code,
        language=language,
    )

    evidence = merge_evidence(
        static_result=static_result,
        dynamic_result=dynamic_result,
    )
    evidence.final = apply_confidence_policy(evidence.final)
    return evidence


def build_complexity_review_handoff(
    source_code: str,
    language: str,
    evidence: ComplexityEvidence,
) -> dict:
    """Return a safe optional-review payload with no private target data."""
    return build_llm_handoff(source_code, language, evidence.final)


def final_complexity_result(
    evidence: ComplexityEvidence,
) -> ComplexityAnalysis:
    if evidence.final is not None:
        return evidence.final

    return ComplexityAnalysis(
        status="REVIEW_REQUIRED",
        method="none",
        confidence=0.0,
        explanation="No final complexity result is available.",
    )
