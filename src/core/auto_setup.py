
import os
import shutil
import tempfile
from src.core.git_provider import GitProvider
from src.core.runner import get_env_with_token

TEMPLATE_PYPROJECT = """[tool.poetry]
name = "mega-project"
version = "0.1.0"
description = "Created by MegaSchool Agent"
authors = ["Agent <agent@megaschool.ai>"]

[tool.poetry.dependencies]
python = "^3.11"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
bandit = "^1.7"
ruff = "^0.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
"""

TEMPLATE_CI = """name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
    - name: Run Tests
      run: poetry run pytest
    - name: Security Check
      run: poetry run bandit -r src -f custom || true
"""

def run_auto_setup(installation_id: int, repositories: list):
    """
    Checks each repo. If empty, creates a Setup PR.
    """
    print(f"Starting Auto-Setup for {len(repositories)} repos...")
    
    for repo_info in repositories:
        repo_full_name = repo_info["full_name"]
        print(f"Checking {repo_full_name}...")
        
        # Generate token env for this repo
        try:
             env = get_env_with_token(installation_id)
        except Exception as e:
             print(f"Failed to get token for {repo_full_name}: {e}")
             continue

        token = env.get("GITHUB_TOKEN")
        
        # Clone to check content
        # Note: Ideally we use API to check file count, but cloning is reliable backend logic
        with tempfile.TemporaryDirectory() as temp_dir:
             git_provider = GitProvider(repo_path=temp_dir, token=token)
             
             # Clone
             clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
             os.system(f"git clone {clone_url} {temp_dir} > /dev/null 2>&1")
             
             # Check if "Empty" (only .git and maybe README)
             files = [f for f in os.listdir(temp_dir) if f != ".git"]
             if len(files) > 2: # heuristic: if lots of files, skip
                 print(f"Repo {repo_full_name} is not empty. Skipping.")
                 continue
                 
             print(f"Repo {repo_full_name} seems empty. initializing...")
             
             # Create Branch
             git_provider.create_branch("agent/initial-setup")
             
             # Write Files
             with open(os.path.join(temp_dir, "pyproject.toml"), "w") as f:
                 f.write(TEMPLATE_PYPROJECT)
                 
             os.makedirs(os.path.join(temp_dir, ".github", "workflows"), exist_ok=True)
             with open(os.path.join(temp_dir, ".github", "workflows", "ci.yml"), "w") as f:
                 f.write(TEMPLATE_CI)
                 
             os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
             with open(os.path.join(temp_dir, "src", "__init__.py"), "w") as f:
                 f.write("")
                 
             # Commit & Push
             git_provider.repo.index.add(["pyproject.toml", ".github/workflows/ci.yml", "src/__init__.py"])
             git_provider.commit_changes("chore: Initial project setup (Poetry + CI)")
             
             try:
                 pr_url = git_provider.create_pr("Initial Project Setup by Agent", "I noticed this repo is empty. Here is a standard Python setup with Testing and CI.")
                 print(f"Setup PR created: {pr_url}")
             except Exception as e:
                 print(f"Title to create PR: {e}")
