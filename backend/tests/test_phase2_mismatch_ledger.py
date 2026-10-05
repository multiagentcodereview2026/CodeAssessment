import json

from analysis.build_phase2_mismatch_ledger import build


def test_mismatch_ledger_groups_space_only_record(tmp_path):
    report = tmp_path / "report.json"
    corpus = tmp_path / "corpus.jsonl"
    ledger = tmp_path / "ledger.jsonl"
    summary = tmp_path / "summary.json"
    report.write_text(json.dumps({"records": [{
        "problem_id": "p1", "title": "Frequency", "category": "Array", "language": "python",
        "target_time": "O(n)", "detected_time": "O(n)",
        "target_space": "O(1)", "detected_space": "O(n)",
        "equivalent_to_target": False, "signals": ["dynamic-allocation"], "confidence": 0.95,
    }]}), encoding="utf-8")
    corpus.write_text(json.dumps({"problem_id": "p1", "reference_solution_sources": {"python": "x = {}"}}) + "\n", encoding="utf-8")
    result = build(report, corpus, ledger, summary)
    item = json.loads(ledger.read_text(encoding="utf-8"))
    assert result["exact_failures"] == 1
    assert item["cluster"] == "SPACE_ONLY"
    assert item["triage_status"] == "AST_SPACE_RULE_CANDIDATE"
