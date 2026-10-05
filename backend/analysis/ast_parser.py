import re
from typing import Dict, List, Optional, Set, Tuple, Any
from .complexity_ir import ComplexityIR, LoopIR, RecursionIR, GraphIR

# Tree-sitter imports - handle gracefully if not available
AST_AVAILABLE = False
try:
    from tree_sitter import Language, Node, Parser, Tree
    AST_AVAILABLE = True
except Exception:
    # Tree-sitter not available - use regex fallback
    Node = type('Node', (), {})
    Parser = type('Parser', (), {})
    Tree = type('Tree', (), {})
    Language = type('Language', (), {})




def parse_cpp_ast(source: str):
    """Factory function for backward compatibility with static_analyzer_v2.py"""
    try:
        return ASTComplexityAnalyzer(source, 'cpp')
    except Exception:
        return None


class ASTComplexityAnalyzer:
    """
    AST-based complexity analyzer for multi-language code.
    Falls back to regex analysis when tree-sitter is unavailable.
    """

    def __init__(self, source_code: str, language: str = 'cpp'):
        self.source = source_code
        self.language = language.lower()
        self.parser = None
        self.tree = None
        self.use_ast = AST_AVAILABLE

        if AST_AVAILABLE:
            self._initialize_parser()

    def _initialize_parser(self) -> None:
        """Initialize tree-sitter parser for the given language."""
        if not AST_AVAILABLE:
            return

        lang_map = {
            'cpp': ('tree_sitter_cpp', 'language'),
            'c++': ('tree_sitter_cpp', 'language'),
            'c': ('tree_sitter_c', 'language'),
            'python': ('tree_sitter_python', 'language'),
            'py': ('tree_sitter_python', 'language'),
            'java': ('tree_sitter_java', 'language'),
        }

        lang_key = self.language.lower().strip()

        try:
            if lang_key in lang_map:
                mod_name, fn_name = lang_map[lang_key]
                mod = __import__(mod_name)
                lang_fn = getattr(mod, fn_name)
                ts_lang = Language(lang_fn())
                try:
                    self.parser = Parser(ts_lang)
                except Exception:
                    self.parser = Parser()
                    self.parser.set_language(ts_lang)

                self.tree = self.parser.parse(bytes(self.source, 'utf-8'))
                self.use_ast = True
                return
        except Exception:
            pass

        try:
            from tree_sitter_languages import get_parser
            mapped_lang = 'cpp' if lang_key in {'cpp', 'c++'} else lang_key
            self.parser = get_parser(mapped_lang)
            if self.parser:
                self.tree = self.parser.parse(bytes(self.source, 'utf-8'))
                self.use_ast = True
        except Exception:
            self.use_ast = False
            self.parser = None
            self.tree = None


    def analyze(self) -> ComplexityIR:
        """
        Main analysis entry point.
        Returns ComplexityIR with extracted features.
        """
        if self.use_ast and self.tree and self.tree.root_node:
            return self._ast_analysis()
        else:
            return self._regex_analysis()

    def _ast_analysis(self) -> ComplexityIR:
        """AST-based analysis (when tree-sitter is available)."""
        ir = ComplexityIR(language=self.language, source=self.source)

        try:
            # Extract features from AST
            ir.loop = self._extract_loop_features(self.tree.root_node)
            ir.recursion = self._extract_recursion_features(self.tree.root_node)
            ir.graph = self._extract_graph_features(self.tree.root_node)

            # Extract additional algorithm patterns
            ir.has_heap_operations = self._detect_heap_operations()
            ir.has_matrix_bounds = self._detect_matrix_bounds()
            ir.has_dynamic_allocation = self._detect_dynamic_allocation()
            ir.has_2d_allocation = self._detect_2d_allocation()
            ir.is_constant_lookup = self._detect_constant_lookup()
            ir.multiple_input_bounds = ir.loop.multiple_input_bounds
            ir.has_merged_both = self._detect_merged_both_inputs()

        except Exception:
            # If AST extraction fails, fall back to regex
            return self._regex_analysis()

        return ir

    def _regex_analysis(self) -> ComplexityIR:
        """
        Fallback regex-based analysis when AST parsing fails or is unavailable.
        Enhanced version with comprehensive pattern detection.
        """
        ir = ComplexityIR(language=self.language, source=self.source)
        src = self.source.lower()

        # === LOOP DETECTION ===

        for_loops = len(re.findall(r'\bfor\s*\(', src))
        while_loops = len(re.findall(r'\bwhile\s*\(', src))
        do_loops = len(re.findall(r'\bdo\s*\{', src))

        total_loops = for_loops + while_loops + do_loops

        if total_loops > 0:
            # Detect TRUE nesting vs sequential patterns
            # for(...) { for(...) } = truly nested O(n^2)
            # for(...) { for(...) { for(...) } } = triple nested O(n^3)
            # for(...) {} for(...) {} = sequential O(n)

            # Count nested depth by checking for patterns like for{...for{...}}
            # We need to distinguish between for{...} for{...} (sequential) vs for{...for{...}} (nested)

            # Check for triple nested: for{...for{...for{...}}}
            triple_nested = bool(re.search(r'for\s*\([^}]*for\s*\([^}]*for\s*\(', src, re.DOTALL))

            # Check for double nested: for{...for{...}}
            double_nested = bool(re.search(r'for\s*\([^}]*for\s*\(', src, re.DOTALL)) and not triple_nested

            # Check for sequential: for{...} for{...} (loops separated, not nested)
            # Pattern: for(...){...} some_code for(...){...}
            sequential_pattern = re.search(r'for\s*\([^}]*\}\s*[^}]*for\s*\(', src, re.DOTALL)
            is_sequential = bool(sequential_pattern) and not double_nested and not triple_nested

            # Check for logarithmic inner loop: while(x>1) x/=2 inside for loop
            has_log_inner = bool(re.search(r'for\s*\([^}]*while\s*\([^)]*x\s*/=\s*2', src, re.DOTALL))

            # Check for amortized patterns: sliding window, two-pointer, monotonic stack, heap ops
            is_sliding_window = bool(re.search(r'\bwhile\s*\([^)]*sum|l\+\+|left\+\+', src))
            is_monotonic_stack = bool(re.search(r'st\.pop\(\)|stack.*pop|st\.push|stack.*push', src))
            is_heap_while = bool(re.search(r'\bwhile\s*\([^)]*pq\.|heap|priority_queue', src))

            if triple_nested:
                ir.loop.depth = 3
                ir.loop.structure = "triple_nested"
            elif double_nested:
                ir.loop.depth = 2
                ir.loop.structure = "nested"
            elif is_sequential:
                ir.loop.depth = 1  # Sequential loops = O(n) not O(n²)
                ir.loop.structure = "sequential"
            elif has_log_inner:
                # for(i<n){while(x>1)x/=2;} = O(n log n)
                ir.loop.depth = 1
                ir.loop.structure = "logarithmic_nested"
            elif total_loops > 1:
                ir.loop.depth = 1
                ir.loop.structure = "sequential"
            else:
                ir.loop.depth = 1
                ir.loop.structure = "single"

        # === ALGORITHM PATTERN DETECTION ===

        # Binary search patterns
        binary_search_patterns = [
            r'lower_bound\s*\(',
            r'upper_bound\s*\(',
            r'binary_search\s*\(',
            r'while\s*\(\s*\w+\s*<=\s*\w+\s*\)',  # while(left <= right)
            r'mid\s*=\s*\([^)]*\+[^)]*\)\s*/\s*2',  # mid = (left + right) / 2
        ]
        ir.loop.has_binary_search = any(re.search(p, src) for p in binary_search_patterns)

        # Sort operations
        sort_patterns = [r'sort\s*\(', r'std::sort\s*\(', r'\.sort\s*\(', r'qsort\s*\(']
        ir.loop.has_sort = any(re.search(p, src) for p in sort_patterns)

        # Logarithmic step patterns
        log_patterns = [r'\*=\s*2', r'/=\s*2', r'\*=\s*10', r'/=\s*10', r'<<=', r'>>=']
        ir.loop.is_logarithmic_step = any(re.search(p, src) for p in log_patterns)

        # Heap operations - only priority_queue specific patterns, not generic push/pop
        ir.has_heap_operations = self._detect_heap_operations()
        ir.loop.has_heap_operations = ir.has_heap_operations

        # Matrix bounds detection
        ir.has_matrix_bounds = self._detect_matrix_bounds()
        ir.loop.has_matrix_bounds = ir.has_matrix_bounds

        # Multiple input bounds (e.g., m and n)
        bounds_vars = set()
        for match in re.finditer(r'\b([a-zA-Z_]\w*)\s*\.\s*size\s*\(\)', src):
            bounds_vars.add(match.group(1))
        for match in re.finditer(r'\bfor\s*\([^)]*<\s*(\w+)[^)]*\)', src):
            bounds_vars.add(match.group(1))

        # Also look for m,n variables used in bounds
        for match in re.finditer(r'\b(m|n|rows|cols)\b', src):
            if match.group(1) not in ['main', 'min', 'max']:  # exclude keywords
                bounds_vars.add(match.group(1))

        ir.loop.multiple_input_bounds = len(bounds_vars) >= 2
        ir.multiple_input_bounds = ir.loop.multiple_input_bounds
        if hasattr(ir.loop, 'distinct_params'):
            ir.loop.distinct_params = list(bounds_vars)

        # === RECURSION DETECTION ===

        # Find function names and check for recursive calls
        # Exclude C++ keywords that have parentheses like for, while, if, switch
        cpp_keywords = {'for', 'while', 'if', 'switch', 'catch', 'try'}
        func_matches = list(re.finditer(r'\b(\w+)\s*\([^)]*\)\s*\{', src))
        for func_match in func_matches:
            func_name = func_match.group(1)

            # Skip C++ keywords (for loops, while loops, if statements, etc.)
            if func_name in cpp_keywords:
                continue

            body_start = func_match.end()
            remaining_code = src[body_start:]

            # Look for actual function calls (func_name followed by '(')
            # Use word boundary and ensure it's not part of another word (like 'for' containing 'f')
            call_pattern = rf'(?<!\w){func_name}(?!\w)\s*\('
            recursive_calls = list(re.finditer(call_pattern, remaining_code))
            call_count = len(recursive_calls)

            if call_count > 0:
                ir.recursion.is_recursive = True
                ir.recursion.branch_factor = min(call_count, 4)

                # Check for memoization
                if any(pattern in src for pattern in ['dp[', 'memo[', 'cache[']):
                    ir.recursion.has_memoization = True
                    ir.recursion.pattern = "memoized"
                elif call_count >= 2:
                    ir.recursion.pattern = "branching"
                else:
                    ir.recursion.pattern = "linear"

                # Check for divide and conquer (detect m= or mid= with l+r pattern OR pivot-based partitioning)
                has_mid_var = any(re.search(pattern, src) for pattern in [
                    r'\bm\s*=\s*\(\s*l\s*\+\s*r\s*\)',  # m = (l + r)
                    r'\bmid\s*=\s*\(\s*l\s*\+\s*r\s*\)',
                    r'\bm\s*=\s*\(\s*l\s*\+\s*r\s*\)\s*/\s*\d+',  # m = (l + r) / 2
                    r'\bmid\s*=\s*\(\s*l\s*\+\s*r\s*\)\s*/\s*\d+',
                    r'\bm\s*=\s*l\s*\+\s*\(\s*r\s*-\s*l\s*\)\s*/\s*\d+',  # m = l + (r - l) / 2
                ])

                # Quick Sort detection: partition with pivot, recursive calls f(a,l,i-1) and f(a,i+1,r)
                is_quicksort = (
                    (re.search(rf'(?<!\w){func_name}\s*\(\s*a\s*,\s*l\s*,\s*i\s*-\s*1\s*\)', src) and
                     re.search(rf'(?<!\w){func_name}\s*\(\s*a\s*,\s*i\s*\+\s*1\s*,\s*r\s*\)', src)) or
                    (re.search(r'p\s*=\s*a\[', src) and call_count == 2 and
                     re.search(r'for\s*\([^)]*j[^)]*\)', src))
                )

                if has_mid_var or 'mid' in src or 'middle' in src or is_quicksort:
                    ir.recursion.is_divide_and_conquer = True
                    ir.recursion.pattern = "divide_and_conquer"

                    # Check if it's a simple D&C (no merge work) or standard D&C
                    # Simple D&C: just returns max/min of two halves, no O(n) merge
                    has_merge_work = any(re.search(pattern, src) for pattern in [
                        r'\.push_back\s*\(', r'\.emplace_back\s*\(',
                        r'\bmerge\b', r'while\s*\(\s*i\b', r'while\s*\(\s*j\b',
                        r'vector\s*<.*>\s+\w+\s*;',  # auxiliary array declaration
                        r'\bfor\s*\(',              # FOR loop inside = O(n) work
                        r'\bwhile\s*\(',            # WHILE loop inside = O(n) work
                    ])
                    if not has_merge_work and call_count == 2:
                        ir.recursion.pattern = "simple_divide_and_conquer"

                # Check for path compression (Union Find pattern)
                # Must be exact pattern p[x] = find(p, p[x]) where LHS is exactly p[x] or parent[x]
                path_compression_pattern1 = rf'\bp\[\w+\]\s*=\s*{func_name}\s*\(\s*[^)]*p\[\w+\]\s*\)'
                path_compression_pattern2 = rf'\bparent\[\w+\]\s*=\s*{func_name}\s*\(\s*[^)]*parent\[\w+\]\s*\)'

                if re.search(path_compression_pattern1, src) or re.search(path_compression_pattern2, src):
                    ir.recursion.pattern = "path_compression"
                    ir.recursion.branch_factor = 1

                # Check for auxiliary array allocation in recursive functions
                if any(kw in remaining_code for kw in ['push_back', 'emplace_back', 'vector<']):
                    ir.recursion.has_auxiliary_array = True

                break

        # === GRAPH DETECTION ===
        # Only detect as graph if it has graph-specific patterns, not just vector<vector>

        # Graph-specific indicators
        graph_indicators = [
            r'\bdfs\s*\(',
            r'\bbfs\s*\(',
            r'\bvis\b.*\bvis\b',  # visited array used multiple times
            r'adjacency',
            r'\bNode\b',
            r'\badj\b',
        ]

        # vector<vector> is only a graph if combined with graph indicators
        has_vector_vector = bool(re.search(r'vector\s*<\s*vector\s*<', src))
        has_graph_indicator = any(re.search(p, src) for p in graph_indicators)

        # Parameter name hints for graph (g, graph, adj)
        has_graph_param = bool(re.search(r'\b(g|graph|adj)\b', src))

        if has_vector_vector and (has_graph_indicator or has_graph_param):
            ir.graph.is_graph = True
            ir.graph.structure = "adj_list"
        elif has_graph_indicator:
            ir.graph.is_graph = True
        elif re.search(r'\[\s*\]\s*\[\s*\]', src):
            ir.graph.structure = "adj_matrix"

        # DFS with recursive call on adjacency list is a graph algorithm
        if ir.recursion.is_recursive and has_graph_param and has_vector_vector:
            ir.graph.is_graph = True
            ir.graph.structure = "adj_list"

        # === SPACE COMPLEXITY PATTERNS ===

        ir.has_dynamic_allocation = self._detect_dynamic_allocation()
        ir.has_2d_allocation = self._detect_2d_allocation()
        ir.is_constant_lookup = self._detect_constant_lookup()
        ir.has_merged_both = self._detect_merged_both_inputs()

        return ir

    def _detect_heap_operations(self) -> bool:
        """Detect priority queue / heap operations that add O(log n) factor."""
        src = self.source.lower()

        heap_patterns = [
            r"priority_queue\s*<[^>]*>\s*\w+",
            r"make_heap\s*\(",
            r"push_heap\s*\(",
            r"pop_heap\s*\(",
            r"heappush\s*\(",
            r"heappop\s*\(",
        ]

        # Also detect priority_queue usage via pq.push/pq.pop/pq.top
        has_pq_decl = bool(re.search(r'priority_queue', src))
        has_pq_ops = has_pq_decl and any(
            re.search(p, src) for p in [r'\.push\s*\(', r'\.pop\s*\(', r'\.top\s*\(']
        )

        return has_pq_ops or any(re.search(p, src) for p in heap_patterns)

    def _detect_matrix_bounds(self) -> bool:
        """Detect matrix operations with distinct m*n bounds."""
        src = self.source.lower()

        # Look for nested loops with different bounds like a.size() and a[i].size()
        has_matrix_access = bool(re.search(r"a\[\s*i\s*\]\.\s*size\s*\(\)", src)) or \
                           bool(re.search(r"matrix\[\s*i\s*\]\.\s*size\s*\(\)", src)) or \
                           bool(re.search(r"grid\[\s*i\s*\]\.\s*size\s*\(\)", src)) or \
                           bool(re.search(r"a\[0\]\.size\(\)", src)) or \
                           bool(re.search(r"vector\s*<\s*vector\s*<", src))

        # Look for explicit m*n parameters or bounds
        has_mn_params = bool(re.search(r"\bm\b.*\bn\b", src)) or \
                       bool(re.search(r"rows.*cols", src))

        return has_matrix_access or has_mn_params

    def _detect_dynamic_allocation(self) -> bool:
        """Detect dynamic memory allocation inside function body."""
        src = self.source.lower()

        # Find the function body (after first '{')
        brace_pos = src.find('{')
        if brace_pos < 0:
            function_body = src if self.language in {'python', 'py'} else ''
            if not function_body:
                return False
        else:
            function_body = src[brace_pos:]

        # Check for dynamic allocation operations IN the function body
        body_allocation_patterns = [
            r'\.push_back\s*\(',
            r'\.emplace_back\s*\(',
            r'\.resize\s*\(',
            r'\.reserve\s*\(',
            r'\.insert\s*\(',
            r'\bnew\s+\w+',
            r'\bmalloc\s*\(',
            # Python containers and mutating operations.
            r'\b(?:list|dict|set|deque|defaultdict)\s*\(',
            r'\.(?:append|extend|add|update|setdefault|popleft|appendleft)\s*\(',
            r'\bheapq\.(?:heappush|heappop|heapify)\s*\(',
            r'\[\s*\]',
        ]


        has_body_ops = any(re.search(p, function_body) for p in body_allocation_patterns)
        if has_body_ops:
            return True

        # Check for local variable declarations of containers (not parameters)
        # More flexible patterns that match vector<T> name( or name;
        local_container_patterns = [
            r'vector\s*<[^>]+>\s+\w+\s*[\(;]',          # vector<T> name ( or ;
            r'unordered_map\s*<[^>]+>\s+\w+\s*[\(;]',
            r'unordered_set\s*<[^>]+>\s+\w+\s*[\(;]',
            r'map\s*<[^>]+>\s+\w+\s*[\(;]',
            r'set\s*<[^>]+>\s+\w+\s*[\(;]',
            r'stack\s*<[^>]+>\s+\w+\s*[\(;]',
            r'queue\s*<[^>]+>\s+\w+\s*[\(;]',
            r'priority_queue\s*<[^>]+>\s+\w+\s*[\(;]',
            r'list\s*<[^>]+>\s+\w+\s*[\(;]',
        ]

        # Also check for array-style declarations inside function
        array_allocation_patterns = [
            r'int\s+\w+\s*\[\s*\w+\s*\]',      # int arr[n]
            r'float\s+\w+\s*\[\s*\w+\s*\]',
            r'double\s+\w+\s*\[\s*\w+\s*\]',
            r'char\s+\w+\s*\[\s*\w+\s*\]',
        ]

        # SIMPLIFIED: Just check if any container declaration exists in function body
        container_keywords = [
            'vector<', 'unordered_map<', 'unordered_set<', 'map<', 'set<',
            'stack<', 'queue<', 'priority_queue<', 'list<'
        ]

        for keyword in container_keywords:
            # Check if keyword exists in function body
            if keyword in function_body:
                # Make sure it's not just a parameter (should have variable after >)
                # Allow 0 or more spaces between > and variable name, and allow ( or ; or {}
                pattern = rf'{keyword}[^>]+>\s*\w+\s*[\(;{{]'
                if re.search(pattern, function_body):
                    return True

        # Check for DP/memoization pattern (vector<int>& dp parameter)
        # Even though it's a reference parameter, recursion uses O(n) space for the DP table
        dp_patterns = [
            r'vector\s*<[^>]+>&\s+dp',
            r'unordered_map\s*<[^>]+>&\s+dp',
            r'map\s*<[^>]+>&\s+dp',
            r'\bmemo\b',
            r'\bcache\b',
        ]

        if any(re.search(p, src) for p in dp_patterns):
            return True

        # Check for Quick Sort pattern: divide-and-conquer with partition and 2 recursive calls
        # Quick Sort worst-case space is O(n) for recursion stack
        has_quick_sort_pattern = False
        if re.search(r'p\s*=\s*a\[', src) or re.search(r'pivot\s*=', src):
            # Has pivot partitioning
            if re.search(r'for\s*\([^)]*j[^)]*\)', src):
                # Has inner loop (partitioning loop)
                has_quick_sort_pattern = True

        if has_quick_sort_pattern:
            return True

        # Check array declarations
        for pattern in array_allocation_patterns:
            if re.search(pattern, function_body):
                return True

        return False

    def _detect_2d_allocation(self) -> bool:
        """Detect 2D dynamic allocation."""
        src = self.source.lower()

        brace_pos = src.find('{')
        if brace_pos < 0:
            function_body = src if self.language in {'python', 'py'} else ''
            if not function_body:
                return False
        else:
            function_body = src[brace_pos:]

        # Look for local 2D vector declarations: vector<vector<T>> name(...) or name = ...
        vec_decl = bool(re.search(r'vector\s*<\s*vector\s*<[^>]+\s*>\s*>\s*\w+', function_body))

        # Look for 2D dynamic arrays: new T[n][m] or type arr[n][m] declaration
        arr_decl = bool(re.search(r'\bnew\s+\w+\s*\[[^\]]+\]\s*\[[^\]]+\]', function_body)) or \
                   bool(re.search(r'\b(?:int|float|double|char|bool)\s+\w+\s*\[[^\]]+\]\s*\[[^\]]+\]', function_body))

        # Python nested-list comprehensions, e.g. [[0] * m for _ in range(n)].
        python_2d = bool(re.search(
            r'\[\s*\[[^\]]*\]\s*(?:for|\*)', function_body
        ))

        return vec_decl or arr_decl or python_2d

    def _detect_constant_lookup(self) -> bool:
        """Detect constant-time lookup operations."""
        src = self.source.lower()

        lookup_patterns = [
            r"unordered_map",
            r"unordered_set",
            r"hash_map",
            r"hash_set",
            r"dict\s*\[",
        ]

        return any(re.search(p, src) for p in lookup_patterns)

    def _detect_merged_both_inputs(self) -> bool:
        """Detect if algorithm merges two inputs (e.g., median of two sorted arrays)."""
        src = self.source.lower()

        patterns = [
            r"merge\s+two",
            r"median\s+of\s+two",
            r"intersection\s+of\s+two",
            r"union\s+of\s+two",
            r"two\s+pointers",
            r"merge\s*sorted",
            r"nums1.*nums2",
            r"arr1.*arr2",
        ]

        return any(re.search(p, src) for p in patterns)

    # === AST-SPECIFIC METHODS (only used when tree-sitter is available) ===

    # === AST-SPECIFIC METHODS ===

    def _extract_loop_features(self, root) -> LoopIR:
        """Extract loop features by traversing tree-sitter AST nodes."""
        loop = LoopIR()
        loop_types = {
            'for_statement', 'while_statement', 'do_statement',
            'for_range_loop', 'enhanced_for_statement',
            # Python comprehensions execute an input-sized iteration even
            # though they do not appear as a standalone for_statement.
            'list_comprehension', 'set_comprehension',
            'dictionary_comprehension', 'generator_expression',
        }

        loop_nodes = []

        def find_loops(node):
            if node.type in loop_types:
                loop_nodes.append(node)
            for child in node.children:
                find_loops(child)

        find_loops(root)

        if not loop_nodes:
            return loop

        def is_constant_bounded(node):
            """Return True for loops whose iteration count is input-independent."""
            text = node.text.decode('utf-8', errors='ignore') if isinstance(node.text, bytes) else str(node.text)
            # Inspect only the loop header.  A complete outer-node string
            # includes nested bodies, so literals such as range(4) or <26
            # must not make the outer input-sized loop look constant.
            body = node.child_by_field_name('body')
            if body is not None:
                body_text = body.text.decode('utf-8', errors='ignore') if isinstance(body.text, bytes) else str(body.text)
                header = text[:text.find(body_text)] if body_text in text else text
            else:
                header = text
            lower = header.lower()
            # Python range literals (range(4), range(0, 26), ...).
            if re.search(r'\brange\s*\(\s*(?:0\s*,\s*)?\d+\s*\)', lower):
                return True
            # C/C++ loop conditions bounded by a numeric literal.
            if re.search(r';[^;]*[<>]=?\s*\d+\b', lower):
                return True
            # Small fixed direction/array-alphabet loops are also constant.
            if re.search(r'\b(?:4|8|26|27|36|52)\b', lower) and ('for' in lower or 'range' in lower):
                return True
            return False

        constant_loop_ids = {id(node) for node in loop_nodes if is_constant_bounded(node)}

        # 1. Determine nesting depth and parent-child hierarchy
        max_depth = 0
        loop_ancestor_counts = []
        for node in loop_nodes:
            ancestors = 0
            curr = node.parent
            while curr:
                if curr.type in loop_types and id(curr) not in constant_loop_ids:
                    ancestors += 1
                curr = curr.parent
            loop_ancestor_counts.append(ancestors)
            if id(node) not in constant_loop_ids:
                max_depth = max(max_depth, ancestors + 1)

        loop.depth = max_depth

        # Check if loops are sequential vs nested
        top_level_loops = [loop_nodes[i] for i, anc in enumerate(loop_ancestor_counts)
                           if anc == 0 and id(loop_nodes[i]) not in constant_loop_ids]
        if max_depth == 1 and len(top_level_loops) > 1:
            loop.structure = "sequential"
        elif max_depth == 2:
            loop.structure = "nested"
        elif max_depth >= 3:
            loop.structure = "triple_nested"
        else:
            loop.structure = "single"

        # 2. Check logarithmic step patterns across loops (% b, &=, /= 2, *= 2, >>= 1)
        log_loop_count = 0
        for node in loop_nodes:
            if id(node) in constant_loop_ids:
                continue
            # Always define full_text first so while/do branches never hit NameError
            full_text = node.text.decode('utf-8', errors='ignore').lower() if isinstance(node.text, bytes) else str(node.text).lower()
            body = node.child_by_field_name('body')
            if body:
                body_text = body.text.decode('utf-8', errors='ignore').lower() if isinstance(body.text, bytes) else str(body.text).lower()
                header_text = full_text[:full_text.find(body_text)] if body_text in full_text else full_text
            else:
                header_text = full_text
                body_text = full_text

            if node.type in ['while_statement', 'do_statement']:
                check_text = full_text
            else:
                check_text = header_text

            if any(op in check_text for op in ['*=', '/=', '>>=', '<<=', '/ 2', '/10', '* 2', '* 10', '%', '&=']):
                log_loop_count += 1

        if log_loop_count >= 2:
            loop.is_logarithmic_step = True
            loop.structure = "log_squared"
        elif log_loop_count == 1:
            loop.is_logarithmic_step = True
            if max_depth >= 2:
                loop.structure = "logarithmic_nested"

        # 3. Check algorithm operations (sort, binary search, heap) inside/outside loops
        src_lower = self.source.lower()
        loop.has_sort = any(s in src_lower for s in [
            'sort(', 'std::sort', '.sort(', 'sorted(',
        ])
        # A sort performed for every input item composes multiplicatively with
        # its surrounding loop.  Keep this separate from one preprocessing
        # sort followed by a scan.
        loop.sort_inside_loop = loop.has_sort and any(
            any(marker in (
                (node.child_by_field_name('body').text.decode('utf-8', errors='ignore')
                 if isinstance(node.child_by_field_name('body').text, bytes)
                 else str(node.child_by_field_name('body').text))
                if node.child_by_field_name('body') is not None else ''
            ).lower() for marker in ('sort(', 'std::sort', '.sort(', 'sorted('))
            for node in loop_nodes
        )
        explicit_binary_call = bool(re.search(
            r'\b(?:lower_bound|upper_bound|binary_search|bisect_left|bisect_right)\s*\(',
            src_lower,
        ))
        halving_loop = bool(
            re.search(r'\b(?:while|for)\s*\([^)]*(?:<=|>=)[^)]*\)', src_lower)
            and re.search(r'\b(?:mid|middle|m)\s*=\s*[^\n;]*(?:/\s*2|>>\s*1)', src_lower)
            and re.search(r'\b(?:left|right|l|r)\s*=\s*[^\n;]*\b(?:mid|middle|m)\b', src_lower)
        )
        loop.has_binary_search = explicit_binary_call or halving_loop
        # A binary-search call nested in another loop is multiplicative.  Keep
        # this separate from a loop whose own update halves the search range.
        binary_call_patterns = [
            r'\b(?:binary_search|lower_bound|upper_bound|bisect_left|bisect_right)\s*\(',
        ]
        loop.binary_search_inside_loop = any(
            any(re.search(pattern, (node.text.decode('utf-8', errors='ignore')
                                     if isinstance(node.text, bytes) else str(node.text)).lower())
                for pattern in binary_call_patterns)
            for node in loop_nodes
        )
        loop.binary_search_loop_depth = max_depth if loop.binary_search_inside_loop else 0
        loop.has_heap_operations = self._detect_heap_operations()
        # Amortized patterns are recognized structurally, rather than by a
        # generic pop/increment token.  This prevents unrelated nested loops
        # from being incorrectly collapsed to O(n).
        has_window_pointer = bool(re.search(
            r'\b(?:left|start|l)\s*(?:\+\+|\+=\s*1|=\s*\w+\s*\+\s*1)',
            src_lower,
        ))
        # Python writes ``while condition:``, C-family languages write
        # ``while (condition)``. The pointer movement requirement above keeps
        # this broad loop marker from classifying arbitrary nested loops as a
        # sliding window.
        has_window_loop = bool(re.search(r'\bwhile\b', src_lower))
        loop.is_sliding_window = max_depth >= 2 and has_window_pointer and has_window_loop

        has_stack_container = bool(re.search(
            r'\b(?:stack|deque|vector)\s*<[^>]+>\s*(?:stack|st|s|dq)\b'
            r'|\b(?:stack|st|s|dq)\s*=\s*\['
            r'|\b(?:stack|st|s|dq)\s*=\s*(?:deque|list)\s*\(',
            src_lower,
        ))
        has_stack_push = bool(re.search(r'\.(?:push|push_back|append|appendleft)\s*\(', src_lower))
        has_stack_pop = bool(re.search(r'\.(?:pop|pop_back|popleft)\s*\(', src_lower))
        loop.is_monotonic_stack = max_depth >= 2 and has_stack_container and has_stack_push and has_stack_pop
        # Detect Fenwick/BIT work only from unambiguous identifiers or the
        # canonical lowbit update. A bare ``bit`` token is too broad because
        # it also appears in ordinary bit-manipulation solutions.
        loop.has_bit_operations = bool(re.search(
            r'\b(?:fenwick(?:tree)?|bitree|binary_indexed(?:_tree)?)\b'
            r'|\b(?:bit|tree)\s*\.\s*(?:add|sum|query|update)\s*\('
            r'|\b(\w+)\s*[+\-]=\s*\1\s*&\s*-\s*\1\b',
            src_lower,
        ))
        loop.has_matrix_bounds = self._detect_matrix_bounds()

        # Check for multiple input bounds (e.g. m and n or w/W or size calls)
        loop_counter_vars = set(re.findall(r'\bfor\s*\(\s*(?:[a-zA-Z_]\w*\s+)?([a-zA-Z_]\w*)\s*=', src_lower))
        loop_counter_vars.update(re.findall(r'\bfor\s+([a-zA-Z_]\w*)\s+in\s+', src_lower))
        loop_counter_vars.update({'i', 'j', 'k', 'x', 'y', 'z', 'idx', 'index', 'row', 'col', 'r', 'c', 'it'})

        bounds_vars = list(dict.fromkeys(re.findall(r'\b([a-zA-Z_]\w*)\s*\.\s*size\s*\(\)', src_lower)))
        for match in re.finditer(r'\bfor\s*\([^)]*<\s*=?\s*(\w+)[^)]*\)', src_lower):
            v = match.group(1)
            if v not in ['0', '1', '2'] and v not in bounds_vars and v not in loop_counter_vars:
                bounds_vars.append(v)
        # Container identifiers from ``a.size()`` are not independent
        # asymptotic dimensions when the loop is otherwise bounded by the
        # derived scalar ``n`` (a common two-pass array pattern).
        if len(bounds_vars) >= 2 and 'n' in bounds_vars:
            arbitrary_containers = [b for b in bounds_vars if b not in {'n', 'm', 'v', 'e', 'rows', 'cols', 'w', 'k'}]
            if arbitrary_containers and len(arbitrary_containers) == len(bounds_vars) - 1:
                bounds_vars = ['n']
        loop.distinct_params = bounds_vars
        loop.multiple_input_bounds = len(bounds_vars) >= 2

        if (loop.is_sliding_window or loop.is_monotonic_stack) and max_depth == 2:
            loop.depth = 1
            loop.structure = "sequential"

        # Preserve the established amortized fallback for compact reference
        # solutions that do not expose descriptive pointer/container names
        # (for example, BFS queues and contest-style ``s.pop()`` stacks).
        # The structured rules above provide stronger evidence when present.
        legacy_amortized = any(token in src_lower for token in (
            '.pop()', 'pop_back()', 'popleft(', 'pop(0)',
            'left++', 'l++', 'start++', 'left += 1', 'left+=1',
            'l += 1', 'l+=1', 'start += 1', 'start+=1',
        ))
        if legacy_amortized and max_depth == 2:
            loop.depth = 1
            loop.structure = "sequential"

        # Counting-sort frequency scans use a fixed alphabet/range table. The
        # inner decrement loop consumes each input item once overall, so it is
        # linear rather than quadratic.
        is_fixed_frequency_scan = bool(re.search(
            r'\b(?:cnt|count|freq|c)\s*\[\s*\d+\s*\]'
            r'|\b(?:cnt|count|freq|c)\s*\[\s*\d+\s*\]\s*=',
            src_lower,
        )) and bool(re.search(r'\b(?:cnt|count|freq|c)\s*\[\s*\w+\s*\]\s*--', src_lower))
        if is_fixed_frequency_scan and max_depth >= 2:
            loop.depth = 1
            loop.structure = "sequential"

        return loop

    def _extract_recursion_features(self, root) -> RecursionIR:
        """Extract recursion features from AST."""
        rec = RecursionIR()
        loop_types = {'for_statement', 'while_statement', 'do_statement', 'for_range_loop', 'enhanced_for_statement'}

        func_nodes = []
        def find_funcs(node):
            if node.type in ['function_definition', 'method_declaration']:
                func_nodes.append(node)
            for child in node.children:
                find_funcs(child)
        find_funcs(root)

        if not func_nodes:
            return self._regex_analysis().recursion

        # Build a small, language-neutral call graph before inspecting the
        # individual functions.  The old extractor only looked for a function
        # calling itself, so patterns such as even() -> odd() -> even() and
        # backtracking split between solve()/choose() were reported as linear.
        # Tree-sitter exposes calls as ``call_expression`` for C-like
        # languages and ``call`` for Python; both are handled here.
        def function_name(fn_node):
            name = ""
            declarator = fn_node.child_by_field_name('declarator')
            if declarator:
                for c in declarator.children:
                    if c.type in ['identifier', 'field_identifier']:
                        name = c.text.decode('utf-8', errors='ignore') if isinstance(c.text, bytes) else str(c.text)
                        break
                if not name and declarator.type in ['identifier', 'field_identifier']:
                    name = declarator.text.decode('utf-8', errors='ignore') if isinstance(declarator.text, bytes) else str(declarator.text)
            if not name:
                name_node = fn_node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf-8', errors='ignore') if isinstance(name_node.text, bytes) else str(name_node.text)
            return name

        graph_records = []
        known_names = set()
        for node in func_nodes:
            name = function_name(node)
            if name and name not in {'main', 'if', 'for', 'while'}:
                text = node.text.decode('utf-8', errors='ignore') if isinstance(node.text, bytes) else str(node.text)
                graph_records.append((name, node, text))
                known_names.add(name)

        adjacency = {name: set() for name in known_names}
        graph_calls = {name: [] for name in known_names}
        for name, fn_node, _ in graph_records:
            def collect_graph_calls(node):
                if node.type in {'call_expression', 'call'}:
                    func_expr = node.child_by_field_name('function') or (node.children[0] if node.children else None)
                    if func_expr:
                        raw = func_expr.text.decode('utf-8', errors='ignore') if isinstance(func_expr.text, bytes) else str(func_expr.text)
                        call_name = raw.split('::')[-1].split('.')[-1].split('->')[-1]
                        if call_name in known_names:
                            in_loop = False
                            parent = node.parent
                            while parent:
                                if parent.type in loop_types:
                                    in_loop = True
                                    break
                                parent = parent.parent
                            adjacency[name].add(call_name)
                            graph_calls[name].append((call_name, in_loop))
                for child in node.children:
                    collect_graph_calls(child)
            collect_graph_calls(fn_node)

        # Find a directed cycle containing more than one function.  A bounded
        # DFS is sufficient here and avoids imposing a graph dependency on the
        # parser; function counts in a submission are small.
        mutual_cycle = []
        for start in known_names:
            stack = [(start, [start])]
            while stack and not mutual_cycle:
                current, path = stack.pop()
                for nxt in adjacency.get(current, ()):
                    if nxt == start and len(path) > 1:
                        mutual_cycle = path[:]
                        break
                    if nxt not in path and len(path) <= len(known_names):
                        stack.append((nxt, path + [nxt]))
        if mutual_cycle:
            cycle_set = set(mutual_cycle)
            cycle_edges = []
            for name in cycle_set:
                cycle_edges.extend((target, inside) for target, inside in graph_calls.get(name, []) if target in cycle_set)
            rec.is_recursive = True
            rec.has_mutual_recursion = True
            rec.call_graph_nodes = len(known_names)
            rec.call_graph_edges = sum(len(v) for v in adjacency.values())
            rec.recursive_cycle_size = len(cycle_set)
            rec.branch_factor = max(1, max((sum(1 for target, _ in graph_calls.get(name, []) if target in cycle_set) for name in cycle_set), default=1))
            rec.calls_inside_loop = any(inside for _, inside in cycle_edges)
            cycle_text = ' '.join(text for name, _, text in graph_records if name in cycle_set).lower()
            permutation_like = bool(re.search(r'\bswap\s*\(|\bpermute\b|\bpermutation\b|\bqueen|\bcolumn', cycle_text))
            rec.pattern = 'factorial' if permutation_like and rec.branch_factor >= 2 else 'mutual_recursive'
            rec.reduction_type = 'linear'
            rec.stack_depth = 'O(n)'
            return rec

        for fn_node in func_nodes:
            fn_name = ""
            declarator = fn_node.child_by_field_name('declarator')
            if declarator:
                for c in declarator.children:
                    if c.type in ['identifier', 'field_identifier']:
                        fn_name = c.text.decode('utf-8', errors='ignore') if isinstance(c.text, bytes) else str(c.text)
                        break
                if not fn_name and declarator.type in ['identifier', 'field_identifier']:
                    fn_name = declarator.text.decode('utf-8', errors='ignore') if isinstance(declarator.text, bytes) else str(declarator.text)

            # Python function definitions expose the name through the
            # ``name`` field rather than a C/C++-style declarator.  Without
            # this fallback, nested helpers such as ``backtrack`` are never
            # recognized as recursive and backtracking is understated as
            # linear time.
            if not fn_name:
                name_node = fn_node.child_by_field_name('name')
                if name_node:
                    fn_name = name_node.text.decode('utf-8', errors='ignore') if isinstance(name_node.text, bytes) else str(name_node.text)

            if not fn_name or fn_name in {'main', 'if', 'for', 'while'}:
                continue

            fn_text = fn_node.text.decode('utf-8', errors='ignore') if isinstance(fn_node.text, bytes) else str(fn_node.text)

            self_calls = []
            calls_inside_loop = False

            def find_calls(node):
                nonlocal calls_inside_loop
                # Tree-sitter names calls ``call_expression`` in C/C++/Java
                # and simply ``call`` in Python.  Treat both uniformly so
                # nested Python backtracking helpers are recognized.
                if node.type in {'call_expression', 'call'}:
                    func_expr = node.child_by_field_name('function') or (node.children[0] if node.children else None)
                    if func_expr:
                        call_name = func_expr.text.decode('utf-8', errors='ignore') if isinstance(func_expr.text, bytes) else str(func_expr.text)
                        if call_name == fn_name:
                            self_calls.append(node)
                            curr = node.parent
                            while curr:
                                if curr.type in loop_types:
                                    calls_inside_loop = True
                                    break
                                curr = curr.parent
                for child in node.children:
                    find_calls(child)

            find_calls(fn_node)

            if self_calls:
                rec.is_recursive = True

                # Determine mutual exclusivity vs simultaneous branching
                is_exclusive = False
                if len(self_calls) >= 2:
                    call1, call2 = self_calls[0], self_calls[1]

                    def get_if_ancestor(node):
                        curr = node.parent
                        prev = node
                        while curr:
                            if curr.type == 'if_statement':
                                return curr, prev
                            prev = curr
                            curr = curr.parent
                        return None, None

                    if1, child1 = get_if_ancestor(call1)
                    if2, child2 = get_if_ancestor(call2)

                    if if1 and if2 and if1.start_byte == if2.start_byte:
                        if child1.type != child2.type or (hasattr(child1, 'start_byte') and hasattr(child2, 'start_byte') and child1.start_byte != child2.start_byte):
                            is_exclusive = True
                    elif if1 and not if2:
                        if 'return' in (if1.text.decode('utf-8', errors='ignore') if isinstance(if1.text, bytes) else str(if1.text)):
                            is_exclusive = True
                    elif if2 and not if1:
                        if 'return' in (if2.text.decode('utf-8', errors='ignore') if isinstance(if2.text, bytes) else str(if2.text)):
                            is_exclusive = True

                rec.branch_factor = 1 if is_exclusive else len(self_calls)

                # Check graph context (Graph DFS with recursive call inside loop over edges/adj)
                # Only suppress calls_inside_loop for true graph DFS — NOT for permutation/backtracking
                # Permutation patterns use swap + recursion inside a loop => must keep calls_inside_loop
                has_swap = 'swap(' in fn_text or 'swap (' in fn_text
                is_graph_func = (
                    any(g in fn_text for g in ['vector<vector', 'adj', 'graph', 'vis', 'visited'])
                    and not has_swap
                )
                if is_graph_func:
                    calls_inside_loop = False

                rec.calls_inside_loop = calls_inside_loop

                div_count = 0
                sub_count = 0
                for call_node in self_calls:
                    args_text = call_node.text.decode('utf-8', errors='ignore') if isinstance(call_node.text, bytes) else str(call_node.text)
                    if '/ 2' in args_text or '/2' in args_text or '>> 1' in args_text:
                        div_count += 1
                    if '- 1' in args_text or '-1' in args_text or '- 2' in args_text:
                        sub_count += 1

                has_pivot_split = rec.branch_factor == 2 and ('-1' in fn_text or '- 1' in fn_text) and ('+1' in fn_text or '+ 1' in fn_text)
                has_dc_split = any(pattern in fn_text for pattern in ['(l + r) / 2', '(l+r)/2', 'mid =', 'm = (l', 'm=(l', 'pivot', 'partition']) or has_pivot_split
                if has_dc_split or div_count > 0:
                    rec.reduction_type = "divide"
                    rec.is_divide_and_conquer = True
                    rec.stack_depth = "O(log n)"
                else:
                    rec.reduction_type = "linear"
                    rec.stack_depth = "O(n)"

                is_path_compression = bool(re.search(rf'\bparent\[\w+\]\s*=\s*{fn_name}', fn_text)) or \
                                       bool(re.search(rf'\bpar\[\w+\]\s*=\s*{fn_name}', fn_text)) or \
                                       bool(re.search(rf'\bp\[\w+\]\s*=\s*{fn_name}', fn_text))

                if is_path_compression:
                    rec.pattern = "path_compression"
                elif any(m in fn_text for m in ['memo[', 'dp[', 'cache[']):
                    rec.has_memoization = True
                    rec.pattern = "memoized"
                elif calls_inside_loop:
                    rec.pattern = "factorial"
                elif rec.branch_factor >= 2:
                    rec.pattern = "branching"
                elif rec.reduction_type == "divide":
                    rec.pattern = "divide_and_conquer"
                else:
                    rec.pattern = "linear"

                return rec

        return self._regex_analysis().recursion

    def _extract_graph_features(self, root) -> GraphIR:
        """Extract graph features from AST."""
        graph = self._regex_analysis().graph
        src_lower = self.source.lower()
        if ('p[' in src_lower or 'parent[' in src_lower) and ('p[a]' in src_lower or 'p[b]' in src_lower or 'sz[' in src_lower or 'size[' in src_lower):
            graph.is_graph = True
            graph.structure = "edge_list"
        return graph
