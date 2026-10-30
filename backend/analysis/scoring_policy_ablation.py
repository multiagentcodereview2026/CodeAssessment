"""Controlled synthetic scoring-rule comparison; not grading-accuracy evidence.

Hold component inputs and weights fixed while varying only the correctness
constraint. Reuse the existing 28-case sensitivity grid without fitting to labels.
All arithmetic invariants are compared before rounding. Decimal presentation is
examined separately, since the deployed ceiling uses conservative rounding.
"""
import argparse
import json
import math
from pathlib import Path

from analysis.scoring_policy_audit import POLICIES, audit, score


RULES = ("weighted_only", "fixed_cap_79", "multiplicative_correctness", "correctness_ceiling")


def evaluate(row, weights):
    c = row["correctness"]
    q = sum(row[key] * weights[key] / 100 for key in weights)
    return {
        "weighted_only": q,
        "fixed_cap_79": min(q, 79) if c < 100 else q,
        "multiplicative_correctness": q * c / 100,
        "correctness_ceiling": min(q, c),
    }


def compare_rules():
    rows = audit()["scenarios"]
    results = []
    for profile, weights in POLICIES.items():
        for index, row in enumerate(rows):
            components = {key: row[key] for key in weights}
            results.append({"profile": profile, "scenario": index + 1,
                            "components": components, "unrounded": evaluate(components, weights),
                            "deployed_ceiling_mark": score(components, weights)})
    summary = {}
    for rule in RULES:
        summary[rule] = {
            "evaluations": len(results),
            "exceeds_correctness": sum(r["unrounded"][rule] > r["components"]["correctness"] + 1e-9 for r in results),
            "nonzero_mark_at_zero_correctness": sum(r["components"]["correctness"] == 0 and r["unrounded"][rule] > 1e-9 for r in results),
        }
    # A fixed profile and perfect remaining components isolate the cap's jump
    # at acceptance. These two points are examples, not additional corpus rows.
    boundary = []
    for c in (99, 100):
        row = {"correctness": c, "time": 100, "space": 100, "style": 100}
        boundary.append({"correctness": c, "unrounded": evaluate(row, POLICIES["default"]),
                         "deployed_ceiling_mark": score(row, POLICIES["default"])})
    near_perfect = {"correctness": 99999 / 100000 * 100, "time": 100, "space": 100, "style": 100}
    rounding = {"components": near_perfect,
                "nearest_tenth": {rule: round(value, 1) for rule, value in evaluate(near_perfect, POLICIES["default"]).items()},
                "deployed_ceiling_mark": score(near_perfect, POLICIES["default"])}
    assert all(r["deployed_ceiling_mark"] <= r["components"]["correctness"] for r in results)
    assert math.isclose(rounding["deployed_ceiling_mark"], 99.9)
    return {"kind": "synthetic_scoring_rule_ablation", "input_scenarios": len(rows),
            "weight_profiles": POLICIES, "rule_count": len(RULES), "evaluations_per_rule": len(results),
            "summary": summary, "acceptance_boundary": boundary, "rounding_example": rounding,
            "rows": results,
            "scope": "Identical existing component grid and weights for all four rules; no instructor labels, human outcomes, or AI predictions.",
            "interpretation": "Checks compliance with a chosen correctness-ceiling requirement, not an empirically best grading rule. Multiplication also satisfies the unrounded ceiling but applies an additional correctness factor to the whole weighted score. The fixed-cap comparator uses the new weights to isolate its constraint; it is not a reproduction of every historical application setting."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare_rules()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=2))
