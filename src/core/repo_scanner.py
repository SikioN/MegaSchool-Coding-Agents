from typing import List, Optional
from github import Repository

class RepoScanner:
    """
    Scans a repository to detect missing standard configurations.
    """
    
    REQUIRED_FILES = [
        "pyproject.toml",
        "requirements.txt",
        "setup.py"
    ]
    
    CI_DIRS = [
        ".github/workflows"
    ]

    LINTER_CONFIGS = [
        "pyproject.toml", # Check content for [tool.ruff] etc
        ".flake8",
        ".pylintrc"
    ]

    @staticmethod
    def scan(repo) -> List[str]:
        """
        Scans the repo and returns a list of missing critical components.
        Returns a list of descriptions of what is missing.
        """
        missing = []
        
        # 1. Check Root Files (Package Managers)
        contents = repo.get_contents("")
        root_files = [c.name for c in contents]
        
        has_pkg_manager = any(f in root_files for f in RepoScanner.REQUIRED_FILES)
        if not has_pkg_manager:
            missing.append("Python Package Manager config (pyproject.toml or requirements.txt)")
            
        # 2. Check CI
        has_ci = False
        if ".github" in root_files:
            try:
                # Check workflows dir
                workflows = repo.get_contents(".github/workflows")
                if len(workflows) > 0:
                    has_ci = True
            except Exception:
                pass # path might not exist
        
        if not has_ci:
            missing.append("CI/CD Workflows (.github/workflows)")

        # 3. Check Linters (Simple check for existence)
        # If pyproject.toml exists, we assume it might have config, 
        # but if no config file exists at all, we flag it.
        has_linter = any(f in root_files for f in RepoScanner.LINTER_CONFIGS)
        if not has_linter:
             missing.append("Linter Configuration (ruff/flake8)")

        return missing

import os
import ast
import re

class RepoMapGenerator:
    """
    Generates a skeletal map of the repository structure for various languages.
    Used for Smart Context selection.
    """
    
    @staticmethod
    def generate_map(root_path: str, max_depth: int = 4) -> str:
        """
        Scans the repository and returns a string representation of the structure.
        """
        repo_map = []
        exclude_dirs = {'.git', '.venv', '__pycache__', 'venv', 'env', 'node_modules', 'dist', 'build'}
        
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # Check depth
            rel_path = os.path.relpath(root, root_path)
            if rel_path == ".":
                depth = 0
            else:
                depth = rel_path.count(os.sep) + 1
            
            if depth > max_depth:
                del dirs[:]
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                rel_file_path = os.path.join(rel_path, file) if rel_path != "." else file
                
                # Identify Type
                if file.endswith(".py"):
                    structure = RepoMapGenerator._scan_python(file_path)
                elif file.endswith((".js", ".ts", ".jsx", ".tsx")):
                    structure = RepoMapGenerator._scan_js(file_path)
                elif file.endswith(".go"):
                    structure = RepoMapGenerator._scan_go(file_path)
                else:
                    structure = "" # Just filename
                
                if structure:
                    repo_map.append(f"{rel_file_path}:\n{structure}")
                else:
                    repo_map.append(f"{rel_file_path}")
                    
        return "\n".join(repo_map)

    @staticmethod
    def _scan_python(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
            
            output = []
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    output.append(f"  class {node.name}:")
                    for item in node.body:
                         if isinstance(item, ast.FunctionDef):
                             args = [a.arg for a in item.args.args]
                             output.append(f"    def {item.name}({', '.join(args)}): ...")
                elif isinstance(node, ast.FunctionDef):
                    args = [a.arg for a in node.args.args]
                    output.append(f"  def {node.name}({', '.join(args)}): ...")
            
            return "\n".join(output)
        except Exception:
            return "  (Parser Error)"

    @staticmethod
    def _scan_js(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            output = []
            # Very basic regex for demonstration
            # Function definitions
            funcs = re.findall(r'function\s+(\w+)\s*\(', content)
            for f in funcs:
                output.append(f"  function {f}(...)")
                
            # Headers / Components (const X = () =>)
            arrows = re.findall(r'const\s+(\w+)\s*=\s*\(.*?\)\s*=>', content)
            for a in arrows:
                output.append(f"  const {a} = (...) =>")
                
            # Classes
            classes = re.findall(r'class\s+(\w+)', content)
            for c in classes:
                output.append(f"  class {c}")
                
            return "\n".join(output)
        except:
             return ""

    @staticmethod
    def _scan_go(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            output = []
            # func Name(...)
            funcs = re.findall(r'func\s+(\w+)\s*\(', content)
            for f in funcs:
                output.append(f"  func {f}(...)")
            
            # type X struct
            structs = re.findall(r'type\s+(\w+)\s+struct', content)
            for s in structs:
                output.append(f"  type {s} struct")

            return "\n".join(output)
        except:
            return ""
