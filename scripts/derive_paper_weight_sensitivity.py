"""Summarize the published synthetic grid; no student data or model calls."""
import argparse
import json
from pathlib import Path
from statistics import mean, median


def derive(report):
    summaries = []
    for profile, weights in report["weight_profiles"].items():
        rows = [row for row in report["rows"] if row["profile"] == profile]
        assert len(rows) == 28
        scores = []
        active = 0
        for row in rows:
            c = row["components"]
            quality = sum(c[key] * weight / 100 for key, weight in weights.items())
            score = min(quality, c["correctness"])
            assert abs(score - row["unrounded"]["correctness_ceiling"]) < 1e-9
            scores.append(score)
            active += quality > c["correctness"] + 1e-9
        summaries.append({"profile": profile, "weights": weights, "n": len(rows),
                          "mean": round(mean(scores), 3), "median": round(median(scores), 3),
                          "minimum": min(scores), "maximum": max(scores),
                          "strictly_ceiling_limited": active})
    return {"kind": "synthetic_weight_sensitivity", "source": "paper-artifacts-20261030/scoring-rule-ablation.json",
            "score": "unrounded min(Q,C)", "rows": summaries,
            "scope": "Same 28 equally weighted synthetic component vectors per profile. Not student grade distributions, optimal-weight evidence, or a human study."}


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=root / "docs/research-paper/artifacts/scoring-rule-ablation.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = derive(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
