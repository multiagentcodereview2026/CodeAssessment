"""
Test suite for the 30 previously failed complexity detection cases.
This validates the enhanced static analyzer fixes.
"""
import pytest
from analysis.static_analyzer_v2 import analyze_cpp as analyze_cpp_enhanced


# ═══════════════════════════════════════════════════════════════════════════
# ARRAY & STRING PATTERNS
# ═══════════════════════════════════════════════════════════════════════════

def test_array_two_pass():
    """Two independent sequential loops: O(n) + O(n) = O(n)"""
    code = """
    int f(vector<int>& a) {
        int sum = 0;
        for (int x : a) sum += x;
        int maxv = 0;
        for (int x : a) maxv = max(maxv, x);
        return sum + maxv;
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(1)"


def test_string_reverse():
    """String reversal with swap: O(n) time, O(n) space"""
    code = """
    void f(string& s) {
        int l = 0, r = s.size() - 1;
        while (l < r) {
            swap(s[l], s[r]);
            l++; r--;
        }
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(n)"


def test_binary_search():
    """Binary search: O(log n)"""
    code = """
    int f(vector<int>& a, int target) {
        int low = 0, right = a.size() - 1;
        while (low <= right) {
            int mid = (low + right) / 2;
            if (a[mid] < target) low = mid + 1;
            else right = mid - 1;
        }
        return -1;
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(log n)"
    assert result.space_complexity == "O(1)"


def test_bubble_sort():
    """Bubble sort: O(n^2)"""
    code = """
    void f(vector<int>& a) {
        for (int i = 0; i < a.size(); i++) {
            for (int j = 0; j < a.size() - i - 1; j++) {
                if (a[j] > a[j+1]) swap(a[j], a[j+1]);
            }
        }
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(n^2)"
    assert result.space_complexity == "O(1)"


# ═══════════════════════════════════════════════════════════════════════════
# RECURSION & BACKTRACKING
# ═══════════════════════════════════════════════════════════════════════════

def test_dp_fib_memo():
    """Memoized fibonacci: O(n) not O(2^n)"""
    code = """
    int f(int n, vector<int>& dp) {
        if (n <= 1) return n;
        if (dp[n] != -1) return dp[n];
        return dp[n] = f(n-1, dp) + f(n-2, dp);
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"


def test_permutations():
    """Permutations backtracking: O(n*n!)"""
    code = """
    void f(vector<int>& a, int l) {
        if (l == a.size()) return;
        for (int i = l; i < a.size(); i++) {
            swap(a[l], a[i]);
            f(a, l+1);
            swap(a[l], a[i]);
        }
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(n!)"
    assert result.space_complexity == "O(n)"


def test_combination_sum():
    """Combination sum: O(2^n)"""
    code = """
    void f(vector<int>& a, int t, int i) {
        if (t == 0) return;
        if (i == a.size()) return;
        for (int j = i; j < a.size(); j++)
            if (a[j] <= t) f(a, t - a[j], j);
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(2^n)"
    assert result.space_complexity == "O(n)"


def test_n_queens():
    """N-Queens: O(n!)"""
    code = """
    bool f(vector<string>& b, int r) {
        if (r == b.size()) return true;
        for (int c = 0; c < b.size(); c++) {
            if (b[r][c] == 0) {
                b[r][c] = 1;
                if (f(b, r+1)) return true;
                b[r][c] = 0;
            }
        }
        return false;
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(n!)"


# ═══════════════════════════════════════════════════════════════════════════
# GRAPH ALGORITHMS
# ═══════════════════════════════════════════════════════════════════════════

def test_graph_dfs():
    """Graph DFS with adjacency list: O(V+E)"""
    code = """
    void dfs(int u, vector<vector<int>>& g, vector<int>& v) {
        v[u] = 1;
        for (int x : g[u])
            if (!v[x]) dfs(x, g, v);
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(V+E)"
    assert result.space_complexity == "O(V)"


def test_graph_bfs():
    """Graph BFS: O(V+E)"""
    code = """
    void bfs(int s, vector<vector<int>>& g) {
        queue<int> q;
        q.push(s);
        vector<int> v(g.size());
        v[s] = 1;
        while (!q.empty()) {
            int u = q.front();
            q.pop();
            for (int x : g[u])
                if (!v[x]) {
                    v[x] = 1;
                    q.push(x);
                }
        }
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(V+E)"
    assert result.space_complexity == "O(V)"


# ═══════════════════════════════════════════════════════════════════════════
# GREEDY ALGORITHMS
# ═══════════════════════════════════════════════════════════════════════════

def test_activity_selection():
    """Activity selection with sort: O(n log n)"""
    code = """
    int f(vector<pair<int,int>>& a) {
        sort(a.begin(), a.end());
        int cnt = 0, last = -1;
        for (auto x : a)
            if (x.first >= last) {
                cnt++;
                last = x.second;
            }
        return cnt;
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(n log n)"
    assert result.space_complexity == "O(1)"


def test_candy():
    """Candy distribution (two passes): O(n)"""
    code = """
    int f(vector<int>& a) {
        int n = a.size();
        vector<int> c(n, 1);
        for (int i = 1; i < n; i++)
            if (a[i] > a[i-1]) c[i] = c[i-1] + 1;
        for (int i = n-2; i >= 0; i--)
            if (a[i] > a[i+1]) c[i] = max(c[i], c[i+1] + 1);
        return accumulate(c.begin(), c.end(), 0);
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(n)"


def test_partition_labels():
    """Partition labels (two passes): O(n)"""
    code = """
    vector<int> f(string& s) {
        vector<int> last(26);
        for (int i = 0; i < s.size(); i++)
            last[s[i] - 97] = i;
        vector<int> r;
        int end = 0, start = 0;
        for (int i = 0; i < s.size(); i++) {
            end = max(end, last[s[i] - 97]);
            if (i == end) {
                r.push_back(i - start + 1);
                start = i + 1;
            }
        }
        return r;
    }
    """
    result = analyze_cpp_enhanced(code)
    assert result.time_complexity == "O(n)"
    assert result.space_complexity == "O(1)"


# ═══════════════════════════════════════════════════════════════════════════
# Run all tests
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Running enhanced complexity analyzer tests...")
    print("\n=== ARRAY & STRING PATTERNS ===")
    test_array_two_pass()
    print("✓ ARRAY_TWO_PASS")
    test_string_reverse()
    print("✓ STRING_REVERSE")
    test_binary_search()
    print("✓ BINARY_SEARCH")
    test_bubble_sort()
    print("✓ BUBBLE_SORT")

    print("\n=== RECURSION & BACKTRACKING ===")
    test_dp_fib_memo()
    print("✓ DP_FIB_MEMO")
    test_permutations()
    print("✓ PERMUTATIONS")
    test_combination_sum()
    print("✓ COMBINATION_SUM")
    test_n_queens()
    print("✓ N_QUEENS")

    print("\n=== GRAPH ALGORITHMS ===")
    test_graph_dfs()
    print("✓ GRAPH_DFS")
    test_graph_bfs()
    print("✓ GRAPH_BFS")

    print("\n=== GREEDY ALGORITHMS ===")
    test_activity_selection()
    print("✓ ACTIVITY_SELECTION")
    test_candy()
    print("✓ CANDY")
    test_partition_labels()
    print("✓ PARTITION_LABELS")

    print("\n✅ All enhanced analyzer tests passed!")
