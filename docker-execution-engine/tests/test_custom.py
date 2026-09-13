import os
import sys

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from app.languages import get_language_config
from app.sandbox import execute_in_sandbox


# =========================================================
# MANUALLY WRITE YOUR CODE & TEST CASES BELOW:
# =========================================================

# 1. Select Language: "python", "c", "cpp", or "java"
LANGUAGE = "cpp"

# 2. Write your solution code here (No imports needed for built-in functions):
STUDENT_CODE = """
#include <iostream>
#include <vector>
#include <queue>

using namespace std;

int shortestPath(vector<vector<int>>& grid) {
    int m = grid.size();
    int n = grid[0].size();
    if (grid[0][0] == 1 || grid[m - 1][n - 1] == 1) return -1;

    vector<vector<int>> dist(m, vector<int>(n, -1));
    queue<pair<int, int>> q;
    q.push({0, 0});
    dist[0][0] = 0;

    int dr[] = {-1, 1, 0, 0};
    int dc[] = {0, 0, -1, 1};

    while (!q.empty()) {
        auto [r, c] = q.front();
        q.pop();

        if (r == m - 1 && c == n - 1)
            return dist[r][c];

        for (int i = 0; i < 4; i++) {
            int nr = r + dr[i];
            int nc = c + dc[i];

            if (nr >= 0 && nr < m &&
                nc >= 0 && nc < n &&
                grid[nr][nc] == 0 &&
                dist[nr][nc] == -1) {

                dist[nr][nc] = dist[r][c] + 1;
                q.push({nr, nc});
            }
        }
    }

    return -1;
}

int main() {
    int m, n;
    if (cin >> m >> n) {
        vector<vector<int>> grid(m, vector<int>(n));
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                cin >> grid[i][j];
            }
        }
        cout << shortestPath(grid) << endl;
    }
    return 0;
}
"""

# 3. Add your custom test cases manually here:

TEST_CASES = [
    {
        "id": 1,
        "input": "3 3\n0 0 0\n1 1 0\n0 0 0",
        "expected_output": "4",
        "is_hidden": False
    },
    {
        "id": 2,
        "input": "3 3\n0 1 0\n0 1 0\n0 0 0",
        "expected_output": "4",
        "is_hidden": False
    },
    {
        "id": 3,
        "input": "3 3\n0 1 1\n1 1 0\n0 0 0",
        "expected_output": "-1",
        "is_hidden": True
    },
    {
        "id": 4,
        "input": "4 4\n0 0 0 0\n0 1 1 0\n0 0 0 0\n1 1 1 0",
        "expected_output": "6",
        "is_hidden": True
    }
]
# =========================================================
# RUNNER SCRIPT
# =========================================================

def run_custom_test():

    print("=" * 60)
    print(f"  RUNNING MANUAL CUSTOM CODE TEST ({LANGUAGE.upper()})")
    print("=" * 60)

    lang_cfg = get_language_config(LANGUAGE)

    if not lang_cfg:
        print(f"Error: Language '{LANGUAGE}' is not supported!")
        return

    for idx, tc in enumerate(TEST_CASES, start=1):
        print(f"\n--- Test Case #{idx} (Hidden: {tc['is_hidden']}) ---")
        print(f"Input           : {tc['input']!r}")
        print(f"Expected Output : {tc['expected_output']!r}")

        result = execute_in_sandbox(
            code=STUDENT_CODE,
            lang_config=lang_cfg,
            input_data=tc["input"],
            expected_output=tc["expected_output"]
        )

        print(f"Status          : {result.status}")
        print(f"Runtime         : {result.runtime_ms} ms")

        if result.compile_stderr:
            print(f"Compile Error   : {result.compile_stderr.strip()}")

        if result.actual_output is not None:
            print(f"Actual Output   : {result.actual_output.strip()!r}")

        if result.stderr:
            print(f"Stderr Logs     : {result.stderr.strip()}")

    print("\n" + "=" * 60)


if __name__ == "__main__":

    run_custom_test()
