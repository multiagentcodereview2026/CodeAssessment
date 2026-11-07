import asyncio

import pytest

from analysis import analyzer_service
from analysis.library_costs import detect_library_costs
from analysis.static_analyzer import _has_only_constant_bound_loops, analyze_source
from config.settings import settings


@pytest.mark.parametrize("name", ["n", "amount", "lengthValue"])
def test_reverse_loop_input_start_is_not_constant(name):
    assert not _has_only_constant_bound_loops(
        f"for (int index = {name} - 1; index >= 0; --index) {{ use(index); }}"
    )


def test_fixed_reverse_loop_is_constant():
    assert _has_only_constant_bound_loops(
        "for (int index = 25; index >= 0; --index) { use(index); }"
    )


@pytest.mark.parametrize("receiver", ["result", "buffer", "anything"])
def test_shift_cost_cannot_be_certified_as_unit_work(receiver):
    source = f"""vector<int> transform(vector<int>& input) {{
        vector<int> {receiver};
        for (int cursor = input.size() - 1; cursor >= 0; --cursor) {{
            {receiver}.insert({receiver}.begin(), input[cursor]);
        }}
        return {receiver};
    }}"""
    result = analyze_source(source, "cpp", mode="structural")
    assert result.time_complexity is None
    assert result.confidence < settings.COMPLEXITY_AST_DIRECT_CONFIDENCE
    assert result.status == "REVIEW_REQUIRED"
    assert "structural-review-blocked" not in result.signals


def test_insert_name_does_not_imply_hash_cost():
    assert not detect_library_costs("vector<int> a; a.insert(a.begin(), 3);", "cpp").hash_average_constant
    assert not detect_library_costs("set<int> a; a.insert(3);", "cpp").hash_average_constant
    assert detect_library_costs("unordered_set<int> a; a.insert(3);", "cpp").hash_average_constant


def test_unresolved_ast_operation_reaches_existing_ai_fallback(monkeypatch):
    source = """vector<int> transform(vector<int>& a) {
        vector<int> b;
        for (int i = a.size()-1; i >= 0; --i) b.insert(b.begin(), a[i]);
        return b;
    }"""
    calls = []

    async def reviewer(payload):
        calls.append(payload)
        return {
            "time_complexity": "O(n^2)", "space_complexity": "O(1)",
            "confidence": 0.92, "status": "AGREEMENT_CANDIDATE",
            "evidence": ["Each front insertion shifts the growing contiguous sequence."],
        }

    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True)
    monkeypatch.setattr(analyzer_service, "_invoke_complexity_reviewer", reviewer)
    monkeypatch.setattr(analyzer_service, "_review_cache", analyzer_service.ComplexityReviewCache(60))
    monkeypatch.setattr(analyzer_service, "_review_limiter", analyzer_service.AIReviewRateLimiter(20, 1))
    evidence = asyncio.run(analyzer_service.analyze_submission_complexity(source, "cpp"))
    assert len(calls) == 1
    assert evidence.ai_review is not None
    assert evidence.final.time_complexity == "O(n^2)"
    assert "ai-filled-missing-ast-field" in evidence.final.signals
