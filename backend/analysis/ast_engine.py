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
    recognized_bounds = {p.lower() for p in loop.distinct_params} & {'m', 'n', 'v', 'e', 'w', 'k', 'rows', 'cols'}
    has_true_multi_bounds = len(recognized_bounds) >= 2 or ir.has_merged_both

    # === TIME & SPACE COMPLEXITY INFERENCE ===

    # 1. RECURSION PATTERNS
    if recursion.is_recursive:

        # 1a. Graph DFS / BFS (recursive traversal on graph)
        if graph.is_graph:
            time_complexity = "O(V+E)"
            space_complexity = "O(V)"

        # Phase-L: recursion can be distributed over multiple functions.  A
        # mutual cycle with one recursive call per level is linear; multiple
        # cycle calls represent branching recursion.  Keep this before the
        # single-function factorial heuristics so helper names do not get
        # mistaken for a recursive loop in one body.
        elif recursion.has_mutual_recursion:
            if recursion.pattern == "factorial":
                time_complexity = "O(n!)"
            elif recursion.branch_factor >= 2 or recursion.calls_inside_loop:
                time_complexity = "O(2^n)"
            else:
                time_complexity = "O(n)"
            space_complexity = "O(n)"

        # 1b. Combination Backtracking (k-choice recursion)
        elif recursion.is_recursive and ("combine" in ir.source.lower() or "int k" in ir.source.lower()) and loop.depth >= 1:
            time_complexity = "O(n^k)"
            space_complexity = "O(k)"

        # 1c. Factorial recursion (recursive call inside a loop)
        elif recursion.pattern == "factorial" or (
            recursion.calls_inside_loop and re.search(r"\b\w+\s*\(\s*n\s*-\s*1\s*\)", ir.source)
        ):
            source_lower = (ir.source or '').lower()
            permutation_like = bool(re.search(
                r'\bswap\s*\(|\bpermute\b|\bpermutation\b|\bi\s*=\s*l\b|\bl\s*\+\+|'
                r'\b(?:queen|queens|board|column|col)\b|\bb\s*\[.*\]\s*=',
                source_lower,
            ))
            explicit_factorial = bool(re.search(r'\b\w+\s*\(\s*n\s*-\s*1\s*\)', source_lower))
            time_complexity = "O(n!)" if (permutation_like or explicit_factorial) else "O(2^n)"
            space_complexity = "O(n)"

        # 1d. Single branch divide recursion T(n) = T(n/2) + O(1) (e.g. power(x, n/2))
        elif recursion.reduction_type == "divide" and recursion.branch_factor == 1:
            time_complexity = "O(log n)"
            space_complexity = "O(log n)"

        # 1e. Divide and Conquer patterns (MergeSort, QuickSort vs simple D&C O(n))
        elif recursion.is_divide_and_conquer or recursion.pattern == "divide_and_conquer":
            if recursion.branch_factor == 1:
                time_complexity = "O(log n)"
                space_complexity = "O(log n)"
            elif recursion.pattern == "simple_divide_and_conquer" or (loop.depth == 0 and not loop.has_sort and not recursion.has_linear_combine and not recursion.has_auxiliary_array and not ir.has_dynamic_allocation):
                time_complexity = "O(n)"
                space_complexity = "O(log n)"
            else:
                time_complexity = "O(n log n)"
                space_complexity = "O(n)" if (recursion.has_auxiliary_array or ir.has_dynamic_allocation) else "O(log n)"

        # 1d. Recursive function with loop inside (e.g. T(n) = T(n-1) + O(n))
        elif recursion.reduction_type == "linear" and loop.depth >= 1 and not recursion.has_memoization:
            time_complexity = "O(n^2)"
            space_complexity = "O(n)"

        # 1e. Path compression (Union Find / DSU)
        elif recursion.pattern == "path_compression":
            time_complexity = "O(E log V)"
            space_complexity = "O(V)"

        # 1d. Memoized recursion: O(n) time, O(n) space
        elif recursion.has_memoization:
            time_complexity = "O(n)"
            space_complexity = "O(n)"

        # 1e. Logarithmic single recursion T(n) = T(n/2) + O(1)
        elif recursion.reduction_type == "divide" and recursion.branch_factor == 1:
            time_complexity = "O(log n)"
            space_complexity = "O(log n)"

        # 1f. Divide and Conquer patterns (e.g. MergeSort, QuickSort vs simple D&C)
        elif recursion.is_divide_and_conquer:
            if recursion.pattern == "simple_divide_and_conquer" or (recursion.branch_factor == 2 and loop.depth == 0 and not recursion.has_linear_combine and not recursion.has_auxiliary_array and not ir.has_dynamic_allocation):
                time_complexity = "O(n)"
                space_complexity = "O(log n)"
            else:
                time_complexity = "O(n log n)"
                if recursion.has_auxiliary_array or ir.has_dynamic_allocation:
                    space_complexity = "O(n)"
                else:
                    space_complexity = "O(log n)"

        # 1g. Graph DFS (recursive)
        elif graph.is_graph:
            time_complexity = "O(V+E)"
            space_complexity = "O(V)"

        # 1h. Standard linear / exponential branching recursion
        else:
            branch_factor = recursion.branch_factor

            if recursion.calls_inside_loop and branch_factor == 1:
                time_complexity = "O(2^n)"
                space_complexity = "O(n)"
            elif recursion.pattern == "tail" or branch_factor == 1:
                time_complexity = "O(n)"
                space_complexity = "O(n)"
            elif branch_factor == 2:
                time_complexity = "O(2^n)"
                space_complexity = "O(n)"
            elif branch_factor == 3:
                time_complexity = "O(3^n)"
                space_complexity = "O(n)"
            elif branch_factor >= 4:
                # A loop-driven recursive search (combination/subset style)
                # is exponential. Factorial is reserved for permutations.
                source_lower = (ir.source or '').lower()
                permutation_like = bool(re.search(
                    r'\bswap\s*\(|\bpermute\b|\bpermutation\b|\bi\s*=\s*l\b|\bl\s*\+\+',
                    source_lower,
                ))
                time_complexity = "O(n!)" if permutation_like else "O(2^n)"
                space_complexity = "O(n)"
            else:
                time_complexity = "O(n)"
                space_complexity = "O(n)"

    # 2. GRAPH ALGORITHMS (non-recursive)
    elif graph.is_graph:
        if graph.traversal_inside_loop:
            time_complexity = "O(V*(V+E))"
            space_complexity = "O(V)"
        elif ir.has_heap_operations:
            time_complexity = "O((V+E)logV)"
            space_complexity = "O(V)"
        elif graph.structure == "adj_matrix":
            time_complexity = "O(V^2)"
            space_complexity = "O(V^2)"
        elif graph.structure == "adj_list":
            time_complexity = "O(V+E)"
            space_complexity = "O(V)"
        elif graph.structure == "edge_list":
            time_complexity = "O(E log V)"
            space_complexity = "O(V)"
        else:
            time_complexity = "O(V+E)"
            space_complexity = "O(V)"

    # 3. BINARY SEARCH INSIDE A LINEAR LOOP: multiplicative O(n log n).
    elif loop.has_binary_search and loop.binary_search_inside_loop:
        time_complexity = "O(n log n)"
        space_complexity = "O(1)"

    # 3b. BINARY SEARCH (STANDALONE)
    elif loop.has_binary_search and not loop.binary_search_inside_loop and loop.depth <= 1:
        time_complexity = "O(log n)"
        space_complexity = "O(1)"

    # 4. LOGARITHMIC STEP (e.g. x /= 10, x *= 2)
    elif loop.is_logarithmic_step and loop.depth <= 1:
        time_complexity = "O(log n)"
        space_complexity = "O(1)"

    # 5. Fenwick/BIT update or query. One logarithmic operation per input
    # element composes to O(n log n); a standalone operation is O(log n).
    elif loop.has_bit_operations:
        time_complexity = "O(n log n)" if loop.depth >= 1 else "O(log n)"
        space_complexity = "O(n)" if ir.has_dynamic_allocation else "O(1)"

    # 6. HEAP OPERATIONS
    elif ir.has_heap_operations and loop.depth <= 1:
        time_complexity = "O(n log n)"
        # Sorting an input in place does not allocate auxiliary storage under
        # the project convention.  Count space only when the source creates a
        # separate dynamic container in addition to the input.
        space_complexity = "O(1)"

    # 6. MULTI-INPUT BOUNDS.  Ignore container identifiers such as ``a``
    # from ``a.size()`` unless there are two genuine symbolic dimensions.
    elif has_true_multi_bounds and loop.depth <= 1:
        time_complexity = "O(m+n)"
        if ir.has_dynamic_allocation and ir.has_merged_both:
            space_complexity = "O(m+n)"
        elif ir.has_dynamic_allocation:
            space_complexity = "O(n)"
        else:
            space_complexity = "O(1)"

    # 7. AMORTIZED LINEAR PATTERNS
    elif loop.is_sliding_window:
        time_complexity = "O(n)"
        space_complexity = "O(n)" if ir.has_dynamic_allocation else "O(1)"

    elif loop.is_monotonic_stack:
        time_complexity = "O(n)"
        space_complexity = "O(n)"

    # A bounded inner alphabet/range adds only constant work per input item.
    elif loop.has_constant_inner_loop:
        time_complexity = "O(n log n)" if loop.has_sort else "O(n)"
        space_complexity = "O(n)" if ir.has_dynamic_allocation else "O(1)"

    elif loop.is_grouped_partition or loop.is_amortized_membership or loop.is_amortized_index_placement:
        time_complexity = "O(n)"
        space_complexity = "O(n)" if ir.has_dynamic_allocation else "O(1)"

    # 8. SORT OPERATIONS
    elif loop.has_sort:
        if loop.sort_inside_loop:
            time_complexity = "O(n^2 log n)" if loop.depth >= 1 else "O(n log n)"
        else:
            if loop.depth >= 3:
                time_complexity = "O(n^3)"
            elif loop.depth == 2:
                time_complexity = "O(n^2)"
            else:
                time_complexity = "O(n log n)"

        if ir.has_dynamic_allocation:
            space_complexity = "O(n)"
        else:
            space_complexity = "O(1)"

    # 9. LOOP-BASED ALGORITHMS
    elif loop.depth > 0:
        if loop.structure == "log_squared":
            time_complexity = "O(log^2 n)"
        elif loop.structure == "logarithmic_nested" or (loop.depth >= 2 and loop.is_logarithmic_step):
            time_complexity = "O(n log n)"
        elif loop.depth == 1:
            if loop.is_logarithmic_step or loop.has_binary_search:
                time_complexity = "O(log n)"
            elif has_true_multi_bounds:
                time_complexity = "O(m+n)"
            else:
                time_complexity = "O(n)"
        elif loop.depth == 2:
            params_lower = [p.lower() for p in loop.distinct_params]
            if 'w' in params_lower or 'W' in loop.distinct_params:
                time_complexity = "O(nW)"
            elif 'n' in params_lower and 'm' in params_lower:
                if params_lower.index('n') < params_lower.index('m'):
                    time_complexity = "O(n*m)"
                else:
                    time_complexity = "O(m*n)"
            elif loop.has_matrix_bounds or len(params_lower) >= 2:
                # Map first two distinct params to canonical n/m in their appearance order.
                # E.g. params=['a','b'] → outer='a'(→n), inner='b'(→m) → O(n*m)
                # E.g. params=['m','n'] → outer='m', inner='n' → O(m*n) (handled above)
                if len(params_lower) >= 2:
                    # First param corresponds to n (outer loop bound),
                    # second corresponds to m (inner loop bound)
                    first_is_row = params_lower[0] in ('m', 'row', 'rows', 'r')
                    if first_is_row:
                        time_complexity = "O(m*n)"
                    else:
                        time_complexity = "O(n*m)"
                else:
                    time_complexity = "O(m*n)"
            else:
                time_complexity = "O(n^2)"
        elif loop.depth == 3:
            time_complexity = "O(n^3)"
        elif loop.depth >= 4:
            time_complexity = "O(n^4+)"

        if loop.has_heap_operations and "log n" not in time_complexity:
            time_complexity = time_complexity.replace(")", " log n)")

        if loop.has_binary_search and loop.binary_search_inside_loop and "log n" not in time_complexity:
            time_complexity = time_complexity.replace(")", " log n)")

    # === SPACE COMPLEXITY DETERMINATION ===
    if not space_complexity or space_complexity == "O(1)":
        source_lower = ir.source.lower() if ir.source else ''
        fixed_size_patterns = [
            r'\b(?:int|float|double|char|bool|long)\s+\w+\s*\[\s*\d+\s*\]',
            r'\bcnt\[\d+\]',
            r'\bfreq\[\d+\]',
            r'\bcount\[\d+\]',
            r'\[[^\]]+\]\s*\*\s*\d+',
        ]
        is_fixed_size = any(re.search(pattern, source_lower) for pattern in fixed_size_patterns)

        if ir.has_2d_allocation:
            params_lower = [p.lower() for p in loop.distinct_params]
            if 'w' in params_lower or 'W' in loop.distinct_params:
                space_complexity = "O(W)"
            elif loop.multiple_input_bounds or len(params_lower) >= 2 or loop.has_matrix_bounds:
                space_complexity = "O(n*m)"
            else:
                space_complexity = "O(n^2)"

            if time_complexity == "O(1)":
                time_complexity = space_complexity
        elif ir.has_dynamic_allocation and not is_fixed_size:
            if 'w' in source_lower and ('dp(w' in source_lower or 'vector<int> dp(w' in source_lower or 'vector<int> dp(w+1)' in source_lower):
                space_complexity = "O(W)"
            elif loop.multiple_input_bounds and ir.has_merged_both:
                space_complexity = "O(m+n)"
            else:
                space_complexity = "O(n)"

    # Also handle pattern:constant-work that allocates
    if ir.algorithm_pattern == "constant-work" and ir.has_dynamic_allocation and not is_fixed_size:
        space_complexity = "O(n)"

    # Time complexity must be at least as large as space complexity if we're dynamically allocating
    if time_complexity == "O(1)" and space_complexity != "O(1)":
        time_complexity = space_complexity

    signals = []
    if loop.depth:
        signals.append(f"loop-depth:{loop.depth}")
    if loop.is_logarithmic_step:
        signals.append("logarithmic-step")
    if loop.has_sort:
        signals.append("library-sort")
    if loop.has_binary_search:
        signals.append("binary-search")
    if recursion.is_recursive:
        signals.append(f"recursion:{recursion.pattern}")
    if graph.is_graph:
        signals.append(f"graph:{graph.structure or 'traversal'}")
    if ir.has_dynamic_allocation:
        signals.append("dynamic-allocation")
    if ir.has_2d_allocation:
        signals.append("two-dimensional-allocation")
    if ir.has_heap_operations:
        signals.append("heap-operation")
    if ir.algorithm_pattern and ir.algorithm_pattern != "unknown":
        signals.append(f"pattern:{ir.algorithm_pattern}")
    # A syntactically valid AST with no loops, recursion, allocation, graph,
    # or heap evidence is still a deterministic constant-work program. Treat
    # it as analyzed instead of discarding simple O(1) solutions.
    if not signals:
        signals.append("constant-work")
    confidence = 0.95 if signals != ["constant-work"] else 0.85
    status = "ANALYZED"

    return ComplexityAnalysis(
        time_complexity=normalize_complexity(time_complexity) or "O(1)",
        space_complexity=normalize_complexity(space_complexity) or "O(1)",
        confidence=confidence,
        method="ast",
        status=status,
        signals=signals,
        explanation=(
            "Complexity inferred from structural AST evidence."
            if signals != ["constant-work"] else
            "No scalable structural evidence found; constant work inferred from the valid AST."
        ),
    )
