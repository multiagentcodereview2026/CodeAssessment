import re

from .complexity_normalizer import normalize_complexity
from .models import ComplexityAnalysis


# ─── Loop Depth ────────────────────────────────────────────────────────────────

def _loop_depth(source: str) -> int:
    """
    Returns the maximum nesting depth of for/while/do loops.
    Returns exact depth (1 for single loop, 2 for nested 2, 3 for nested 3,
    4 for nested 4, 5 for nested 5, etc.)
    """
    max_depth = 0
    brace_depth = 0
    loop_at_brace: list[int] = []

    tokens = re.finditer(r"\b(for|while|do)\b|[{}]", source, re.IGNORECASE)

    for token in tokens:
        value = token.group()

        if value == "{":
            brace_depth += 1

        elif value == "}":
            if loop_at_brace and loop_at_brace[-1] == brace_depth:
                loop_at_brace.pop()
            brace_depth = max(0, brace_depth - 1)

        else:
            loop_at_brace.append(brace_depth + 1)
            max_depth = max(max_depth, len(loop_at_brace))

    return max_depth


# ─── Recursion Detection ────────────────────────────────────────────────────────

def _detect_recursion(source: str) -> tuple[bool, int]:
    """
    Returns (has_recursion, effective_branches).
    Finds user-defined function definitions and counts how many times
    each calls itself. Distinguishes exclusive branching (if/else return)
    from simultaneous multi-branching recursion (like fibonacci).
    """
    SKIP = {"main", "if", "while", "for", "switch", "return", "new", "delete",
            "cout", "cin", "printf", "scanf", "size", "push_back", "emplace"}

    func_defs = re.finditer(
        r"\b(?:[\w:<>*&]+\s+)+(\w+)\s*\([^)]*\)\s*(?:const\s*)?\{",
        source
    )

    max_self_calls = 0
    is_exclusive = False

    for fn_match in func_defs:
        name = fn_match.group(1)
        if name in SKIP or len(name) < 1:
            continue
        all_calls = re.findall(rf"\b{re.escape(name)}\s*\(", source)
        self_calls = max(0, len(all_calls) - 1)
        if self_calls > max_self_calls:
            max_self_calls = self_calls
            return_calls = re.findall(
                rf"return\s+{re.escape(name)}\s*\(", source
            )
            is_exclusive = (
                self_calls >= 2
                and len(return_calls) == self_calls
                and bool(re.search(r"\belse\b", source))
            )

    effective_branches = 1 if is_exclusive else max_self_calls
    return max_self_calls >= 1, effective_branches


# ─── Graph Context Detectors ───────────────────────────────────────────────────

def _is_graph_context(source: str) -> bool:
    """Returns True if code is operating on a graph / tree / network."""
    src = source.lower()
    keywords = [
        r"\badj\b", r"\bgraph\b", r"\bedges?\b", r"\bvertices\b", r"\bvertex\b",
        r"\bindegree\b", r"\bindeg\b", r"\bvisited\b", r"\bvis\b",
        r"\bdijkstra\b", r"\bbellman\b", r"\bfloyd\b", r"\bkruskal\b", r"\bprim\b",
        r"\btoposort\b", r"\btopological\b", r"\bnumcourses\b", r"\bdisjointset\b",
        r"\bparent\b", r"\bneighbors?\b", r"\bdist\b"
    ]
    has_vertex_param = bool(re.search(r"\bint\s+v\b|\b[ijk]\s*<\s*v\b|\bv\s*-\s*1\b|\bv\b", src)) and bool(re.search(r"\b(?:adj|graph|edges|vis|visited|dist|edge|matrix|mat)\b", src))
    has_v_loop = bool(re.search(r"\b[ijk]\s*<\s*v\b|\bint\s+v\b", src))
    return any(re.search(kw, src) for kw in keywords) or has_vertex_param or has_v_loop


def _has_adjacency_matrix(source: str) -> bool:
    """Detects 2D adjacency / distance matrix allocation (V x V)."""
    src = source.lower()
    # vector<vector<int>> matrix(V, vector<int>(V, ...))
    m = re.search(r"vector\s*<\s*vector\s*<[^>]+>\s*>\s*\w+\s*\(\s*(\w+)\s*,\s*vector\s*<[^>]+>\s*\(\s*(\w+)", src)
    if m:
        return True
    # matrix[V][V] where both dimensions are non-trivial (> 3) or equal
    m2 = re.search(r"\w+\s+(?:matrix|grid|dist|cost|graph|g|adj)\s*\[\s*([^\]]+)\s*\]\s*\[\s*([^\]]+)\s*\]", src)
    if m2:
        d1, d2 = m2.group(1).strip().lower(), m2.group(2).strip().lower()
        if d2 not in {"2", "3"}:
            return True
    return bool(
        re.search(r"\bvector\s*<\s*vector\s*<[^>]+>\s*>\s*(?:matrix|grid|dist|cost)\b", src)
    )


def _has_adjacency_list(source: str) -> bool:
    """Detects adjacency list declaration or dynamic edge pushing."""
    src = source.lower()
    if _has_adjacency_matrix(source):
        return False
    return bool(
        re.search(r"\bvector\s*<\s*vector\s*<[^>]+>\s*>\s*(?:adj|graph|g)\b", src)
        or re.search(r"\bvector\s*<[^>]+>\s+(?:adj|graph|g)\s*\[", src)
        or re.search(r"\bunordered_map\s*<[^>]+,\s*vector\s*<", src)
        or re.search(r"\b(?:adj|graph|g)\[[^\]]+\]\.push_back", src)
    )


