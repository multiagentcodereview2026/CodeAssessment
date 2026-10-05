from analysis.static_analyzer import analyze_source


def test_layer1_fixed_inner_alphabet_is_linear():
    result = analyze_source(
        "int f(vector<int>& a){ int total=0; for(int i=0;i<a.size();++i) "
        "for(int d=0;d<26;++d) total += a[i]+d; return total; }",
        "cpp",
    )
    assert result.time_complexity == "O(n)"


def test_layer2_python_frequency_dict_is_linear_space():
    result = analyze_source(
        "def f(values):\n"
        "    counts = {}\n"
        "    for value in values:\n"
        "        counts[value] = counts.get(value, 0) + 1\n"
        "    return counts\n",
        "python",
    )
    assert result.space_complexity == "O(n)"


def test_layer4_python_graph_traversal_is_graph_linear():
    result = analyze_source(
        "from collections import deque\n"
        "def bfs(graph, start):\n"
        "    seen = {start}\n"
        "    q = deque([start])\n"
        "    while q:\n"
        "        node = q.popleft()\n"
        "        for neighbor in graph[node]:\n"
        "            if neighbor not in seen:\n"
        "                seen.add(neighbor); q.append(neighbor)\n"
        "    return seen\n",
        "python",
    )
    assert result.time_complexity == "O(V+E)"
    assert result.space_complexity == "O(V)"
