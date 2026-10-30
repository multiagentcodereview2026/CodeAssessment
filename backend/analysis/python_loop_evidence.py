"""Narrow Python size identities and explicit reasons to abstain from scoring.

This adds evidence to the existing engine, not a new complexity estimator.
Only simple, unmodified names and single assignments are equated. Unsupported
iterators/call costs remain review cases; no source is executed here.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from .models import ComplexityAnalysis


@dataclass
class PythonLoopEvidence:
    dimensions: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


def python_loop_evidence(source: str) -> PythonLoopEvidence:
    facts = PythonLoopEvidence()
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError):
        facts.issues.append("python-syntax-unresolved")
        return facts

    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}

    def scope(node):
        while node in parents:
            node = parents[node]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                return node
        return tree

    nodes = list(ast.walk(tree))
    scopes = {n: scope(n) for n in nodes}
    assignments_by_name = {}
    write_counts = {}
    writes_by_name = {}
    aliases = {}
    for n in nodes:
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            key = (scopes[n], n.id)
            write_counts[key] = write_counts.get(key, 0) + 1
            writes_by_name.setdefault(key, []).append(n)
        if isinstance(n, ast.Assign):
            for target in n.targets:
                if isinstance(target, ast.Name):
                    assignments_by_name.setdefault((scopes[n], target.id), []).append(n)
                    if isinstance(n.value, ast.Name):
                        aliases.setdefault((scopes[n], n.value.id), set()).add(target.id)
    builtin_names = {"range", "len", "enumerate"}
    bindings = {n.id for n in nodes if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    bindings.update(n.arg for n in nodes if isinstance(n, ast.arg))
    bindings.update(n.name for n in nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    if bindings & builtin_names:
        facts.issues.append("python-shadowed-iteration-builtin")

    defined = {n.name for n in nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    fixed_cost_calls = {"range", "len", "enumerate", "int", "float", "bool", "abs"}
    mutators = {"append", "extend", "insert", "pop", "remove", "clear"}

    def identity(expr, loop, seen=frozenset()):
        if isinstance(expr, ast.Name):
            if expr.id in seen:
                return None
            key = (scopes[loop], expr.id)
            assignments = assignments_by_name.get(key, [])
            if len(assignments) == write_counts.get(key, 0) == 1 and assignments[0].lineno < loop.lineno:
                value = assignments[0].value
                if isinstance(value, ast.Name) or (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
                                                 and value.func.id == "len"):
                    referenced = {n.id for n in ast.walk(value) if isinstance(n, ast.Name)} - builtin_names
                    if any(assignments[0].lineno < write.lineno <= loop.lineno
                           for name in referenced for write in writes_by_name.get((scopes[loop], name), [])):
                        facts.issues.append("python-size-alias-rebound")
                        return None
                    return identity(value, loop, seen | {expr.id})
            return f"{getattr(scopes[loop], 'lineno', 0)}:{expr.id}"
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            name = expr.func.id
            if name in {"len", "enumerate"} and len(expr.args) == 1 and not expr.keywords:
                return identity(expr.args[0], loop, seen)
            if name == "range" and 1 <= len(expr.args) <= 3 and not expr.keywords:
                # Only fixed start/step; a variable step needs separate analysis.
                bound = expr.args[0] if len(expr.args) == 1 else expr.args[1]
                other = [] if len(expr.args) == 1 else [expr.args[0], *expr.args[2:]]
                if all(isinstance(v, ast.Constant) and isinstance(v.value, int) for v in other):
                    return identity(bound, loop, seen)
        if isinstance(expr, ast.Constant) and isinstance(expr.value, int):
            return "constant"
        return None

    for loop in (n for n in nodes if isinstance(n, (ast.For, ast.AsyncFor))):
        dimension = identity(loop.iter, loop)
        if dimension is None:
            facts.issues.append("python-unresolved-iterator-bound")
        elif dimension != "constant":
            facts.dimensions.append(dimension)
        names = {n.id for n in ast.walk(loop.iter) if isinstance(n, ast.Name)} - builtin_names
        if dimension and dimension != "constant":
            names.add(dimension.rsplit(":", 1)[-1])
        # Include direct aliases of the traversed collection when checking mutations.
        for name in list(names):
            names.update(aliases.get((scopes[loop], name), set()))
        for statement in loop.body:
            for n in ast.walk(statement):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id in names:
                    facts.issues.append("python-loop-bound-rebound")
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name):
                    if n.func.value.id in names and n.func.attr in mutators:
                        facts.issues.append("python-iterated-collection-mutated")
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id not in fixed_cost_calls | defined:
                    facts.issues.append("python-unresolved-loop-call-cost")
    facts.dimensions = list(dict.fromkeys(facts.dimensions))
    facts.issues = list(dict.fromkeys(facts.issues))
    return facts


def guard_python_complexity(source: str, language: str, result: ComplexityAnalysis) -> ComplexityAnalysis:
    if language.lower().strip() not in {"python", "py"}:
        return result
    facts = python_loop_evidence(source)
    if not facts.issues:
        return result
    return ComplexityAnalysis(time_complexity=result.time_complexity, space_complexity=result.space_complexity,
                   confidence=result.confidence, method=getattr(result, "method", "ast"), status="REVIEW_REQUIRED", evidence_quality="unresolved",
                   signals=list(dict.fromkeys([*result.signals, "structural-review-blocked", *facts.issues])),
                   dynamic_measurements=list(getattr(result, "dynamic_measurements", []) or []),
                   explanation="Structural complexity needs review: " + ", ".join(facts.issues) + ". No complexity marks can be finalized from these heuristics.")