def _has_edge_list(source: str) -> bool:
    """Detects edge list declaration (1D vector of pairs/edges or 2D array with small fixed 2nd dim like E x 2)."""
    src = source.lower()
    m2 = re.search(r"\w+\s+(?:edges|edge_list|e|edge)\s*\[\s*([^\]]+)\s*\]\s*\[\s*([23])\s*\]", src)
    if m2:
        return True
    return bool(
        re.search(r"\bvector\s*<\s*(?:pair\s*<[^>]+>|edge|vector\s*<int>\s*>)\s*>\s*(?:edges|edge_list|e)\b", src)
        or re.search(r"\bvector\s*<\s*vector\s*<int>\s*>\s*(?:edges|edge_list)\s*\([^,]+,\s*vector\s*<int>\s*\([23]\)", src)
    )


def _has_graph_traversal(source: str) -> bool:
    """Detects BFS / DFS / Toposort on an adjacency list or graph edges."""
    src = source.lower()
    has_queue_or_stack = bool(re.search(r"\b(?:queue|stack)\s*<", src))
    has_while_q = bool(re.search(r"while\s*\(\s*!\s*(?:q|queue|st|s)\.empty\(\)\s*\)", src))
    has_edge_iter = bool(re.search(r"for\s*\([^)]*:\s*(?:adj\[|graph\[|edges|e\b)", src))
    has_dfs_func = bool(re.search(r"\b(?:dfs|bfs)\s*\(", src))
    has_nested_adj = bool(re.search(r"for\s*\([^)]*;\s*[a-zA-Z0-9_]+\s*<\s*v[^)]*\)\s*\{?\s*for\s*\([^)]*:\s*adj", src))
    return (has_queue_or_stack and (has_while_q or has_edge_iter)) or (has_dfs_func and has_edge_iter) or (has_edge_iter and "adj" in src) or has_nested_adj


def _has_bellman_ford(source: str) -> bool:
    """Detects Bellman-Ford style relaxation: outer loop on V, inner loop on edges."""
    src = source.lower()
    if _has_priority_queue(source) or _loop_depth(source) < 2:
        return False
    has_v_loop = bool(re.search(r"for\s*\([^;]*;\s*[a-zA-Z0-9_]+\s*<\s*(?:v|n)\s*(?:-\s*1)?\s*;", src))
    has_edge_loop = bool(re.search(r"for\s*\([^)]*:\s*edges\)", src) or re.search(r"for\s*\([^;]*;\s*[a-zA-Z0-9_]+\s*<\s*e\s*;", src) or ("edges" in src and "dist" in src))
    return has_v_loop and has_edge_loop


# ─── Tree & Heap Pattern Detectors ──────────────────────────────────────────────

def _is_tree_context(source: str) -> bool:
    """Returns True if code operates on a tree / BST / heap data structure."""
    src = source.lower()
    # Exclude binary search patterns: "low", "right", "mid" together indicate array binary search, not trees
    if bool(re.search(r"\blow\b", src)) and bool(re.search(r"\bright\b", src)) and bool(re.search(r"\bmid\b", src)):
        return False
    tree_keywords = [
        r"\btreenode\b", r"\bnode\s*\*", r"\broot\b", r"\bleft\b", r"\bright\b",
        r"\bbst\b", r"\bbinarytree\b", r"\bheapify\b", r"\bbuildheap\b", r"\bheapsort\b",
        r"\bmorris\b", r"\blca\b", r"\blowestcommonancestor\b", r"\binorder\b",
        r"\bpreorder\b", r"\bpostorder\b", r"\blevelorder\b", r"\bmaxdepth\b", r"\bmindepth\b"
    ]
    return any(re.search(kw, src) for kw in tree_keywords)


def _is_morris_traversal(source: str) -> bool:
    """Detects Morris Inorder / Preorder Traversal (O(N) TC, O(1) SC)."""
    src = source.lower()
    has_pre_thread = "pre->right" in src or "pre.right" in src or "predecessor->right" in src or "predecessor.right" in src
    has_while_thread = bool(
        re.search(r"while\s*\(\s*(?:cur|curr|current)\b", src)
        and re.search(r"(?:cur|curr|current)\s*->\s*left", src)
        and re.search(r"->\s*right\s*=\s*(?:cur|curr|current)\b", src)
    )
    return has_pre_thread or has_while_thread


def _has_tree_bfs(source: str) -> bool:
    """Detects Level-order / BFS Traversal on Tree (O(N) TC, O(N) SC)."""
    src = source.lower()
    has_queue = bool(re.search(r"\bqueue\s*<", src) or "queue" in src or "deque" in src)
    has_node = bool("treenode" in src or "node" in src or "root" in src)
    has_pop = bool("pop" in src or "poll" in src or "popleft" in src)
    return has_queue and has_node and has_pop


