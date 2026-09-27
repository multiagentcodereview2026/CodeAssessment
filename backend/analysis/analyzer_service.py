from .evidence_merger import merge_evidence
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

    return merge_evidence(
        static_result=static_result,
        dynamic_result=dynamic_result,
    )


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