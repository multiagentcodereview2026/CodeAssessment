"""Reproducible scoring sensitivity checks; never claim model accuracy.

Run: python -m analysis.scoring_policy_audit --output /tmp/scoring-audit.json
Optional --reviews JSONL rows: id, correctness, time, space, style,
instructor_score, reviewed_by (two distinct independent reviewers).
These are reviewed component percentages, not analyzer-generated labels.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from scoring.rubric import DEFAULT_WEIGHT_PERCENT, RUBRIC_VERSION, student_rubric_score

POLICIES = {
    "default": DEFAULT_WEIGHT_PERCENT,
    "equal_weight_comparator": dict.fromkeys(DEFAULT_WEIGHT_PERCENT, 25),
    "correctness_heavier_comparator": {"correctness": 40, "time": 30, "space": 20, "style": 10},
}


def score(row, weights):
    return student_rubric_score(row["correctness"], {
        "time_score": row["time"], "time_score_max": 100,
        "space_score": row["space"], "space_score_max": 100,
    }, row["style"], weights)[0]


def audit(reviews=None):
    scenarios = []
    for c in (0, 25, 50, 75, 90, 99, 100):
        for t, m, y in ((100, 100, 100), (50, 100, 80), (100, 50, 80), (50, 50, 80)):
            row = {"correctness": c, "time": t, "space": m, "style": y}
            scores = {name: score(row, weights) for name, weights in POLICIES.items()}
            assert all(0 <= value <= c for value in scores.values())
            scenarios.append({**row, "scores": scores})
    result = {"rubric_version": RUBRIC_VERSION, "kind": "synthetic_policy_sensitivity",
              "policies": POLICIES, "scenarios": scenarios,
              "correctness_ceiling_holds": True, "human_validation": "pending",
              "warning": "Synthetic arithmetic checks do not establish grading validity or application accuracy."}
    if reviews is not None:
        rows = [json.loads(line) for line in reviews.splitlines() if line.strip()]
        if not rows:
            raise ValueError("Review dataset is empty")
        ids = set()
        for row in rows:
            if not row.get("id") or row["id"] in ids:
                raise ValueError("Each review needs a unique id")
            ids.add(row["id"])
            reviewers = row.get("reviewed_by", [])
            if not isinstance(reviewers, list) or len(set(reviewers)) < 2 or not all(isinstance(r, str) and r.strip() for r in reviewers):
                raise ValueError("Two distinct independent reviewer identifiers are required")
            for key in (*DEFAULT_WEIGHT_PERCENT, "instructor_score"):
                value = row.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
                    raise ValueError(f"{key} must be a finite percentage")
        result["human_validation"] = "reviewed_sample_comparison_only"
        result["review_count"] = len(rows)
        result["review_sha256"] = hashlib.sha256(reviews.encode()).hexdigest()
        result["mean_absolute_error_against_instructor"] = {
            name: round(sum(abs(score(row, weights) - row["instructor_score"]) for row in rows) / len(rows), 4)
            for name, weights in POLICIES.items()
        }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.reviews.read_text(encoding="utf-8-sig") if args.reviews else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in {"scenarios", "policies"}}))
