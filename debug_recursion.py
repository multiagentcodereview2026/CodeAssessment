import sys
import re
sys.path.append('/app')

from analysis.complexity_ir import ComplexityIR, LoopIR, RecursionIR

# Manual test of the recursion logic
code = '''int f(vector<int>& a){int s=0;for(int i=0;i<a.size();i++) for(int j=0;j<a.size();j++) s+=a[i]+a[j];return s;}'''
src = code.lower()

print("MANUAL RECURSION DETECTION TEST:")
print("Source:", src)
print()

# Create a fresh IR
ir = ComplexityIR(language='cpp', source=code)
print("Initial recursion state:")
print(f"  is_recursive: {ir.recursion.is_recursive}")
print(f"  branch_factor: {ir.recursion.branch_factor}")
print()

# Manually run the recursion detection logic
func_matches = list(re.finditer(r'\b(\w+)\s*\([^)]*\)\s*\{', src))
print(f"Function matches found: {len(func_matches)}")

for func_match in func_matches:
    func_name = func_match.group(1)
    print(f"\nProcessing function: '{func_name}'")

    body_start = func_match.end()
    remaining_code = src[body_start:]
    print(f"Remaining code: {remaining_code[:50]}...")

    # Look for actual function calls
    call_pattern = rf'\b{func_name}\s*\([^)]*\)'
    recursive_calls = list(re.finditer(call_pattern, remaining_code))
    call_count = len(recursive_calls)

    print(f"Call pattern: {call_pattern}")
    print(f"Recursive calls found: {call_count}")

    if call_count > 0:
        print("Setting is_recursive = True")
        ir.recursion.is_recursive = True
        ir.recursion.branch_factor = min(call_count, 4)
        break
    else:
        print("No recursive calls - is_recursive remains False")

print()
print("Final recursion state:")
print(f"  is_recursive: {ir.recursion.is_recursive}")
print(f"  branch_factor: {ir.recursion.branch_factor}")