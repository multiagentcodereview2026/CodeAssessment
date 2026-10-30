import asyncio
import pytest

from agents.complexity import complexity_node
from analysis import analyzer_service
from analysis.dynamic_profiler import profile_execution_results
from analysis.models import ComplexityAnalysis
from config.settings import settings


SOURCE = """
#include <iostream>
int main() {
    int n;
    std::cin >> n;
    int total = 0;
    for (int i = 0; i < n; ++i) total += i;
    return total;
}
"""


@pytest.fixture
def require_ai_review(monkeypatch):
    """Exercise corroboration independently of the production direct threshold."""
    monkeypatch.setattr(settings, "COMPLEXITY_AST_DIRECT_CONFIDENCE", 0.90)


def test_low_confidence_ast_is_ai_corroborated_before_becoming_analyzed(monkeypatch, require_ai_review):
    async def agreeing_provider(payload):
        assert set(payload) == {"instruction", "language", "source_code"}
        return {
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
            "confidence": 0.82,
            "evidence": ["The source has one input-bounded loop and scalar state."],
            "status": "AGREEMENT_CANDIDATE",
        }

    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True)
    monkeypatch.setattr(analyzer_service, "_invoke_complexity_reviewer", agreeing_provider)
    monkeypatch.setattr(analyzer_service, "_review_cache", analyzer_service.ComplexityReviewCache(60))
    monkeypatch.setattr(analyzer_service, "_review_limiter", analyzer_service.AIReviewRateLimiter(20, 1))

    evidence = asyncio.run(analyzer_service.analyze_submission_complexity(SOURCE, "cpp"))

    assert evidence.ai_review is not None
    assert evidence.ai_review["status"] == "AGREEMENT"
    assert evidence.final is not None
    assert evidence.final.status == "ANALYZED"
    assert evidence.final.method == "ast+ai-corroborated"


def test_higher_confidence_ai_disagreement_never_replaces_ast_formula(monkeypatch, require_ai_review):
    async def disagreeing_provider(payload):
        assert "ast_evidence" not in payload
        return {
            "time_complexity": "O(n^2)",
            "space_complexity": "O(n)",
            "confidence": 0.99,
            "evidence": ["The source appears to have nested input-bounded work."],
            "status": "AGREEMENT_CANDIDATE",
        }

    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True)
    monkeypatch.setattr(analyzer_service, "_invoke_complexity_reviewer", disagreeing_provider)
    monkeypatch.setattr(analyzer_service, "_review_cache", analyzer_service.ComplexityReviewCache(60))
    monkeypatch.setattr(analyzer_service, "_review_limiter", analyzer_service.AIReviewRateLimiter(20, 1))

    evidence = asyncio.run(analyzer_service.analyze_submission_complexity(SOURCE, "cpp"))
    analysis = {
        "time_complexity": evidence.final.time_complexity,
        "space_complexity": evidence.final.space_complexity,
        "status": evidence.final.status,
        "method": evidence.final.method,
        "confidence": evidence.final.confidence,
    }
    scored = asyncio.run(
        complexity_node(
            {
                "precomputed_complexity_analysis": analysis,
                "execution_result": {"compile_status": "success"},
                "complexity_target": {"time": "O(n^2)", "space": "O(n)"},
            }
        )
    )

    assert evidence.final.status == "REVIEW_REQUIRED"
    assert evidence.final.method == "ast+ai-review"
    assert evidence.final.time_complexity == "O(n)"
    assert scored["complexity_score"] is None
    assert scored["complexity_details"]["analysis_status"] == "REVIEW_REQUIRED"


