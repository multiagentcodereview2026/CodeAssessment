"""Shared, conservative algorithm-pattern classification.

The parser extracts structural evidence and the engine applies precedence.
This module is the common vocabulary between them, preventing individual
branches from inventing subtly different names for the same algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass

from .complexity_ir import ComplexityIR


@dataclass(frozen=True)
class PatternMatch:
    name: str
    confidence: float
    reason: str


def classify_pattern(ir: ComplexityIR) -> PatternMatch:
    """Return the strongest structural pattern supported by *ir*.

    The ordering is deliberately conservative: a graph or recursive pattern
    wins over a generic loop, and amortized structures win over raw nesting.
    No source-specific problem names are used.
    """
    rec = ir.recursion
    loop = ir.loop
    graph = ir.graph

    if rec.has_mutual_recursion:
        return PatternMatch("mutual-recursion", 0.98, "recursive cycle in the call graph")
    if rec.is_recursive and rec.pattern == "path_compression":
        return PatternMatch("disjoint-set-find", 0.98, "parent-pointer path compression")
    if graph.is_graph:
        return PatternMatch("graph-traversal", 0.96, "graph representation or traversal evidence")
    if rec.is_recursive and rec.pattern == "factorial":
        return PatternMatch("backtracking", 0.94, "recursive branch inside a search loop")
    if rec.is_recursive and rec.has_memoization:
        return PatternMatch("dynamic-programming", 0.95, "recursive state cache/memo table")
    if loop.is_sliding_window:
        return PatternMatch("sliding-window", 0.96, "moving window boundaries")
    if loop.is_monotonic_stack:
        return PatternMatch("monotonic-stack", 0.96, "amortized stack push/pop")
    if loop.has_bit_operations:
        return PatternMatch("fenwick-or-bit", 0.94, "lowbit update/query progression")
    if loop.has_binary_search:
        return PatternMatch("binary-search", 0.94, "halving search interval")
    if loop.has_sort:
        return PatternMatch("comparison-sort", 0.93, "library sort operation")
    if ir.has_heap_operations:
        return PatternMatch("heap-processing", 0.93, "priority queue/heap operations")
    if ir.has_2d_allocation or loop.has_matrix_bounds:
        return PatternMatch("matrix-or-dp", 0.90, "two-dimensional state space")
    if loop.depth:
        return PatternMatch("iterative-loop", 0.80, "bounded loop structure")
    if ir.has_dynamic_allocation:
        return PatternMatch("dynamic-storage", 0.75, "input-sized dynamic storage")
    return PatternMatch("constant-work", 0.85, "no scalable structural evidence")
