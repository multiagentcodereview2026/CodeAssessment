import sys
sys.path.append(".")

from backend.analysis.ast_parser import ASTComplexityAnalyzer
from backend.analysis.ast_engine import infer_complexity_from_ir


def norm(s):
    return str(s).replace(" ", "").lower().replace("*", "").replace("×", "")


tests = [

    # Arrays / strings
    ["Array Maximum",
     "int f(vector<int>&a){int mx=a[0];for(int x:a)mx=max(mx,x);return mx;}",
     "O(n)", "O(1)"],

    ["String Frequency",
     "int f(string s){int cnt[26]={0};for(char c:s)cnt[c-'a']++;return cnt[0];}",
     "O(n)", "O(1)"],

    ["Prefix + Query",
     "int f(vector<int>&a,int l,int r){vector<int>p(a.size()+1);for(int i=0;i<a.size();i++)p[i+1]=p[i]+a[i];return p[r+1]-p[l];}",
     "O(n)", "O(n)"],

    # Sorting variants
    ["Counting Sort",
     "void f(vector<int>&a){int c[101]={0};for(int x:a)c[x]++;int k=0;for(int i=0;i<=100;i++)while(c[i]--)a[k++]=i;}",
     "O(n)", "O(1)"],

    ["Heap Sort",
     "void f(vector<int>&a){priority_queue<int>q;for(int x:a)q.push(x);for(int i=a.size()-1;i>=0;i--){a[i]=q.top();q.pop();}}",
     "O(n log n)", "O(n)"],

    # Recursion
    ["Divide And Conquer",
     "int f(vector<int>&a,int l,int r){if(l==r)return a[l];int m=(l+r)/2;return max(f(a,l,m),f(a,m+1,r));}",
     "O(n)", "O(log n)"],

    ["Power Recursion",
     "long long f(long long a,long long n){if(n==0)return 1;if(n%2==0){long long x=f(a,n/2);return x*x;}return a*f(a,n-1);}",
     "O(log n)", "O(log n)"],

    # Backtracking
    ["Permutation Backtracking",
     "void f(vector<int>&a,int i){if(i==a.size())return;for(int j=i;j<a.size();j++){swap(a[i],a[j]);f(a,i+1);swap(a[i],a[j]);}}",
     "O(n!)", "O(n)"],

    ["Combination Backtracking",
     "void f(int n,int k,int start,vector<int>&cur){if(cur.size()==k)return;for(int i=start;i<=n;i++){cur.push_back(i);f(n,k,i+1,cur);cur.pop_back();}}",
     "O(n^k)", "O(k)"],

    # Stack / Queue
    ["Stack Matching",
     "bool f(string&s){stack<char>st;for(char c:s){if(c=='(')st.push(c);else if(!st.empty())st.pop();}return st.empty();}",
     "O(n)", "O(n)"],

    ["Deque Sliding Window",
     "vector<int>f(vector<int>&a,int k){deque<int>dq;vector<int>ans;for(int i=0;i<a.size();i++){while(!dq.empty()&&dq.front()<=i-k)dq.pop_front();while(!dq.empty()&&a[dq.back()]<=a[i])dq.pop_back();dq.push_back(i);if(i>=k-1)ans.push_back(a[dq.front()]);}return ans;}",
     "O(n)", "O(n)"],

    # Graph
    ["Cycle DFS",
     "bool f(vector<vector<int>>&g,int u,vector<int>&vis,vector<int>&path){vis[u]=path[u]=1;for(int v:g[u]){if(!vis[v]&&f(g,v,vis,path))return true;if(path[v])return true;}path[u]=0;return false;}",
     "O(V+E)", "O(V)"],

    ["Topological Sort",
     "vector<int>f(vector<vector<int>>&g){vector<int>in(g.size()),ans;queue<int>q;for(int u=0;u<g.size();u++)for(int v:g[u])in[v]++;for(int i=0;i<g.size();i++)if(!in[i])q.push(i);while(!q.empty()){int u=q.front();q.pop();ans.push_back(u);for(int v:g[u])if(--in[v]==0)q.push(v);}return ans;}",
     "O(V+E)", "O(V)"],

    ["Bipartite BFS",
     "bool f(vector<vector<int>>&g){vector<int>c(g.size(),-1);for(int s=0;s<g.size();s++)if(c[s]==-1){queue<int>q;q.push(s);c[s]=0;while(!q.empty()){int u=q.front();q.pop();for(int v:g[u]){if(c[v]==-1)c[v]=c[u]^1,q.push(v);else if(c[v]==c[u])return false;}}}return true;}",
     "O(V+E)", "O(V)"],

    # Graph / DSU
    ["DSU Operations",
     "int f(int n,vector<pair<int,int>>&e){vector<int>p(n),sz(n,1);for(int i=0;i<n;i++)p[i]=i;for(auto [a,b]:e){while(p[a]!=a)a=p[a];while(p[b]!=b)b=p[b];if(a!=b){if(sz[a]<sz[b])swap(a,b);p[b]=a;sz[a]+=sz[b];}}return p[0];}",
     "O(E log V)", "O(V)"],

    # DP
    ["Knapsack DP",
     "int f(vector<int>&w,vector<int>&v,int W){vector<int>dp(W+1);for(int i=0;i<w.size();i++)for(int j=W;j>=w[i];j--)dp[j]=max(dp[j],dp[j-w[i]]+v[i]);return dp[W];}",
     "O(nW)", "O(W)"],

    ["LCS DP",
     "int f(string&a,string&b){vector<vector<int>>dp(a.size()+1,vector<int>(b.size()+1));for(int i=1;i<=a.size();i++)for(int j=1;j<=b.size();j++)dp[i][j]=a[i-1]==b[j-1]?dp[i-1][j-1]+1:max(dp[i-1][j],dp[i][j-1]);return dp[a.size()][b.size()];}",
     "O(n*m)", "O(n*m)"],

    # Matrix
    ["Matrix Multiplication",
     "void f(vector<vector<int>>&a,vector<vector<int>>&b,vector<vector<int>>&c){for(int i=0;i<a.size();i++)for(int j=0;j<b[0].size();j++)for(int k=0;k<b.size();k++)c[i][j]+=a[i][k]*b[k][j];}",
     "O(n^3)", "O(1)"],

    # Greedy
    ["Activity Selection",
     "int f(vector<pair<int,int>>&a){sort(a.begin(),a.end(),[](auto&x,auto&y){return x.second<y.second;});int last=-1,c=0;for(auto [s,e]:a)if(s>=last)last=e,c++;return c;}",
     "O(n log n)", "O(1)"],

    # Searching / hashing
    ["Duplicate Detection",
     "bool f(vector<int>&a){unordered_set<int>s;for(int x:a){if(s.find(x)!=s.end())return true;s.insert(x);}return false;}",
     "O(n)", "O(n)"],

    ["Frequency Map",
     "unordered_map<int,int> f(vector<int>&a){unordered_map<int,int>m;for(int x:a)m[x]++;return m;}",
     "O(n)", "O(n)"],

    # Bit manipulation
    ["Bit Counting",
     "int f(int n){int c=0;while(n){n&=n-1;c++;}return c;}",
     "O(log n)", "O(1)"],

    # Mathematical
    ["Euclidean GCD",
     "int f(int a,int b){while(b){int t=a%b;a=b;b=t;}return a;}",
     "O(log n)", "O(1)"]
]


passed = 0
failed = 0

print("=" * 95)
print("STAGE-3 ALGORITHM VERIFICATION")
print("=" * 95)

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

print("=" * 95)
print(f"TOTAL:      {total}")
print(f"PASSED:     {passed}")
print(f"FAILED:     {failed}")
print(f"PASS RATE:  {passed * 100 / total:.2f}%")
print("=" * 95)