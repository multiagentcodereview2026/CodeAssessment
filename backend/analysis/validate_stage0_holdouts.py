"""Validate the frozen unseen/adversarial datasets required by Stage 0."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_LANGUAGES = {"python", "cpp", "c", "java", "javascript"}


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def validate(path: Path, baseline_ids: set[str]) -> dict[str, Any]:
    rows = _rows(path)
    errors: list[str] = []
    ids: set[str] = set()
    languages: set[str] = set()
    for index, row in enumerate(rows, 1):
        problem_id = str(row.get("id") or row.get("problem_id") or "")
        language = str(row.get("language") or "").lower()
        if not problem_id:
            errors.append(f"row {index}: missing id")
        elif problem_id in ids:
            errors.append(f"row {index}: duplicate id {problem_id}")
        elif problem_id in baseline_ids:
            errors.append(f"row {index}: overlaps frozen baseline {problem_id}")
        ids.add(problem_id)
        languages.add(language)
        if not row.get("source") and not row.get("reference_source"):
            errors.append(f"row {index}: missing source")
        if not row.get("target_time_complexity") or not row.get("target_space_complexity"):
            errors.append(f"row {index}: missing reviewed TC/SC")
        if row.get("label_source") not in {"human", "mentor", "reviewed"}:
            errors.append(f"row {index}: label_source must be human, mentor, or reviewed")
    return {
        "path": str(path),
        "rows": len(rows),
        "languages": sorted(languages),
        "missing_languages": sorted(REQUIRED_LANGUAGES - languages),
        "baseline_overlap": sum(1 for row in rows if str(row.get("id") or row.get("problem_id")) in baseline_ids),
        "errors": errors,
        "valid": not errors and REQUIRED_LANGUAGES <= languages,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True, help="Frozen Stage 0 baseline JSON")
    parser.add_argument("--unseen", type=Path, required=True)
    parser.add_argument("--adversarial", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    baseline_ids = {str(row.get("problem_id")) for row in baseline.get("records", [])}
    report = {
        "stage": "0",
        "unseen": validate(args.unseen, baseline_ids),
        "adversarial": validate(args.adversarial, baseline_ids),
    }
    report["valid"] = report["unseen"]["valid"] and report["adversarial"]["valid"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
