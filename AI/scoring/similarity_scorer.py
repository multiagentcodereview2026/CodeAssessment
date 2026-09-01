import ast


def normalize_ast(code: str) -> ast.AST:
    """
    Parse Python code and normalize names/constants so that
    superficial differences do not dominate similarity.
    """

    tree = ast.parse(code)

    for node in ast.walk(tree):

        if isinstance(node, ast.Name):
            node.id = "VAR"

        elif isinstance(node, ast.arg):
            node.arg = "ARG"

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.name = "FUNCTION"

        elif isinstance(node, ast.ClassDef):
            node.name = "CLASS"

        elif isinstance(node, ast.Constant):
            node.value = "CONST"

    return tree


def ast_structure(code: str) -> list[str]:
    """
    Convert the AST into an ordered structural representation.
    """

    tree = normalize_ast(code)

    structure = []

    for node in ast.walk(tree):
        structure.append(type(node).__name__)

    return structure


def calculate_similarity(
    code1: str,
    code2: str
) -> float:
    """
    Calculate structural similarity between two Python programs.

    Uses ordered AST node sequences and SequenceMatcher.
    Returns a value between 0 and 100.
    """

    from difflib import SequenceMatcher

    structure1 = ast_structure(code1)
    structure2 = ast_structure(code2)

    if not structure1 or not structure2:
        return 0.0

    similarity = SequenceMatcher(
        None,
        structure1,
        structure2
    ).ratio()

    return round(similarity * 100, 2)


def calculate_originality(similarity: float) -> float:
    """
    Convert similarity percentage into originality percentage.
    """

    originality = 100 - similarity

    return round(
        max(0.0, originality),
        2
    )