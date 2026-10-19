import json

from analysis.stage10_final_evaluation import evaluate
from analysis.validate_stage10_real_benchmark import validate


def _report(rows=10, rate=0.75):
    return {
        "dataset_rows": rows,
        "analyzed_rows": rows,
        "missing_reference_source": 0,
        "missing_labels": 0,
        "splits": {"test": {"rows": max(1, rows // 5), "exact_rate": rate}},
        "freeze_fingerprint": "test-fixture",
    }


def _write_report(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_final_gate_rejects_empty_holdouts(tmp_path):
    empty = _report(rows=0, rate=None)
    result = evaluate(
        _write_report(tmp_path / "baseline.json", _report()),
        _write_report(tmp_path / "unseen.json", empty),
        _write_report(tmp_path / "adversarial.json", empty),
    )
    assert result["baseline"]["ready"] is True
    assert result["unseen"]["ready"] is False
    assert result["adversarial"]["ready"] is False
    assert result["holdouts_valid"] is False
    assert result["status"] == "HOLD"


def test_final_gate_accepts_only_complete_reports_with_fraction_metrics(tmp_path):
    result = evaluate(*[
        _write_report(tmp_path / f"{name}.json", _report())
        for name in ("baseline", "unseen", "adversarial")
    ])
    assert result["holdouts_valid"] is True
    assert result["status"] == "READY_FOR_FINAL_REVIEW"
    assert result["baseline"]["test_exact_rate"] == 0.75


def test_final_gate_rejects_invalid_exact_rates(tmp_path):
    for bad_rate in ("0.5", float("nan"), 1.1, -0.1, True):
        payload = _report(rate=bad_rate)
        result = evaluate(*[
            _write_report(tmp_path / f"{index}-{name}.json", payload)
            for index, name in enumerate(("baseline", "unseen", "adversarial"))
        ])
        assert result["status"] == "HOLD"


def test_real_benchmark_validator_checks_unique_ids_labels_and_sources(tmp_path):
    valid_rows = [
        {
            "problem_id": f"problem-{language}",
            "language": language,
            "reference_source": "function solve() {}",
            "target_time_complexity": "O(n)",
            "target_space_complexity": "O(1)",
            "label_source": "reviewed",
        }
        for language in ("python", "cpp", "c", "java", "javascript")
    ]
    path = tmp_path / "holdout.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in valid_rows), encoding="utf-8")
    assert validate(str(path), minimum=5)["valid"] is True

    valid_rows[1]["problem_id"] = valid_rows[0]["problem_id"]
    valid_rows[1]["target_space_complexity"] = ""
    valid_rows[1]["label_source"] = "model_generated"
    path.write_text("".join(json.dumps(row) + "\n" for row in valid_rows), encoding="utf-8")
    result = validate(str(path), minimum=5)
    assert result["valid"] is False
    assert "duplicate_ids" in result["errors"]
    assert "row_1:missing_labels" in result["errors"]
    assert "row_1:unreviewed_label_source" in result["errors"]
