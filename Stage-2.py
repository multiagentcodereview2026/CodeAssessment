import sys
sys.path.append(".")

from backend.analysis.ast_parser import ASTComplexityAnalyzer
from backend.analysis.ast_engine import infer_complexity_from_ir


def norm(s):
    return str(s).replace(" ", "").lower().replace("*", "").replace("×", "")


tests = [

    # =========================
    # BASIC ALGORITHMS
    # =========================

    [
        "Linear Search",
        "int f(vector<int>&a,int x){for(int i=0;i<a.size();i++)if(a[i]==x)return i;return -1;}",
        "O(n)", "O(1)"
    ],

    [
        "Binary Search",
        "int f(vector<int>&a,int x){int l=0,r=a.size()-1;while(l<=r){int m=l+(r-l)/2;if(a[m]==x)return m;if(a[m]<x)l=m+1;else r=m-1;}return -1;}",
        "O(log n)", "O(1)"
    ],

    [
        "Two Pointer",
        "bool f(vector<int>&a,int x){int l=0,r=a.size()-1;while(l<r){int s=a[l]+a[r];if(s==x)return true;if(s<x)l++;else r--;}return false;}",
        "O(n)", "O(1)"
    ],

    [
        "Sliding Window",
        "int f(vector<int>&a,int k){int l=0,s=0,ans=0;for(int r=0;r<a.size();r++){s+=a[r];while(s>k)s-=a[l++];ans=max(ans,r-l+1);}return ans;}",
        "O(n)", "O(1)"
    ],

    # =========================
    # SORTING
    # =========================

    [
        "Bubble Sort",
        "void f(vector<int>&a){for(int i=0;i<a.size();i++)for(int j=0;j+1<a.size()-i;j++)if(a[j]>a[j+1])swap(a[j],a[j+1]);}",
        "O(n^2)", "O(1)"
    ],

    [
        "Selection Sort",
        "void f(vector<int>&a){for(int i=0;i<a.size();i++){int p=i;for(int j=i+1;j<a.size();j++)if(a[j]<a[p])p=j;swap(a[i],a[p]);}}",
        "O(n^2)", "O(1)"
    ],

    [
        "Insertion Sort",
        "void f(vector<int>&a){for(int i=1;i<a.size();i++){int x=a[i],j=i-1;while(j>=0&&a[j]>x){a[j+1]=a[j];j--;}a[j+1]=x;}}",
        "O(n^2)", "O(1)"
    ],

    [
        "Merge Sort",
        "void f(vector<int>&a,int l,int r){if(l>=r)return;int m=(l+r)/2;f(a,l,m);f(a,m+1,r);vector<int>t;int i=l,j=m+1;while(i<=m&&j<=r){if(a[i]<a[j])t.push_back(a[i++]);else t.push_back(a[j++]);}while(i<=m)t.push_back(a[i++]);while(j<=r)t.push_back(a[j++]);}",
        "O(n log n)", "O(n)"
    ],

    [
        "Quick Sort",
        "void f(vector<int>&a,int l,int r){if(l>=r)return;int p=a[r],i=l;for(int j=l;j<r;j++)if(a[j]<p)swap(a[i++],a[j]);swap(a[i],a[r]);f(a,l,i-1);f(a,i+1,r);}",
        "O(n log n)", "O(n)"
    ],

    # =========================
    # RECURSION
    # =========================

    [
        "Linear Recursion",
        "int f(int n){if(n<=0)return 0;return 1+f(n-1);}",
        "O(n)", "O(n)"
    ],

    [
        "Binary Recursion",
        "int f(int n){if(n<=1)return n;return f(n-1)+f(n-2);}",
        "O(2^n)", "O(n)"
    ],

    # =========================
    # DP
    # =========================

    [
        "Memoization",
        "int f(int n,vector<int>&dp){if(n<=1)return n;if(dp[n]!=-1)return dp[n];return dp[n]=f(n-1,dp)+f(n-2,dp);}",
        "O(n)", "O(n)"
    ],

    [
        "1D Dynamic Programming",
        "int f(vector<int>&a){vector<int>dp(a.size());dp[0]=a[0];for(int i=1;i<a.size();i++)dp[i]=max(dp[i-1]+a[i],a[i]);return *max_element(dp.begin(),dp.end());}",
        "O(n)", "O(n)"
    ],

    # =========================
    # BACKTRACKING
    # =========================

    [
        "Backtracking",
        "void f(vector<int>&a,int i){if(i==a.size())return;f(a,i+1);f(a,i+1);}",
        "O(2^n)", "O(n)"
    ],

    # =========================
    # STACK / QUEUE / HASH
    # =========================

    [
        "Monotonic Stack",
        "vector<int>f(vector<int>&a){vector<int>ans(a.size());stack<int>st;for(int i=0;i<a.size();i++){while(!st.empty()&&a[i]>a[st.top()]){int j=st.top();st.pop();ans[j]=i-j;}st.push(i);}return ans;}",
        "O(n)", "O(n)"
    ],

    [
        "Hash Table",
        "bool f(vector<int>&a){unordered_set<int>s;for(int x:a){if(s.count(x))return true;s.insert(x);}return false;}",
        "O(n)", "O(n)"
    ],

    [
        "Heap",
        "int f(vector<int>&a){priority_queue<int>pq;for(int x:a)pq.push(x);int s=0;while(!pq.empty()){s+=pq.top();pq.pop();}return s;}",
        "O(n log n)", "O(n)"
    ],

    # =========================
    # GRAPH
    # =========================

    [
        "BFS",
        "void f(vector<vector<int>>&g,int s){vector<int>vis(g.size(),0);queue<int>q;q.push(s);vis[s]=1;while(!q.empty()){int u=q.front();q.pop();for(int v:g[u])if(!vis[v]){vis[v]=1;q.push(v);}}}",
        "O(V+E)", "O(V)"
    ],

    [
        "DFS",
        "void f(vector<vector<int>>&g,int u,vector<int>&vis){vis[u]=1;for(int v:g[u])if(!vis[v])f(g,v,vis);}",
        "O(V+E)", "O(V)"
    ],

    [
        "Dijkstra",
        "void f(vector<vector<pair<int,int>>>&g,int s){vector<int>d(g.size(),1e9);priority_queue<pair<int,int>,vector<pair<int,int>>,greater<pair<int,int>>>pq;d[s]=0;pq.push({0,s});while(!pq.empty()){auto [du,u]=pq.top();pq.pop();for(auto [v,w]:g[u])if(du+w<d[v]){d[v]=du+w;pq.push({d[v],v});}}}",
        "O((V+E) log V)", "O(V)"
    ],

    # =========================
    # MATRIX / PREFIX / GREEDY
    # =========================

    [
        "Matrix Traversal",
        "int f(vector<vector<int>>&a){int s=0;for(int i=0;i<a.size();i++)for(int j=0;j<a[i].size();j++)s+=a[i][j];return s;}",
        "O(m*n)", "O(1)"
    ],

    [
        "Prefix Sum",
        "vector<int>f(vector<int>&a){vector<int>p(a.size()+1);for(int i=0;i<a.size();i++)p[i+1]=p[i]+a[i];return p;}",
        "O(n)", "O(n)"
    ],

    [
        "Greedy",
        "int f(vector<int>&a){sort(a.begin(),a.end());int s=0;for(int x:a)s+=x;return s;}",
        "O(n log n)", "O(1)"
    ]
]


passed = 0
failed = 0

print("=" * 90)
print("STAGE-2 ALGORITHM VERIFICATION")
print("=" * 90)

for name, code, expected_tc, expected_sc in tests:

    try:
        ir = ASTComplexityAnalyzer(code).analyze()
        result = infer_complexity_from_ir(ir)

        actual_tc = norm(result.time_complexity)
        actual_sc = norm(result.space_complexity)

        expected_tc_n = norm(expected_tc)
        expected_sc_n = norm(expected_sc)

        ok = (
            actual_tc == expected_tc_n
            and actual_sc == expected_sc_n
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
rate = passed * 100 / total

print("=" * 90)
print(f"TOTAL:      {total}")
print(f"PASSED:     {passed}")
print(f"FAILED:     {failed}")
print(f"PASS RATE:  {rate:.2f}%")
print("=" * 90)