def _has_bst_single_path(source: str) -> bool:
    """Detects BST search / min / max / succ / single branch traversal (O(log N) / O(H) TC, O(H) SC)."""
    src = source.lower()
    if not _is_tree_context(source) or _has_tree_all_nodes_dfs(source) or "maxdepth" in src or "mindepth" in src or "height" in src:
        return False
    is_search = bool(
        "search" in src or "find" in src or "insert" in src or "delete" in src
        or "succ" in src or "pred" in src or "findmin" in src or "findmax" in src
        or ("min" in src and "max" in src and "val" not in src)
    )
    has_conditional_child = bool(
        re.search(r"root\s*->\s*left|root\s*->\s*right|node\s*->\s*left|node\s*->\s*right|root\.left|root\.right", src)
    )
    return is_search and has_conditional_child


def _has_tree_all_nodes_dfs(source: str) -> bool:
    """Detects recursive tree traversal visiting all nodes (O(N) TC, O(H) SC)."""
    src = source.lower()
    if not _is_tree_context(source):
        return False
    
    full_traversal_keywords = [
        "maxdepth", "mindepth", "height", "inorder", "preorder", "postorder",
        "invert", "mirror", "identical", "same", "lca", "diameter", "pathsum",
        "valid", "validate", "isvalid"
    ]
    if any(kw in src for kw in full_traversal_keywords):
        return True

    # Combined expressions like max(dfs(left), dfs(right)) or dfs(left) + dfs(right)
    has_combined_call = bool(
        re.search(r"\bmax\b\s*\([^)]*left[^)]*,\s*[^)]*right[^)]*\)", src)
        or re.search(r"\bmin\b\s*\([^)]*left[^)]*,\s*[^)]*right[^)]*\)", src)
        or (re.search(r"left", src) and re.search(r"right", src) and "+" in src)
    )
    if has_combined_call:
        return True

    # Sequential calls without return/else in between e.g. dfs(left); dfs(right);
    has_unconditional_both = bool(
        re.search(r"\b\w+\s*\([^)]*left[^)]*\)\s*;\s*(?:(?!return|else).)*\b\w+\s*\([^)]*right[^)]*\)\s*;", src, flags=re.DOTALL)
    )
    return has_unconditional_both


def _has_kth_bst(source: str) -> bool:
    """Detects Kth smallest / Kth largest element in BST (O(H + K) TC, O(H) SC)."""
    src = source.lower()
    return _is_tree_context(source) and ("kth" in src or ("k" in src and "bst" in src))


def _has_heap_sort(source: str) -> bool:
    """Detects Heap Sort (O(N log N) TC, O(1) SC)."""
    src = source.lower()
    return "heapsort" in src or ("buildheap" in src and "heapify" in src and "swap" in src)


def _has_build_heap(source: str) -> bool:
    """Detects Build Heap / Heapify array (O(N) TC, O(1) SC)."""
    src = source.lower()
    return ("buildheap" in src or "make_heap" in src) and not "heapsort" in src


# ─── Variable Scope Helpers ─────────────────────────────────────────────────────

def _uses_two_loop_variables(source: str) -> tuple[bool, bool]:
    """
    Returns (has_two_vars, are_nested).
    Checks if loops iterate over two distinct size variables (e.g. m and n, or V and E).
    """
    loop_conditions = re.findall(r"\b(?:for|while)\s*\([^)]+\)", source)
    mn_vars = {"m", "n", "v", "e"}
    vars_seen: set[str] = set()

    for cond in loop_conditions:
        bounds = re.findall(
            r"\b[ijk]\s*[<>]=?\s*(\w+)"
            r"|\bsize\(\)\s*-?\s*(\w+)"
            r"|\b(\w+)\.size\(\)",
            cond
        )
        for group in bounds:
            for v in group:
                if v.lower() in mn_vars:
                    vars_seen.add(v.lower())

    has_rows_cols = (
        bool(re.search(r"\brows\b", source.lower()))
        and bool(re.search(r"\bcols\b", source.lower()))
    )

    has_two_vars = len(vars_seen) >= 2 or has_rows_cols
    are_nested = has_two_vars and _loop_depth(source) >= 2

    return has_two_vars, are_nested


def _is_pure_graph_setup(source: str) -> bool:
    """Detects if code is purely building/populating graph structures without algorithmic processing."""
    src = source.lower()
    if _has_graph_traversal(source) or _has_bellman_ford(source) or _has_priority_queue(source):
        return False
    has_push_back = "push_back" in src or "emplace_back" in src or "insert" in src
    has_matrix_fill = bool(re.search(r"\bgraph\s*\[[^\]]+\]\s*\[[^\]]+\]\s*=", src)) or bool(re.search(r"\badj\s*\[[^\]]+\]\s*\[[^\]]+\]\s*=", src))
    return has_push_back or has_matrix_fill


