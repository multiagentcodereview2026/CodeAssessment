import re
import sys
sys.path.append('/app')
from analysis.ast_parser import ASTComplexityAnalyzer
from analysis.ast_engine import infer_complexity_from_ir

# Test the 6 remaining failures
fail_cases = [
    ('Merge Sort', 'void f(vector<int>& a,int l,int r){if(l>=r) return;int m=(l+r)/2;f(a,l,m);f(a,m+1,r);vector<int> t;int i=l,j=m+1;while(i<=m && j<=r){if(a[i]<a[j]) t.push_back(a[i++]);else t.push_back(a[j++]);}while(i<=m) t.push_back(a[i++]);while(j<=r) t.push_back(a[j++]);}', 'O(n log n)', 'O(n)'),
    ('Quick Sort', 'void f(vector<int>& a,int l,int r){if(l>=r) return;int p=a[r];int i=l;for(int j=l;j<r;j++){if(a[j]<p) swap(a[i++],a[j]);}swap(a[i],a[r]);f(a,l,i-1);f(a,i+1,r);}', 'O(n log n)', 'O(n)'),
    ('Memoization', 'int f(int n,vector<int>& dp){if(n<=1) return n;if(dp[n]!=-1) return dp[n];return dp[n]=f(n-1,dp)+f(n-2,dp);}', 'O(n)', 'O(n)'),
    ('Heap', 'int f(vector<int>& a){priority_queue<int> pq;for(int x:a) pq.push(x);int ans=0;while(!pq.empty()){ans+=pq.top();pq.pop();}return ans;}', 'O(n log n)', 'O(n)'),
    ('Matrix Traversal', 'int f(vector<vector<int>>& a){int s=0;for(int i=0;i<a.size();i++) for(int j=0;j<a[i].size();j++) s+=a[i][j];return s;}', 'O(m*n)', 'O(1)'),
    ('Divide and Conquer', 'int f(vector<int>& a,int l,int r){if(l==r) return a[l];int m=(l+r)/2;int x=f(a,l,m);int y=f(a,m+1,r);return max(x,y);}', 'O(n)', 'O(log n)'),
]

print("DEBUG REMAINING FAILURES:")
print("="*70)

for name, code, exp_t, exp_s in fail_cases:
    ir = ASTComplexityAnalyzer(code).analyze()
    r = infer_complexity_from_ir(ir)

    print(f"\n{name}:")
    print(f"  Recursive: {ir.recursion.is_recursive}")
    print(f"  Branch factor: {ir.recursion.branch_factor}")
    print(f"  Pattern: {ir.recursion.pattern}")
    print(f"  Is D&C: {ir.recursion.is_divide_and_conquer}")
    print(f"  Loop depth: {ir.loop.depth}")
    print(f"  Loop structure: {ir.loop.structure}")
    print(f"  Has heap ops: {ir.has_heap_operations}")
    print(f"  TC: {r.time_complexity} (expected {exp_t})")
    print(f"  SC: {r.space_complexity} (expected {exp_s})")