def test_ai_fallback_cannot_replace_any_existing_ast_formula(monkeypatch, require_ai_review):
    async def provider(_payload):
        return {
            "time_complexity": "O(n^3)",
            "space_complexity": "O(n)",
            "confidence": 0.99,
            "evidence": ["The code has three nested loops and stores its input."],
        }

    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True)
    monkeypatch.setattr(analyzer_service, "_invoke_complexity_reviewer", provider)
    monkeypatch.setattr(analyzer_service, "_review_cache", analyzer_service.ComplexityReviewCache(60))
    monkeypatch.setattr(analyzer_service, "_review_limiter", analyzer_service.AIReviewRateLimiter(20, 1))
    static = ComplexityAnalysis(
        time_complexity="O(n^2)",
        space_complexity="O(n)",
        confidence=0.85,
        method="ast",
        status="ANALYZED",
        signals=["structural:stdin-input-sized-allocation"],
    )

    evidence = asyncio.run(
        analyzer_service.analyze_submission_complexity(
            SOURCE, "cpp", static_result=static,
        )
    )

    assert evidence.final is not None
    assert evidence.final.time_complexity == "O(n^2)"
    assert evidence.final.space_complexity == "O(n)"
    assert evidence.final.method == "ast+ai-review"


def test_identical_ai_fallback_review_is_cached(monkeypatch, require_ai_review):
    calls = 0

    async def provider(_payload):
        nonlocal calls
        calls += 1
        return {
            "time_complexity": "O(n^3)",
            "space_complexity": "O(n)",
            "confidence": 0.99,
            "evidence": ["Nested loops dominate the work."],
        }

    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True)
    monkeypatch.setattr(analyzer_service, "_invoke_complexity_reviewer", provider)
    monkeypatch.setattr(analyzer_service, "_review_cache", analyzer_service.ComplexityReviewCache(60))
    monkeypatch.setattr(analyzer_service, "_review_limiter", analyzer_service.AIReviewRateLimiter(20, 1))
    static = ComplexityAnalysis(
        time_complexity="O(n^2)", space_complexity="O(1)", confidence=0.85,
        method="ast", status="ANALYZED",
    )

    first = asyncio.run(analyzer_service.analyze_submission_complexity(SOURCE, "cpp", static_result=static))
    second = asyncio.run(analyzer_service.analyze_submission_complexity(SOURCE, "cpp", static_result=static))

    assert calls == 1
    assert first.final is not None and second.final is not None
    assert first.final.time_complexity == second.final.time_complexity == "O(n^2)"
    assert first.final.space_complexity == second.final.space_complexity == "O(1)"


@pytest.mark.parametrize("confidence", [0.85, 0.95])
def test_ast_at_or_above_direct_threshold_skips_ai(monkeypatch, confidence):
    calls = []

    async def provider(payload):
        calls.append(payload)
        raise AssertionError("Confident AST must not call the optional AI reviewer")

    monkeypatch.setattr(settings, "COMPLEXITY_AST_DIRECT_CONFIDENCE", 0.85)
    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True)
    monkeypatch.setattr(analyzer_service, "_invoke_complexity_reviewer", provider)
    static = ComplexityAnalysis(
        time_complexity="O(n)", space_complexity="O(1)",
        confidence=confidence, method="ast", status="ANALYZED",
    )
    evidence = asyncio.run(analyzer_service.analyze_submission_complexity(
        SOURCE, "cpp", static_result=static,
    ))
    assert calls == []
    assert evidence.ai_review is None
    assert evidence.final.status == "ANALYZED"
    assert evidence.final.method == "ast"
    assert evidence.final.time_complexity == "O(n)"
    assert evidence.final.space_complexity == "O(1)"


def test_missing_ast_estimate_is_saved_as_analysis_failed_and_is_not_scored(monkeypatch):
    monkeypatch.setattr(
        analyzer_service,
        "analyze_source",
        lambda **_kwargs: ComplexityAnalysis(
            confidence=0.0,
            method="ast",
            status="REVIEW_REQUIRED",
            signals=["parser-no-supported-structure"],
            explanation="No supported structural estimate was available.",
        ),
    )

    evidence = asyncio.run(analyzer_service.analyze_submission_complexity("unrecognized", "cpp"))
    assert evidence.final is not None
    assert evidence.final.status == "ANALYSIS_FAILED"
    assert evidence.final.time_complexity is None
    assert evidence.final.space_complexity is None

    scored = asyncio.run(
        complexity_node(
            {
                "precomputed_complexity_analysis": {
                    "status": evidence.final.status,
                    "method": evidence.final.method,
                    "confidence": evidence.final.confidence,
                }
            }
        )
    )
    assert scored["complexity_score"] is None
    assert scored["complexity_details"]["analysis_status"] == "ANALYSIS_FAILED"


