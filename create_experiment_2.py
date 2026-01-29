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
Please create a new module `src/utils/string_tools.py`.
It should contain:
1. `reverse_string(s: str) -> str`
2. `is_palindrome(s: str) -> bool`

Also please add docstrings.
"""

issue = repo.create_issue(
    title="Feature: Add String Utilities",
    body=item_body
)

print(f"Issue created: {issue.html_url}")
print(f"ISSUE_URL={issue.html_url}")
