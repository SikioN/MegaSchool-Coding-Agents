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
Please create a simple python script named `demo_agent.py`.
It should contain a function `greet(name)` that prints "Hello, {name}!".
And a main block that calls `greet("Reviewer")`.
"""

issue = repo.create_issue(
    title="Demo: Create Hello World script",
    body=item_body
)

print(f"Issue created: {issue.html_url}")
print(f"ISSUE_URL={issue.html_url}")
