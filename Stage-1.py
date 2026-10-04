import sys
sys.path.append(".")

from backend.analysis.ast_parser import ASTComplexityAnalyzer
from backend.analysis.ast_engine import infer_complexity_from_ir


def norm(s):
    return (
        str(s)
        .replace(" ", "")
        .replace("*", "")
        .replace("×", "")
        .lower()
    )


tests = [

    # ============================================================
    # O(1)
    # ============================================================

    [
        "Constant",
        "int f(int n){int x=10;return x;}",
        "O(1)",
        "O(1)"
    ],

    # ============================================================
    # O(log n)
    # ============================================================

    [
        "Logarithmic",
        "int f(int n){int x=1;while(x<n)x*=2;return x;}",
        "O(log n)",
        "O(1)"
    ],

    # ============================================================
    # O(n)
    # ============================================================

    [
        "Linear",
        "int f(int n){int s=0;for(int i=0;i<n;i++)s+=i;return s;}",
        "O(n)",
        "O(1)"
    ],

    # ============================================================
    # O(n) - while
    # ============================================================

    [
        "Linear While",
        "int f(int n){int i=0;while(i<n){i++;}return i;}",
        "O(n)",
        "O(1)"
    ],

    # ============================================================
    # O(n)
    # Sequential loops
    # ============================================================

    [
        "Sequential Loops",
        "int f(int n){int s=0;for(int i=0;i<n;i++)s++;for(int i=0;i<n;i++)s++;return s;}",
        "O(n)",
        "O(1)"
    ],

    # ============================================================
    # O(n log n)
    # ============================================================

    [
        "N Log N",
        "int f(int n){int s=0;for(int i=0;i<n;i++){int x=n;while(x>1){x/=2;s++;}}return s;}",
        "O(n log n)",
        "O(1)"
    ],

    # ============================================================
    # O(n^2)
    # ============================================================

    [
        "Nested Loops",
        "int f(int n){int s=0;for(int i=0;i<n;i++)for(int j=0;j<n;j++)s++;return s;}",
        "O(n^2)",
        "O(1)"
    ],

    # ============================================================
    # O(n^3)
    # ============================================================

    [
        "Triple Nested",
        "int f(int n){int s=0;for(int i=0;i<n;i++)for(int j=0;j<n;j++)for(int k=0;k<n;k++)s++;return s;}",
        "O(n^3)",
        "O(1)"
    ],

    # ============================================================
    # O(log n) recursive
    # ============================================================

    [
        "Recursive Log",
        "int f(int n){if(n<=1)return 1;return f(n/2)+1;}",
        "O(log n)",
        "O(log n)"
    ],

    # ============================================================
    # O(n) recursive
    # ============================================================

    [
        "Recursive Linear",
        "int f(int n){if(n<=1)return 1;return f(n-1)+1;}",
        "O(n)",
        "O(n)"
    ],

    # ============================================================
    # O(2^n)
    # ============================================================

    [
        "Binary Recursion",
        "int f(int n){if(n<=1)return 1;return f(n-1)+f(n-1);}",
        "O(2^n)",
        "O(n)"
    ],

    # ============================================================
    # O(n!)
    # ============================================================

    [
        "Factorial Recursion",
        "int f(int n){if(n<=1)return 1;int s=0;for(int i=0;i<n;i++)s+=f(n-1);return s;}",
        "O(n!)",
        "O(n)"
    ],

    # ============================================================
    # O(n) space
    # ============================================================

    [
        "Linear Space",
        "vector<int> f(int n){vector<int>a(n);for(int i=0;i<n;i++)a[i]=i;return a;}",
        "O(n)",
        "O(n)"
    ],

    # ============================================================
    # O(n^2) space
    # ============================================================

    [
        "Quadratic Space",
        "vector<vector<int>> f(int n){vector<vector<int>>a(n,vector<int>(n));return a;}",
        "O(n^2)",
        "O(n^2)"
    ],

    # ============================================================
    # O(1) space
    # ============================================================

    [
        "Constant Space",
        "int f(vector<int>&a){int s=0;for(int x:a)s+=x;return s;}",
        "O(n)",
        "O(1)"
    ],

    # ============================================================
    # Binary Search
    # ============================================================

    [
        "Binary Search",
        "int f(vector<int>&a,int x){int l=0,r=a.size()-1;while(l<=r){int m=(l+r)/2;if(a[m]==x)return m;if(a[m]<x)l=m+1;else r=m-1;}return -1;}",
        "O(log n)",
        "O(1)"
    ],

    # ============================================================
    # Two sequential operations
    # ============================================================

    [
        "Linear + Constant",
        "int f(vector<int>&a){int s=0;for(int x:a)s+=x;int x=10;return s+x;}",
        "O(n)",
        "O(1)"
    ],

    # ============================================================
    # Nested loop with constant inner work
    # ============================================================

    [
        "Nested Dependent",
        "int f(int n){int s=0;for(int i=0;i<n;i++)for(int j=0;j<=i;j++)s++;return s;}",
        "O(n^2)",
        "O(1)"
    ],

    # ============================================================
    # Array allocation
    # ============================================================

    [
        "Array Allocation",
        "int* f(int n){int* a=new int[n];for(int i=0;i<n;i++)a[i]=i;return a;}",
        "O(n)",
        "O(n)"
    ],

    # ============================================================
    # Recursion + loop
    # ============================================================

    [
        "Recursive Loop",
        "int f(int n){if(n<=1)return 1;for(int i=0;i<n;i++){}return f(n-1);}",
        "O(n^2)",
        "O(n)"
    ],
]


passed = 0
failed = 0


print("=" * 100)
print("PHASE-1 BASIC COMPLEXITY VERIFICATION")
print("=" * 100)


for name, code, expected_tc, expected_sc in tests:

    try:
        analyzer = ASTComplexityAnalyzer(code)
        ir = analyzer.analyze()

        result = infer_complexity_from_ir(ir)

        actual_tc = result.time_complexity
        actual_sc = result.space_complexity

        tc_ok = norm(actual_tc) == norm(expected_tc)
        sc_ok = norm(actual_sc) == norm(expected_sc)

        ok = tc_ok and sc_ok

        if ok:
            passed += 1
        else:
            failed += 1

        print(
            f"{'PASS' if ok else 'FAIL'} | "
            f"{name:<24} | "
            f"TC: {str(actual_tc):<16} / {expected_tc:<12} | "
            f"SC: {str(actual_sc):<10} / {expected_sc}"
        )

    except Exception as e:
        failed += 1

        print(
            f"ERROR | "
            f"{name:<24} | "
            f"{type(e).__name__}: {e}"
        )


total = len(tests)

print("=" * 100)
print(f"TOTAL:      {total}")
print(f"PASSED:     {passed}")
print(f"FAILED:     {failed}")
print(f"PASS RATE:  {passed * 100 / total:.2f}%")
print("=" * 100)