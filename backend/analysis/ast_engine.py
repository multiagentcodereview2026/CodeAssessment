import re
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

    # 1. RECURSION PATTERNS (check first to avoid confusion with loops)
    if recursion.is_recursive:

        # 1a. Path compression (Union Find) - nearly O(1) amortized
        if recursion.pattern == "path_compression":
            time_complexity = "O(alpha(n))"
            space_complexity = "O(n)"

        # 1b. Memoized recursion: O(n) time, O(n) space
        elif recursion.has_memoization:
            time_complexity = "O(n)"
            space_complexity = "O(n)"

        # 1c. Divide and Conquer patterns
        elif recursion.is_divide_and_conquer:
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

        # 1d. Graph DFS (recursive)
        elif graph.is_graph:
            time_complexity = "O(V+E)"
            space_complexity = "O(V)"

        # 1e. Standard recursion patterns
        else:
            branch_factor = recursion.branch_factor

            if recursion.pattern == "tail" or branch_factor == 1:
                time_complexity = "O(n)"
                space_complexity = "O(n)"
            elif branch_factor == 2:
                time_complexity = "O(2^n)"
                space_complexity = "O(n)"
            elif branch_factor == 3:
                time_complexity = "O(3^n)"
                space_complexity = "O(n)"
            elif branch_factor >= 4:
                time_complexity = "O(n!)"
                space_complexity = "O(n)"
            else:
                time_complexity = "O(n)"
                space_complexity = "O(n)"

    # 2. GRAPH ALGORITHMS (non-recursive, check after recursion)
    elif graph.is_graph:
        if graph.traversal_inside_loop:
            time_complexity = "O(V*(V+E))"
            space_complexity = "O(V)"
        elif ir.has_heap_operations:
            # Dijkstra: graph + heap = O((V+E) log V)
            time_complexity = "O((V+E)logV)"
            space_complexity = "O(V)"
        elif graph.structure == "adj_matrix":
            time_complexity = "O(V^2)"
            space_complexity = "O(V^2)"
        elif graph.structure == "adj_list":
            time_complexity = "O(V+E)"
            space_complexity = "O(V)"
        elif graph.structure == "edge_list":
            time_complexity = "O(E)"
            space_complexity = "O(E)"
        else:
            time_complexity = "O(V+E)"
            space_complexity = "O(V)"

    # 3. BINARY SEARCH (STANDALONE)
    elif loop.has_binary_search and not loop.binary_search_inside_loop and loop.depth <= 1:
        time_complexity = "O(log n)"
        space_complexity = "O(1)"

    # 4. LOGARITHMIC STEP (e.g. x /= 10)
    elif loop.is_logarithmic_step and loop.depth <= 1:
        time_complexity = "O(log n)"
        space_complexity = "O(1)"

    # 5. HEAP OPERATIONS (standalone or in single loop)
    elif ir.has_heap_operations and loop.depth <= 1:
        time_complexity = "O(n log n)"
        if ir.has_dynamic_allocation:
            space_complexity = "O(n)"
        else:
            space_complexity = "O(1)"

    # 6. MULTI-INPUT BOUNDS (e.g. Median of 2 sorted arrays)
    elif loop.multiple_input_bounds and loop.depth <= 1:
        time_complexity = "O(m+n)"
        if ir.has_dynamic_allocation and ir.has_merged_both:
            space_complexity = "O(m+n)"
        elif ir.has_dynamic_allocation:
            space_complexity = "O(n)"
        else:
            space_complexity = "O(1)"

    # 7. SORT OPERATIONS
    elif loop.has_sort:
        if loop.sort_inside_loop:
            if loop.depth >= 2:
                time_complexity = "O(n^2 log n)"
            else:
                time_complexity = "O(n log n)"
        else:
            # Sequential sort outside loop: max(O(n log n), loop_complexity)
            if loop.depth >= 3:
                time_complexity = "O(n^3)"
            elif loop.depth == 2:
                time_complexity = "O(n^2)"
            else:
                time_complexity = "O(n log n)"

        space_complexity = "O(n)" if ir.has_dynamic_allocation else "O(1)"

    # 8. LOOP-BASED ALGORITHMS
    elif loop.depth > 0:
        # Determine time complexity based on loop structure
        if loop.depth == 1:
            if loop.is_logarithmic_step:
                time_complexity = "O(log n)"
            elif loop.multiple_input_bounds:
                time_complexity = "O(m+n)"
            else:
                time_complexity = "O(n)"
        elif loop.depth == 2:
            if loop.has_matrix_bounds:
                time_complexity = "O(m*n)"
            else:
                time_complexity = "O(n^2)"
        elif loop.depth == 3:
            time_complexity = "O(n^3)"
        elif loop.depth >= 4:
            time_complexity = "O(n^4+)"

        # Handle special logarithmic nested case (for{while(x/=2)})
        if loop.structure == "logarithmic_nested":
            time_complexity = "O(n log n)"

        # Apply heap operations multiplier if present
        if loop.has_heap_operations:
            if "log n" not in time_complexity:
                time_complexity = time_complexity.replace(")", " log n)")

        # Apply binary search multiplier if inside loop
        if loop.has_binary_search and loop.binary_search_inside_loop:
            if "log n" not in time_complexity:
                time_complexity = time_complexity.replace(")", " log n)")

    # === SPACE COMPLEXITY DETERMINATION ===

    # Don't override space complexity if already set by recursion/graph analysis
    if space_complexity == "O(1)":
        # Check for specific space patterns
        source_lower = ir.source.lower() if ir.source else ''

        # Check for fixed-size allocations that should be O(1)
        fixed_size_patterns = [
            r'cnt\[\d+\]',      # Fixed count arrays like cnt[26]
            r'freq\[\d+\]',
            r'count\[\d+\]',
            r'\[\s*26\s*\]',    # Character count arrays
            r'\[\s*10\s*\]',    # Small fixed arrays
            r'\[\s*100\s*\]',
            r'\[\s*128\s*\]',
            r'\[\s*256\s*\]',
        ]
        is_fixed_size = any(re.search(pattern, source_lower) for pattern in fixed_size_patterns)

        if ir.has_2d_allocation:
            space_complexity = "O(n^2)"
        elif ir.has_dynamic_allocation and not is_fixed_size:
            if loop.multiple_input_bounds and ir.has_merged_both:
                space_complexity = "O(m+n)"
            else:
                space_complexity = "O(n)"

    return ComplexityAnalysis(
        time_complexity=normalize_complexity(time_complexity) or "O(1)",
        space_complexity=normalize_complexity(space_complexity) or "O(1)",
        confidence=0.95,
        method="ast",
        status="ANALYZED"
    )