def _get_loop_bounds_sequence(source: str) -> list[str]:
    """Returns the list of loop bound variables (e.g. ['n', 'm'] or ['v', 'e']) in order of appearance."""
    src = source.lower()
    conditions = re.findall(r"\b(?:for|while)\s*\(([^)]+)\)", src)
    bounds = []
    
    # Check variable assignments before while loops e.g. int x = m; while(x > 1) { x /= 2; }
    assigned_var_map = {}
    for var, src_val in re.findall(r"\b(?:int|long|auto)?\s*([a-zA-Z0-9_]+)\s*=\s*([a-zA-Z0-9_]+)\s*;", src):
        if src_val.lower() in {"n", "m", "v", "e"}:
            assigned_var_map[var.lower()] = src_val.lower()

    for cond in conditions:
        m_ve = re.search(r"(?:<|<=|>|>=|!=)\s*(?:\(?\s*v\s*\+\s*e\s*\)?|v_plus_e)", cond)
        if m_ve:
            bounds.append("v+e")
            continue

        m = re.search(r"(?:<|<=|>|>=|!=)\s*([a-zA-Z0-9_]+)", cond)
        m_left = re.search(r"([a-zA-Z0-9_]+)\s*(?:<|<=|>|>=|!=)", cond)
        left_v = m_left.group(1).lower() if m_left else ""
        if m:
            v = m.group(1).lower()
            if v in {"n", "m", "v", "e", "rows", "cols"}:
                bounds.append(v)
            elif left_v in assigned_var_map:
                bounds.append(assigned_var_map[left_v])
            elif "m" in v:
                bounds.append("m")
            elif "n" in v:
                bounds.append("n")
            elif "v" in v:
                bounds.append("v")
            elif "e" in v:
                bounds.append("e")
            elif left_v in {"n", "m", "v", "e"}:
                bounds.append(left_v)
        elif left_v in assigned_var_map:
            bounds.append(assigned_var_map[left_v])
        elif "m" in cond and "n" not in cond:
            bounds.append("m")
        elif "n" in cond and "m" not in cond:
            bounds.append("n")
        elif "v" in cond and "e" not in cond:
            bounds.append("v")
        elif "e" in cond and "v" not in cond:
            bounds.append("e")
    return bounds


def _get_log_target_var(source: str, default_var: str = "n") -> str:
    """Finds which variable is being logarithmically searched / halved / sorted."""
    src = source.lower()
    m = re.search(r"while\s*\([^)<>=!]*[<>=!]+\s*([a-zA-Z0-9_]+)\)", src)
    if m:
        v = m.group(1).lower()
        if v in {"m", "n", "v", "e"}:
            return "V" if v == "v" else ("E" if v == "e" else v)
        if "v" in v:
            return "V"
        if "m" in v:
            return "m"
        if "n" in v:
            return "n"

    fn_calls = re.findall(r"(?:sort|lower_bound|upper_bound|binary_search)\s*\(\s*([^,)]+)", src)
    for target in fn_calls:
        base_var = re.split(r"[\.\[\->\(]", target.strip())[0].strip()
        if re.search(r"\b(?:v|vertices)\b", base_var) or "_v" in base_var:
            return "V"
        if re.search(r"\b(?:e|edges)\b", base_var) or "_e" in base_var:
            return "E"
        if re.search(r"\b(?:m|arr_m|arr2|nums2|v2|b|cols)\b", base_var) or "_m" in base_var:
            return "m"
        if re.search(r"\b(?:n|arr_n|arr1|nums1|v1|a|rows)\b", base_var) or "_n" in base_var:
            return "n"

    if bool(re.search(r"\bv\b|\bvertices\b", src)) and not bool(re.search(r"\bn\b", src)):
        return "V"
    if bool(re.search(r"\bm\b", src)) and not bool(re.search(r"\bn\b", src)):
        return "m"
    return default_var


# ─── Pattern Detectors ──────────────────────────────────────────────────────────

def _has_sort(source: str) -> bool:
    return bool(re.search(r"\b(?:sort|stable_sort)\s*\(", source.lower()))


def _has_priority_queue(source: str) -> bool:
    return bool(re.search(r"\bpriority_queue\s*<", source.lower()))


def _has_binary_search_call(source: str) -> bool:
    return bool(re.search(
        r"\b(?:binary_search|lower_bound|upper_bound)\b",
        source.lower()
    ))


def _has_recursive_binary_search(source: str) -> bool:
    """Detects divide-and-conquer / binary halving in recursive functions."""
    src = source.lower()
    has_mid_calculation = bool(
        re.search(r"/\s*2|>>\s*1|\bmid\b|\bm\s*=\s*l\s*\+|\bm\s*=\s*\(|\bv\s*/\s*2", src)
    )
    has_subrange_calls = bool(
        re.search(r"\b\w+\s*\([^)]*[+-]\s*1[^)]*\)", src)
        or re.search(r"[+-]\s*1", src)
        or re.search(r"\b\w+\s*\([^)]*/\s*2[^)]*\)", src)
    )
    return has_mid_calculation and has_subrange_calls


def _has_log_loop(source: str) -> bool:
    """Detects a logarithmically-bounded loop: variable doubled/halved each step, or binary search pointer updates."""
    # Classic log patterns: x *= 2, x /= 2, x >>= 1, x <<= 1, x = x * 2, x = x / 2
    if bool(re.search(r"\b\w+\s*(?:\*=\s*2|/=\s*2|>>=\s*1|<<=\s*1)", source)) or \
       bool(re.search(r"\b\w+\s*=\s*\w+\s*(?:\*\s*2|/\s*2)\b", source)):
        return True

    # Binary search pattern: while(low <= right) with mid = (low+right)/2 and low = mid+1 / right = mid-1
    src_lower = source.lower()
    has_mid_calc = bool(re.search(r"\bmid\s*=\s*\(?\s*(?:low|left|l)\s*\+\s*(?:right|high|r|right)\s*\)?\s*/\s*2", src_lower))
    has_pointer_update = bool(re.search(r"\b(?:low|left|l)\s*=\s*mid\s*[+\-]\s*1", src_lower)) or \
                         bool(re.search(r"\b(?:right|high|r)\s*=\s*mid\s*[+\-]\s*1", src_lower))
    has_log_condition = bool(re.search(r"while\s*\(\s*(?:low|left|l)\s*<=?\s*(?:right|high|r)", src_lower))

    return has_mid_calc and has_pointer_update and has_log_condition


