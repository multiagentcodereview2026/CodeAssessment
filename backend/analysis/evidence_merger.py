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
                signals=static_result.signals + dynamic_result.signals,
                dynamic_measurements=dynamic_result.dynamic_measurements,
                explanation=(
                    "Static structure and dynamic runtime measurements "
                    "agree."
                ),
            )

        return ComplexityAnalysis(
            confidence=0.0,
            method="static+dynamic",
            status="REVIEW_REQUIRED",
            signals=static_result.signals + dynamic_result.signals + ["llm-handoff-required"],
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
