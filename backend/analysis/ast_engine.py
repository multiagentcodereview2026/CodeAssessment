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
        if graph.traversal_inside_loop:
            # Traversal inside vertex loop e.g. for s = 0; s < V; s++ reach(s, s, g, vis)
            time_complexity = "O(V*(V+E))"
            space_complexity = "O(V+E)"
        elif graph.structure == "adj_matrix":
            time_complexity = "O(V^2)"
            space_complexity = "O(V^2)"
        elif graph.structure == "adj_list":
            time_complexity = "O(V+E)"
            space_complexity = "O(V+E)"
        elif graph.structure == "edge_list":
            time_complexity = "O(E)"
            space_complexity = "O(E)"
        else:
            time_complexity = "O(V+E)"
            space_complexity = "O(V+E)"

    # 2. RECURSION PATTERNS
    elif recursion.is_recursive:
        if recursion.has_memoization:
            # Memoized recursion: O(n) time, O(n) space
            time_complexity = "O(n)"
            space_complexity = "O(n)"
        elif recursion.is_divide_and_conquer:
            # Divide and Conquer patterns
            if recursion.pattern == "simple_divide_and_conquer":
                # Simple D&C like finding max: T(n) = 2T(n/2) + O(1) = O(n)
                time_complexity = "O(n)"
                space_complexity = "O(log n)"
            else:
                # MergeSort, QuickSort: T(n) = 2T(n/2) + O(n) = O(n log n)
                time_complexity = "O(n log n)"
                if recursion.has_auxiliary_array or ir.has_dynamic_allocation:
                    space_complexity = "O(n)"  # MergeSort auxiliary buffer
                else:
                    space_complexity = "O(log n)"  # QuickSort recursion stack
        else:
            branch_factor = recursion.branch_factor
            pattern = recursion.pattern

            if pattern == "tail" or branch_factor == 1:
                time_complexity = "O(n)"
                space_complexity = "O(n)"
            elif branch_factor == 2:
                time_complexity = "O(2^n)"
                space_complexity = "O(n)"
            elif branch_factor == 3:
                time_complexity = "O(3^n)"
                space_complexity = "O(n)"
            elif branch_factor == 4:
                time_complexity = "O(4^n)"
                space_complexity = "O(n)"
            elif branch_factor >= 5:
                time_complexity = "O(n!)"
                space_complexity = "O(n)"
            else:
                time_complexity = "O(n)"
                space_complexity = "O(n)"

    # 3. BINARY SEARCH (STANDALONE)
    elif loop.has_binary_search and not loop.binary_search_inside_loop and loop.depth <= 1:
        time_complexity = "O(log n)"
        space_complexity = "O(1)"

    # 4. LOGARITHMIC STEP (e.g. x /= 10)
    elif loop.is_logarithmic_step and loop.depth <= 1:
        time_complexity = "O(log n)"
        space_complexity = "O(1)"

    # 5. MULTI-INPUT BOUNDS (e.g. Median of 2 sorted arrays)
    elif loop.multiple_input_bounds and loop.depth <= 1:
        time_complexity = "O(m+n)"
        if ir.has_dynamic_allocation and ir.has_merged_both:
            space_complexity = "O(m+n)"
        elif ir.has_dynamic_allocation:
            space_complexity = "O(n)"
        else:
            space_complexity = "O(1)"

    # 6. LOOP-BASED ALGORITHMS
    elif loop.depth > 0:
        # Check heap operations inside loops
        if loop.has_heap_operations:
            if loop.depth == 1:
                time_complexity = "O(n log n)"  # Single loop with heap ops
            else:
                time_complexity = f"O(n^{loop.depth} log n)"
        # Check binary search inside loop
        elif loop.has_binary_search and loop.binary_search_inside_loop:
            if loop.binary_search_loop_depth >= 2:
                time_complexity = "O(n^2 log n)"  # e.g. 3Sum with binary search
            else:
                time_complexity = "O(n log n)"    # e.g. LIS with lower_bound
        # Check sort interaction
        elif loop.has_sort:
            if loop.sort_inside_loop:
                if loop.depth >= 2:
                    time_complexity = "O(n^2 log n)"
                else:
                    time_complexity = "O(n log n)"
            else:
                # Sequential sort outside loop: max(O(n log n), loop_complexity)
                if loop.depth >= 3:
                    time_complexity = "O(n^3)"  # 4Sum: O(n log n) + O(n^3) = O(n^3)
                elif loop.depth == 2:
                    time_complexity = "O(n^2)"  # 3Sum: O(n log n) + O(n^2) = O(n^2)
                else:
                    time_complexity = "O(n log n)"  # Merge Intervals: O(n log n) + O(n) = O(n log n)
        elif loop.structure == "sequential":
            if loop.multiple_input_bounds:
                time_complexity = "O(m+n)"
            else:
                time_complexity = "O(n)"
        elif loop.depth == 1:
            if loop.is_logarithmic_step:
                time_complexity = "O(log n)"
            elif loop.multiple_input_bounds:
                time_complexity = "O(m+n)"
            else:
                time_complexity = "O(n)"
        elif loop.depth == 2:
            unique_bounds = set(loop.bounds)
            if len(unique_bounds) >= 2 and "v" in unique_bounds and "e" in unique_bounds:
                time_complexity = "O(V+E)"
            elif loop.has_matrix_bounds:
                time_complexity = "O(m*n)"
            else:
                time_complexity = "O(n^2)"
        elif loop.depth == 3:
            time_complexity = "O(n^3)"
        elif loop.depth >= 4:
            time_complexity = "O(n^4+)"

        # Determine space complexity
        if ir.is_constant_lookup:
            space_complexity = "O(1)"
        elif ir.has_2d_allocation:
            space_complexity = "O(n^2)"
        elif ir.has_dynamic_allocation:
            if loop.multiple_input_bounds and ir.has_merged_both:
                space_complexity = "O(m+n)"
            else:
                space_complexity = "O(n)"
        else:
            space_complexity = "O(1)"

    # 7. JUST SORT, NO LOOPS
    elif loop.has_sort:
        time_complexity = "O(n log n)"
        space_complexity = "O(n)" if ir.has_dynamic_allocation else "O(1)"

    # Final space check for constant lookups and 2D allocations
    if ir.is_constant_lookup:
        space_complexity = "O(1)"
    elif ir.has_2d_allocation:
        space_complexity = "O(n^2)"

    return ComplexityAnalysis(
        time_complexity=normalize_complexity(time_complexity) or "O(1)",
        space_complexity=normalize_complexity(space_complexity) or "O(1)",
        confidence=0.95,
        method="ast",
        status="ANALYZED"
    )
