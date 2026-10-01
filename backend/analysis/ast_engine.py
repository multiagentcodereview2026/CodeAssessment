from typing import Optional
from .complexity_ir import ComplexityIR
from .models import ComplexityAnalysis
from .complexity_normalizer import normalize_complexity

def infer_complexity_from_ir(ir: ComplexityIR) -> ComplexityAnalysis:
    """
    Deterministically computes Time and Space complexity from ComplexityIR
    using standard Big-O composition rules.
    """
    time_complexity = "O(1)"
    space_complexity = "O(1)"

    loop = ir.loop
    recursion = ir.recursion
    graph = ir.graph

    # === TIME & SPACE COMPLEXITY INFERENCE ===

    # 1. GRAPH ALGORITHMS
    if graph.is_graph:
        if graph.structure == "adj_matrix":
            time_complexity = "O(V^2)"
            space_complexity = "O(V^2)"
        elif graph.structure == "adj_list":
            time_complexity = "O(V+E)"
            space_complexity = "O(V)"
        elif graph.structure == "edge_list":
            time_complexity = "O(E)"
            space_complexity = "O(E)"
        else:
            # Generic graph traversal fallback
            time_complexity = "O(V+E)"
            space_complexity = "O(V)"

    # 2. RECURSION PATTERNS
    elif recursion.is_recursive:
        if recursion.has_memoization:
            # Memoized recursion: O(n) time, O(n) space
            time_complexity = "O(n)"
            space_complexity = "O(n)"
        else:
            branch_factor = recursion.branch_factor
            pattern = recursion.pattern

            if pattern == "tail" or branch_factor == 1:
                time_complexity = "O(n)"
            elif branch_factor == 2:
                time_complexity = "O(2^n)"
            elif branch_factor == 3:
                time_complexity = "O(3^n)"
            elif branch_factor == 4:
                time_complexity = "O(4^n)"
            elif branch_factor >= 5:
                time_complexity = "O(n!)"

            # Space = recursion depth
            space_complexity = "O(n)"

    # 3. BINARY SEARCH
    elif loop.has_binary_search:
        time_complexity = "O(log n)"
        space_complexity = "O(1)"

    # 4. LOOP-BASED ALGORITHMS
    elif loop.depth > 0:
        # Check for sort inside loop
        if loop.has_sort and loop.depth >= 1:
            if loop.structure == "nested" and loop.depth >= 2:
                time_complexity = "O(n^2 log n)"
            else:
                time_complexity = "O(n log n)"
        elif loop.structure == "sequential":
            # Independent sequential loops: O(n) + O(n) = O(n)
            if loop.has_sort:
                time_complexity = "O(n log n)"
            else:
                time_complexity = "O(n)"
        elif loop.depth == 1:
            time_complexity = "O(n)"
        elif loop.depth == 2:
            # Check if bounds are different (m, n)
            unique_bounds = set(loop.bounds)
            if len(unique_bounds) >= 2 and "v" in unique_bounds and "e" in unique_bounds:
                time_complexity = "O(V+E)"
            elif len(unique_bounds) >= 2:
                time_complexity = "O(mn)"
            else:
                time_complexity = "O(n^2)"
        elif loop.depth == 3:
            time_complexity = "O(n^3)"
        elif loop.depth >= 4:
            time_complexity = "O(n^4+)"

        # Check for data structure allocation
        if ir.has_dynamic_allocation:
            space_complexity = "O(n)"

    # 5. JUST SORT, NO LOOPS
    elif loop.has_sort:
        time_complexity = "O(n log n)"
        space_complexity = "O(1)"

    return ComplexityAnalysis(
        time_complexity=normalize_complexity(time_complexity) or "O(1)",
        space_complexity=normalize_complexity(space_complexity) or "O(1)",
        confidence=0.9,
        method="ast",
        status="ANALYZED"
    )
