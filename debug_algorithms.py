# Diagnostic script to debug algorithm detection
import sys
sys.path.append('.')  # Add current directory to path

from analysis.ast_parser import ASTComplexityAnalyzer
from analysis.ast_engine import infer_complexity_from_ir

def debug_algorithm(name, code):
    print(f'\n{"="*60}')
    print(f'DEBUG: {name}')
    print(f'{"="*60}')
    print(f'Code: {code[:100]}...' if len(code) > 100 else f'Code: {code}')

    try:
        # Get IR analysis
        ir = ASTComplexityAnalyzer(code).analyze()

        print(f'\n--- IR DETECTION RESULTS ---')
        print(f'Language: {ir.language}')
        print(f'Source length: {len(ir.source)}')

        # Loop detection
        print(f'\nLOOP ANALYSIS:')
        print(f'  Depth: {ir.loop.depth}')
        print(f'  Structure: {ir.loop.structure}')
        print(f'  Has binary search: {ir.loop.has_binary_search}')
        print(f'  Has sort: {ir.loop.has_sort}')
        print(f'  Is logarithmic step: {ir.loop.is_logarithmic_step}')
        print(f'  Multiple input bounds: {ir.loop.multiple_input_bounds}')
        print(f'  Has heap operations: {ir.loop.has_heap_operations}')
        print(f'  Has matrix bounds: {ir.loop.has_matrix_bounds}')

        # Space complexity patterns
        print(f'\nSPACE ANALYSIS:')
        print(f'  Has dynamic allocation: {ir.has_dynamic_allocation}')
        print(f'  Has 2D allocation: {ir.has_2d_allocation}')
        print(f'  Is constant lookup: {ir.is_constant_lookup}')

        # Recursion and graph
        print(f'\nOTHER ANALYSIS:')
        print(f'  Is recursive: {ir.recursion.is_recursive}')
        print(f'  Is graph: {ir.graph.is_graph}')
        print(f'  Graph structure: {ir.graph.structure}')

        # Get final complexity
        result = infer_complexity_from_ir(ir)
        print(f'\nFINAL COMPLEXITY:')
        print(f'  Time: {result.time_complexity}')
        print(f'  Space: {result.space_complexity}')

    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()

# Test cases that are failing
test_cases = [
    ('Linear Scan', '''int f(vector<int>& a){int s=0;for(int x:a) s+=x;return s;}'''),
    ('Nested Loops', '''int f(vector<int>& a){int s=0;for(int i=0;i<a.size();i++) for(int j=0;j<a.size();j++) s+=a[i]+a[j];return s;}'''),
    ('Binary Search', '''int f(vector<int>& a,int x){int l=0,r=a.size()-1;while(l<=r){int m=l+(r-l)/2;if(a[m]==x) return m;if(a[m]<x) l=m+1;else r=m-1;}return -1;}'''),
    ('Heap', '''int f(vector<int>& a){priority_queue<int> pq;for(int x:a) pq.push(x);int ans=0;while(!pq.empty()){ans+=pq.top();pq.pop();}return ans;}'''),
    ('Fixed Size Array', '''int f(string s){int cnt[26]={0};for(char c:s) cnt[c-'a']++;return cnt[0];}'''),
]

print('COMPREHENSIVE ALGORITHM DEBUGGING')
print('='*60)

for name, code in test_cases:
    debug_algorithm(name, code)

print(f'\n{"="*60}')
print('DIAGNOSTIC COMPLETE')
print('='*60)