import sys
sys.path.insert(0, '.')
from backend.analysis.ast_parser import ASTComplexityAnalyzer
from backend.analysis.ast_engine import infer_complexity_from_ir

def same(a,b):
    a_norm = str(a).replace(' ','').lower().replace('*','').replace('×','')
    b_norm = str(b).replace(' ','').lower().replace('*','').replace('×','')
    return a_norm == b_norm

tests = [
('Linear Scan', 'int f(vector<int>& a){int s=0;for(int x:a) s+=x;return s;}', 'O(n)','O(1)'),
('Nested Loops', 'int f(vector<int>& a){int s=0;for(int i=0;i<a.size();i++) for(int j=0;j<a.size();j++) s+=a[i]+a[j];return s;}', 'O(n^2)','O(1)'),
('Logarithmic Loop', 'int f(int n){int x=1;while(x<n) x*=2;return x;}', 'O(log n)','O(1)'),
('Binary Search', 'int f(vector<int>& a,int x){int l=0,r=a.size()-1;while(l<=r){int m=l+(r-l)/2;if(a[m]==x) return m;if(a[m]<x) l=m+1;else r=m-1;}return -1;}', 'O(log n)','O(1)'),
('Two Pointer', 'bool f(vector<int>& a,int x){int l=0,r=a.size()-1;while(l<r){if(a[l]+a[r]==x) return true;if(a[l]+a[r]<x) l++;else r--;}return false;}', 'O(n)','O(1)'),
('Sliding Window', 'int f(vector<int>& a,int k){int l=0,sum=0,ans=0;for(int r=0;r<a.size();r++){sum+=a[r];while(sum>k){sum-=a[l++];}ans=max(ans,r-l+1);}return ans;}', 'O(n)','O(1)'),
('Merge Sort', "void f(vector<int>& a,int l,int r){if(l>=r) return;int m=(l+r)/2;f(a,l,m);f(a,m+1,r);vector<int> t;int i=l,j=m+1;while(i<=m && j<=r){if(a[i]<a[j]) t.push_back(a[i++]);else t.push_back(a[j++]);}while(i<=m) t.push_back(a[i++]);while(j<=r) t.push_back(a[j++]);}", 'O(n log n)','O(n)'),
('Quick Sort', 'void f(vector<int>& a,int l,int r){if(l>=r) return;int p=a[r];int i=l;for(int j=l;j<r;j++){if(a[j]<p) swap(a[i++],a[j]);}swap(a[i],a[r]);f(a,l,i-1);f(a,i+1,r);}', 'O(n log n)','O(n)'),
('Binary Recursion', 'int f(int n){if(n<=1) return n;return f(n-1)+f(n-2);}', 'O(2^n)','O(n)'),
('Memoization', 'int f(int n,vector<int>& dp){if(n<=1) return n;if(dp[n]!=-1) return dp[n];return dp[n]=f(n-1,dp)+f(n-2,dp);}', 'O(n)','O(n)'),
('Backtracking', 'void f(vector<int>& a,int i){if(i==a.size()) return;f(a,i+1);f(a,i+1);}', 'O(2^n)','O(n)'),
('Monotonic Stack', 'vector<int> f(vector<int>& a){vector<int> ans(a.size());stack<int> st;for(int i=0;i<a.size();i++){while(!st.empty() && a[i]>a[st.top()]){int j=st.top();st.pop();ans[j]=i-j;}st.push(i);}return ans;}', 'O(n)','O(n)'),
('Hash Table', 'bool f(vector<int>& a){unordered_set<int> s;for(int x:a){if(s.count(x)) return true;s.insert(x);}return false;}', 'O(n)','O(n)'),
('Heap', 'int f(vector<int>& a){priority_queue<int> pq;for(int x:a) pq.push(x);int ans=0;while(!pq.empty()){ans+=pq.top();pq.pop();}return ans;}', 'O(n log n)','O(n)'),
('BFS', 'void f(vector<vector<int>>& g,int s){vector<int> vis(g.size(),0);queue<int> q;q.push(s);vis[s]=1;while(!q.empty()){int u=q.front();q.pop();for(int v:g[u]){if(!vis[v]){vis[v]=1;q.push(v);}}}}', 'O(V+E)','O(V)'),
('DFS', 'void f(vector<vector<int>>& g,int u,vector<int>& vis){vis[u]=1;for(int v:g[u]){if(!vis[v]) f(g,v,vis);}}', 'O(V+E)','O(V)'),
('Dijkstra', 'vector<int> f(vector<vector<pair<int,int>>>& g,int s){vector<int> d(g.size(),1000000000);priority_queue<pair<int,int>,vector<pair<int,int>>,greater<pair<int,int>>> pq;d[s]=0;pq.push({0,s});while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=d[u]) continue;for(auto [v,w]:g[u]){if(d[v]>du+w){d[v]=du+w;pq.push({d[v],v});}}return d;}', 'O((V+E)logV)','O(V)'),
('Union Find', 'int find(vector<int>& p,int x){if(p[x]==x) return x;return p[x]=find(p,p[x]);}void unite(vector<int>& p,vector<int>& rank,int a,int b){a=find(p,a);b=find(p,b);if(a==b) return;if(rank[a]<rank[b]) swap(a,b);p[b]=a;if(rank[a]==rank[b]) rank[a]++;}', 'O(alpha(n))','O(n)'),
('Dynamic Programming', 'int f(vector<int>& a){vector<int> dp(a.size());dp[0]=a[0];for(int i=1;i<a.size();i++) dp[i]=max(dp[i-1]+a[i],a[i]);return *max_element(dp.begin(),dp.end());}', 'O(n)','O(n)'),
('Matrix Traversal', 'int f(vector<vector<int>>& a){int s=0;for(int i=0;i<a.size();i++) for(int j=0;j<a[i].size();j++) s+=a[i][j];return s;}', 'O(m*n)','O(1)'),
('Fixed Size Array', "int f(string s){int cnt[26]={0};for(char c:s) cnt[c-'a']++;return cnt[0];}", 'O(n)','O(1)'),
('Prefix Sum', 'vector<int> f(vector<int>& a){vector<int> p(a.size()+1);for(int i=0;i<a.size();i++) p[i+1]=p[i]+a[i];return p;}', 'O(n)','O(n)'),
('Greedy', 'int f(vector<int>& a){sort(a.begin(),a.end());int ans=0;for(int x:a) ans+=x;return ans;}', 'O(n log n)','O(1)'),
('Divide and Conquer', 'int f(vector<int>& a,int l,int r){if(l==r) return a[l];int m=(l+r)/2;int x=f(a,l,m);int y=f(a,m+1,r);return max(x,y);}', 'O(n)','O(log n)')
]

