    def _detect_heap_operations(self) -> bool:
        """Detect priority queue / heap operations that add O(log n) factor."""
        src = self.source.lower()

        heap_patterns = [
            r"priority_queue\s*<[^>]*>\s*\w+",
            r"\.push\s*\(",
            r"\.pop\s*\(",
            r"\.top\s*\(",
            r"make_heap\s*\(",
            r"push_heap\s*\(",
            r"pop_heap\s*\(",
            r"heappush\s*\(",
            r"heappop\s*\(",
        ]
        return any(re.search(p, src) for p in heap_patterns)

    def _detect_matrix_bounds(self) -> bool:
        """Detect matrix operations with distinct m*n bounds."""
        src = self.source.lower()

        # Look for nested loops with different bounds like a.size() and a[i].size()
        has_matrix_access = bool(re.search(r"a\[\s*i\s*\]\.\s*size\s*\(\)", src)) or \
                           bool(re.search(r"matrix\[\s*i\s*\]\.\s*size\s*\(\)", src)) or \
                           bool(re.search(r"grid\[\s*i\s*\]\.\s*size\s*\(\)", src))

        # Look for explicit m*n parameters or bounds
        has_mn_params = bool(re.search(r"\bm\b.*\bn\b", src)) or \
                       bool(re.search(r"rows.*cols", src))

        return has_matrix_access or has_mn_params

    def _detect_union_find_operations(self) -> bool:
        """Detect Union-Find operations with inverse Ackermann complexity."""
        src = self.source.lower()

        uf_patterns = [
            r"find\s*\(\s*\w+\s*,\s*\w+\s*\)",
            r"union\s*\(\s*\w+\s*,\s*\w+\s*\)",
            r"unite\s*\(\s*\w+\s*,\s*\w+\s*\)",
            r"p\[\s*x\s*\]\s*=\s*find\s*\(\s*p\s*,\s*p\[\s*x\s*\]", # Path compression
            r"rank\[\s*\w+\s*\]", # Union by rank
        ]
        return any(re.search(p, src) for p in uf_patterns)