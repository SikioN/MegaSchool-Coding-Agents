
import time
import os
import sys
from typing import List
# Mock config to avoid loading real env if missing
sys.path.append(os.getcwd())
from src.agents.code_agent import CodeAgent
# We need to mock GitProvider to avoid real pushes
from unittest.mock import MagicMock

class MockGitProvider:
    def get_issue(self, url):
        return TASKS.get(url, "Unknown task")
    def _get_repo_name_from_remote(self): return "bench/repo"
    def create_branch(self, name): pass
    def commit_changes(self, msg): pass
    def create_pr(self, title, body, base="main"): return "http://mock.pr/1"
    def post_comment(self, u, b): pass

TASKS = {
    "task/1": "Create a function `factorial(n)` in `math_lib.py`.",
    "task/2": "Create `fibonacci(n)` in `math_lib.py` returning list.",
    "task/3": "Create `is_palindrome(s)` in `str_utils.py`.",
    "task/4": "Create `bubble_sort(arr)` in `sort.py`.",
    "task/5": "Create `binary_search(arr, target)` in `search.py`.",
    "task/6": "Create `validate_email(s)` in `validators.py` with regex.",
    "task/7": "Create `flatten(nested_list)` in `utils.py`.",
    "task/8": "Create `count_words(text)` in `text_stats.py`.",
    "task/9": "Create `transpose_matrix(matrix)` in `matrix.py`.",
    "task/10": "Create `to_json(data)` helper in `json_utils.py`."
}

def run_benchmark():
    print("🚀 Starting Benchmark (10 tasks)...")
    success_count = 0
    total_time = 0
    
    agent = CodeAgent(git_provider=MockGitProvider())
    # Mock LLM if no key (fallback)
    if not os.getenv("LLM_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("⚠️ No API Key found. Using Mock LLM for demonstration.")
        agent.llm = MagicMock()
        agent.llm.generate.return_value = "File: `mock.py`\n```python\ndef mock(): pass\n```"

    for i, (url, prompt) in enumerate(TASKS.items(), 1):
        print(f"[{i}/10] Running task: {prompt[:30]}...")
        start = time.time()
        try:
            # We override get_issue logic by injecting our prompt via mock, 
            # but CodeAgent calls self.git.get_issue(issue_url).
            # Our MockGitProvider handles this.
            agent.run(url)
            duration = time.time() - start
            success_count += 1
            total_time += duration
            print(f"   ✅ Success ({duration:.2f}s)")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

    print("\n📊 Results:")
    print(f"Success Rate: {success_count}/10 ({success_count*10}%)")
    print(f"Avg Time: {total_time/10:.2f}s")

if __name__ == "__main__":
    run_benchmark()
