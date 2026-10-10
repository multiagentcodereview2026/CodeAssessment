"""Validate a real-world Stage 10 benchmark before measuring accuracy."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

LANGUAGES = {"python", "cpp", "c", "java", "javascript"}
ACCEPTED_LABEL_SOURCES = {"human", "mentor", "reviewed", "expert"}


def _rows(path: str) -> list[dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def validate(path: str, baseline_path: str | None = None, minimum: int = 200) -> dict:
    rows = _rows(path)
    ids = [row.get("problem_id") or row.get("id") for row in rows]
    languages = Counter(str(row.get("language", "")).lower() for row in rows)
    baseline_ids: set[str] = set()
    if baseline_path:
        baseline_ids = {
            str(row.get("problem_id") or row.get("id"))
            for row in _rows(baseline_path)
        }
    errors: list[str] = []
    if len(rows) < minimum:
        errors.append(f"minimum_rows:{len(rows)}<{minimum}")
    if len(set(ids)) != len(ids):
        errors.append("duplicate_ids")
    if not LANGUAGES.issubset(languages):
        errors.append("missing_languages:" + ",".join(sorted(LANGUAGES - set(languages))))
    overlap = len(set(ids) & baseline_ids)
    if overlap:
        errors.append(f"baseline_overlap:{overlap}")
    for index, row in enumerate(rows):
        if not row.get("reference_source") and not row.get("source") and not row.get("code"):
            errors.append(f"row_{index}:missing_source")
        if not row.get("target_time_complexity") or not row.get("target_space_complexity"):
            errors.append(f"row_{index}:missing_labels")
        if row.get("label_source") not in ACCEPTED_LABEL_SOURCES:
            errors.append(f"row_{index}:unreviewed_label_source")
    return {
        "stage": "10",
        "path": path,
        "rows": len(rows),
        "languages": dict(sorted(languages.items())),
        "baseline_overlap": overlap,
        "errors": errors,
        "valid": not errors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--baseline")
    parser.add_argument("--minimum", type=int, default=200)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = validate(args.dataset, args.baseline, args.minimum)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
