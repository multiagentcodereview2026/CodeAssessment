from services.executor import execute_cpp_code

code = r'''
#include <iostream>
#include <vector>
#include <sstream>
#include <string>
using namespace std;

int main() {
    string line;
    getline(cin, line);

    if (!line.empty() && line.front() == '[')
        line.erase(0, 1);

    if (!line.empty() && line.back() == ']')
        line.pop_back();

    vector<int> nums;
    stringstream ss(line);
    string value;

    while (getline(ss, value, ',')) {
        if (!value.empty()) {
            nums.push_back(stoi(value));
        }
    }

    int target;
    cin >> target;

    for (int i = 0; i < (int)nums.size(); i++) {
        for (int j = i + 1; j < (int)nums.size(); j++) {
            if (nums[i] + nums[j] == target) {
                cout << "[" << i << "," << j << "]";
                return 0;
            }
        }
    }

    return 0;
}
'''

result = execute_cpp_code(
    code=code,
    input_data="[2,7,11,15]\n9\n",
    timeout=10
)

print(result)