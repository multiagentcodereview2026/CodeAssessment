# Simple test for nested loops
test_code = '''int f(vector<int>& a){int s=0;for(int i=0;i<a.size();i++) for(int j=0;j<a.size();j++) s+=a[i]+a[j];return s;}'''

print("Testing nested loops...")
print("Code:", test_code)
print()

# Docker test command
docker_cmd = f'''docker exec codeassessment-backend-1 python3 -c "from analysis.ast_parser import ASTComplexityAnalyzer;from analysis.ast_engine import infer_complexity_from_ir;ir=ASTComplexityAnalyzer('{test_code}').analyze();r=infer_complexity_from_ir(ir);print('Loop depth:',ir.loop.depth);print('Loop structure:',ir.loop.structure);print('Time complexity:',r.time_complexity);print('Expected: O(n^2)');print('Result:','PASS' if str(r.time_complexity)=='O(n^2)' else 'FAIL')"'''

print("Run this command:")
print(docker_cmd)