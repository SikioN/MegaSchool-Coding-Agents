
def run_auto_setup(installation_id: int, repositories: list):
    """
    Scans new repositories and creates setup issues if needed.
    """
    from github import Github, Auth
    from src.core.repo_scanner import RepoScanner
    
    print(f"🔍 Starting Auto-Setup for Installation {installation_id}")
    
    token = GitHubAppAuth.get_installation_token(installation_id)
    auth = Auth.Token(token)
    gh = Github(auth=auth)
    
    for repo_data in repositories:
        full_name = repo_data["full_name"]
        print(f"  - Scanning {full_name}...")
        
        try:
            repo = gh.get_repo(full_name)
            missing_items = RepoScanner.scan(repo)
            
            if missing_items:
                print(f"    ⚠️ Missing: {missing_items}")
                # Create Issue
                title = "feat: Configure Development Environment (Auto-Setup)"
                body = (
                    "🤖 **Auto-Setup Detected**\n\n"
                    "I noticed this repository is missing some standard configurations:\n"
                )
                for item in missing_items:
                    body += f"- [ ] {item}\n"
                
                body += (
                    "\n**Shall I set them up for you?**\n"
                    "I have assigned the `ready-to-code` label, so I will start working on this immediately!\n\n"
                    "*(If you do not want this, please close this issue or remove the label)*"
                )
                
                issue = repo.create_issue(title=title, body=body, labels=["ready-to-code"])
                print(f"    ✅ Created Issue #{issue.number}: {issue.html_url}")
                
                # Log event to DB
                log_event("auto_setup", full_name, {
                    "action": "created_issue",
                    "issue_url": issue.html_url,
                    "missing": missing_items
                })
                
                # Run agent directly
                from src.core.runner import run_code_agent_task
                run_code_agent_task(installation_id, full_name, issue.html_url)
            else:
                print("    ✨ Repo seems healthy.")
                
        except Exception as e:
            print(f"    ❌ Error scanning {full_name}: {e}")
