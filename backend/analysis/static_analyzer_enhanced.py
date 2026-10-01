"""
Enhanced C++ static complexity analyzer with fixes for 30 advanced pattern failures.
Addresses: recursion with memoization, multi-variable bounds, graph algorithms,
sequential vs nested loops, and algorithm composition.
"""
import re
from typing import Tuple, Optional, List, Set

from .complexity_normalizer import normalize_complexity
from .models import ComplexityAnalysis


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: RECURSION & MEMOIZATION DETECTION
# ═══════════════════════════════════════════════════════════════════════════

def _has_memoization(source: str) -> bool:
    """Detect if code uses memoization array (dp[], memo[], cache[], visited[])."""
    src = source.lower()

    # Pattern 1: Early return check for cached value
    # if (dp[i] != -1) return dp[i];
    # if (memo[key] != -1) return memo[key];
    memo_check = bool(re.search(r"if\s*\(\s*(?:dp|memo|cache)\[[^\]]+\]\s*!=\s*-1", src))

    # Pattern 2: Store and return pattern
    # return dp[i] = f(i-1) + f(i-2);
    memo_store = bool(re.search(r"return\s+(?:dp|memo|cache)\[[^\]]+\]\s*=", src))

    # Pattern 3: Explicit check before recursion
    # if (dp[n] != 0) return dp[n];
    memo_guard = bool(re.search(r"if\s*\(\s*(?:dp|memo|cache)\[[^\]]+\]\s*[!=]=", src))

    return memo_check or memo_store or memo_guard


def _count_recursive_branches(source: str, func_name: str) -> int:
    """
    Count the number of recursive call sites in a function.
    Returns 1 for tail/linear, 2+ for branching recursion.
    """
    # Find all calls to the function itself
    pattern = rf"\b{re.escape(func_name)}\s*\("
    calls = re.findall(pattern, source)

    # Subtract 1 for the function definition itself
    return max(0, len(calls) - 1)


def _detect_recursion_pattern(source: str) -> Tuple[bool, int, bool]:
    """
    Returns (is_recursive, branch_factor, has_memo).

    Branch factor:
    - 0: not recursive
    - 1: tail/linear recursion
    - 2: binary branching (fibonacci, binary tree)
    - 3+: n-ary branching
    """
    src = source.lower()

    # Find function definitions
    func_defs = re.finditer(
        r"\b(?:[\w:<>*&]+\s+)+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{",
        source
    )

    SKIP_NAMES = {"main", "if", "while", "for", "return", "size", "push_back"}

    max_branches = 0
    has_memo = _has_memoization(source)

    for match in func_defs:
        func_name = match.group(1)
        if func_name in SKIP_NAMES or len(func_name) < 2:
            continue

        branches = _count_recursive_branches(source, func_name)
        if branches > 0:
            max_branches = max(max_branches, branches)

    return max_branches > 0, max_branches, has_memo


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: MULTI-VARIABLE BOUND TRACKING
# ═══════════════════════════════════════════════════════════════════════════

def _extract_loop_variables(source: str) -> List[str]:
    """
    Extract loop bound variables from for/while conditions.
    Returns list like ['n', 'm'], ['v', 'e'], etc.
    """
    src = source.lower()
    bounds = []

    # Pattern 1: for (int i = 0; i < n; i++)
    for_patterns = re.findall(r"for\s*\([^;]*;\s*[a-z0-9_]+\s*[<>]=?\s*([a-z0-9_]+)", src)
    bounds.extend(for_patterns)

    # Pattern 2: while (i < n)
    while_patterns = re.findall(r"while\s*\([^)]*[<>]=?\s*([a-z0-9_]+)\)", src)
    bounds.extend(while_patterns)

    # Pattern 3: .size() calls
    if ".size()" in src:
        bounds.append("n")

    # Filter to known complexity variables
    known_vars = {"n", "m", "v", "e", "rows", "cols"}
    filtered = [b for b in bounds if b in known_vars]

    return filtered


def _detect_graph_structure(source: str) -> Optional[str]:
    """
    Detect graph data structure type.
    Returns: 'adj_list' (V+E), 'adj_matrix' (V²), 'edge_list' (E), or None.
    """
    src = source.lower()

    # Adjacency matrix: vector<vector<int>> matrix(V, vector<int>(V))
    # or int matrix[V][V]
    if re.search(r"vector\s*<\s*vector.*\(\s*v\s*,\s*vector.*\(\s*v", src):
        return "adj_matrix"
    if re.search(r"\[\s*v\s*\]\s*\[\s*v\s*\]", src):
        return "adj_matrix"

    # Adjacency list: vector<vector<int>> adj(V)
    # or vector<int> adj[V]
    if re.search(r"vector\s*<\s*vector.*adj", src) and "adj" in src:
        return "adj_list"

    # Edge list: vector<pair<int,int>> edges
    if re.search(r"vector\s*<\s*(?:pair|edge)", src) and "edge" in src:
        return "edge_list"

    return None


