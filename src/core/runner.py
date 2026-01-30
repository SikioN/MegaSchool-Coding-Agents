import os
import subprocess
import tempfile
from typing import List
from src.core.config import Config
from src.core.github_app_auth import GitHubAppAuth

def get_env_with_token(installation_id: int) -> dict:
    """Generates env vars with Installation Token for the subprocess."""
    token = GitHubAppAuth.get_installation_token(installation_id)
    
    env = os.environ.copy()
    env["GITHUB_TOKEN"] = token
    # Ensure other secrets are passed
    env["LLM_API_KEY"] = Config.OPENAI_API_KEY or ""
    env["YC_FOLDER_ID"] = Config.YC_FOLDER_ID or ""
    env["LLM_BASE_URL"] = Config.LLM_BASE_URL or ""
    env["LLM_MODEL"] = Config.LLM_MODEL or ""
    return env

def run_in_temp_repo(repo_full_name: str, env: dict, command: List[str]):
    """Clones repo and runs command in temp dir."""
    token = env["GITHUB_TOKEN"]
    # Clone URL with token
    clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Cloning {repo_full_name} to {temp_dir}...")
        try:
            subprocess.run(["git", "clone", clone_url, temp_dir], check=True, capture_output=True)
            # Configure user for commits
            subprocess.run(["git", "config", "user.email", "agent@megaschool.ai"], cwd=temp_dir, check=True)
            subprocess.run(["git", "config", "user.name", "MegaSchool Agent"], cwd=temp_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone: {e.stderr}")
            return

        print(f"Running command: {' '.join(command)}")
        try:
            import sys
            # Ensure we run with the same python executable
            full_command = [sys.executable, "-m"] + command[2:] if command[0] == "python" else command
            
            result = subprocess.run(
                full_command, 
                cwd=temp_dir, 
                env=env,
                capture_output=True,
                text=True
            )
            print(f"Agent Output:\n{result.stdout}")
            if result.stderr:
                print(f"Agent Error:\n{result.stderr}")
                
        except Exception as e:
            print(f"Error running agent: {e}")

def run_code_agent_task(installation_id: int, repo_name: str, issue_url: str):
    env = get_env_with_token(installation_id)
    command = ["python", "-m", "src.main", "code", "--issue", issue_url]
    run_in_temp_repo(repo_name, env, command)

def run_fix_agent_task(installation_id: int, repo_name: str, pr_url: str, issue_url: str):
    env = get_env_with_token(installation_id)
    command = ["python", "-m", "src.main", "fix", "--pr", pr_url, "--issue", issue_url]
    run_in_temp_repo(repo_name, env, command)

def run_reviewer_agent_task(installation_id: int, repo_name: str, pr_url: str):
    env = get_env_with_token(installation_id)
    # Reviewer typically treats PR as issue for linking
    command = ["python", "-m", "src.main", "review", "--pr", pr_url, "--issue", pr_url]
    run_in_temp_repo(repo_name, env, command)