def test_medium_confidence_ast_and_strong_runtime_agreement_skip_ai(monkeypatch):
    calls = 0

    async def should_not_run(_payload):
        nonlocal calls
        calls += 1
        raise AssertionError("AI must not run when AST and runtime agree")

    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True)
    monkeypatch.setattr(analyzer_service, "_invoke_complexity_reviewer", should_not_run)
    static = ComplexityAnalysis(
        time_complexity="O(n)", space_complexity="O(1)", confidence=0.85,
        method="ast", status="ANALYZED",
    )
    runtime = ComplexityAnalysis(
        time_complexity="O(n)", confidence=0.65, method="runtime-profile",
        status="ANALYZED", evidence_quality="strong",
        dynamic_measurements=[{"input_size": 10, "runtime_ms": 1}],
    )

    evidence = asyncio.run(
        analyzer_service.analyze_submission_complexity(
            SOURCE, "cpp", static_result=static, dynamic_result=runtime,
        )
    )

    assert calls == 0
    assert evidence.final is not None
    assert evidence.final.method == "static+dynamic"
    assert evidence.final.time_complexity == "O(n)"


def test_runtime_supported_ai_fallback_receives_raw_measurements_only(monkeypatch):
    async def provider(payload):
        assert "ast_evidence" not in payload
        assert "detected_time_complexity" not in payload
        assert payload["runtime_measurements"] == [{"input_size": 10, "runtime_ms": 1}]
        return {
            "time_complexity": "O(n log n)",
            "space_complexity": "O(n)",
            "confidence": 0.97,
            "evidence": ["The source sorts n values before a linear scan."],
        }

    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True)
    monkeypatch.setattr(analyzer_service, "_invoke_complexity_reviewer", provider)
    monkeypatch.setattr(analyzer_service, "_review_cache", analyzer_service.ComplexityReviewCache(60))
    monkeypatch.setattr(analyzer_service, "_review_limiter", analyzer_service.AIReviewRateLimiter(20, 1))
    static = ComplexityAnalysis(
        time_complexity="O(n^2)", space_complexity="O(1)", confidence=0.85,
        method="ast", status="ANALYZED",
    )
    runtime = ComplexityAnalysis(
        time_complexity="O(n log n)", confidence=0.65, method="runtime-profile",
        status="ANALYZED", evidence_quality="strong",
        dynamic_measurements=[{"input_size": 10, "runtime_ms": 1}],
    )

    evidence = asyncio.run(
        analyzer_service.analyze_submission_complexity(
            SOURCE, "cpp", static_result=static, dynamic_result=runtime,
        )
    )

    assert evidence.final is not None
    assert evidence.final.method == "ast+ai-review"
    assert evidence.final.status == "REVIEW_REQUIRED"
    assert evidence.final.time_complexity == "O(n^2)"


def test_observational_judge_timings_do_not_veto_confident_static_analysis(monkeypatch):
    """Container-per-case timings are not controlled complexity benchmarks."""
    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", False)
    observed = profile_execution_results(
        [
            {"input": "2 1 2"},
            {"input": "4 1 2 3 4"},
            {"input": "8 1 2 3 4 5 6 7 8"},
        ],
        {
            "results": [
                {"status": "accepted", "runtime_ms": 10},
                {"status": "accepted", "runtime_ms": 12},
                {"status": "accepted", "runtime_ms": 14},
            ],
        },
    )
    static = ComplexityAnalysis(
        time_complexity="O(n^2 log n)",
        space_complexity="O(1)",
        confidence=0.85,
        method="ast",
        status="ANALYZED",
    )

    evidence = asyncio.run(
        analyzer_service.analyze_submission_complexity(
            SOURCE, "cpp", static_result=static, dynamic_result=observed,
        )
    )

    assert observed.evidence_quality == "limited"
    assert evidence.final is not None
    assert evidence.final.status == "ANALYZED"
    assert evidence.final.method == "static-authoritative"
    assert evidence.final.time_complexity == "O(n^2 log n)"
