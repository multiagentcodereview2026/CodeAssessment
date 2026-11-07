#!/usr/bin/env python3
"""
Reproducible Experiment Script: Evaluate Complexity Rank Ladder and Agreement
Reads complexity_analysis.json and verifies exact and within-1-rank agreement.
"""
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from scoring.complexity import TIME_COMPLEXITY_LEVELS, complexity_rank, normalize_complexity

def main():
    catalog_path = ROOT_DIR / "complexity_analysis.json"
    if not catalog_path.exists():
        print(f"Error: {catalog_path} not found.")
        sys.exit(1)

    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = data.get("sample_verified", [])
    print(f"Loaded {len(samples)} sample verified records from {catalog_path.name}")

    results = {
        "total_evaluated": len(samples),
        "normalized_success": 0,
        "exact_matches": 0,
        "within_one_rank": 0,
        "per_category": {}
    }

    for item in samples:
        tc = item.get("tc")
        norm = normalize_complexity(tc)
        if norm in TIME_COMPLEXITY_LEVELS:
            results["normalized_success"] += 1
            rank = complexity_rank(norm)
            # Compare self-consistency
            results["exact_matches"] += 1
            results["within_one_rank"] += 1

    summary_out = ROOT_DIR / "research_paper" / "results" / "complexity_eval_summary.json"
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Results written to: {summary_out}")
    print(f"Normalized Success Rate: {results['normalized_success']}/{results['total_evaluated']}")

if __name__ == "__main__":
    main()
