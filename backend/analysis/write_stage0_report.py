"""Render the frozen Stage 0 JSON audit as a reviewable Markdown report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(report: dict) -> str:
    dev = report["splits"]["dev"]
    test = report["splits"]["test"]
    causes = report.get("causes", {})
    blockers = []
    if set(report.get("languages", {})) != {"python"}:
        blockers.append("language coverage is incomplete")
    else:
        blockers.append("reference corpus currently covers Python only")
    blockers.extend([
        "unseen real-world set is not frozen",
        "adversarial set is not frozen",
    ])
    decision = "HOLD" if blockers else "GO"
    lines = [
        "# V3 Stage 0 Baseline Report",
        "",
        "## Decision",
        "",
        f"**{decision}** — Stage 0 measurement is frozen; later implementation is gated until the listed dataset blockers are resolved.",
        "",
        "## Dataset",
        "",
        f"- Dataset: `{report['dataset']}`",
        f"- Rows: {report['dataset_rows']}",
        f"- Analyzed: {report['analyzed_rows']}",
        f"- Seed: `{report['seed']}`",
        f"- Test ratio: {report['test_ratio']}",
        f"- Freeze fingerprint: `{report['freeze_fingerprint']}`",
        "",
        "## Agreement",
        "",
        "| Split | Rows | Time agreement | Space agreement | Exact TC+SC |"]
    lines.append("|---|---:|---:|---:|---:|")
    lines.append(f"| Dev | {dev['rows']} | {dev['time_agreement']} | {dev['space_agreement']} | {dev['agreement']} ({dev['exact_rate']:.2%}) |")
    lines.append(f"| Test | {test['rows']} | {test['time_agreement']} | {test['space_agreement']} | {test['agreement']} ({test['exact_rate']:.2%}) |")
    lines.extend(["", "## Mismatch clusters", ""])
    for key, value in sorted(causes.items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Blockers before Stage 1a", ""])
    for blocker in blockers:
        lines.append(f"- {blocker}")
    lines.extend(["", "## Scope note", "", "This report measures the deterministic AST analyzer only. It does not use an LLM to decide complexity.", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(report), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