passed=0
failed=0
fail_list=[]

print()
print('='*65)
print('    24-ALGORITHM VERIFICATION SUITE (AFTER RECURSION FIX)')
print('='*65)
print()

for name,code,expected_time,expected_space in tests:
    try:
        ir=ASTComplexityAnalyzer(code).analyze()
        result=infer_complexity_from_ir(ir)
        actual_time=result.time_complexity
        actual_space=result.space_complexity
        t_ok=same(actual_time,expected_time)
        s_ok=same(actual_space,expected_space)
        if t_ok and s_ok:
            status='PASS'
            passed+=1
        else:
            status='FAIL'
            failed+=1
            fail_list.append((name, actual_time, expected_time, actual_space, expected_space))
        print(f'{status} | {name:22} | TC: {actual_time:14} / {expected_time:14} | SC: {actual_space:10} / {expected_space:10}')
    except Exception as e:
        failed+=1
        fail_list.append((name, 'ERROR', '', str(e), ''))
        print(f'ERR  | {name:22} | {e}')

print()
print('='*65)
print(f'TOTAL:  {len(tests)}')
print(f'PASSED: {passed}')
print(f'FAILED: {failed}')
print(f'PASS RATE: {round(passed*100/len(tests),2)}%')
print('='*65)
print(f'Previous Pass Rate: 54.17% (13/24)')
print(f'Improvement: +{round((passed-13)*100/24,2)} percentage points')
print()

if fail_list:
    print('FAILED CASES:')
    for name, at, et, asc, esc in fail_list:
        print(f'  {name}: TC={at} (exp {et}), SC={asc} (exp {esc})')
