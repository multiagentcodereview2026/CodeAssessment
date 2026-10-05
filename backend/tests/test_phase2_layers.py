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


def test_layer3_python_sorted_without_explicit_loop_is_n_log_n():
    result = analyze_source(
        "def f(left, right):\n"
        "    return sorted(left) == sorted(right)\n",
        "python",
    )
    assert result.time_complexity == "O(n log n)"


def test_layer3_python_counter_without_explicit_loop_is_linear():
    result = analyze_source(
        "from collections import Counter\n"
        "def f(values):\n"
        "    counts = Counter(values)\n"
        "    return max(counts.values())\n",
        "python",
    )
    assert result.time_complexity == "O(n)"


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


def test_layer2_grouped_partition_is_linear_total_work():
    result = analyze_source(
        "def f(groups):\n"
        "    total = 0\n"
        "    for group in groups.values():\n"
        "        for item in group:\n"
        "            total += item\n"
        "    return total\n",
        "python",
    )
    assert result.time_complexity == "O(n)"


def test_layer1_monotonic_name_membership_is_amortized():
    result = analyze_source(
        "def f(names):\n"
        "    used = {}\n"
        "    for name in names:\n"
        "        k = 1\n"
        "        while name + str(k) in used:\n"
        "            k += 1\n"
        "        used[name + str(k)] = 1\n"
        "    return used\n",
        "python",
    )
    assert result.time_complexity == "O(n)"


def test_python_dfs_helper_without_adjacency_is_not_graph():
    result = analyze_source(
        "def f(balls):\n"
        "    def dfs(i, remaining, diff):\n"
        "        if i == len(balls): return diff == 0\n"
        "        for x in range(balls[i] + 1):\n"
        "            dfs(i + 1, remaining - x, diff)\n"
        "        return False\n"
        "    return dfs(0, 0, 0)\n",
        "python",
    )
    assert result.time_complexity != "O(V+E)"
