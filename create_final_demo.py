import os
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "SikioN/MegaSchool-Coding-Agents"

auth = Auth.Token(TOKEN)
g = Github(auth=auth)
repo = g.get_repo(REPO_NAME)

print(f"Target Repo: {REPO_NAME}")

# Create Issue
item_body = """
Please create a python script `src/algo/fibonacci.py`.
It should contain a function `fib(n: int) -> int` that returns the n-th Fibonacci number.
Implement it recursively.
Add type hints and docstrings.
"""

issue = repo.create_issue(
    title="Feature: Add Fibonacci Algorithm",
    body=item_body
)

print(f"Issue created: {issue.html_url}")
print(f"ISSUE_URL={issue.html_url}")
