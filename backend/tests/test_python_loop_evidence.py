import asyncio
import pytest

from agents.complexity import complexity_node
from analysis.analyzer_service import analyze_static_complexity, analyze_submission_complexity
from analysis import analyzer_service
from analysis.models import ComplexityAnalysis
from analysis.python_loop_evidence import python_loop_evidence
from config.settings import settings
from scoring.rubric import student_rubric_score
from scoring.complexity import time_complexity_assessment


@pytest.mark.parametrize("outer,inner", [
    ("range(len(a))", "a"), ("a", "range(len(a))"),
    ("enumerate(a)", "a"), ("range(len(a))", "range(len(a))"),
])
def test_same_input_has_one_dimension(outer, inner):
    source = f"def work(a):\n    total = 0\n    for i in {outer}:\n        for value in {inner}:\n            total += 1\n    return total\n"
    facts = python_loop_evidence(source)
    assert not facts.issues
    assert len(facts.dimensions) == 1
    result = analyze_static_complexity(source, "python")
    assert result.status == "ANALYZED"
    assert result.time_complexity == "O(n^2)"


def test_original_listing_is_quadratic_without_model():
    source = "def solve(a):\n    total = 0\n    for i in range(len(a)):\n        total = 0\n        for value in a:\n            total += value\n    return total\n"
    result = analyze_static_complexity(source, "python")
    assert (result.time_complexity, result.space_complexity, result.status) == ("O(n^2)", "O(1)", "ANALYZED")


@pytest.mark.parametrize("target", ["O(n)", "O(n^2)"])
def test_diagnostic_label_correction_does_not_inflate_grade(target):
    before = time_complexity_assessment(target, "O(m*n)")
    after = time_complexity_assessment(target, "O(n^2)")
    assert before["time_score"] == after["time_score"]


def test_unmodified_length_alias_is_same_dimension():
    source = "def f(a):\n    n = len(a)\n    for i in range(n):\n        for x in a:\n            pass\n"
    assert len(python_loop_evidence(source).dimensions) == 1


@pytest.mark.parametrize("alias", ["a", "b"])
def test_iterated_alias_mutation_is_blocked(alias):
    source = f"def f(a):\n    b = a\n    for x in b:\n        {alias}.append(x)\n"
    assert "python-iterated-collection-mutated" in python_loop_evidence(source).issues


def test_length_snapshot_is_not_unified_after_input_rebinding():
    source = "def f(a,b):\n    n = len(a)\n    a = b\n    for i in range(n):\n        for x in a:\n            pass\n"
    result = analyze_static_complexity(source, "python")
    assert result.status == "REVIEW_REQUIRED"
    assert "python-size-alias-rebound" in result.signals


@pytest.mark.parametrize("outer,inner", [("range(len(a))", "b"), ("a", "range(len(b))"), ("a", "b")])
def test_distinct_inputs_remain_independent(outer, inner):
    source = f"def work(a,b):\n    total = 0\n    for i in {outer}:\n        for value in {inner}:\n            total += 1\n    return total\n"
    facts = python_loop_evidence(source)
    assert not facts.issues and len(facts.dimensions) == 2
    result = analyze_static_complexity(source, "python")
    assert result.time_complexity in {"O(m*n)", "O(n*m)"}


def test_sequential_passes_are_not_multiplied():
    source = "def f(a):\n    total=0\n    for i in range(len(a)):\n        total += 1\n    for x in a:\n        total += x\n    return total\n"
    assert analyze_static_complexity(source, "python").time_complexity == "O(n)"


@pytest.mark.parametrize("source,issue", [
    ("def f(a):\n    for x in make_items(a):\n        pass\n", "python-unresolved-iterator-bound"),
    ("def f(a):\n    for x in a:\n        a.append(x)\n", "python-iterated-collection-mutated"),
    ("def f(a):\n    for x in a:\n        a=[]\n", "python-loop-bound-rebound"),
    ("def f(a):\n    for x in a:\n        opaque_work(x)\n", "python-unresolved-loop-call-cost"),
    ("def f(a, range):\n    for i in range(len(a)):\n        pass\n", "python-shadowed-iteration-builtin"),
    ("def f(a):\n    for x in a[0]:\n        pass\n", "python-unresolved-iterator-bound"),
    ("def f(a):\n    for x in\n", "python-syntax-unresolved"),
])
def test_unresolved_source_blocks_grade_even_with_high_confidence_and_ai(monkeypatch, source, issue):
    async def forbidden_provider(_payload):
        raise AssertionError("A model cannot remove a structural safety block")
    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", True)
    monkeypatch.setattr(analyzer_service, "_invoke_complexity_reviewer", forbidden_provider)
    guess = ComplexityAnalysis(time_complexity="O(n)", space_complexity="O(1)", confidence=.99, status="ANALYZED")
    runtime = ComplexityAnalysis(time_complexity="O(n)", status="ANALYZED", evidence_quality="strong")
    evidence = asyncio.run(analyze_submission_complexity(source, "python", static_result=guess, dynamic_result=runtime))
    assert evidence.final.status == "REVIEW_REQUIRED"
    assert issue in evidence.final.signals
    analysis = vars(evidence.final)
    scored = asyncio.run(complexity_node({"precomputed_complexity_analysis": analysis, "execution_result": {"compile_status": "success"}}))
    assert scored['complexity_details']['time_score'] is None
    final, breakdown = student_rubric_score(100, scored['complexity_details'], 90)
    assert final is None
    assert breakdown['assessment']['status'] == 'incomplete'
    assert set(breakdown['assessment']['missing_components']) == {'time', 'space'}


def test_review_status_is_not_bypassed_by_high_confidence(monkeypatch):
    monkeypatch.setattr(settings, "COMPLEXITY_AI_REVIEW_ENABLED", False)
    guess = ComplexityAnalysis(time_complexity="O(n)", space_complexity="O(1)", confidence=.99, status="REVIEW_REQUIRED")
    result = asyncio.run(analyze_submission_complexity("int f(int n) { return n; }", "cpp", static_result=guess))
    assert result.final.status != "ANALYZED"
