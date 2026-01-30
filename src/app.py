import os
import shutil
import tempfile
import asyncio
import subprocess
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from src.core.config import Config
from src.core.github_app_auth import GitHubAppAuth
from src.core.webhook_handler import WebhookVerificator
from src.core.db import init_db, log_event, get_recent_events

app = FastAPI(title="MegaSchool Coding Agent")
templates = Jinja2Templates(directory="src/templates")

@app.on_event("startup")
def startup_event():
    init_db()

# ---------------------------------------------------------------------
# Dashboard Routes
# ---------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/events")
async def read_events():
    return get_recent_events()

# ---------------------------------------------------------------------
# Webhook Handler
# ---------------------------------------------------------------------

@app.post("/webhook")
async def handle_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    _ = Depends(WebhookVerificator.verify_signature)
):
    event_type = request.headers.get("X-GitHub-Event")
    payload = await request.json()
    
    print(f"Received event: {event_type}")
    repo_name = payload.get("repository", {}).get("full_name", "unknown")
    
    # 1. Log Event to DB
    log_details = {"action": payload.get("action"), "hook_id": payload.get("hook_id")}
    
    if event_type == "issues":
        log_details["title"] = payload.get("issue", {}).get("title")
        log_details["url"] = payload.get("issue", {}).get("html_url")
    elif event_type == "pull_request":
        log_details["title"] = payload.get("pull_request", {}).get("title")
        log_details["url"] = payload.get("pull_request", {}).get("html_url")
    
    log_event(event_type, repo_name, log_details)

    # 2. Process Event
    if event_type == "ping":
        return {"status": "pong"}
    
    if event_type == "issues" and payload.get("action") == "labeled":
        triggered_label = payload.get("label", {}).get("name")
        if triggered_label == "ready-to-code":
             background_tasks.add_task(run_code_agent, payload)
        return {"status": "processing_issue"}

    elif event_type == "issue_comment" and payload.get("action") == "created":
        comment_body = payload["comment"]["body"]
        if "/fix" in comment_body:
             if "pull_request" in payload["issue"]:
                  background_tasks.add_task(run_fix_agent, payload)
        return {"status": "processing_comment"}

    elif event_type == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
        background_tasks.add_task(run_reviewer_agent, payload)
        return {"status": "processing_pr"}

    return {"status": "ignored"}

# ---------------------------------------------------------------------
# Agent Runners (Subprocess wrappers)
# ---------------------------------------------------------------------

def _get_env_with_token(installation_id: int) -> dict:
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

def _run_in_temp_repo(repo_full_name: str, env: dict, command: list):
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
            full_command = [sys.executable, "-m"] + command[2:] 
            
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


def run_code_agent(payload: dict):
    installation_id = payload["installation"]["id"]
    repo_name = payload["repository"]["full_name"]
    issue_url = payload["issue"]["html_url"]
    
    env = _get_env_with_token(installation_id)
    command = ["python", "-m", "src.main", "code", "--issue", issue_url]
    _run_in_temp_repo(repo_name, env, command)

def run_fix_agent(payload: dict):
    installation_id = payload["installation"]["id"]
    repo_name = payload["repository"]["full_name"]
    pr_url = payload["issue"]["pull_request"]["html_url"]
    issue_url = payload["issue"]["html_url"]
    
    env = _get_env_with_token(installation_id)
    command = ["python", "-m", "src.main", "fix", "--pr", pr_url, "--issue", issue_url]
    _run_in_temp_repo(repo_name, env, command)

def run_reviewer_agent(payload: dict):
    installation_id = payload["installation"]["id"]
    repo_name = payload["repository"]["full_name"]
    pr_url = payload["pull_request"]["html_url"]
    issue_url = pr_url 
    
    env = _get_env_with_token(installation_id)
    command = ["python", "-m", "src.main", "review", "--pr", pr_url, "--issue", issue_url]
    _run_in_temp_repo(repo_name, env, command)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
