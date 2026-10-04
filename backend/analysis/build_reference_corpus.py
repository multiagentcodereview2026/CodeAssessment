"""Build a separate AST benchmark corpus from raw LeetCode responses."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FENCE = re.compile(r"```\s*([A-Za-z+#.-]*)\s*\n(.*?)```", re.DOTALL)
LANGUAGE_MAP = {
    "py": "python", "python": "python", "cpp": "cpp", "c++": "cpp",
    "c": "c", "java": "java", "javascript": "javascript", "js": "javascript",
}


def extract_sources(response: str) -> dict[str, str]:
    sources: dict[str, str] = {}
    for raw_language, body in FENCE.findall(response or ""):
        language = LANGUAGE_MAP.get(raw_language.strip().lower())
        if language and body.strip() and language not in sources:
            sources[language] = body.strip()
    return sources


def load_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--normalized", required=True, type=Path)
    parser.add_argument("--raw", required=True, nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    targets = {}
    with args.normalized.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                targets[str(row.get("problem_id"))] = row

    output: list[dict[str, Any]] = []
    for raw in load_rows(args.raw):
        question_id = str(raw.get("question_id") or "").strip()
        problem_id = f"leetcode-{question_id}" if question_id.isdigit() else ""
        target = targets.get(problem_id)
        sources = extract_sources(str(raw.get("response") or ""))
        if not target or not sources:
            continue
        output.append({
            "problem_id": problem_id,
            "title": target.get("title"),
            "category": (target.get("tags") or ["Uncategorized"])[0],
            "reference_solution_sources": sources,
            "target_time_complexity": target.get("target_time_complexity"),
            "target_space_complexity": target.get("target_space_complexity"),
            "source_task_id": raw.get("task_id"),
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in output:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"reference_records": len(output), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
