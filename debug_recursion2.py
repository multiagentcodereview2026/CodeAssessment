import sys
import re
sys.path.append('/app')

from analysis.ast_parser import ASTComplexityAnalyzer

code = '''int f(vector<int>& a){int s=0;for(int i=0;i<a.size();i++) for(int j=0;j<a.size();j++) s+=a[i]+a[j];return s;}'''

# Create a custom version with debug prints
class DebugASTComplexityAnalyzer(ASTComplexityAnalyzer):
    def _regex_analysis(self):
        # Copy the original logic but with debug prints
        from analysis.complexity_ir import ComplexityIR
        ir = ComplexityIR(language=self.language, source=self.source)
        src = self.source.lower()

        print("=== RECURSION DETECTION DEBUG ===")

        # Find function names and check for recursive calls
        func_matches = list(re.finditer(r'\b(\w+)\s*\([^)]*\)\s*\{', src))
        print(f"Function matches: {len(func_matches)}")

        for i, func_match in enumerate(func_matches):
            func_name = func_match.group(1)
            print(f"\nFunction {i+1}: '{func_name}'")

            body_start = func_match.end()
            remaining_code = src[body_start:]
            print(f"  Remaining code: {remaining_code[:50]}...")

            # Look for actual function calls
            call_pattern = rf'\b{func_name}\s*\([^)]*\)'
            recursive_calls = list(re.finditer(call_pattern, remaining_code))
            call_count = len(recursive_calls)

            print(f"  Call count: {call_count}")
            print(f"  Before: is_recursive={ir.recursion.is_recursive}, branch_factor={ir.recursion.branch_factor}")

            if call_count > 0:
                print("  -> Setting is_recursive = True")
                ir.recursion.is_recursive = True
                ir.recursion.branch_factor = min(call_count, 4)
                ir.recursion.pattern = "linear"
                break
            else:
                print("  -> No recursive calls, continuing")

        print(f"\nFinal state: is_recursive={ir.recursion.is_recursive}, branch_factor={ir.recursion.branch_factor}")

        # Now call the parent method to get the full analysis
        return super()._regex_analysis()

# Test with debug version
analyzer = DebugASTComplexityAnalyzer(code)
ir = analyzer._regex_analysis()
print(f"\nFINAL RESULT: is_recursive={ir.recursion.is_recursive}, branch_factor={ir.recursion.branch_factor}")