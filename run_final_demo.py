import os
import time
from src.core.git_provider import GitProvider
from src.agents.code_agent import CodeAgent
from src.agents.reviewer_agent import ReviewerAgent
from dotenv import load_dotenv

load_dotenv()

def run_demo():
    print("🚀 Starting Final Demonstration...")
    git = GitProvider()
    
    # 1. Create Issue
    print("1. Creating Demo Issue...")
    title = "Demo: Implement Matrix Math"
    body = """
    Please create a python file `src/algo/matrix.py`.
    Implement a class `Matrix` with:
    - `__init__(self, rows, cols)`
    - `multiply(self, other_matrix)`
    - `transpose(self)`
    Add docstrings and type hints.
    """
    repo_name = "SikioN/MegaSchool-Coding-Agents" # Hardcoded for reliability
    repo = git.gh.get_repo(repo_name)
    issue = repo.create_issue(title=title, body=body, labels=["ready-to-code"])
    print(f"✅ Issue Created: {issue.html_url}")
    
    # 2. Run Code Agent
    print("\n2. Launching Code Agent...")
    code_agent = CodeAgent()
    code_agent.run(issue.html_url)
    
    # Wait a bit for PR to be ready (api lag)
    time.sleep(5)
    
    # Find the PR created by the agent
    pulls = repo.get_pulls(state='open', sort='created', direction='desc')
    pr = pulls[0]
    print(f"✅ PR Detected: {pr.html_url}")
    
    # 3. Run Reviewer Agent
    print("\n3. Launching Reviewer Agent...")
    reviewer = ReviewerAgent()
    reviewer.run(pr.html_url, issue.html_url)
    print("✅ Review Complete.")
    
    return issue.html_url, pr.html_url

if __name__ == "__main__":
    issue_url, pr_url = run_demo()
    
    # Generate Report
    with open("DEMO.md", "w") as f:
        f.write("# 🧪 Demonstration Report\n\n")
        f.write("We conducted a live experiment to demonstrate the agent's capabilities.\n\n")
        f.write(f"### 1. Task Creation\nWe created an Issue requesting a Matrix Multiplication class:\n- **Issue**: [{issue_url}]({issue_url})\n\n")
        f.write(f"### 2. Autonomous Coding\nThe Code Agent analyzed the task, wrote the code in `src/algo/matrix.py`, and submitted a Pull Request:\n- **Pull Request**: [{pr_url}]({pr_url})\n\n")
        f.write(f"### 3. AI Review\nThe Reviewer Agent analyzed the changes and posted feedback directly in the PR.\n")
    
    print("\n🎉 Demo finished! Report saved to DEMO.md")
