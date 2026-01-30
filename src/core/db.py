import os
import time
import json
import sqlite3
import requests
import boto3
from typing import List, Dict, Any

DB_PATH = "events.db"

# S3 Configuration
S3_BUCKET = os.environ.get("S3_BUCKET_NAME")
S3_ENDPOINT = "https://storage.yandexcloud.net"

def _get_s3_client():
    # Use IAM role if available (Serverless), or fallback to env vars (Local)
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        # If credentials are not explicitly provided, boto3 looks for env vars 
        # or Instance Metadata (which works in Yandex Serverless with Service Account)
    )

def init_db():
    if S3_BUCKET:
        print(f"✅ Using S3 Storage: {S3_BUCKET}")
        return
        
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
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Init Error: {e}")

def log_event(event_type: str, repo_name: str, details: Dict[str, Any]):
    # 1. Remote Logging (Agent -> Server)
    # If we are the Agent (running in GitHub Actions) and have a Dashboard URL
    dashboard_url = os.environ.get("DASHBOARD_API_URL")
    if dashboard_url:
        try:
            if not dashboard_url.endswith("/"):
                dashboard_url += "/"
            api_endpoint = dashboard_url + "api/logs"
            payload = {
                "event_type": event_type,
                "repo_name": repo_name,
                "details": details
            }
            requests.post(api_endpoint, json=payload, timeout=2)
            return # If remote log sent, we are done
        except Exception as e:
            print(f"Remote Log Warning: {e}")

    # 2. S3 Logging (Server Side)
    if S3_BUCKET:
        try:
            s3 = _get_s3_client()
            timestamp = time.time()
            # Key format: events/TIMESTAMP_UUID.json to ensure uniqueness and sortability
            import uuid
            key = f"events/{int(timestamp * 1000)}_{uuid.uuid4().hex[:6]}.json"
            
            data = {
                "id": key, # Use key as ID
                "event_type": event_type,
                "repo_name": repo_name,
                "details": details,
                "timestamp": timestamp
            }
            
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=json.dumps(data),
                ContentType='application/json'
            )
            print(f"Logged to S3: {key}")
            return
        except Exception as e:
            print(f"S3 Log Error: {e}")
            # Fallback to local DB if S3 fails

    # 3. Local SQLite Logging (Fallback / Local Dev)
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

def get_recent_events(limit: int = 50, repo_name: str = None) -> List[Dict[str, Any]]:
    # 1. S3 Reading
    if S3_BUCKET:
        try:
            s3 = _get_s3_client()
            # List objects in 'events/' prefix
            response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="events/")
            
            if 'Contents' not in response:
                return []
                
            # Sort by Key (which starts with timestamp) Descending
            objects = sorted(response['Contents'], key=lambda x: x['Key'], reverse=True)
            
            # Take top N
            objects = objects[:limit]
            
            events = []
            for obj in objects:
                # Fetch object content
                # Optimization: In a real system, we might index this. 
                # unique S3 reads for each refresh is naive but fine for a demo.
                obj_resp = s3.get_object(Bucket=S3_BUCKET, Key=obj['Key'])
                content = obj_resp['Body'].read().decode('utf-8')
                event = json.loads(content)
                
                if repo_name and event.get('repo_name') != repo_name:
                    continue
                    
                events.append(event)
                
            return events
        except Exception as e:
            print(f"S3 Read Error: {e}")
            return []

    # 2. Local SQLite Reading
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = "SELECT * FROM events"
        params = []
        
        if repo_name:
            query += " WHERE repo_name = ?"
            params.append(repo_name)
            
        query += " ORDER BY id DESC LIMIT ?"
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
