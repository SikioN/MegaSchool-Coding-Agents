import os
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
# We use the PLAYGROUND for the issue/code changes, but the AGENTS from the RELEASE repo will control it.
REPO_NAME = "SikioN/test-agent-playground" 

auth = Auth.Token(TOKEN)
g = Github(auth=auth)
repo = g.get_repo(REPO_NAME)

print(f"Creating verification issue in {REPO_NAME}...")
issue = repo.create_issue(
    title="Verification: Create dummy file",
    body="Please create a file named `verified.txt` with the text 'Works!'."
)
print(f"Issue created: {issue.html_url}")
print(issue.html_url)
