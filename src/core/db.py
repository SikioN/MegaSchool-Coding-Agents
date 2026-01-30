import sqlite3
import json
import time
from typing import List, Dict, Any

DB_PATH = "events.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                repo_name TEXT,
                details TEXT,
                timestamp REAL
            )
        ''')
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON events (timestamp)
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Init Error: {e}")

import os
import requests

def log_event(event_type: str, repo_name: str, details: Dict[str, Any]):
    # 1. Remote Logging (for GitHub Actions)
    dashboard_url = os.environ.get("DASHBOARD_API_URL") # e.g. https://func-url.../
    
    if dashboard_url:
        try:
            # Clean URL
            if not dashboard_url.endswith("/"):
                dashboard_url += "/"
            
            api_endpoint = dashboard_url + "api/logs"
            
            payload = {
                "event_type": event_type,
                "repo_name": repo_name,
                "details": details
            }
            # Timeout is short to not block the agent
            requests.post(api_endpoint, json=payload, timeout=2)
        except Exception as e:
            # Silent fail for remote logs, don't crash agent
            print(f"Remote Log Warning: {e}")

    # 2. Local Logging (Always log locally as backup/for Server mode)
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO events (event_type, repo_name, details, timestamp) VALUES (?, ?, ?, ?)",
            (event_type, repo_name, json.dumps(details), time.time())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Log Error: {e}")

def get_recent_events(limit: int = 20, repo_name: str = None) -> List[Dict[str, Any]]:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = "SELECT * FROM events"
        params = []
        
        if repo_name:
            query += " WHERE repo_name = ?"
            params.append(repo_name)
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        c.execute(query, tuple(params))
        rows = c.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append({
                "id": row["id"],
                "event_type": row["event_type"],
                "repo_name": row["repo_name"],
                "details": json.loads(row["details"]),
                "timestamp": row["timestamp"]
            })
        return events
    except Exception:
        return []
