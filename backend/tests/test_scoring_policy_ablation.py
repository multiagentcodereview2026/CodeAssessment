import math

from analysis.scoring_policy_ablation import compare_rules, evaluate
from analysis.scoring_policy_audit import POLICIES


def test_controlled_rules_hold_weights_fixed_and_expose_distinct_constraints():
    row = {"correctness": 25, "time": 100, "space": 100, "style": 100}
    values = evaluate(row, POLICIES["default"])
    assert values["weighted_only"] == 77.5
    assert values["fixed_cap_79"] == 77.5
    assert values["multiplicative_correctness"] == 19.375
    assert values["correctness_ceiling"] == 25


def test_ablation_covers_all_profiles_and_keeps_accuracy_claims_out():
    report = compare_rules()
    assert report["input_scenarios"] == 28
    assert report["evaluations_per_rule"] == 84
    assert len(report["rows"]) == 84
    for rule in ("multiplicative_correctness", "correctness_ceiling"):
        assert report["summary"][rule]["exceeds_correctness"] == 0
        assert report["summary"][rule]["nonzero_mark_at_zero_correctness"] == 0
    for rule in ("weighted_only", "fixed_cap_79"):
        assert report["summary"][rule]["exceeds_correctness"] > 0
        assert report["summary"][rule]["nonzero_mark_at_zero_correctness"] == 12
    assert "not an empirically best" in report["interpretation"]
    assert "accuracy" not in report


def test_rounding_and_acceptance_boundary_are_reported_separately():
    report = compare_rules()
    before, after = report["acceptance_boundary"]
    assert after["unrounded"]["fixed_cap_79"] - before["unrounded"]["fixed_cap_79"] == 21
    assert after["deployed_ceiling_mark"] - before["deployed_ceiling_mark"] == 1
    assert report["rounding_example"]["nearest_tenth"]["correctness_ceiling"] == 100
    assert math.isclose(report["rounding_example"]["deployed_ceiling_mark"], 99.9)
