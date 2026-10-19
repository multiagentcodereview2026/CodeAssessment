import asyncio

from analysis.ai_complexity_reviewer import (
    AIReviewRateLimiter,
    ComplexityReviewCache,
    resolve_review,
    review_with_limits,
)
from analysis.verify_hybrid_complexity import verify


AST_RESULT = {
    "time_complexity": "O(n)",
    "space_complexity": "O(1)",
    "confidence": 0.72,
    "signals": ["loop-depth:1"],
}


def test_ai_agreement_requires_independent_source_evidence():
    review = resolve_review(
        AST_RESULT,
        {
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
            "confidence": 0.82,
            "evidence": ["One input-bound loop performs constant work per iteration."],
        },
    )

    assert review.status == "AGREEMENT"
    assert review.time_complexity == "O(n)"


def test_higher_confidence_ai_can_be_used_as_low_confidence_ast_fallback():
    review = resolve_review(
        AST_RESULT,
        {
            "time_complexity": "O(n^2)",
            "space_complexity": "O(n)",
            "confidence": 0.99,
            "evidence": ["The source contains nested input-bound loops."],
        },
    )

    assert review.status == "AI_FALLBACK"
    assert review.time_complexity == "O(n^2)"
    assert review.space_complexity == "O(n)"


def test_limited_reviews_are_cached_and_do_not_reinvoke_ai():
    calls = 0

    async def invoke(_payload):
        nonlocal calls
        calls += 1
        return {
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
            "confidence": 0.82,
            "evidence": ["One source loop scans the input once."],
        }

    async def run():
        limiter = AIReviewRateLimiter(requests_per_minute=1, max_concurrency=1)
        cache = ComplexityReviewCache(ttl_seconds=60)
        first = await review_with_limits(
            "for item in values: pass", "python", AST_RESULT,
            invoke=invoke, limiter=limiter, cache=cache,
        )
        second = await review_with_limits(
            "for item in values: pass", "python", AST_RESULT,
            invoke=invoke, limiter=limiter, cache=cache,
        )
        return first, second

    first, second = asyncio.run(run())
    assert first.status == "AGREEMENT"
    assert second.status == "AGREEMENT"
    assert calls == 1


def test_cli_policy_fixture_uses_higher_confidence_ai_fallback():
    result = verify(
        "int scan(int n) { return n; }",
        "cpp",
        ast_fixture={
            "time_complexity": "O(n^3)",
            "space_complexity": "O(n^2)",
            "confidence": 0.55,
            "signals": ["loop-depth:3"],
        },
        ai_fixture={
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
            "confidence": 0.95,
            "evidence": ["The source has one linear scan and constant auxiliary state."],
        },
    )

    assert result["route"] == "AI_FALLBACK"
    assert result["final"]["status"] == "ANALYZED"
    assert result["final"]["time_complexity"] == "O(n)"
