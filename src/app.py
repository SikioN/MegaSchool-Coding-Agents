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
from src.core.auto_setup import run_auto_setup
from src.core.runner import run_code_agent_task, run_fix_agent_task, run_reviewer_agent_task

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
async def read_events(repo: str = None):
    return get_recent_events(repo_name=repo)

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

    elif event_type == "installation" and payload.get("action") == "created":
        # Handle new installation -> Scan Repos
        installation_id = payload["installation"]["id"]
        repositories = payload.get("repositories", [])
        
        if repositories:
             background_tasks.add_task(run_auto_setup, installation_id, repositories)
        return {"status": "scanning_repos"}

    elif event_type == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
        background_tasks.add_task(run_reviewer_agent, payload)
        return {"status": "processing_pr"}

    return {"status": "ignored"}

# ---------------------------------------------------------------------
# Agent Runners (Payload Wrappers)
# ---------------------------------------------------------------------

def run_code_agent(payload: dict):
    installation_id = payload["installation"]["id"]
    repo_name = payload["repository"]["full_name"]
    issue_url = payload["issue"]["html_url"]
    run_code_agent_task(installation_id, repo_name, issue_url)

def run_fix_agent(payload: dict):
    installation_id = payload["installation"]["id"]
    repo_name = payload["repository"]["full_name"]
    pr_url = payload["issue"]["pull_request"]["html_url"]
    issue_url = payload["issue"]["html_url"]
    run_fix_agent_task(installation_id, repo_name, pr_url, issue_url)

def run_reviewer_agent(payload: dict):
    installation_id = payload["installation"]["id"]
    repo_name = payload["repository"]["full_name"]
    pr_url = payload["pull_request"]["html_url"]
    run_reviewer_agent_task(installation_id, repo_name, pr_url)

if __name__ == "__main__":
    import uvicorn
    import sys
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
