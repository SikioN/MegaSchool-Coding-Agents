
import sys
import os
import json

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.repo_scanner import RepoMapGenerator
from src.agents.code_agent import CodeAgent
from src.core.git_provider import GitProvider

def test_smart_context():
    print("🧪 Testing Smart Context...")
    
    # 1. Test Map Generation
    print("\n[1] Generating Repo Map...")
    repo_map = RepoMapGenerator.generate_map(".")
    print(f"✅ Map generated. Length: {len(repo_map)} chars")
    print(f"First 500 chars:\n{repo_map[:500]}...\n")
    
    # Check if key files are present
    assert "src/agents/code_agent.py" in repo_map
    assert "src/app.py" in repo_map
    print("✅ Key files found in map.")
    
    # 2. Test Selection (requires LLM)
    if not os.environ.get("LLM_API_KEY"):
         print("⚠️ No LLM_API_KEY found. Skipping LLM selection test.")
         return

    print("\n[2] Testing LLM File Selection...")
    agent = CodeAgent(GitProvider()) # No token needed for this test part
    
    task = "Update the README to include new features about Smart Context."
    print(f"Task: {task}")
    
    files = agent._select_relevant_files(task, repo_map)
    print(f"🤖 Selected Files: {files}")
    
    if "README.md" in files:
        print("✅ SUCCESS: README.md was selected!")
    else:
        print("❌ FAILURE: README.md was NOT selected.")
        
    # Test 2: Python Code Task
    task2 = "Add a new method to GitProvider to list branches."
    print(f"\nTask 2: {task2}")
    files2 = agent._select_relevant_files(task2, repo_map)
    print(f"🤖 Selected Files: {files2}")
    
    if any("git_provider.py" in f for f in files2):
         print("✅ SUCCESS: git_provider.py selected.")
    else:
         print("❌ FAILURE: git_provider.py missed.")

if __name__ == "__main__":
    test_smart_context()