def _is_graph_traversal(source: str) -> bool:
    """Detect DFS/BFS graph traversal pattern."""
    src = source.lower()

    has_visited = "visited" in src or "vis[" in src
    has_queue = "queue<" in src or "queue " in src
    has_dfs_call = "dfs(" in src or "bfs(" in src
    has_adj_loop = bool(re.search(r"for\s*\([^)]*:\s*(?:adj|graph)\[", src))

    return (has_visited and (has_queue or has_dfs_call)) or has_adj_loop


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: LOOP STRUCTURE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def _analyze_loop_structure(source: str) -> Tuple[int, str, List[str]]:
    """
    Returns (depth, structure, bounds).

    structure:
    - 'sequential': multiple independent loops (O(n) + O(n) = O(n))
    - 'nested': loops inside loops (O(n) × O(m) = O(nm))
    - 'single': one loop
    """
    depth = 0
    current_depth = 0
    brace_depth = 0
    loop_depths = []
    max_concurrent = 0

    tokens = re.finditer(r"\b(for|while|do)\b|[{}]", source, re.IGNORECASE)

    for token in tokens:
        value = token.group()

        if value == "{":
            brace_depth += 1
        elif value == "}":
            brace_depth = max(0, brace_depth - 1)
            if loop_depths and loop_depths[-1] == brace_depth + 1:
                loop_depths.pop()
                current_depth = len(loop_depths)
        else:  # for/while/do
            loop_depths.append(brace_depth + 1)
            current_depth = len(loop_depths)
            depth = max(depth, current_depth)
            max_concurrent = max(max_concurrent, current_depth)

    # Extract bounds
    bounds = _extract_loop_variables(source)

    # Determine structure
    if depth == 0:
        structure = "none"
    elif max_concurrent >= 2:
        structure = "nested"
    elif depth == 1:
        # Check if multiple sequential loops
        loop_count = source.lower().count("for") + source.lower().count("while")
        structure = "sequential" if loop_count >= 2 else "single"
    else:
        structure = "nested"

    return depth, structure, bounds


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: SPECIAL PATTERN DETECTORS
# ═══════════════════════════════════════════════════════════════════════════

def _is_binary_search(source: str) -> bool:
    """Detect binary search pattern."""
    src = source.lower()

    has_low_high = ("low" in src or "left" in src) and ("high" in src or "right" in src)
    has_mid = "mid" in src
    has_mid_calc = bool(re.search(r"mid\s*=\s*\([^)]*\+[^)]*\)\s*/\s*2", src))
    has_pointer_update = bool(re.search(r"(?:low|left)\s*=\s*mid\s*[+\-]", src))

    return has_low_high and has_mid and (has_mid_calc or has_pointer_update)


def _is_two_pass_array(source: str) -> bool:
    """Detect independent two-pass array algorithm (O(n) + O(n) = O(n))."""
    src = source.lower()

    # Count distinct for/while loops
    for_loops = re.findall(r"for\s*\([^;]+;[^;]+;[^)]+\)", src)
    if len(for_loops) >= 2:
        # Ensure no nested loops with { ... for ... }
        nested = bool(re.search(r"for\s*\([^)]+\)\s*\{[^}]*for\s*\(", src))
        return not nested

    return False


def _has_sort_algorithm(source: str) -> bool:
    """Detect sort() or stable_sort() call."""
    return bool(re.search(r"\bsort\s*\(", source.lower()))


def _is_string_reversal(source: str) -> bool:
    """Detect string reversal via swap (still O(n), not O(1))."""
    src = source.lower()
    has_swap = "swap" in src
    has_string = "string" in src or "char" in src
    has_loop = "for" in src or "while" in src
    return has_swap and has_string and has_loop


