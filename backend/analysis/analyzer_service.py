from dataclasses import asdict

from agents.base import invoke_agent, load_prompt, sanitize_code_comments
from config.settings import settings
from .ai_complexity_reviewer import (
    AIComplexityReview,
    AIReviewRateLimiter,
    ComplexityReviewCache,
    review_with_limits,
)
from .evidence_merger import merge_evidence
from .confidence_policy import apply_confidence_policy, build_llm_handoff
from .models import ComplexityAnalysis, ComplexityEvidence
from .static_analyzer import analyze_source


_review_limiter = AIReviewRateLimiter(
    settings.COMPLEXITY_AI_REQUESTS_PER_MINUTE,
    settings.COMPLEXITY_AI_MAX_CONCURRENCY,
)
_review_cache = ComplexityReviewCache(settings.COMPLEXITY_AI_CACHE_TTL_SECONDS)


def analyze_static_complexity(source_code: str, language: str) -> ComplexityAnalysis:
    """Run only the deterministic AST stage; never contacts an AI provider."""
    return apply_confidence_policy(
        analyze_source(source=source_code, language=language)
    ) or ComplexityAnalysis(status="REVIEW_REQUIRED", method="ast")


async def _invoke_complexity_reviewer(payload: dict) -> dict:
    """Call the configured AI provider with no benchmark or hidden-test data."""
    safe_payload = dict(payload)
    safe_payload["source_code"] = sanitize_code_comments(str(payload.get("source_code") or ""))
    return await invoke_agent(
        load_prompt("complexity_review"),
        safe_payload,
        AIComplexityReview,
        {
            "status": "NEEDS_REVIEW",
            "confidence": 0.0,
            "reasoning": "The optional AI complexity reviewer was unavailable.",
            "evidence": [],
        },
    )


def _review_required_result(result: ComplexityAnalysis, review_status: str) -> ComplexityAnalysis:
    """Preserve AST facts but prevent uncorroborated AI from being scored."""
    return ComplexityAnalysis(
        time_complexity=result.time_complexity,
        space_complexity=result.space_complexity,
        confidence=result.confidence,
        method="ast+ai-review",
        status="REVIEW_REQUIRED",
        signals=[*result.signals, f"ai-review:{review_status.lower()}", "llm-handoff-required"],
        dynamic_measurements=list(result.dynamic_measurements or []),
        evidence_quality=result.evidence_quality,
        explanation="Complexity evidence needs review before it can be scored.",
    )


def _complete(result: ComplexityAnalysis | None) -> bool:
    return bool(result and result.time_complexity and result.space_complexity)


def _strong_runtime(result: ComplexityAnalysis | None) -> bool:
    return bool(
        result
        and result.status == "ANALYZED"
        and result.evidence_quality == "strong"
        and result.time_complexity
    )


def _has_authoritative_space_evidence(result: ComplexityAnalysis | None) -> bool:
    """Whether a static space result is backed by a direct allocation fact.

    A collection allocated by a stdin/main submission belongs to the student
    program and counts as O(n) space under this application's scoring policy.
    An optional AI review may refine time complexity but must not replace that
    direct allocation fact with O(1) merely because it uses a function-input
    auxiliary-space convention.
    """
    return bool(
        result
        and result.space_complexity
        and "structural:stdin-input-sized-allocation"
        in (result.signals or [])
    )


async def analyze_submission_complexity(
    source_code: str,
    language: str,
    dynamic_result: ComplexityAnalysis | None = None,
    static_result: ComplexityAnalysis | None = None,
) -> ComplexityEvidence:
    static_result = static_result or analyze_static_complexity(
        source_code, language,
    )

    evidence = merge_evidence(
        static_result=static_result,
        dynamic_result=dynamic_result,
    )
    final = apply_confidence_policy(evidence.final)
    evidence.final = final
    static_is_complete = _complete(static_result)
    dynamic_is_strong = _strong_runtime(dynamic_result)
    runtime_measurements = list(dynamic_result.dynamic_measurements or []) if dynamic_result else []
    runtime_agrees = bool(
        static_is_complete
        and dynamic_is_strong
        and static_result.time_complexity == dynamic_result.time_complexity
    )

    # A high-confidence AST answer is fast and free. It bypasses profiling and
    # AI when no runtime evidence was requested for the submission.
    if (
        static_is_complete
        and static_result.confidence >= settings.COMPLEXITY_AST_DIRECT_CONFIDENCE
        and dynamic_result is None
    ):
        evidence.final = static_result
        return evidence

    # Medium-confidence AST is acceptable without AI only when controlled
    # runtime growth independently supports the time estimate.
    if runtime_agrees and final and final.method == "static+dynamic":
        evidence.final = final
        return evidence

    should_review_with_ai = settings.COMPLEXITY_AI_REVIEW_ENABLED
    if should_review_with_ai:
        review = await review_with_limits(
            source_code,
            language,
            asdict(static_result) if static_result else {},
            invoke=_invoke_complexity_reviewer,
            limiter=_review_limiter,
            cache=_review_cache,
            minimum_confidence=settings.COMPLEXITY_AI_MIN_CONFIDENCE,
            runtime_measurements=(
                list(dynamic_result.dynamic_measurements or [])
                if dynamic_result is not None
                else None
            ),
        )
        evidence.ai_review = asdict(review)
        # Strong runtime data is an independent guard. Do not select an AI
        # result that contradicts it merely because AST was weaker.
        if (
            dynamic_is_strong
            and review.ai_time_complexity
            and review.ai_time_complexity != dynamic_result.time_complexity
        ):
            evidence.final = _review_required_result(
                static_result or ComplexityAnalysis(), "runtime-conflict",
            )
        elif review.status == "AGREEMENT":
            evidence.final = ComplexityAnalysis(
                time_complexity=static_result.time_complexity,
                space_complexity=static_result.space_complexity,
                confidence=review.confidence,
                method="ast+ai-corroborated",
                status="ANALYZED",
                signals=[*static_result.signals, "ai-corroborated"],
                dynamic_measurements=runtime_measurements,
                evidence_quality="corroborated",
                explanation="AST complexity evidence was corroborated by an independent AI review.",
            )
        elif review.status == "AI_FALLBACK":
            preserve_static_space = _has_authoritative_space_evidence(static_result)
            evidence.final = ComplexityAnalysis(
                time_complexity=review.time_complexity,
                space_complexity=(
                    static_result.space_complexity
                    if preserve_static_space and static_result is not None
                    else review.space_complexity
                ),
                confidence=review.confidence,
                method=(
                    "ai-fallback+ast-space"
                    if preserve_static_space
                    else "ai-fallback"
                ),
                status="ANALYZED",
                signals=[
                    *(static_result.signals if static_result else []),
                    "ai-fallback:lower-confidence-ast",
                    *(
                        ["ast-space-preserved:authoritative-stdin-allocation"]
                        if preserve_static_space
                        else []
                    ),
                ],
                dynamic_measurements=runtime_measurements,
                evidence_quality="ai-fallback",
                explanation=(
                    "A code-only AI review supplied a higher-confidence time estimate "
                    "than the lower-confidence AST analysis."
                    if preserve_static_space
                    else "A code-only AI review supplied a higher-confidence estimate "
                    "than the lower-confidence AST analysis."
                ),
            )
        else:
            evidence.final = _review_required_result(
                static_result or ComplexityAnalysis(), review.status,
            )
    if not _complete(evidence.final):
        evidence.final = ComplexityAnalysis(
            status="ANALYSIS_FAILED",
            method="ast+runtime+ai",
            explanation="Complexity could not be determined from the submitted code.",
        )
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
