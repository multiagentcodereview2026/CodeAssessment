from types import SimpleNamespace
import pytest
from analysis import benchmark_ai_ast as benchmark


def row():
    return {"solution_id": "s1", "problem_id": "p1", "source": "a loop", "language": "python", "snippet_time_complexity": "O(n)", "snippet_space_complexity": "O(1)"}


def test_ast_comparator_uses_static_only_and_reports_both_dimensions(monkeypatch):
    calls = []
    def static(source, language):
        calls.append((source, language))
        return SimpleNamespace(time_complexity="O(n)", space_complexity="O(n)", confidence=.95, signals=[], explanation="test fixture", status="ANALYZED")
    monkeypatch.setattr(benchmark, "analyze_static_complexity", static)
    report = benchmark.evaluate_rows([row()])
    assert calls == [("a loop", "python")]
    assert report["ast"]["time_accuracy"] == 1
    assert report["ast"]["space_accuracy"] == 0
    assert report["ast"]["accuracy"] == 0
    assert report["ast"]["coverage"] == 1
    assert report["ai"]["coverage"] == 0
    assert report["ai"]["accuracy"] is None


def test_unreviewed_estimate_is_abstention_not_an_accuracy_success(monkeypatch):
    monkeypatch.setattr(benchmark, "analyze_static_complexity", lambda *_: SimpleNamespace(time_complexity="O(n)", space_complexity="O(1)", confidence=.2, signals=[], explanation="uncertain", status="REVIEW_REQUIRED"))
    report = benchmark.evaluate_rows([row()])
    assert report["ast"]["eligible"] == 0
    assert report["ast"]["accuracy"] is None
    assert report["ast"]["accuracy_all_rows"] == 0
    assert report["ast"]["coverage"] == 0
    with pytest.raises(ValueError):
        benchmark.evaluate_rows([{**row(), "snippet_time_complexity": None}])
