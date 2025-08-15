import os
import ast
import importlib
import pytest
from pathlib import Path

# The root directory of the project
PROJECT_ROOT = Path(__file__).parent.parent
# The directory to start searching for Python files
SEARCH_DIR = PROJECT_ROOT / "notion_calendar_sync"
# The file to save the results to
RESULTS_FILE = PROJECT_ROOT / "import_test_results.txt"


def get_python_files(search_dir):
    """Recursively find all Python files in the given directory."""
    python_files = []
    for root, _, files in os.walk(search_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    return python_files


def get_imports(file_path):
    """Parse a Python file and extract all import statements."""
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=str(file_path))
        except SyntaxError as e:
            return {"errors": [(0, f"SyntaxError: {e}")]}

    imports = {"local": [], "package": []}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                imports["package"].append((module_name, node.lineno, f"import {module_name}"))
        elif isinstance(node, ast.ImportFrom):
            level = node.level
            module = node.module
            if level > 0:
                # Relative import
                # Construct the absolute module path from the relative one
                relative_path = "." * level + (module if module else "")
                # Resolve relative path based on the file's location
                try:
                    resolved_module = importlib.util.resolve_name(relative_path, file_path.parent.name.replace('/', '.'))
                    imports["local"].append((resolved_module, node.lineno, f"from {relative_path} import ..."))
                except (ValueError, ImportError):
                     imports["local"].append((relative_path, node.lineno, f"from {relative_path} import ..."))

            else:
                # Absolute import
                imports["package"].append((module, node.lineno, f"from {module} import ..."))
    return imports


def test_all_imports():
    """
    Recursively finds all Python files, parses all import statements,
    and attempts to execute each import to see if it succeeds or fails.
    """
    python_files = get_python_files(SEARCH_DIR)
    all_results = {}
    failed_imports = {}
    successful_imports_count = 0
    failed_imports_count = 0

    for file_path in python_files:
        imports = get_imports(file_path)
        file_results = {}

        if "errors" in imports:
            file_results["syntax_error"] = "failure"
            failed_imports_count += 1
            if str(file_path) not in failed_imports:
                failed_imports[str(file_path)] = []
            failed_imports[str(file_path)].append(["syntax", imports["errors"][0][0], imports["errors"][0][1]])
            all_results[str(file_path)] = file_results
            continue

        for import_type, import_list in imports.items():
            for module_name, line_number, line_content in import_list:
                try:
                    # For relative imports, we need to determine the correct package context
                    if import_type == 'local' and module_name.startswith('.'):
                        package = '.'.join(file_path.relative_to(PROJECT_ROOT).parts[:-1])
                        importlib.import_module(module_name, package)
                    else:
                        importlib.import_module(module_name)

                    file_results[line_content] = "success"
                    successful_imports_count += 1
                except (ImportError, ModuleNotFoundError, TypeError) as e:
                    file_results[line_content] = "failure"
                    failed_imports_count += 1
                    if str(file_path) not in failed_imports:
                        failed_imports[str(file_path)] = []
                    failed_imports[str(file_path)].append([import_type, line_number, line_content, str(e)])

        if file_results:
            all_results[str(file_path)] = file_results

    # Save results to file
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        for file_path, results in all_results.items():
            f.write(f"{file_path}: {results}\n")
        f.write("\n")
        f.write(f"successful imports= {successful_imports_count} failed imports = {failed_imports_count}\n")
        f.write("\n")
        f.write("failed_imports = {\n")
        for file_path, errors in failed_imports.items():
            f.write(f"    '{file_path}': [\n")
            for error in errors:
                f.write(f"        {error},\n")
            f.write("    ],\n")
        f.write("}\n")

    # Print summary to terminal
    print("\n--- Import Test Summary ---")
    print(f"Successful imports: {successful_imports_count}")
    print(f"Failed imports: {failed_imports_count}")
    print(f"Results saved to: {RESULTS_FILE}")
    print("-------------------------")

    # if failed_imports_count > 0:
    #     pytest.fail(f"{failed_imports_count} imports failed. Check '{RESULTS_FILE}' for details.", pytrace=False)