def _has_factorial_pattern(source: str) -> bool:
    """Detects factorial/permutation patterns."""
    src = source.lower()
    return bool(re.search(
        r"\b(?:next_permutation|prev_permutation|is_permutation|permute)\b",
        src
    )) or (
        "swap" in src
        and bool(re.search(r"\bfor\s*\(", src))
        and bool(re.search(r"\b(\w+)\s*\(", src))
    )


def _has_subset_pattern(source: str) -> bool:
    src = source.lower()
    return "subset" in src or "power_set" in src or "powerset" in src


# ─── Space Complexity ───────────────────────────────────────────────────────────

def _analyze_space(
    source: str,
    has_recursion: bool,
    branch_count: int,
) -> tuple[str, float, str]:
    """Returns (space_complexity, confidence, signal)."""
    src = source.lower()
    is_graph = _is_graph_context(source)

    has_m = bool(re.search(r"\bm\b", src))
    has_n = bool(re.search(r"\bn\b", src))
    has_v = bool(re.search(r"\bint\s+v\b|\bvertices\b|\b[ijk]\s*<\s*v\b|\bv\s*<|\bv\s*<=|\bnumcourses\b|\bvisited\s*\(\s*v", src))
    has_e = bool(re.search(r"\bint\s+e\b|\bedges\b|\b[ijk]\s*<\s*e\b|\be\s*<|\be\s*<=", src))
    has_two_vars = (has_m and has_n) or (
        bool(re.search(r"\brows\b", src))
        and bool(re.search(r"\bcols\b", src))
    )

    # Exclude pass-by-reference parameters (e.g. vector<...>& adj, vector<...>& matrix)
    src_no_refs = re.sub(r"\([^)]*&[^)]*\)", "()", src)

    # ── Tree Space Complexity ────────────────────────────────────────────────
    if _is_tree_context(source):
        if _is_morris_traversal(source):
            return "O(1)", 0.92, "Morris tree traversal (O(1) auxiliary space) detected"
        if _has_tree_bfs(source) or "serialize" in src or "buildtree" in src or "verticalorder" in src or "zigzag" in src or "topview" in src or "bottomview" in src or "leftview" in src or "rightview" in src:
            return "O(N)", 0.88, "Tree queue / auxiliary structure space (N) detected"
        if has_recursion or _has_tree_all_nodes_dfs(source) or _has_bst_single_path(source) or _has_kth_bst(source) or "stack" in src or "maxdepth" in src or "inorder" in src or "preorder" in src or "postorder" in src:
            return "O(H)", 0.88, "Tree call stack / height space (H) detected"

    # ── Graph Edge List Only Space: O(E) (Checked before general 2D) ─────────
    if (is_graph or has_e) and _has_edge_list(src_no_refs):
        return "O(E)", 0.86, "graph edge list storage (E) detected"

    # ── Graph Adjacency Matrix Space: O(V^2) ─────────────────────────────────
    if (is_graph or has_v) and _has_adjacency_matrix(src_no_refs):
        return "O(V^2)", 0.86, "graph adjacency / distance matrix (V^2) detected"

    # ── Graph Adjacency List Space: O(V+E) ───────────────────────────────────
    if is_graph and _has_adjacency_list(src_no_refs):
        return "O(V+E)", 0.88, "graph adjacency list storage (V+E) detected"

    # ── 4D+ tensor / vector<vector<vector<vector<...>>>> ─────────────────────
    type_decl = re.search(r"((?:vector\s*<\s*)+[a-zA-Z0-9_]+(?:\s*>)+)", src_no_refs)
    vector_nest_count = len(re.findall(r"vector\s*<", type_decl.group(0))) if type_decl else 0

    multi_dim_decl = re.search(r"\w+\s+([a-zA-Z0-9_]+)((?:\s*\[\s*[^\]]+\s*\]){2,})", src_no_refs)
    bracket_dims = 0
    if multi_dim_decl:
        bracket_dims = len(re.findall(r"\[\s*[^\]]+\s*\]", multi_dim_decl.group(2)))

    if vector_nest_count >= 4 or bracket_dims >= 4:
        dim = max(vector_nest_count, bracket_dims)
        return f"O(n^{dim})", 0.80, f"{dim}D array/vector detected"

    # ── 3D array / vector<vector<vector<...>>> ────────────────────────────────
    if re.search(r"\bvector\s*<\s*vector\s*<\s*vector\s*<", src_no_refs) or bracket_dims == 3:
        if has_v:
            return "O(V^3)", 0.82, "3D graph/vertex tensor detected"
        return "O(n^3)", 0.80, "3D array/vector detected"

    # ── 2D matrix (non-adjacency list) ───────────────────────────────────────
    if re.search(r"\bvector\s*<\s*vector\s*<", src_no_refs) or \
       re.search(r"\barray\s*<[^>]+>\s+\w+\s*\[", src_no_refs) or bracket_dims == 2:
        if has_v:
            return "O(V^2)", 0.84, "graph 2D matrix storage detected"
        if has_two_vars:
            return "O(mn)", 0.78, "2D matrix with two distinct dimensions detected"
        return "O(n^2)", 0.78, "2D matrix-like storage detected"

    # ── Two separately declared arrays ───────────────────────────────────────
    named_arrays = re.findall(
        r"\b(?:vector|array)\s*<[^>]+>\s+(\w+)",
        src_no_refs
    )
    unique_arrays = set(named_arrays)
    if len(unique_arrays) >= 2:
        if has_v:
            return "O(V)", 0.78, "vertex auxiliary structures (V) detected"
        if has_e:
            return "O(E)", 0.78, "edge auxiliary structures (E) detected"
        if has_two_vars:
            return "O(m+n)", 0.76, "two independent arrays of different sizes detected"
        return "O(n)", 0.76, "multiple input-sized arrays detected"

    # ── Recursion logarithmic stack ──────────────────────────────────────────
    if has_recursion and (_has_binary_search_call(source) or _has_recursive_binary_search(source)):
        if has_v:
            return "O(log V)", 0.82, "recursive tree/graph divide-and-conquer — O(log V) call stack"
        return "O(log n)", 0.78, "recursive binary search — O(log n) call stack"

    # ── Input-sized auxiliary structures ─────────────────────────────────────
    if re.search(
        r"\b(?:vector|unordered_map|unordered_set|map|set|string|deque|queue|stack|priority_queue)\b",
        src_no_refs
    ):
        if has_v:
            return "O(V)", 0.80, "vertex-sized auxiliary storage detected"
        if has_e:
            return "O(E)", 0.80, "edge-sized auxiliary storage detected"
        if has_m and not has_n:
            return "O(m)", 0.76, "input-sized storage (m) detected"
        return "O(n)", 0.76, "input-sized storage detected"

    # ── Plain recursion stack ────────────────────────────────────────────────
    if has_recursion:
        if has_v:
            return "O(V)", 0.78, "graph recursive DFS stack (V) detected"
        return "O(n)", 0.74, "recursion call stack detected"

    return "O(1)", 0.70, "no input-sized auxiliary storage detected"


