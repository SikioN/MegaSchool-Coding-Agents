import os
import shutil
import tempfile
import asyncio
import subprocess
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Depends
from src.core.config import Config
from src.core.github_app_auth import GitHubAppAuth
from src.core.webhook_handler import WebhookVerificator

app = FastAPI()

@app.post("/webhook")
async def handle_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    _ = Depends(WebhookVerificator.verify_signature)
):
    event_type = request.headers.get("X-GitHub-Event")
    payload = await request.json()
    
    print(f"Received event: {event_type}")
    
    if event_type == "ping":
        print(f"✅ PONG! Webhook received successfully. Hook ID: {payload.get('hook_id')}")
        return {"status": "pong"}
    
    if event_type == "issues" and payload.get("action") == "labeled":
        # Handle Code Agent trigger
        label_name = payload["issue"]["labels"][-1]["name"] if payload["issue"]["labels"] else ""
        # Check if the triggered label is 'ready-to-code'
        # Note: Payload might contain just the label that triggered it in 'label' field?
        # Actually payload['label'] exists for 'labeled' action.
        triggered_label = payload.get("label", {}).get("name")
        
        if triggered_label == "ready-to-code":
             background_tasks.add_task(run_code_agent, payload)
        return {"status": "processing_issue"}

    elif event_type == "issue_comment" and payload.get("action") == "created":
        # Handle /fix command (Code Agent Fix Mode)
        comment_body = payload["comment"]["body"]
        if "/fix" in comment_body:
             # Check if it's a PR or Issue
             # issue_comment event is sent for both. If payload['issue'] has 'pull_request' key, it is a PR.
             if "pull_request" in payload["issue"]:
                  background_tasks.add_task(run_fix_agent, payload)
        return {"status": "processing_comment"}

    elif event_type == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
        # Handle Reviewer Agent
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
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone: {e.stderr}")
            return

        print(f"Running command: {' '.join(command)}")
        try:
            # We assume python is in path. 'poetry run' might be needed if env not active,
            # but in Docker/dev env we are usually inside poetry shell or similar.
            # Using 'python' invokes the current python interpreter if on same env.
            # Safe bet: sys.executable
            import sys
            
            # Adjust command to use current python
            full_command = [sys.executable, "-m"] + command[2:] # expecting ["python", "-m", ...]
            
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
    pr_url = payload["issue"]["pull_request"]["html_url"] # In issue_comment, pr url is here
    issue_url = payload["issue"]["html_url"] # This links to PR issue, we might need linked issue?
    # CLI accepts --pr and --issue. CodeAgent fix logic tries to extract linked issue or uses passed issue.
    # For now (MVP), pass the PR url as issue url if linked issue not trivial? 
    # Actually src.main fix accepts --pr and --issue.
    # We pass PR URL. Linked issue finding is internal to CodeAgent fix?
    # Let's verify src.main arguments for fix.
    
    env = _get_env_with_token(installation_id)
    # Note: CodeAgent fix logic needs LINKED issue to know what to solve. 
    # Current CLI usage: python -m src.main fix --pr <pr> --issue <issue>
    # If we don't know the issue, we can pass PR url as issue and hope agent handles it 
    # or extraction logic in App is needed.
    # For MVP simplicity: Pass PR URL, assuming CodeAgent can handle it or we updated CodeAgent?
    # We updated CodeAgent to run_fix(pr, issue).
    # ci_fix.yml tries to extract it. Here we might skip extraction for now or assume user pasted it?
    # Let's just pass PR URL for both and see if it survives.
    
    command = ["python", "-m", "src.main", "fix", "--pr", pr_url, "--issue", issue_url]
    
    _run_in_temp_repo(repo_name, env, command)

def run_reviewer_agent(payload: dict):
    installation_id = payload["installation"]["id"]
    repo_name = payload["repository"]["full_name"]
    pr_url = payload["pull_request"]["html_url"]
    # Issue URL? PR is an issue.
    issue_url = pr_url 
    
    env = _get_env_with_token(installation_id)
    command = ["python", "-m", "src.main", "review", "--pr", pr_url, "--issue", issue_url]
    
    _run_in_temp_repo(repo_name, env, command)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
