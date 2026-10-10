"""Validate independent snippet-truth corpora before measuring AST accuracy."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

LANGUAGES = {"python", "cpp", "c", "java", "javascript"}
REVIEWED_SOURCES = {"human_reviewed", "expert_reviewed", "mentor_reviewed", "reviewed"}


def _rows(path: str) -> list[dict[str, Any]]:
    dataset = Path(path)
    if not dataset.exists():
        raise FileNotFoundError(
            f"Dataset file does not exist: {dataset}. "
            "Create the JSONL file before running validation."
        )
    if not dataset.is_file():
        raise IsADirectoryError(
            f"Dataset path is a directory, not a JSONL file: {dataset}. "
            "Check the Docker bind-mount source path on the host."
        )
    text = dataset.read_text(encoding="utf-8-sig")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def validate(
    path: str,
    minimum: int = 1,
    require_reviewed: bool = False,
    expected_problems: int | None = None,
    expected_approaches: list[str] | None = None,
) -> dict[str, Any]:
    rows = _rows(path)
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    languages = Counter()
    approaches = Counter()
    problem_languages: dict[str, set[str]] = {}
    problem_approaches: dict[str, set[str]] = {}
    required = {
        "problem_id", "solution_id", "approach", "language", "source",
        "snippet_time_complexity", "snippet_space_complexity", "ground_truth_source",
    }
    for index, row in enumerate(rows):
        missing = sorted(field for field in required if not row.get(field))
        if missing:
            errors.append(f"row_{index}:missing:{','.join(missing)}")
        language = str(row.get("language", "")).lower().strip()
        if language not in LANGUAGES:
            errors.append(f"row_{index}:unsupported_language:{language or '<empty>'}")
        else:
            languages[language] += 1
        key = (str(row.get("problem_id", "")), str(row.get("solution_id", "")))
        if key in seen:
            errors.append(f"row_{index}:duplicate_solution:{key[0]}:{key[1]}")
        seen.add(key)
        approaches[str(row.get("approach", "<empty>"))] += 1
        problem_id = str(row.get("problem_id", "")).strip()
        problem_languages.setdefault(problem_id, set()).add(language)
        problem_approaches.setdefault(problem_id, set()).add(str(row.get("approach", "")).strip())
        if require_reviewed and row.get("ground_truth_source") not in REVIEWED_SOURCES:
            errors.append(f"row_{index}:unreviewed_ground_truth:{row.get('ground_truth_source')}")

    missing_languages = sorted(LANGUAGES - set(languages))
    if len(rows) < minimum:
        errors.append(f"minimum_rows:{len(rows)}<{minimum}")
    if missing_languages:
        errors.append(f"missing_languages:{','.join(missing_languages)}")
    if expected_problems is not None:
        if len(problem_languages) != expected_problems:
            errors.append(f"problem_count:{len(problem_languages)}!={expected_problems}")
        incomplete = sorted(
            problem_id for problem_id, values in problem_languages.items()
            if values != LANGUAGES
        )
        if incomplete:
            errors.append(f"incomplete_language_coverage:{','.join(incomplete[:20])}")
        required_approaches = set(expected_approaches or [])
        if required_approaches:
            incomplete_approaches = sorted(
                problem_id for problem_id, values in problem_approaches.items()
                if values != required_approaches
            )
            if incomplete_approaches:
                errors.append(
                    f"incomplete_approach_coverage:{','.join(incomplete_approaches[:20])}"
                )
    return {
        "dataset": path,
        "rows": len(rows),
        "languages": dict(languages),
        "approaches": dict(approaches),
        "missing_languages": missing_languages,
        "require_reviewed": require_reviewed,
        "errors": errors,
        "valid": not errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--minimum", type=int, default=1)
    parser.add_argument("--require-reviewed", action="store_true")
    parser.add_argument("--expected-problems", type=int)
    parser.add_argument("--expected-approach", action="append", dest="expected_approaches")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = validate(
        args.dataset,
        args.minimum,
        args.require_reviewed,
        args.expected_problems,
        args.expected_approaches,
    )
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["valid"] else 1)


if __name__ == "__main__":
    main()
