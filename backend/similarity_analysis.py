"""Language-independent structural evidence for instructor similarity review.

This module deliberately does not decide misconduct.  It turns parsed syntax
into a small canonical fingerprint, classifies an algorithmic approach from the
existing AST complexity IR, and creates concise evidence explanations.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from analysis.ast_parser import ASTComplexityAnalyzer
from analysis.pattern_library import classify_pattern


def _canonical_node(node_type: str) -> str | None:
    """Map language-specific Tree-sitter node types to common structure."""
    kind = (node_type or "").lower()
    if "for" in kind or "while" in kind or kind in {"do_statement"}:
        return "LOOP"
    if "if" in kind or "switch" in kind or "conditional" in kind:
        return "BRANCH"
    if "function" in kind or "method_declaration" in kind or "lambda" in kind:
        return "FUNCTION"
    if "call" in kind or "invocation" in kind:
        return "CALL"
    if "return" in kind:
        return "RETURN"
    if "assignment" in kind or kind in {"assignment", "assignment_expression"}:
        return "ASSIGN"
    if "binary" in kind or "unary" in kind or "update" in kind:
        return "OPERATION"
    if "subscript" in kind or "index" in kind:
        return "INDEX"
    if any(word in kind for word in ("array", "list", "map", "dictionary", "set", "tuple")):
        return "COLLECTION"
    if "new_expression" in kind or "object_creation" in kind or "allocation" in kind:
        return "ALLOCATION"
    if "identifier" in kind or kind in {"name", "field_identifier", "type_identifier"}:
        return "IDENT"
    if any(word in kind for word in ("integer", "float", "number", "string", "char", "literal")):
        return "LITERAL"
    return None


def _shingles(tokens: list[str], width: int = 3) -> set[tuple[str, ...]]:
    if len(tokens) < width:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[index:index + width]) for index in range(len(tokens) - width + 1)}


def structural_fingerprint(source: str, language: str) -> dict[str, Any]:
    """Return canonical AST facts without retaining identifiers or comments."""
    analyzer = ASTComplexityAnalyzer(source or "", language)
    ir = analyzer.analyze()
    tokens: list[str] = []
    if analyzer.tree and analyzer.tree.root_node:
        stack = [analyzer.tree.root_node]
        while stack:
            node = stack.pop()
            label = _canonical_node(getattr(node, "type", ""))
            if label:
                tokens.append(label)
            # Reverse keeps source-order traversal deterministic.
            stack.extend(reversed(list(getattr(node, "children", []) or [])))

    # A parser fallback still supplies generic structural facts from the
    # complexity IR; this keeps the evidence useful across supported runtimes.
    if not tokens:
        tokens = ["LOOP"] * int(getattr(ir.loop, "depth", 0) or 0)
        if getattr(ir.recursion, "is_recursive", False):
            tokens.append("RECURSION")
        if getattr(ir.graph, "is_graph", False):
            tokens.append("GRAPH")
        if getattr(ir, "has_dynamic_allocation", False):
            tokens.append("ALLOCATION")

    pattern = classify_pattern(ir)
    facts = {
        "loopDepth": int(getattr(ir.loop, "depth", 0) or 0),
        "recursive": bool(getattr(ir.recursion, "is_recursive", False)),
        "graph": bool(getattr(ir.graph, "is_graph", False)),
        "dynamicAllocation": bool(getattr(ir, "has_dynamic_allocation", False)),
        "matrixState": bool(getattr(ir, "has_2d_allocation", False) or getattr(ir.loop, "has_matrix_bounds", False)),
        "algorithm": pattern.name,
        "structures": sorted(set(tokens)),
    }
    return {"tokens": tokens, "shingles": _shingles(tokens), "facts": facts}


def structural_overlap(left: dict[str, Any], right: dict[str, Any]) -> float:
    """Jaccard overlap for canonical AST-shape shingles, in the range 0..1."""
    left_shingles = set(left.get("shingles") or set())
    right_shingles = set(right.get("shingles") or set())
    if not left_shingles or not right_shingles:
        return 0.0
    return len(left_shingles & right_shingles) / len(left_shingles | right_shingles)


def structural_explanation(left: dict[str, Any], right: dict[str, Any], overlap: float) -> list[str]:
    """Explain shared code structure in plain language; no model call is required."""
    left_facts, right_facts = left.get("facts") or {}, right.get("facts") or {}
    details: list[str] = []
    left_patterns = set(left.get("shingles") or set())
    right_patterns = set(right.get("shingles") or set())
    shared_count = len(left_patterns & right_patterns)
    union_count = len(left_patterns | right_patterns)
    if union_count:
        details.append(
            f"The solutions share {shared_count} unique short sequences of programming structure "
            f"out of {union_count} compared ({overlap:.0%} structural overlap)."
        )
    shared_structures = set(left_facts.get("structures") or []) & set(right_facts.get("structures") or [])
    readable_structures = {
        "LOOP": "Both solutions repeat work using a loop.",
        "BRANCH": "Both solutions make decisions with conditions such as if or switch.",
        "ASSIGN": "Both solutions assign intermediate values while processing the input.",
        "RETURN": "Both solutions return a computed result.",
        "CALL": "Both solutions call helper or library functions.",
        "COLLECTION": "Both solutions use a collection such as an array, list, map, or set.",
        "INDEX": "Both solutions access values by position or index.",
        "OPERATION": "Both solutions use similar kinds of arithmetic or comparison operations.",
    }
    for structure, explanation in readable_structures.items():
        if structure in shared_structures:
            details.append(explanation)
    if left_facts.get("loopDepth") == right_facts.get("loopDepth") and left_facts.get("loopDepth", 0):
        depth = left_facts["loopDepth"]
        details.append("Both use loops at the same nesting level." if depth == 1 else f"Both nest loops to depth {depth}.")
    if left_facts.get("recursive") and right_facts.get("recursive"):
        details.append("Both solutions call themselves again to solve smaller parts of the problem.")
    if left_facts.get("matrixState") and right_facts.get("matrixState"):
        details.append("Both solutions store intermediate results in a two-dimensional table.")
    if left_facts.get("algorithm") == right_facts.get("algorithm") and left_facts.get("algorithm") != "unknown":
        approach = str(left_facts["algorithm"]).replace("-", " ")
        details.append(f"The structure checker classified both as using a {approach} approach.")
    return details or ["The submissions solve the same assigned problem, but no specific shared structure stood out. Compare the source code before drawing conclusions."]


def approach_label(fingerprint: dict[str, Any]) -> str:
    """Return a stable generic approach label, never a problem-name label."""
    facts = fingerprint.get("facts") or {}
    label = str(facts.get("algorithm") or "constant-work")
    return label.replace("-", " ").title()


def approach_summary(fingerprint: dict[str, Any]) -> str:
    facts = fingerprint.get("facts") or {}
    parts: list[str] = []
    if facts.get("graph"):
        parts.append("graph structure")
    if facts.get("recursive"):
        parts.append("recursion")
    if facts.get("matrixState"):
        parts.append("matrix-like state")
    if facts.get("loopDepth"):
        parts.append(f"loop depth {facts['loopDepth']}")
    return ", ".join(parts) if parts else "constant-size structural work"
