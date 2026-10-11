"""Assemble a genuine five-language, three-approach benchmark.

This command never invents source code or complexity labels.  It combines one
or more JSONL corpora (for example separate brute/better/optimal exports) and
emits only complete problem groups containing every supported language and all
three approaches.  Incomplete groups are reported so they can be reviewed or
collected later.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

LANGUAGES = ("c", "cpp", "java", "javascript", "python")
APPROACHES = ("brute", "better", "optimal")
REQUIRED = {
    "problem_id", "solution_id", "language", "approach", "source",
    "snippet_time_complexity", "snippet_space_complexity",
}


def _read(path: Path) -> Iterable[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Corpus is not a JSONL file: {path}")
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"Expected an object in {path}:{number}")
        yield row


def build(inputs: list[Path], output: Path, limit: int = 200) -> dict[str, Any]:
    groups: dict[str, dict[tuple[str, str], dict[str, Any]]] = defaultdict(dict)
    duplicate_keys: list[str] = []
    invalid_rows = 0
    for path in inputs:
        for row in _read(path):
            missing = REQUIRED - set(row)
            if missing or not all(str(row.get(k) or "").strip() for k in REQUIRED):
                invalid_rows += 1
                continue
            language = str(row["language"]).strip().lower()
            approach = str(row["approach"]).strip().lower()
            problem = str(row["problem_id"]).strip()
            if language not in LANGUAGES or approach not in APPROACHES or not problem:
                invalid_rows += 1
                continue
            key = (language, approach)
            if key in groups[problem]:
                duplicate_keys.append(f"{problem}:{language}:{approach}")
                continue
            groups[problem][key] = dict(row)

    required_keys = {(language, approach) for language in LANGUAGES for approach in APPROACHES}
    complete = [problem for problem in sorted(groups) if set(groups[problem]) >= required_keys]
    selected = complete[:limit]
    missing = {
        problem: sorted(f"{language}:{approach}" for language, approach in required_keys - set(groups[problem]))
        for problem in sorted(groups)
        if problem not in selected
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for problem in selected:
            for language in LANGUAGES:
                for approach in APPROACHES:
                    stream.write(json.dumps(groups[problem][(language, approach)], ensure_ascii=False) + "\n")

    return {
        "inputs": [str(path) for path in inputs],
        "output": str(output),
        "requested_problems": limit,
        "complete_problems_available": len(complete),
        "problems_emitted": len(selected),
        "rows_emitted": len(selected) * len(LANGUAGES) * len(APPROACHES),
        "languages_per_problem": len(LANGUAGES),
        "approaches_per_problem": len(APPROACHES),
        "invalid_rows": invalid_rows,
        "duplicate_rows_ignored": len(duplicate_keys),
        "duplicate_examples": duplicate_keys[:20],
        "missing_or_unselected_groups": missing,
        "valid": len(selected) == limit,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", dest="inputs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--problems", type=int, default=200)
    args = parser.parse_args()
    if args.problems < 1:
        parser.error("--problems must be positive")
    report = build(args.inputs, args.output, args.problems)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["valid"] else 1)


if __name__ == "__main__":
    main()
