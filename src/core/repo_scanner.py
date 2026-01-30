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
