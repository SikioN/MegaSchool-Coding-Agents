import os
import shutil
import subprocess
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
RELEASE_REPO_NAME = "MegaSchool-Coding-Agents" # Changed name slightly to be specific

if not TOKEN:
    print("Error: GITHUB_TOKEN not found in .env")
    exit(1)

def run_cmd(cmd, cwd=None):
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

try:
    auth = Auth.Token(TOKEN)
    g = Github(auth=auth)
    user = g.get_user()

    # 1. Create Remote Repo
    print(f"Creating repository {RELEASE_REPO_NAME}...")
    try:
        repo = user.get_repo(RELEASE_REPO_NAME)
        print(f"Repository {RELEASE_REPO_NAME} already exists. Using it.")
    except:
        repo = user.create_repo(RELEASE_REPO_NAME, private=True, description="MegaSchool AI Coding Agents System")
        print(f"Created repository: {repo.html_url}")

    repo_url = repo.clone_url.replace("https://", f"https://{TOKEN}@")

    # 2. Push current folder
    # We initialize a temporary git repo here if one doesn't exist, or add a new remote
    
    # Check if .git exists
    if os.path.isdir(".git"):
        print("Existing git detected. Adding 'release' remote...")
        try:
            run_cmd("git remote remove release")
        except:
            pass
        run_cmd(f"git remote add release {repo_url}")
    else:
        print("Initializing new git...")
        run_cmd("git init")
        run_cmd("git branch -M main")
        run_cmd(f"git remote add release {repo_url}")

    print("Adding files...")
    run_cmd("git add .")
    run_cmd('git commit -m "Initial Release of MegaSchool Coding Agents"')
    
    print("Pushing to release...")
    run_cmd("git push -u release main --force")
    
    print("Done! Repository is ready.")
    print(f"URL: {repo.html_url}")

except Exception as e:
    print(f"Error: {e}")
