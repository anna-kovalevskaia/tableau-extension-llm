import ast


ALLOWED_MODULES = {
    "math",
    "statistics",
    "itertools",
    "functools",
    "collections",
    "json",
    "re",
    "datetime",
    "pandas",
    "numpy",
    "scipy",
    "polars"

}

FORBIDDEN_CALLS = {
    "open",
    "eval",
    "exec",
    "compile",
    "__import__",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
    "subprocess",
    "system",
    "popen",
    "execv",
    "execve",
    "socket",
    "requests",
    "pickle",
    "torch",
    "tensorflow",
    "os",
    "sys",
    "pathlib",
    "shutil",
    "ctypes",
    "operator",
    "attrgetter",
    "itemgetter",
    "methodcaller",
    "__subclasses__",
    "__mro__",
    "__dict__",
    "__class__",
    # "__builtins__",
}

FORBIDDEN_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.With,
    ast.Try,
    ast.Raise,
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Lambda,
)

class SafeCodeValidator(ast.NodeVisitor):
    def visit(self, node):
        if isinstance(node, FORBIDDEN_NODES):
            error_message = f"Forbidden node type: {type(node).__name__}"
            raise ValueError(error_message)
        return super().visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr.startswith("__"):
            error_message = f"Dunder attribute forbidden: {node.attr}"
            raise ValueError(error_message)
        if node.attr in FORBIDDEN_CALLS:
            error_message = f"Forbidden attribute: {node.attr}"
            raise ValueError(error_message)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id.startswith("__"):
            error_message = f"Dunder name forbidden: {node.id}"
            raise ValueError(error_message)
        if node.id in FORBIDDEN_CALLS:
            error_message = f"Forbidden name: {node.id}"
            raise ValueError(error_message)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in FORBIDDEN_CALLS:
                error_message = f"Forbidden call: {func_name}"
                raise ValueError(error_message)

        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in FORBIDDEN_CALLS:
                error_message =f"Forbidden attribute call: {attr_name}"
                raise ValueError(error_message)

        self.generic_visit(node)


def validate_code(code: str) -> None:

    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        error_message = f"Syntax error: {e}"
        raise ValueError(error_message)

    validator = SafeCodeValidator()
    validator.visit(tree)

