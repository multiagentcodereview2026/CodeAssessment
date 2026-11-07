import copy

from agents.revision_contract import release_decision, validate_candidate


STEP = {"id": "step_1", "area": "time", "target": {"symbol": "main", "operation": "repeated scan"},
        "change": "Replace the repeated scan with a single maintained value.",
        "expected_complexity": {"time_after": "O(n)"}, "risk": "Keep the same output."}
SOURCE = "int main() { int n; cin >> n; cout << n; }"


def test_candidate_targets_must_exist_in_original_ast():
    step = copy.deepcopy(STEP)
    step["target"]["symbol"] = "missing_array"
    assert "target_not_in_original_ast" in validate_candidate(SOURCE, SOURCE, "cpp", [step])


def test_candidate_precheck_rejects_signature_changes_and_syntax_errors():
    assert "entry_signature_changed" in validate_candidate(SOURCE, "int main(int argc) {return 0;}", "cpp", [STEP])
    assert "candidate_syntax_error" in validate_candidate(SOURCE, "int main( {", "cpp", [STEP])


def test_python_precheck_rejects_process_imports_and_dynamic_execution():
    step = {**STEP, "target": {"symbol": "total", "operation": "input accumulation"}}
    issues = validate_candidate("total=0\nprint(total)", "import subprocess\ntotal=eval('1')\nprint(total)", "python", [step])
    assert "unsupported_import" in issues and "banned_call" in issues


def test_supported_minimal_candidate_passes_precheck():
    assert validate_candidate(SOURCE, SOURCE, "cpp", [STEP]) == []


def test_time_stage_cannot_remove_nested_input_row_length():
    original = "int main(){int n;cin>>n;for(int i=0;i<n;i++){int width,x,y;cin>>width;cin>>x>>y;}}"
    candidate = original.replace("cin>>width;", "")
    assert "input_extraction_removed" in validate_candidate(original, candidate, "cpp", [STEP])


def test_test_failure_is_not_an_incomplete_assessment():
    assert release_decision(93, {}, {"status": "candidate_tests_failed"}, [STEP]) == "correctness_not_complete"


def test_retry_wakeup_respects_persisted_deadline():
    from datetime import datetime, timezone, timedelta
    from revision_jobs import projection_retry_delay
    now = datetime(2026, 11, 7, tzinfo=timezone.utc)
    pending = {"next_retry_at": (now + timedelta(seconds=120)).isoformat()}
    assert projection_retry_delay(pending, now) == 120
    assert projection_retry_delay(pending, now + timedelta(seconds=121)) == 0


def baseline_and_projection():
    baseline = {key: {"score": score} for key, score in {
        "correctness": 100, "time": 60, "space": 100, "style": 95}.items()}
    candidate = {key: {"score": value["score"]} for key, value in baseline.items()}
    candidate["time"]["score"] = 80
    return baseline, {"available": True, "verified": True, "projected_score": 92.5,
                      "score_breakdown": candidate, "measured_complexity": {"time": "O(n)", "space": "O(n)"}}


def test_higher_total_cannot_hide_style_regression():
    baseline, projection = baseline_and_projection()
    projection["score_breakdown"]["style"]["score"] = 90
    assert release_decision(85.5, baseline, projection, [STEP]) == "component_regression"


def test_tiny_incidental_style_variance_does_not_hide_a_verified_gain():
    baseline = {key: {"score": value} for key, value in {
        "correctness": 100, "time": 75, "space": 66.668, "style": 100}.items()}
    candidate = copy.deepcopy(baseline)
    candidate["space"]["score"] = 100
    candidate["style"]["score"] = 99
    projection = {"available": True, "verified": True, "projected_score": 91.2,
        "score_breakdown": candidate, "measured_complexity": {"time": "O(n)", "space": "O(1)"}}
    step = {**STEP, "area": "space", "expected_complexity": {"time_after": "O(n)", "space_after": "O(1)"}}
    assert release_decision(82.9, baseline, projection, [step]) == "passed"
    assert release_decision(82.9, baseline, projection, [step], style_tolerance=0) == "component_regression"
    for key in ("time", "space", "correctness"):
        changed = copy.deepcopy(projection)
        changed["score_breakdown"][key]["score"] = baseline[key]["score"] - 0.01
        assert release_decision(82.9, baseline, changed, [step]) == "component_regression"
    projection["score_breakdown"]["style"]["score"] = 98.9
    assert release_decision(82.9, baseline, projection, [step]) == "component_regression"


def test_style_stage_does_not_receive_an_incidental_style_tolerance():
    baseline, projection = baseline_and_projection()
    projection["score_breakdown"]["style"]["score"] = 94
    assert release_decision(85.5, baseline, projection, [{**STEP, "area": "style"}]) == "component_regression"


def test_gate_requires_minimum_gain_and_confirmed_complexity():
    baseline, projection = baseline_and_projection()
    assert release_decision(85.5, baseline, projection, [STEP]) == "passed"
    projection["projected_score"] = 86.3
    assert release_decision(85.5, baseline, projection, [STEP]) == "no_improvement"
    projection["projected_score"] = 92.5
    projection["measured_complexity"]["time"] = "O(n^2)"
    assert release_decision(85.5, baseline, projection, [STEP]) == "complexity_claim_unconfirmed"


def test_gate_rejects_incomplete_and_nonfinite_assessments():
    baseline, projection = baseline_and_projection()
    projection["projected_score"] = float('nan')
    assert release_decision(85.5, baseline, projection, [STEP]) == "assessment_incomplete"
