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
STYLE_PENALTY_MULTIPLIER = 1


def _finding(category: str, message: str, severity: str = "minor", penalty: int = 1, line: int | None = None, credit: int = 0) -> dict[str, Any]:
    calibrated_penalty = penalty * STYLE_PENALTY_MULTIPLIER
    return {"category": category, "message": message, "severity": severity, "penalty": calibrated_penalty, "credit": credit, "line": line}


def _score(issues: list[dict[str, Any]], category: str) -> float:
    relevant = [i for i in issues if i["category"] == category]
    return max(0.0, min(25.0, 25.0 - sum(i.get("penalty", 0) for i in relevant) + sum(i.get("credit", 0) for i in relevant)))


def _deduplicate_findings(groups: tuple[list[dict[str, Any]], ...]) -> tuple[list[dict[str, Any]], ...]:
    """Remove repeated evidence while preserving deterministic order."""
    result: list[list[dict[str, Any]]] = []
    for group in groups:
        seen: set[tuple[Any, ...]] = set()
        unique: list[dict[str, Any]] = []
        for finding in group:
            key = (
                finding.get("category"),
                finding.get("message"),
                finding.get("line"),
            )
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        result.append(unique)
    return tuple(result)


def _python_metrics(source: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    naming: list[dict[str, Any]] = []
    readability: list[dict[str, Any]] = []
    modularity: list[dict[str, Any]] = []
    maintainability: list[dict[str, Any]] = []
    deep_nesting_detected = False
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
                loop_names = {
                    target.id
                    for loop in ast.walk(node)
                    if isinstance(loop, (ast.For, ast.AsyncFor))
                    for target in ast.walk(loop.target)
                    if isinstance(target, ast.Name)
                }
                for name in args:
                    if len(name) == 1 and name in loop_names:
                        continue
                    if len(name) == 1:
                        naming.append(_finding("naming", f"Parameter `{name}` is too cryptic.", "moderate", 4, node.lineno))
                if len(node.name) <= 1:
                    naming.append(_finding("naming", f"Function `{node.name}` is cryptic.", "major", 8, node.lineno))
                lines = (getattr(node, "end_lineno", node.lineno) - node.lineno + 1)
                if lines > 120:
                    readability.append(_finding("readability", f"Function `{node.name}` is very long.", "major", 5))
                elif lines > 60:
                    readability.append(_finding("readability", f"Function `{node.name}` is long.", "moderate", 3))
                if len(args) > 5:
                    modularity.append(_finding("modularity", f"Function `{node.name}` has many parameters.", "moderate", 6))
                    maintainability.append(_finding("maintainability", f"Function `{node.name}` is difficult to change because it has many parameters.", "moderate", 5, node.lineno))
                # A long sequence of independent statements is difficult to
                # review and change even when it is not deeply nested.
                statement_count = sum(
                    isinstance(child, ast.stmt)
                    for child in ast.walk(node)
                )
                if lines > 20 or statement_count > 20:
                    modularity.append(_finding("modularity", "Function contains too many statements for one responsibility.", "moderate", 4, node.lineno))
                    maintainability.append(_finding("maintainability", "Large statement volume makes the function difficult to change.", "moderate", 4, node.lineno))
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if len(node.id) == 1 and node.id not in _ALLOWED_SHORT:
                    naming.append(_finding("naming", f"Variable `{node.id}` is cryptic.", line=node.lineno))
                elif node.id.lower() in _GENERIC_NAMES:
                    naming.append(_finding("naming", f"Variable `{node.id}` is generic.", line=node.lineno))
            elif isinstance(node, (ast.For, ast.While, ast.If, ast.Try)):
                depth = 0
                parent = getattr(node, "_style_parent", None)
                while parent is not None:
                    if isinstance(parent, (ast.For, ast.While, ast.If, ast.Try)):
                        depth += 1
                    parent = getattr(parent, "_style_parent", None)
                if depth >= 4:
                    if not deep_nesting_detected:
                        readability.append(_finding("readability", "Control flow is deeply nested.", "major", 5, node.lineno))
                        modularity.append(_finding("modularity", "Deeply nested control flow indicates poor separation of responsibilities.", "moderate", 5, node.lineno))
                        maintainability.append(_finding("maintainability", "Deep nesting makes future changes difficult.", "moderate", 5, node.lineno))
                        deep_nesting_detected = True
    lines = source.splitlines()
    # Source-level fallback for nested constructs whose AST parent links are
    # unavailable after parsing/serialization.
    if not deep_nesting_detected and len(re.findall(r"\b(?:if|for|while|try)\b", source)) >= 5:
        readability.append(_finding("readability", "Multiple nested control constructs reduce readability.", "major", 5, 1))
        modularity.append(_finding("modularity", "Control flow is not cleanly separated into helpers.", "moderate", 5, 1))
        maintainability.append(_finding("maintainability", "Highly nested logic is difficult to extend safely.", "moderate", 5, 1))
    if any(len(line) > 120 for line in lines):
        line = next((i for i, text in enumerate(lines, 1) if len(text) > 120), None)
        readability.append(_finding("readability", "One or more lines exceed 120 characters.", "minor", 1, line))
    if source.strip() and not re.search(r"(^|\n)\s*#", source):
        readability.append(_finding("readability", "No explanatory comments were found.", "minor", 1, 1))
    if tree is not None and sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree)) == 1:
        functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if functions and (getattr(functions[0], "end_lineno", 0) - functions[0].lineno) > 40:
            modularity.append(_finding("modularity", "A large implementation could be decomposed into helpers.", "moderate", 3, functions[0].lineno))
        if functions:
            function_source = ast.get_source_segment(source, functions[0]) or source
            has_io = bool(re.search(r"\b(?:input|print|open)\s*\(", function_source))
            has_iteration = bool(re.search(r"\b(?:for|while)\b", function_source))
            if has_io and has_iteration:
                modularity.append(_finding("modularity", "One function combines input/output with core iteration logic.", "moderate", 6, functions[0].lineno))
            called_names = {
                call.func.id
                for call in ast.walk(functions[0])
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
            }
            if len(called_names) >= 6:
                maintainability.append(_finding("maintainability", "Function is highly coupled to many separate operations.", "moderate", 6, functions[0].lineno))
    python_lines = [re.sub(r"\s+", " ", line.strip()) for line in lines if line.strip() and not line.strip().startswith("#")]
    repeated_python = {line for line in python_lines if len(line) >= 12 and python_lines.count(line) >= 2}
    if repeated_python:
        modularity.append(_finding("modularity", "Repeated Python statements suggest duplicated logic.", "moderate", 5, 1))
        maintainability.append(_finding("maintainability", "Duplicated Python logic increases maintenance cost.", "moderate", 6, 1))
    if re.search(r"\b(?:TODO|FIXME)\b", source, re.I):
        line = next((i for i, text in enumerate(lines, 1) if re.search(r"\b(?:TODO|FIXME)\b", text, re.I)), None)
        maintainability.append(_finding("maintainability", "TODO/FIXME markers remain in the submission.", "minor", 1, line))
    return naming, readability, modularity, maintainability