def _is_bubble_sort(source: str) -> bool:
    """Detect bubble sort pattern (nested loop with swap)."""
    src = source.lower()
    has_nested = bool(re.search(r"for\s*\([^)]+\)\s*\{[^}]*for\s*\([^)]+\)", src))
    has_swap = "swap" in src
    has_comparison = bool(re.search(r"if\s*\([^)]*[<>][^)]*\)", src))
    return has_nested and has_swap and has_comparison


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def analyze_cpp_enhanced(source: str) -> ComplexityAnalysis:
    """
    Enhanced C++ complexity analyzer with fixes for 30 advanced patterns.
    """
    src = source.lower()

    # Phase 1: Recursion Analysis
    is_recursive, branch_factor, has_memo = _detect_recursion_pattern(source)

    # Phase 2: Graph Analysis
    graph_structure = _detect_graph_structure(source)
    is_graph_trav = _is_graph_traversal(source)

    # Phase 3: Loop Analysis
    loop_depth, loop_structure, loop_bounds = _analyze_loop_structure(source)

    # Phase 4: Special Patterns
    is_binsearch = _is_binary_search(source)
    is_two_pass = _is_two_pass_array(source)
    has_sort = _has_sort_algorithm(source)
    is_str_reverse = _is_string_reversal(source)
    is_bubble = _is_bubble_sort(source)

    # ═══════════════════════════════════════════════════════════════════════
    # TIME COMPLEXITY INFERENCE
    # ═══════════════════════════════════════════════════════════════════════

    time_complexity = "O(1)"
    space_complexity = "O(1)"

    # RECURSION PATTERNS
    if is_recursive:
        if has_memo:
            # Memoized recursion: O(n) time, O(n) space
            time_complexity = "O(n)"
            space_complexity = "O(n)"
        elif branch_factor == 1:
            # Tail/linear recursion: O(n)
            time_complexity = "O(n)"
            space_complexity = "O(n)"  # call stack
        elif branch_factor == 2:
            # Binary branching: O(2^n)
            time_complexity = "O(2^n)"
            space_complexity = "O(n)"
        elif branch_factor == 3:
            time_complexity = "O(3^n)"
            space_complexity = "O(n)"
        elif branch_factor == 4:
            time_complexity = "O(4^n)"
            space_complexity = "O(n)"
        elif branch_factor >= 5:
            # Permutations/backtracking: O(n!)
            time_complexity = "O(n!)"
            space_complexity = "O(n)"

    # GRAPH ALGORITHMS
    elif graph_structure or is_graph_trav:
        if graph_structure == "adj_matrix":
            time_complexity = "O(V^2)"
            space_complexity = "O(V^2)"
        elif graph_structure == "adj_list" or is_graph_trav:
            time_complexity = "O(V+E)"
            space_complexity = "O(V)"
        elif graph_structure == "edge_list":
            time_complexity = "O(E)"
            space_complexity = "O(E)"

    # BINARY SEARCH
    elif is_binsearch:
        time_complexity = "O(log n)"
        space_complexity = "O(1)"

    # STRING REVERSAL (two-pointer swap)
    elif is_str_reverse:
        time_complexity = "O(n)"
        space_complexity = "O(n)"  # assuming string allocation

    # BUBBLE SORT
    elif is_bubble:
        time_complexity = "O(n^2)"
        space_complexity = "O(1)"

    # TWO-PASS SEQUENTIAL LOOPS
    elif is_two_pass:
        if has_sort:
            time_complexity = "O(n log n)"
        else:
            time_complexity = "O(n)"
        space_complexity = "O(1)"

    # LOOP-BASED ALGORITHMS
    elif loop_depth > 0:
        if has_sort and loop_depth >= 1:
            if loop_structure == "nested" and loop_depth >= 2:
                time_complexity = "O(n^2 log n)"
            else:
                time_complexity = "O(n log n)"
        elif loop_structure == "sequential":
            time_complexity = "O(n log n)" if has_sort else "O(n)"
        elif loop_depth == 1:
            time_complexity = "O(n)"
        elif loop_depth == 2:
            # Check for multi-variable
            unique_bounds = set(loop_bounds)
            if len(unique_bounds) >= 2 and "v" in unique_bounds and "e" in unique_bounds:
                time_complexity = "O(V+E)"
            elif len(unique_bounds) >= 2:
                time_complexity = "O(mn)"
            else:
                time_complexity = "O(n^2)"
        elif loop_depth == 3:
            time_complexity = "O(n^3)"
        elif loop_depth >= 4:
            time_complexity = "O(n^4+)"

        # Space: check for dynamic data structure allocation (ignore fixed-size like vector(26))
        has_dynamic_alloc = "unordered_map" in src or "unordered_set" in src or "map<" in src or "set<" in src
        if not has_dynamic_alloc:
            vector_matches = re.finditer(r"vector\s*<[^>]+>\s+\w+\s*\(\s*([^,\)]+)", src)
            for m in vector_matches:
                size_arg = m.group(1).strip()
                if any(t in size_arg for t in ['int', 'string', 'char', 'auto', 'const', 'bool', 'float', 'double', '&', '*']):
                    continue
                if re.match(r"^\d+$", size_arg):
                    if int(size_arg) > 1000:
                        has_dynamic_alloc = True
                else:
                    has_dynamic_alloc = True
        if has_dynamic_alloc:
            space_complexity = "O(n)"

    # JUST SORT, NO LOOPS
    elif has_sort:
        time_complexity = "O(n log n)"
        space_complexity = "O(1)"

    return ComplexityAnalysis(
        time_complexity=normalize_complexity(time_complexity) or "O(1)",
        space_complexity=normalize_complexity(space_complexity) or "O(1)"
    )
