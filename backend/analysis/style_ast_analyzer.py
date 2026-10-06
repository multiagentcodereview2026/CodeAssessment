"""Deterministic, language-neutral style analysis.

This module deliberately does not inspect or infer algorithmic complexity.
It produces repeatable style evidence for the style component only.
"""

from __future__ import annotations

import ast
import re
from typing import Any


_ALLOWED_SHORT = {"i", "j", "k", "n", "m", "x", "y", "u", "v", "r", "c"}
_GENERIC_NAMES = {"tmp", "temp", "data", "val", "value", "obj", "res", "result", "var"}


def _finding(category: str, message: str, severity: str = "minor", penalty: int = 1) -> dict[str, Any]:
    return {"category": category, "message": message, "severity": severity, "penalty": penalty}


def _score(issues: list[dict[str, Any]], category: str) -> float:
    return max(0.0, min(25.0, 25.0 - sum(i["penalty"] for i in issues if i["category"] == category)))


def _python_metrics(source: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    naming: list[dict[str, Any]] = []
    readability: list[dict[str, Any]] = []
    modularity: list[dict[str, Any]] = []
    maintainability: list[dict[str, Any]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = None

    if tree is not None:
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child._style_parent = parent
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [a.arg for a in node.args.args]
                for name in args:
                    if len(name) == 1 and name not in _ALLOWED_SHORT:
                        naming.append(_finding("naming", f"Parameter `{name}` is too cryptic."))
                lines = (getattr(node, "end_lineno", node.lineno) - node.lineno + 1)
                if lines > 120:
                    readability.append(_finding("readability", f"Function `{node.name}` is very long.", "major", 5))
                elif lines > 60:
                    readability.append(_finding("readability", f"Function `{node.name}` is long.", "moderate", 3))
                if len(args) > 5:
                    modularity.append(_finding("modularity", f"Function `{node.name}` has many parameters.", "moderate", 3))
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if len(node.id) == 1 and node.id not in _ALLOWED_SHORT:
                    naming.append(_finding("naming", f"Variable `{node.id}` is cryptic."))
                elif node.id.lower() in _GENERIC_NAMES:
                    naming.append(_finding("naming", f"Variable `{node.id}` is generic."))
            elif isinstance(node, (ast.For, ast.While, ast.If, ast.Try)):
                depth = 0
                parent = getattr(node, "_style_parent", None)
                while parent is not None:
                    if isinstance(parent, (ast.For, ast.While, ast.If, ast.Try)):
                        depth += 1
                    parent = getattr(parent, "_style_parent", None)
                if depth >= 4:
                    readability.append(_finding("readability", "Control flow is deeply nested.", "moderate", 3))
    lines = source.splitlines()
    if any(len(line) > 120 for line in lines):
        readability.append(_finding("readability", "One or more lines exceed 120 characters.", "minor", 1))
    if source.strip() and not re.search(r"(^|\n)\s*#", source):
        readability.append(_finding("readability", "No explanatory comments were found.", "minor", 1))
    if tree is not None and sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree)) == 1:
        functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if functions and (getattr(functions[0], "end_lineno", 0) - functions[0].lineno) > 40:
            modularity.append(_finding("modularity", "A large implementation could be decomposed into helpers.", "minor", 1))
    if re.search(r"\b(?:TODO|FIXME)\b", source, re.I):
        maintainability.append(_finding("maintainability", "TODO/FIXME markers remain in the submission.", "minor", 1))
    return naming, readability, modularity, maintainability


def _generic_metrics(source: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    naming, readability, modularity, maintainability = [], [], [], []
    for name in re.findall(r"\b(?:int|long|double|string|auto|var|let|const)\s+([A-Za-z_]\w*)", source):
        if len(name) == 1 and name not in _ALLOWED_SHORT:
            naming.append(_finding("naming", f"Variable `{name}` is cryptic."))
        elif name.lower() in _GENERIC_NAMES:
            naming.append(_finding("naming", f"Variable `{name}` is generic."))
    if any(len(line) > 120 for line in source.splitlines()):
        readability.append(_finding("readability", "One or more lines exceed 120 characters.", "minor", 1))
    if source.strip() and not re.search(r"(^|\n)\s*(//|/\*|\*)", source):
        readability.append(_finding("readability", "No explanatory comments were found.", "minor", 1))
    depth = max(((len(line) - len(line.lstrip(" \t"))) // 4 for line in source.splitlines()), default=0)
    if depth >= 5:
        readability.append(_finding("readability", "Control flow appears deeply nested.", "moderate", 3))
    if len(re.findall(r"\b(?:void|int|bool|string|auto)\s+\w+\s*\([^)]*\)", source)) == 1 and source.count("\n") > 60:
        modularity.append(_finding("modularity", "A large implementation could be decomposed into helpers.", "minor", 1))
    return naming, readability, modularity, maintainability


def analyze_style(source: str, language: str) -> dict[str, Any]:
    source = source or ""
    if language.lower() in {"python", "py"}:
        groups = _python_metrics(source)
    else:
        groups = _generic_metrics(source)
    all_issues = [item for group in groups for item in group]
    naming, readability, modularity, maintainability = groups
    scores = {
        "naming_score": _score(all_issues, "naming"),
        "readability_score": _score(all_issues, "readability"),
        "modularity_score": _score(all_issues, "modularity"),
        "maintainability_score": _score(all_issues, "maintainability"),
    }
    positives = []
    if not naming: positives.append("Identifiers are reasonably descriptive.")
    if not readability: positives.append("Formatting and control flow are readable.")
    if not modularity: positives.append("The implementation has acceptable decomposition.")
    return {
        **scores,
        "style_score": round(sum(scores.values()), 2),
        "naming_issues": naming,
        "readability_issues": readability,
        "modularity_issues": modularity,
        "maintainability_issues": maintainability,
        "positive_aspects": positives,
        "summary": "Deterministic AST/style checks completed.",
        "method": "ast",
        "status": "ANALYZED",
    }