def _generic_metrics(source: str, language: str = "") -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    naming, readability, modularity, maintainability = [], [], [], []
    lines = source.splitlines()
    for match in re.finditer(r"\b(?:int|long|double|string|auto|var|let|const)\s+([A-Za-z_]\w*)", source):
        name = match.group(1)
        line = source.count("\n", 0, match.start()) + 1
        # A function declaration is not a variable declaration.  Skipping it
        # here prevents `f` from receiving both variable and function findings.
        after_name = source[match.end():]
        if re.match(r"\s*\(", after_name):
            continue
        # Conventional short names are valid in local loop/index contexts.
        declaration_prefix = source[max(0, match.start() - 24):match.start()]
        in_loop_header = bool(re.search(r"\b(?:for|while)\s*\([^)]*$", declaration_prefix))
        if len(name) == 1 and name not in _ALLOWED_SHORT:
            naming.append(_finding("naming", f"Variable `{name}` is cryptic.", "moderate", 4, line))
        elif len(name) == 1 and not in_loop_header and name not in {"i", "j", "k", "n", "m"}:
            naming.append(_finding("naming", f"Contextually unclear variable `{name}`.", "minor", 2, line))
        elif len(name) == 1 and language.lower() in {"java", "javascript", "js"} and name not in {"i", "j", "k", "n", "m"}:
            naming.append(_finding("naming", f"Contextually unclear variable `{name}`.", "minor", 2, line))
        elif name.lower() in _GENERIC_NAMES:
            naming.append(_finding("naming", f"Variable `{name}` is generic.", line=line))
    # Inspect function names and parameters as well as local declarations.
    # This catches compressed interview-style submissions such as `f(a,t)`.
    for match in re.finditer(r"\b(?:\w[\w:<>,&*\s]*\s+)?([A-Za-z_]\w*)\s*\(([^()]*)\)\s*\{", source):
        function_name, parameters = match.group(1), match.group(2)
        line = source.count("\n", 0, match.start()) + 1
        if function_name in {"if", "for", "while", "switch", "catch"}:
            continue
        if len(function_name) <= 1:
            naming.append(_finding("naming", f"Function `{function_name}` is cryptic.", "major", 8, line))
        # Use a small context window for parameter names.  Conventional index
        # names are acceptable when the body actually uses them as indexes or
        # loop counters; otherwise they remain eligible for a naming finding.
        body_context = source[match.end():]
        for parameter in parameters.split(","):
            parameter = parameter.strip()
            if not parameter:
                continue
            parameter_name_match = re.search(r"([A-Za-z_]\w*)\s*(?:\]|>|$)", parameter)
            if parameter_name_match and len(parameter_name_match.group(1)) == 1:
                parameter_name = parameter_name_match.group(1)
                index_context = parameter_name in {"i", "j", "k"} and bool(
                    re.search(
                        rf"(?:\bfor\b[^{{}};]*\b{re.escape(parameter_name)}\b|"
                        rf"\b{re.escape(parameter_name)}\s*(?:\+\+|--)|"
                        rf"(?:\[\s*{re.escape(parameter_name)}\s*\]))",
                        body_context,
                    )
                )
                if not index_context:
                    naming.append(_finding("naming", f"Parameter `{parameter_name}` is too cryptic.", "moderate", 4, line))
    if any(len(line) > 120 for line in lines):
        line = next((i for i, text in enumerate(lines, 1) if len(text) > 120), None)
        readability.append(_finding("readability", "One or more lines exceed 120 characters.", "minor", 3, line))
    comment_matches = re.findall(r"(?:^|\n)\s*(?://|/\*+|\*+)(.*)", source)
    meaningful_comment = any(len(re.findall(r"[A-Za-z]{3,}", text)) >= 4 for text in comment_matches)
    control_count = len(re.findall(r"\b(?:for|while|if|switch|try|catch)\b", source))
    complex_logic = control_count >= 3 or bool(re.search(r"(?:\?[^:]+:|&&.*&&|\|\|.*\|\|)", source))
    if complex_logic and not meaningful_comment:
        readability.append(_finding("readability", "No useful explanation was found for non-obvious logic.", "minor", 3, 1))
    elif meaningful_comment:
        comment_line = next((i for i, text in enumerate(lines, 1) if re.search(r"//|/\*|\*", text)), 1)
        readability.append(_finding("readability", "Useful explanatory comment detected.", "info", 0, comment_line, credit=2))
    depth = max(((len(line) - len(line.lstrip(" \t"))) // 4 for line in source.splitlines()), default=0)
    if depth >= 5:
        readability.append(_finding("readability", "Control flow appears deeply nested.", "moderate", 5, 1))
    nonempty_lines = [line for line in source.splitlines() if line.strip()]
    packed_statement_lines = [
        line for line in nonempty_lines
        if (len(line) > 120 and line.count(";") >= 2)
        or (language.lower() in {"java", "javascript", "js"} and line.count(";") >= 3 and not line.lstrip().startswith("for ("))
        or (len(line) > 60 and line.count(";") >= 3 and not line.lstrip().startswith("for ("))
    ]
    if packed_statement_lines or any(len(line) > 160 and ("{" in line or "}" in line) for line in nonempty_lines):
        readability.append(_finding("readability", "Code is excessively compressed onto very few lines.", "major", 10, 1))
    if packed_statement_lines:
        modularity.append(_finding("modularity", "Packed statements make responsibility boundaries unclear.", "moderate", 4, 1))
        maintainability.append(_finding("maintainability", "Packed statements create a difficult-to-change structure.", "moderate", 6, 1))
    if source.count(";") >= 5 and len(nonempty_lines) <= 6:
        maintainability.append(_finding("maintainability", "Many statements are packed into a compressed layout.", "major", 6, 1))
    function_count = len(re.findall(r"\b(?:void|int|bool|string|auto|[A-Za-z_]\w*(?:<[^>]+>)?)\s+\w+\s*\([^)]*\)", source))
    if function_count >= 2 and len(nonempty_lines) >= 3 and not packed_statement_lines:
        modularity.append(_finding("modularity", "Multiple named functions provide reusable decomposition.", "info", 0, 1, credit=3))
    if function_count == 1 and source.count("\n") > 60:
        modularity.append(_finding("modularity", "A large implementation could be decomposed into helpers.", "minor", 1, 1))
    normalized_lines = [re.sub(r"\s+", " ", line.strip()) for line in nonempty_lines]
    repeated = {line for line in normalized_lines if len(line) >= 12 and normalized_lines.count(line) >= 2}
    if repeated:
        modularity.append(_finding("modularity", "Repeated statements suggest duplicated logic.", "moderate", 5, 1))
        maintainability.append(_finding("maintainability", "Duplicated logic increases maintenance cost.", "moderate", 6, 1))
    numeric_literals = [int(value) for value in re.findall(r"(?<![A-Za-z_])(-?\d+)(?![A-Za-z_])", source)]
    significant_constants = [value for value in numeric_literals if value not in {-1, 0, 1}]
    if len(significant_constants) >= 2:
        maintainability.append(_finding("maintainability", "Multiple unexplained numeric constants may be magic numbers.", "minor", 3, 1))
    return naming, readability, modularity, maintainability


def analyze_style(source: str, language: str) -> dict[str, Any]:
    source = source or ""
    normalized_language = (language or "").lower().strip()
    if normalized_language in {"python", "py"}:
        groups = _python_metrics(source)
    elif normalized_language in {"cpp", "c++", "c", "java", "javascript", "js"}:
        # Keep language dispatch explicit.  These languages currently share
        # the conservative source/structure adapter; each can be upgraded to
        # a native parser without changing the scoring contract.
        groups = _generic_metrics(source, normalized_language)
    else:
        # Unknown languages receive conservative generic evidence rather than
        # being misclassified as Python.
        groups = _generic_metrics(source, normalized_language)
    groups = _deduplicate_findings(groups)
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
