"""Stage 0 audit for the V3 complexity plan.

This module is deliberately evaluation-only: it does not alter the analyzer,
database, or corpus.  It freezes a deterministic dev/test split and records
baseline agreement, coverage, label quality, and disagreement clusters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from .benchmark_problem_bank import _category, _equivalent_complexity
from .static_analyzer import analyze_source


def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _source(row: dict[str, Any]) -> str | None:
    value = _first(row, "reference_source", "source", "code", "solution")
    return str(value) if value not in (None, "") else None


def _target_time(row: dict[str, Any]) -> str | None:
    value = _first(row, "target_time_complexity", "target_time", "time_complexity")
    return str(value) if value not in (None, "") else None


def _target_space(row: dict[str, Any]) -> str | None:
    value = _first(row, "target_space_complexity", "target_space", "space_complexity")
    return str(value) if value not in (None, "") else None


def audit(path: Path, seed: int = 20261007, test_ratio: float = 0.30) -> dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    records: list[dict[str, Any]] = []
    causes: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    label_rows = 0
    missing_reference_source = 0
    missing_labels = 0
    for row in rows:
        source = _source(row)
        target_time, target_space = _target_time(row), _target_space(row)
        language = str(row.get("language") or "unknown").lower()
        if target_time and target_space:
            label_rows += 1
        else:
            missing_labels += 1
        if not source:
            missing_reference_source += 1
            causes["missing_reference_source"] += 1
            continue
        if not target_time or not target_space:
            causes["missing_label"] += 1
            continue
        result = analyze_source(source, language)
        time_ok = _equivalent_complexity(result.time_complexity, target_time, _category(row))
        space_ok = _equivalent_complexity(result.space_complexity, target_space, _category(row))
        if time_ok and space_ok:
            cause = "agreement"
        elif not time_ok and not space_ok:
            cause = "both_mismatch"
        elif not time_ok:
            cause = "time_mismatch"
        else:
            cause = "space_mismatch"
        causes[cause] += 1
        languages[language] += 1
        records.append({
            "problem_id": row.get("problem_id") or row.get("id"),
            "category": _category(row),
            "language": language,
            "target_time": target_time,
            "target_space": target_space,
            "detected_time": result.time_complexity,
            "detected_space": result.space_complexity,
            "status": result.status,
            "confidence": result.confidence,
            "cause": cause,
        })

    ordered = sorted(records, key=lambda item: str(item["problem_id"]))
    rng = random.Random(seed)
    shuffled = list(ordered)
    rng.shuffle(shuffled)
    test_count = round(len(shuffled) * test_ratio)
    test_ids = {str(item["problem_id"]) for item in shuffled[:test_count]}
    for item in ordered:
        item["split"] = "test" if str(item["problem_id"]) in test_ids else "dev"

    def split_summary(name: str) -> dict[str, Any]:
        subset = [item for item in ordered if item["split"] == name]
        return {
            "rows": len(subset),
            "agreement": sum(item["cause"] == "agreement" for item in subset),
            "time_agreement": sum(item["cause"] in {"agreement", "space_mismatch"} for item in subset),
            "space_agreement": sum(item["cause"] in {"agreement", "time_mismatch"} for item in subset),
            "exact_rate": round(sum(item["cause"] == "agreement" for item in subset) / len(subset), 4) if subset else None,
        }

    return {
        "stage": "0",
        "seed": seed,
        "test_ratio": test_ratio,
        "dataset": str(path),
        "dataset_rows": len(rows),
        "analyzed_rows": len(records),
        "label_rows": label_rows,
        "missing_reference_source": missing_reference_source,
        "missing_labels": missing_labels,
        "languages": dict(sorted(languages.items())),
        "causes": dict(causes),
        "splits": {"dev": split_summary("dev"), "test": split_summary("test")},
        "records": ordered,
        "freeze_fingerprint": hashlib.sha256(
            json.dumps(ordered, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--test-ratio", type=float, default=0.30)
    args = parser.parse_args()
    report = audit(args.dataset, args.seed, args.test_ratio)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in {"records"}}, indent=2))


if __name__ == "__main__":
    main()
