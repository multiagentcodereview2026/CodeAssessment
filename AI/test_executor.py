from execution.docker_executor import execute_python


code = """
print("Hello from student code")
"""

result = execute_python(code)

print("STDOUT:")
print(result["stdout"])

print("STDERR:")
print(result["stderr"])

print("EXIT CODE:")
print(result["exit_code"])

print("TIMED OUT:")
print(result["timed_out"])