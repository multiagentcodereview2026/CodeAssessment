from services.executor import execute_code

code = """
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        int a = sc.nextInt();
        int b = sc.nextInt();

        System.out.println(a + b);
    }
}
"""

result = execute_code(
    language="java",
    code=code,
    input_data="10 20\n",
    timeout=30
)

print(result)