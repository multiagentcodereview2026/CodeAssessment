"""
Comprehensive fix for edge case algorithm detections
Issues to fix:
1. Sequential vs nested loops detection
2. Triple nested loops (depth=3)
3. 2D allocation detection
4. Triangular loop (geometric series) detection
5. Recursive binary search O(log n)
"""

import re
import sys
sys.path.append('.')
from backend.analysis.ast_parser import ASTComplexityAnalyzer
from backend.analysis.ast_engine import infer_complexity_from_ir

print("DEBUG: Analyzing specific failing edge cases...")
print("="*70)

# Test case 1: Sequential Loops
code1 = 'int f(vector<int>&a){int s=0;for(int x:a)s+=x;for(int x:a)s-=x;return s;}'
print("\n1. Sequential Loops Analysis:")
print(f"Code: {code1}")
ir1 = ASTComplexityAnalyzer(code1).analyze()
print(f"Loop depth: {ir1.loop.depth}")
print(f"Loop structure: {ir1.loop.structure}")
seq_pattern = re.search(r'for[^{]*\{[^}]*\}.*for', code1)
print(f"Has sequential loops pattern? {bool(seq_pattern)}")

# Test case 2: Triple Nested Loops
code2 = 'int f(int n){int s=0;for(int i=0;i<n;i++)for(int j=0;j<n;j++)for(int k=0;k<n;k++)s++;return s;}'
print("\n2. Triple Nested Loops Analysis:")
print(f"Code snippet: {code2}")
# Count 'for(' occurrences
for_count = len(re.findall(r'for\s*\(', code2.lower()))
print(f"'for(' count: {for_count}")
nest_pattern = re.search(r'for[^{]*\{[^}]*for[^{]*\{[^}]*for', code2)
print(f"Nesting detection: {bool(nest_pattern)}")

# Test case 3: 2D DP allocation
code3 = 'int f(int n){vector<vector<int>>dp(n,vector<int>(n));for(int i=0;i<n;i++)for(int j=0;j<n;j++)dp[i][j]=i+j;return dp[n-1][n-1];}'
print("\n3. 2D DP Allocation Analysis:")
print(f"Code: {code3}")
# Check for vector<vector pattern
has_vector_vector = bool(re.search(r'vector\s*<\s*vector\s*<', code3.lower()))
print(f"Has vector<vector>: {has_vector_vector}")
# Check local declaration
func_body = code3.lower().split('{', 1)[1] if '{' in code3.lower() else code3.lower()
vector_pattern = re.search(r'vector\s*<\s*vector\s*<[^>]+>\s*>\s+\w+\s*\(', func_body)
print(f"In function body: {bool(vector_pattern)}")

# Test case 4: Triangular Loop (geometric series)
code4 = 'int f(int n){int s=0;for(int i=n;i>0;i/=2)for(int j=0;j<i;j++)s++;return s;}'
print("\n4. Triangular Loop Analysis:")
print(f"Code: {code4}")
# Check for i/=2 pattern with inner loop
has_i_div_2 = bool(re.search(r'i\s*/=\s*2', code4.lower()))
has_j_lt_i = bool(re.search(r'j\s*<\s*i', code4.lower()))
print(f"Has i/=2: {has_i_div_2}")
print(f"Has j<i: {has_j_lt_i}")

# Test case 5: Recursive Binary Search
code5 = 'int f(vector<int>&a,int l,int r,int x){if(l>r)return -1;int m=l+(r-l)/2;if(a[m]==x)return m;if(a[m]<x)return f(a,m+1,r,x);return f(a,l,m-1,x);}'
print("\n5. Recursive Binary Search Analysis:")
print(f"Code snippet: {code5[:80]}...")
# Check for mid calculation pattern
has_mid_calc = bool(re.search(r'l\s*\+\s*\(\s*r\s*-\s*l\s*\)\s*/\s*2', code5.lower()))
has_l_gt_r = bool(re.search(r'l\s*>\s*r', code5.lower()))
print(f"Has mid = l + (r-l)/2: {has_mid_calc}")
print(f"Has l>r base case: {has_l_gt_r}")