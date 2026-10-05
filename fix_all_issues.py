# Comprehensive fix for all remaining issues
# Issues:
# 1. Nested Loops: TC O(n) not O(n²), SC O(n) not O(1) - recursion false positive
# 2. Quick Sort: SC O(log n) not O(n) - missing auxiliary array detection
# 3. Monotonic Stack/DP/Heap/Prefix Sum: SC O(1) not O(n) - dynamic allocation detection failing
# 4. DFS: TC O(n) not O(V+E) - graph detection failing
# 5. Matrix Traversal: TC O(n²) not O(m*n) - multiple bounds detection

import re
import sys
sys.path.append('.')
from backend.analysis.ast_parser import ASTComplexityAnalyzer
from backend.analysis.ast_engine import infer_complexity_from_ir

print("COMPREHENSIVE FIX FOR REMAINING ISSUES")
print("="*70)

# Fix 1: Nested Loops recursion false positive
print("\n1. FIXING NESTED LOOPS RECURSION FALSE POSITIVE")
code1='int f(int n){for(int i=0;i<n;i++){for(int j=0;j<n;j++){} }}'
ir1=ASTComplexityAnalyzer(code1).analyze()
print(f"Before fix - Recursive: {ir1.recursion.is_recursive}, Pattern: {ir1.recursion.pattern}")
print(f"Loop depth: {ir1.loop.depth}, structure: {ir1.loop.structure}")

# The issue might be that f(i) is being detected as recursive call
# Let's add debug to see what's happening
src1=code1.lower()
func_matches = list(re.finditer(r'\b(\w+)\s*\([^)]*\)\s*\{', src1))
if func_matches:
    func_name = func_matches[0].group(1)
    print(f"Function name: '{func_name}'")
    body_start = func_matches[0].end()
    remaining = src1[body_start:]
    print(f"Remaining code contains '{func_name}': '{func_name}' in remaining = {func_name in remaining}")

# Fix 2: Quick Sort space complexity
print("\n2. FIXING QUICK SORT SPACE COMPLEXITY")
code2='void f(vector<int>&a,int l,int r){if(l>=r)return;int p=a[r],i=l;for(int j=l;j<r;j++){if(a[j]<p)swap(a[i++],a[j]);}swap(a[i],a[r]);f(a,l,i-1);f(a,i+1,r);}'
ir2=ASTComplexityAnalyzer(code2).analyze()
print(f"Quick Sort D&C: {ir2.recursion.is_divide_and_conquer}")
print(f"Has auxiliary array: {ir2.recursion.has_auxiliary_array}")
print(f"Has dynamic allocation: {ir2.has_dynamic_allocation}")

# Fix 3: Dynamic allocation detection
print("\n3. TESTING DYNAMIC ALLOCATION DETECTION")
test_cases = [
    ('Monotonic Stack', 'vector<int> f(vector<int>&a){stack<int>s;for(int x:a){while(!s.empty()&&s.top()<x)s.pop();s.push(x);}return a;}'),
    ('DP', 'int f(vector<int>&a){int n=a.size();vector<int>dp(n+1);for(int i=1;i<=n;i++)dp[i]=dp[i-1]+a[i-1];return dp[n];}'),
    ('Heap', 'int f(vector<int>&a){priority_queue<int>pq;for(int x:a)pq.push(x);while(!pq.empty())pq.pop();return 0;}'),
    ('Prefix Sum', 'vector<int> f(vector<int>&a){vector<int>p(a.size());for(int i=0;i<a.size();i++)p[i]=a[i]+(i?p[i-1]:0);return p;}'),
]

for name, code in test_cases:
    ir = ASTComplexityAnalyzer(code).analyze()
    print(f"{name}: has_dynamic_allocation={ir.has_dynamic_allocation}")

# Fix 4: Graph detection for DFS
print("\n4. FIXING DFS GRAPH DETECTION")
code4='void f(Node*x){if(!x)return;for(Node*y:x->adj)f(y);}'
ir4=ASTComplexityAnalyzer(code4).analyze()
print(f"DFS - Is graph: {ir4.graph.is_graph}")
print(f"DFS - Recursive: {ir4.recursion.is_recursive}")

# Fix 5: Matrix Traversal multiple bounds
print("\n5. FIXING MATRIX TRAVERSAL")
code5='int f(vector<vector<int>>&a){int m=a.size(),n=a[0].size(),s=0;for(int i=0;i<m;i++)for(int j=0;j<n;j++)s+=a[i][j];return s;}'
ir5=ASTComplexityAnalyzer(code5).analyze()
print(f"Matrix Traversal - Multiple bounds: {ir5.loop.multiple_input_bounds}")
print(f"Matrix Traversal - Matrix bounds: {ir5.loop.has_matrix_bounds}")
print(f"Bounds variables detection: {ir5.loop.distinct_params if hasattr(ir5.loop, 'distinct_params') else 'N/A'}")