# ─── Main Analyzer ──────────────────────────────────────────────────────────────

def analyze_cpp(source: str) -> ComplexityAnalysis:
    if not source.strip():
        return ComplexityAnalysis(
            status="REVIEW_REQUIRED",
            method="static",
            explanation="Source code is empty.",
        )

    signals: list[str] = []
    src = source.lower()

    depth = _loop_depth(source)
    has_recursion, branch_count = _detect_recursion(source)
    has_two_vars, loops_nested = _uses_two_loop_variables(source)
    loop_bounds = _get_loop_bounds_sequence(source)
    is_graph = _is_graph_context(source)

    has_v = bool(re.search(r"\bint\s+v\b|\bvertices\b|\b[ijk]\s*<\s*v\b|\bv\s*<|\bv\s*<=|\bnumcourses\b|\bvisited\s*\(\s*v", src))
    has_e = bool(re.search(r"\bint\s+e\b|\bedges\b|\b[ijk]\s*<\s*e\b|\be\s*<|\be\s*<=", src))

    # Safe defaults
    time_complexity = "O(1)"
    confidence = 0.55

    # ── Tree & Heap Complexities ─────────────────────────────────────────────
    if _is_tree_context(source):
        if _has_heap_sort(source):
            signals.append("Heap sort (N log N) detected")
            time_complexity = "O(N log N)"
            confidence = 0.90
        elif _has_build_heap(source):
            signals.append("Build heap linear time (N) detected")
            time_complexity = "O(N)"
            confidence = 0.90
        elif _is_morris_traversal(source):
            signals.append("Morris tree traversal linear time (N) detected")
            time_complexity = "O(N)"
            confidence = 0.90
        elif _has_kth_bst(source):
            signals.append("Kth element search in BST (H + K) detected")
            time_complexity = "O(H + K)"
            confidence = 0.88
        elif _has_bst_single_path(source):
            signals.append("BST single path search / insert / delete (log N / H) detected")
            time_complexity = "O(log N)"
            confidence = 0.88
        elif _has_tree_all_nodes_dfs(source) or _has_tree_bfs(source) or "maxdepth" in src or "inorder" in src or "preorder" in src or "postorder" in src or "height" in src:
            signals.append("Tree traversal visiting N nodes detected")
            time_complexity = "O(N)"
            confidence = 0.88

    # ── Recursive Binary Search / Tree Divide & Conquer O(log V) / O(log n) ──
    elif has_recursion and (_has_binary_search_call(source) or _has_recursive_binary_search(source)):
        if has_v:
            signals.append("tree / graph divide-and-conquer (log V) detected")
            time_complexity = "O(log V)"
        else:
            signals.append("recursive binary search divide-and-conquer detected")
            time_complexity = "O(log n)"
        confidence = 0.88

    # ── Factorial O(n!) / O(V!) ───────────────────────────────────────────────
    elif _has_factorial_pattern(source) or branch_count >= 4:
        if is_graph and has_v:
            signals.append("graph permutation / TSP search (V!) detected")
            time_complexity = "O(V!)"
        else:
            signals.append("factorial / permutation pattern detected")
            time_complexity = "O(n!)"
        confidence = 0.80

    # ── Ternary branching O(3^n) ──────────────────────────────────────────────
    elif branch_count == 3:
        signals.append("ternary recursive branching detected")
        time_complexity = "O(3^n)"
        confidence = 0.78

    # ── Binary branching O(2^n) / O(2^V) ──────────────────────────────────────
    elif branch_count == 2 or (
        has_recursion
        and (
            "fib" in src
            or "backtrack" in src
            or _has_subset_pattern(source)
        )
    ):
        if is_graph and has_v:
            signals.append("graph subset / vertex cover branching (2^V) detected")
            time_complexity = "O(2^V)"
        else:
            signals.append("binary recursive branching detected")
            time_complexity = "O(2^n)"
        confidence = 0.78

    # ── Bellman-Ford O(VE) ────────────────────────────────────────────────────
    elif is_graph and _has_bellman_ford(source):
        signals.append("Bellman-Ford vertex-edge relaxation (VE) detected")
        time_complexity = "O(VE)"
        confidence = 0.90

    # ── Dijkstra / Prim / Kruskal with Priority Queue or Sort ────────────────
    elif is_graph and (_has_priority_queue(source) or (_has_sort(source) and (has_e or has_v))):
        if bool(re.search(r"\b\(?\s*v\s*\+\s*e\s*\)?\s*log|\bfor\s*\([^;]*;\s*[a-zA-Z0-9_]+\s*<\s*v\s*;", src)):
            signals.append("Dijkstra with all vertices/edges in heap ((V+E) log V) detected")
            time_complexity = "O((V+E) log V)"
        else:
            signals.append("Dijkstra / Kruskal shortest-path with min-heap (E log V) detected")
            time_complexity = "O(E log V)"
        confidence = 0.88

    # ── Graph BFS / DFS / Kahn's Topological Sort (Adjacency List): O(V+E) ─────
    elif is_graph and _has_graph_traversal(source):
        signals.append("Graph traversal (BFS/DFS/Toposort) on adjacency list (V+E) detected")
        time_complexity = "O(V+E)"
        confidence = 0.88

    # ── Linear recursion O(V) / O(n) ──────────────────────────────────────────
    elif has_recursion:
        if has_v:
            signals.append("graph recursive DFS (V) detected")
            time_complexity = "O(V)"
        else:
            signals.append("linear recursion detected")
            time_complexity = "O(n)"
        confidence = 0.82

    # ── Three+ nested loops (Floyd-Warshall O(V^3), O(n^3), O(n^4)...) ─────────
    elif depth >= 3:
        if has_v or (is_graph and ("dist" in src or "matrix" in src)):
            signals.append("Floyd-Warshall all-pairs shortest path (V^3) detected")
            time_complexity = "O(V^3)"
            confidence = 0.88
        elif has_two_vars and depth == 3:
            signals.append("three nested loops across two variables detected")
            time_complexity = "O(n^2m)"
            confidence = 0.78
        else:
            signals.append(f"{depth} nested loops detected")
            time_complexity = f"O(n^{depth})"
            confidence = 0.82

    # ── Two nested loops (Adjacency Matrix O(V^2), O(VE), O(mn), O(n log n), O(n^2)) ──
    elif depth == 2:
        if has_v and has_e:
            signals.append("nested loops over vertices and edges (VE) detected")
            time_complexity = "O(VE)"
            confidence = 0.88

        elif has_v or (is_graph and _has_adjacency_matrix(source)):
            signals.append("dense graph adjacency matrix traversal (V^2) detected")
            time_complexity = "O(V^2)"
            confidence = 0.86

        elif _has_log_loop(source):
            if len(loop_bounds) >= 2 and loop_bounds[0] != loop_bounds[1]:
                outer_v, inner_v = loop_bounds[0], loop_bounds[1]
                outer_sym = "V+E" if outer_v == "v+e" else (outer_v.upper() if outer_v in {"v", "e"} else outer_v)
                inner_sym = inner_v.upper() if inner_v in {"v", "e"} else inner_v
                if outer_v == "v+e":
                    time_complexity = f"O(({outer_sym}) log {inner_sym})"
                else:
                    time_complexity = f"O({outer_sym} log {inner_sym})"
                signals.append(f"outer loop ({outer_sym}) with inner logarithmic loop ({inner_sym}) detected")
            elif has_two_vars:
                outer_v = loop_bounds[0] if loop_bounds else ("n" if "for" in src and "n" in src else "m")
                inner_v = "m" if outer_v == "n" else "n"
                signals.append(f"outer loop ({outer_v}) with inner logarithmic loop ({inner_v}) detected")
                time_complexity = f"O({outer_v} log {inner_v})"
            else:
                signals.append("outer linear loop with inner logarithmic loop detected")
                time_complexity = "O(n log n)"
            confidence = 0.84

        elif _has_sort(source):
            signals.append("nested loops with sort detected")
            time_complexity = "O(n^2 log n)"
            confidence = 0.82

        elif has_two_vars:
            signals.append("two nested loops over two distinct variables detected")
            time_complexity = "O(mn)"
            confidence = 0.84

        else:
            signals.append("two nested loops detected")
            time_complexity = "O(n^2)"
            confidence = 0.86

    # ── Single loop ───────────────────────────────────────────────────────────
    elif depth == 1:
        outer_v = loop_bounds[0] if loop_bounds else ("m" if "m" in src and "n" not in src else ("v" if has_v else "n"))

        if _is_pure_graph_setup(source):
            signals.append("pure graph setup/allocation detected")
            time_complexity = "O(1)"
            confidence = 0.88

        elif is_graph and _has_graph_traversal(source):
            signals.append("Graph traversal on adjacency list (V+E) detected")
            time_complexity = "O(V+E)"
            confidence = 0.88

        elif _has_log_loop(source):
            target_v = "V" if has_v else ("E" if has_e else outer_v)
            target_sym = target_v.upper() if target_v in {"v", "e"} else target_v
            signals.append(f"single logarithmic loop ({target_sym}) detected")
            time_complexity = f"O(log {target_sym})"
            confidence = 0.82

        elif _has_sort(source):
            log_v = _get_log_target_var(source, default_var=outer_v)
            if outer_v != log_v:
                signals.append(f"single loop ({outer_v}) with sort on ({log_v}) detected")
                time_complexity = f"O({outer_v} {log_v} log {log_v})"
            elif outer_v in {"m", "v", "e"}:
                target_sym = "V" if outer_v == "v" else ("E" if outer_v == "e" else "m")
                signals.append(f"single loop ({target_sym}) with sort detected")
                time_complexity = f"O({target_sym}^2 log {target_sym})"
            else:
                signals.append("single loop (n) with sort detected")
                time_complexity = "O(n^2 log n)"
            confidence = 0.86

        elif _has_binary_search_call(source):
            log_v = _get_log_target_var(source, default_var=outer_v)
            if outer_v != log_v:
                signals.append(f"single loop ({outer_v}) with logarithmic operation on ({log_v}) detected")
                time_complexity = f"O({outer_v} log {log_v})"
            elif outer_v in {"m", "v", "e"}:
                target_sym = "V" if outer_v == "v" else ("E" if outer_v == "e" else "m")
                signals.append(f"single loop ({target_sym}) with logarithmic operation detected")
                time_complexity = f"O({target_sym} log {target_sym})"
            else:
                signals.append("single loop (n) with logarithmic operation detected")
                time_complexity = "O(n log n)"
            confidence = 0.86

        elif (has_two_vars or (has_v and has_e)) and not loops_nested:
            if has_v and has_e:
                signals.append("sequential loops over vertices and edges (V+E) detected")
                time_complexity = "O(V+E)"
            else:
                signals.append("sequential loops over two distinct variables detected")
                time_complexity = "O(m+n)"
            confidence = 0.82

        else:
            target_sym = "V" if has_v and not has_e else ("E" if has_e and not has_v else (outer_v.upper() if outer_v in {"v", "e"} else outer_v))
            signals.append(f"single input-dependent loop ({target_sym}) detected")
            time_complexity = f"O({target_sym})"
            confidence = 0.76

    # ── No loops ──────────────────────────────────────────────────────────────
    else:
        has_m = bool(re.search(r"\bm\b", src))
        has_n = bool(re.search(r"\bn\b", src))

        if is_graph and has_v:
            if _has_binary_search_call(source) or _has_log_loop(source):
                signals.append("binary-search / logarithmic operation on V detected")
                time_complexity = "O(log V)"
            elif _has_sort(source):
                signals.append("sorting operation on V detected")
                time_complexity = "O(V log V)"
            else:
                signals.append("constant time operations in graph context")
                time_complexity = "O(1)"
            confidence = 0.88
        elif _has_binary_search_call(source):
            if has_m and not has_n:
                signals.append("binary-search call on m detected")
                time_complexity = "O(log m)"
            else:
                signals.append("binary-search call detected")
                time_complexity = "O(log n)"
            confidence = 0.90
        elif _has_sort(source):
            if has_m and not has_n:
                signals.append("sorting operation on m detected")
                time_complexity = "O(m log m)"
            else:
                signals.append("sorting operation detected")
                time_complexity = "O(n log n)"
            confidence = 0.88
        else:
            signals.append("no input-dependent loops detected")
            time_complexity = "O(1)"
            confidence = 0.60

    # ── Space Complexity ───────────────────────────────────────────────────────
    space_complexity, space_confidence, space_signal = _analyze_space(
        source, has_recursion, branch_count
    )
    signals.append(space_signal)

    return ComplexityAnalysis(
        time_complexity=normalize_complexity(time_complexity),
        space_complexity=normalize_complexity(space_complexity),
        confidence=round(min(confidence, space_confidence), 3),
        method="static",
        status="ANALYZED",
        signals=signals,
        explanation="Complexity was estimated from the C++ source structure.",
    )


def analyze_source(
    source: str,
    language: str,
) -> ComplexityAnalysis:
    language_name = language.lower().strip()

    if language_name in {"cpp", "c++", "cc", "cxx", "c"}:
        return analyze_cpp(source)

    return ComplexityAnalysis(
        status="REVIEW_REQUIRED",
        method="static",
        confidence=0.0,
        explanation=f"Static analysis for {language} is not implemented yet.",
    )