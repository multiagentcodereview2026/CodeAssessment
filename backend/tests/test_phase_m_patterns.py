from analysis.static_analyzer import analyze_source


def test_phase_m_sliding_window_has_canonical_pattern():
    result = analyze_source(
        "int f(vector<int>& a, int k){ int left=0,sum=0; "
        "for(int right=0; right<a.size(); ++right){ sum+=a[right]; "
        "while(sum>k){sum-=a[left++];} } return sum; }",
        "cpp",
    )
    assert result.time_complexity == "O(n)"
    assert any(signal == "pattern:sliding-window" for signal in result.signals)


def test_phase_m_graph_pattern_is_canonical():
    result = analyze_source(
        "void dfs(int u, vector<vector<int>>& adj, vector<int>& seen){ "
        "seen[u]=1; for(int v:adj[u]) if(!seen[v]) dfs(v,adj,seen); }",
        "cpp",
    )
    assert result.time_complexity == "O(V+E)"
    assert any(signal == "pattern:graph-traversal" for signal in result.signals)


def test_phase_m_constant_work_pattern_is_explicit():
    result = analyze_source("int f(int x){ return x + 1; }", "cpp")
    assert result.time_complexity == "O(1)"
    assert any(signal == "pattern:constant-work" for signal in result.signals)
