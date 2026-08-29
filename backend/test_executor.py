from services.executor import execute_python_code


code = """
a, b = map(int, input().split())
print(a + b)
"""


result = execute_python_code(
    code=code,
    input_data="10 20\n"
)

print(result)