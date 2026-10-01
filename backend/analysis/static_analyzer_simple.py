"""
SIMPLIFIED enhanced analyzer focusing on the core 30 failure patterns.
Fixes: recursion+memo, sequential loops, graph patterns, backtracking.
"""
import re
from typing import Tuple
from .complexity_normalizer import normalize_complexity
from .models import ComplexityAnalysis


def analyze_cpp_enhanced(source: str) -> ComplexityAnalysis:
    """Enhanced C++ complexity analyzer."""
    src = source.lower()

    # ═══ RECURSION DETECTION ═══
    has_memo = bool(re.search(r"if\s*\(\s*dp\[[^\]]+\]\s*!=\s*-1", src))

    # Find function name and count self-calls
    func_match = re.search(r"\b(?:int|bool|void|vector)\s+(\w+)\s*\(", source)
    branch_factor = 0
    if func_match:
        func_name = func_match.group(1)
        # Count how many times function calls itself
        self_calls = len(re.findall(rf"\b{func_name}\s*\(", source)) - 1  # -1 for definition
        branch_factor = self_calls

    is_recursive = branch_factor > 0

    # ═══ GRAPH PATTERNS ═══
    has_graph_param = bool(re.search(r"vector\s*<\s*vector\s*<[^>]+>\s*>\s*&\s*g\b", src))
    has_visited = "visited" in src or ("vector<int>" in src and "v[" in src)
    has_dfs_bfs = "dfs(" in src or "bfs(" in src
    is_graph = has_graph_param or (has_visited and has_dfs_bfs)

    # ═══ LOOP ANALYSIS ═══
    # Count loop keywords
    for_count = src.count("for")
    while_count = src.count("while")
    total_loops = for_count + while_count

    # Check if loops are nested (simple heuristic: look for "for" after "for")
    is_nested = bool(re.search(r"for\s*\([^)]+\)\s*\{[^}]*for\s*\(", src, re.DOTALL))

    has_sort = "sort(" in src
    has_binary_search = "low" in src and "high" in src and "mid" in src
    has_swap = "swap(" in src

    # ═══ TIME COMPLEXITY ═══
    tc = "O(1)"
    sc = "O(1)"

    # RECURSION PATTERNS
    if is_recursive:
        if has_memo:
            tc, sc = "O(n)", "O(n)"
        elif branch_factor == 1:
            tc, sc = "O(n)", "O(n)"
        elif branch_factor == 2:
            tc, sc = "O(2^n)", "O(n)"
        elif branch_factor == 3:
            tc, sc = "O(3^n)", "O(n)"
        elif branch_factor == 4:
            tc, sc = "O(4^n)", "O(n)"
        elif branch_factor >= 5:
            tc, sc = "O(n!)", "O(n)"

    # GRAPH ALGORITHMS
    elif is_graph:
        tc, sc = "O(V+E)", "O(V)"

    # BINARY SEARCH
    elif has_binary_search and not is_nested:
        tc = "O(log n)"

    # BUBBLE SORT (nested + swap)
    elif is_nested and has_swap and total_loops >= 2:
        tc = "O(n^2)"

    # SORTING ALGORITHMS
    elif has_sort:
        if is_nested:
            tc = "O(n^2 log n)"
        else:
            tc = "O(n log n)"

    # SEQUENTIAL LOOPS (multiple loops but NOT nested)
    elif total_loops >= 2 and not is_nested:
        tc = "O(n)"
        if "vector<" in src and "(" in src:
            sc = "O(n)"

    # SINGLE LOOP
    elif total_loops == 1:
        tc = "O(n)"
        if "vector<" in src and "(" in src:
            sc = "O(n)"

    # NESTED LOOPS
    elif is_nested:
        tc = "O(n^2)"
        if "vector<" in src:
            sc = "O(n)"

    return ComplexityAnalysis(
        time_complexity=normalize_complexity(tc) or "O(1)",
        space_complexity=normalize_complexity(sc) or "O(1)"
    )
