from analysis.analyzer_service import (
    analyze_submission_complexity,
    build_complexity_review_handoff,
)
from analysis.confidence_policy import apply_confidence_policy
from analysis.models import ComplexityAnalysis


def test_phase_n_keeps_strong_static_result_analyzed():
    result = apply_confidence_policy(
        ComplexityAnalysis(
            time_complexity="O(n)",
            space_complexity="O(1)",
            confidence=0.95,
            method="ast",
            status="ANALYZED",
            signals=["pattern:iterative-loop"],
        )
    )
    assert result.status == "ANALYZED"
    assert "llm-handoff-required" not in result.signals


def test_phase_n_marks_weak_evidence_for_handoff():
    result = apply_confidence_policy(
        ComplexityAnalysis(
            time_complexity="O(n)",
            space_complexity=None,
            confidence=0.40,
            method="fallback",
            status="ANALYZED",
        )
    )
    assert result.status == "REVIEW_REQUIRED"
    assert "llm-handoff-required" in result.signals


def test_phase_n_handoff_does_not_include_private_target():
    evidence = __import__("asyncio").run(
        analyze_submission_complexity("int f(int n){ return n + 1; }", "cpp")
    )
    payload = build_complexity_review_handoff("int f(int n){ return n + 1; }", "cpp", evidence)
    assert "target" not in payload
    assert "optimal" not in payload
    assert payload["language"] == "cpp"
