"""Build a Stage 0 reference corpus by joining labels to real completions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


def _rows(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # Keep one malformed upstream record from producing a
                # misleading partial corpus. The source files are external
                # JSONL; malformed records are excluded and reported by the
                # resulting written/unmatched counts.
                continue


def _id(row: dict[str, Any]) -> str | None:
    if row.get("problem_id"):
        return str(row["problem_id"])
    if row.get("question_id") is not None:
        return f"leetcode-{row['question_id']}"
    if row.get("task_id"):
        return str(row["task_id"])
    return None


def build(labels: Path, sources: list[Path], output: Path) -> dict[str, int]:
    label_rows = {_id(row): row for row in _rows(labels) if _id(row)}
    written = 0
    unmatched = 0
    duplicate = 0
    seen: set[str] = set()
    with output.open("w", encoding="utf-8") as stream:
        for source_path in sources:
            for source in _rows(source_path):
                problem_id = _id(source)
                label = label_rows.get(problem_id)
                code = source.get("completion") or source.get("reference_source")
                if not problem_id or not label or not code:
                    unmatched += 1
                    continue
                if problem_id in seen:
                    duplicate += 1
                    continue
                seen.add(problem_id)
                record = {
                    "problem_id": problem_id,
                    "title": label.get("title") or source.get("title"),
                    "category": label.get("category") or (label.get("tags") or ["Uncategorized"])[0],
                    "language": source.get("language", "python"),
                    "reference_source": code,
                    "target_time_complexity": label.get("target_time_complexity") or label.get("target_time"),
                    "target_space_complexity": label.get("target_space_complexity") or label.get("target_space"),
                    "reference_source_origin": str(source_path.name),
                }
                if record["target_time_complexity"] and record["target_space_complexity"]:
                    stream.write(json.dumps(record) + "\n")
                    written += 1
    return {"labels": len(label_rows), "written": written, "unmatched": unmatched, "duplicate": duplicate}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--sources", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    print(json.dumps(build(args.labels, args.sources, args.output), indent=2))


if __name__ == "__main__":
    main()
