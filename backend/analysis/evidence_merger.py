from .models import ComplexityAnalysis, ComplexityEvidence


def merge_complexity_evidence(
    static_result: ComplexityAnalysis | None,
    dynamic_result: ComplexityAnalysis | None,
) -> ComplexityAnalysis:
    if static_result and dynamic_result:
        same_time = (
            static_result.time_complexity
            == dynamic_result.time_complexity
        )
        same_space = (
            static_result.space_complexity
            == dynamic_result.space_complexity
        )

        combined_signals = list(dict.fromkeys(
            static_result.signals + dynamic_result.signals
        ))

        if same_time and same_space:
            return ComplexityAnalysis(
                time_complexity=static_result.time_complexity,
                space_complexity=static_result.space_complexity,
                confidence=round(
                    min(
                        1.0,
                        (static_result.confidence + dynamic_result.confidence)
                        / 2
                        + 0.10,
                    ),
                    3,
                ),
                method="static+dynamic",
                status="ANALYZED",
                signals=combined_signals + ["static-dynamic-agreement"],
                dynamic_measurements=dynamic_result.dynamic_measurements,
                evidence_quality=(
                    "strong" if dynamic_result.evidence_quality == "strong"
                    else "corroborated"
                ),
                explanation=(
                    "Static structure and dynamic runtime measurements "
                    "agree."
                ),
            )

        if (
            static_result.status == "ANALYZED"
            and static_result.confidence >= 0.85
            and dynamic_result.evidence_quality in {"limited", "insufficient", "none"}
        ):
            return ComplexityAnalysis(
                time_complexity=static_result.time_complexity,
                space_complexity=static_result.space_complexity,
                confidence=round(static_result.confidence * 0.9, 3),
                method="static-authoritative",
                status="ANALYZED",
                signals=combined_signals + ["static-authoritative"],
                dynamic_measurements=dynamic_result.dynamic_measurements,
                evidence_quality="limited",
                explanation=(
                    "Static analysis was retained because dynamic evidence "
                    "was insufficient to challenge it."
                ),
            )

        return ComplexityAnalysis(
            confidence=0.0,
            method="static+dynamic",
            status="REVIEW_REQUIRED",
            signals=combined_signals + ["llm-handoff-required"],
            dynamic_measurements=dynamic_result.dynamic_measurements,
            explanation=(
                "Static and dynamic analysis produced different "
                "complexity estimates. Review is required before scoring."
            ),
        )

    if static_result and static_result.status == "ANALYZED":
        return static_result

    if dynamic_result and dynamic_result.status == "ANALYZED":
        return dynamic_result

    return ComplexityAnalysis(
        confidence=0.0,
        method="none",
        status="REVIEW_REQUIRED",
        explanation="No reliable complexity evidence is available.",
    )


def merge_evidence(
    static_result: ComplexityAnalysis | None,
    dynamic_result: ComplexityAnalysis | None,
) -> ComplexityEvidence:
    final_result = merge_complexity_evidence(
        static_result,
        dynamic_result,
    )

    return ComplexityEvidence(
        static=static_result,
        dynamic=dynamic_result,
        final=final_result,
    )
