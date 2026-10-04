import sys
sys.path.append(".")

from backend.analysis.ast_parser import ASTComplexityAnalyzer
from backend.analysis.ast_engine import infer_complexity_from_ir


def norm(s):
    return str(s).replace(" ", "").lower().replace("*", "").replace("×", "")


tests = [

    # 1. Nested loops with dependent bounds
    [
        "Dependent Nested",
        "int f(int n){int s=0;for(int i=0;i<n;i++)for(int j=0;j<=i;j++)s++;return s;}",
        "O(n^2)", "O(1)"
    ],

    # 2. Reverse nested loops
    [
        "Reverse Nested",
        "int f(int n){int s=0;for(int i=n;i>0;i--)for(int j=0;j<i;j++)s++;return s;}",
        "O(n^2)", "O(1)"
    ],

    # 3. Three nested loops with different variables
    [
        "Triple Nested",
        "int f(int n){int s=0;for(int i=0;i<n;i++)for(int j=0;j<n;j++)for(int k=0;k<n;k++)s++;return s;}",
        "O(n^3)", "O(1)"
    ],

    # 4. Sequential loops
    [
        "Sequential",
        "int f(vector<int>&a){int s=0;for(int x:a)s+=x;for(int x:a)s-=x;for(int x:a)s+=x;return s;}",
        "O(n)", "O(1)"
    ],

    # 5. Loop with logarithmic inner loop
    [
        "N Log N",
        "int f(int n){int s=0;for(int i=0;i<n;i++){int x=n;while(x>1){x/=2;s++;}}return s;}",
        "O(n log n)", "O(1)"
    ],

    # 6. Nested logarithmic loops
    [
        "Log Squared",
        "int f(int n){int s=0;for(int i=1;i<n;i*=2)for(int j=1;j<n;j*=2)s++;return s;}",
        "O(log^2 n)", "O(1)"
    ],

    # 7. Recursive divide and conquer
    [
        "Divide Recursion",
        "int f(int n){if(n<=1)return 1;return f(n/2)+f(n/2);}",
        "O(n)", "O(log n)"
    ],

    # 8. Single recursive branch
    [
        "Single Recursion",
        "int f(int n){if(n<=1)return 1;return f(n-1)+1;}",
        "O(n)", "O(n)"
    ],

    # 9. Tail recursion
    [
        "Tail Recursion",
        "int f(int n,int s){if(n==0)return s;return f(n-1,s+n);}",
        "O(n)", "O(n)"
    ],

    # 10. Binary search recursion
    [
        "Recursive Binary Search",
        "int f(vector<int>&a,int l,int r,int x){if(l>r)return -1;int m=(l+r)/2;if(a[m]==x)return m;if(a[m]<x)return f(a,m+1,r,x);return f(a,l,m-1,x);}",
        "O(log n)", "O(log n)"
    ],

    # 11. Explicit stack
    [
        "Stack Growth",
        "int f(vector<int>&a){stack<int>s;for(int x:a)s.push(x);return s.size();}",
        "O(n)", "O(n)"
    ],

    # 12. Queue growth
    [
        "Queue Growth",
        "int f(vector<int>&a){queue<int>q;for(int x:a)q.push(x);return q.size();}",
        "O(n)", "O(n)"
    ],

    # 13. Vector allocation
    [
        "Dynamic Array",
        "vector<int> f(int n){vector<int>a;for(int i=0;i<n;i++)a.push_back(i);return a;}",
        "O(n)", "O(n)"
    ],

    # 14. 2D allocation
    [
        "2D Allocation",
        "vector<vector<int>> f(int n){vector<vector<int>>a(n,vector<int>(n));return a;}",
        "O(n^2)", "O(n^2)"
    ],

    # 15. Monotonic stack variant
    [
        "Monotonic Stack Variant",
        "vector<int> f(vector<int>&a){vector<int>r(a.size(),-1);stack<int>s;for(int i=0;i<a.size();i++){while(!s.empty()&&a[s.top()]<a[i]){r[s.top()]=a[i];s.pop();}s.push(i);}return r;}",
        "O(n)", "O(n)"
    ],

    # 16. Hash map with two passes
    [
        "Hash Two Pass",
        "int f(vector<int>&a){unordered_map<int,int>m;for(int x:a)m[x]++;int s=0;for(auto&p:m)s+=p.second;return s;}",
        "O(n)", "O(n)"
    ],

    # 17. Heap construction + extraction
    [
        "Heap Variant",
        "int f(vector<int>&a){priority_queue<int>q(a.begin(),a.end());int s=0;while(!q.empty()){s+=q.top();q.pop();}return s;}",
        "O(n log n)", "O(n)"
    ],

    # 18. BFS with adjacency list
    [
        "BFS Variant",
        "void f(vector<vector<int>>&g){queue<int>q;vector<int>v(g.size());q.push(0);v[0]=1;while(!q.empty()){int u=q.front();q.pop();for(int x:g[u])if(!v[x])v[x]=1,q.push(x);}}",
        "O(V+E)", "O(V)"
    ],

    # 19. DFS iterative
    [
        "Iterative DFS",
        "void f(vector<vector<int>>&g){stack<int>s;vector<int>v(g.size());s.push(0);while(!s.empty()){int u=s.top();s.pop();if(v[u])continue;v[u]=1;for(int x:g[u])if(!v[x])s.push(x);}}",
        "O(V+E)", "O(V)"
    ],

    # 20. Prefix sum with output
    [
        "Prefix Variant",
        "vector<int> f(vector<int>&a){vector<int>p;int s=0;for(int x:a){s+=x;p.push_back(s);}return p;}",
        "O(n)", "O(n)"
    ],

    # 21. Matrix traversal
    [
        "Matrix Variant",
        "int f(vector<vector<int>>&a){int s=0;for(auto&row:a)for(int x:row)s+=x;return s;}",
        "O(m*n)", "O(1)"
    ],

    # 22. String nested comparison
    [
        "String Compare",
        "bool f(string&a,string&b){for(int i=0;i<a.size();i++)for(int j=0;j<b.size();j++)if(a[i]==b[j])return true;return false;}",
        "O(n*m)", "O(1)"
    ],

    # 23. Sorting + linear scan
    [
        "Sort Scan Variant",
        "int f(vector<int>&a){stable_sort(a.begin(),a.end());int s=0;for(int x:a)s+=x;return s;}",
        "O(n log n)", "O(1)"
    ],

    # 24. GCD variant
    [
        "GCD Variant",
        "int f(int a,int b){while(a!=b){if(a>b)a-=b;else b-=a;}return a;}",
        "O(n)", "O(1)"
    ],

    # 25. Bit loop
    [
        "Bit Shift",
        "int f(int n){int c=0;while(n>0){n>>=1;c++;}return c;}",
        "O(log n)", "O(1)"
    ]
]


passed = 0
failed = 0

print("=" * 100)
print("STAGE-4 ROBUSTNESS / EDGE-CASE VERIFICATION")
print("=" * 100)

for name, code, expected_tc, expected_sc in tests:

    try:
        ir = ASTComplexityAnalyzer(code).analyze()
        result = infer_complexity_from_ir(ir)

        actual_tc = norm(result.time_complexity)
        actual_sc = norm(result.space_complexity)

        ok = (
            actual_tc == norm(expected_tc)
            and actual_sc == norm(expected_sc)
        )

        if ok:
            passed += 1
        else:
            failed += 1

        print(
            f"{'PASS' if ok else 'FAIL'} | "
            f"{name:<25} | "
            f"TC: {str(result.time_complexity):<18} / {expected_tc:<15} | "
            f"SC: {str(result.space_complexity):<10} / {expected_sc}"
        )

    except Exception as e:
        failed += 1
        print(f"ERROR | {name:<25} | {e}")


total = len(tests)

print("=" * 100)
print(f"TOTAL:      {total}")
print(f"PASSED:     {passed}")
print(f"FAILED:     {failed}")
print(f"PASS RATE:  {passed * 100 / total:.2f}%")
print("=" * 100)