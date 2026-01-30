# MegaSchool Coding Agents

Autonomous AI-powered development system that writes code, reviews PRs, and fixes bugs based on natural language descriptions.

## What It Does

1. **Code Agent**: Writes code from Issue descriptions
2. **Reviewer Agent**: Automatically reviews Pull Requests
3. **Fixer Loop**: Iteratively fixes code based on feedback (`/fix` command)
4. **Auto-Setup**: Detects empty repos and proposes linter/CI configuration
5. **Interactive Refinement**: Rejects vague tasks and allows refinement via comments (`/retry`)
6. **Smart Context (RAG)**: Builds a project map and selects only relevant files

## Task Lifecycle

1. **Issue**: Create an issue with label `ready-to-code`
2. **Validation**: Agent validates description quality
   - If OK → starts work
   - If rejected → removes label and explains why
3. **Refinement**: Add details in comments (use `/retry` or re-add label)
4. **PR**: Agent creates Pull Request with solution
5. **Review**: Comment on PR with `/fix` to request changes

## Web Dashboard

Monitor agent activity in real-time: [Dashboard](https://bbanv77fpp9clmjgi7r9.containers.yandexcloud.net/)

---

## Demo Experiment: Rejection + Success Flow

This experiment demonstrates the agent's validation mechanism and end-to-end workflow.

### Step 1: Incorrect Request (Rejection)

**Create Issue:**
- **Title**: `Add feature`
- **Body**: `Make it better`
- **Label**: `ready-to-code`

**Expected Result:**
1. Agent validates the issue
2. Rejects it with comment: *"Description is too vague. Please specify what feature to add and provide implementation details."*
3. Removes `ready-to-code` label
4. Dashboard shows: `Task Rejected`

### Step 2: Correct Request (Success)

**Add Comment to Same Issue:**
```
Create a new Python file `src/utils/logger.py` with a simple logging function:
- Function name: setup_logger(name: str)
- Should configure and return a logger instance
- Use Python's built-in logging module
- Set format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

**Expected Result:**
1. Agent re-validates (triggered by `/retry` comment or manual label addition)
2. Validation passes
3. Agent creates branch `fix-issue-<N>`
4. Generates code for `src/utils/logger.py`
5. Creates Pull Request with implementation
6. Dashboard shows timeline:
   - Started working on Issue
   - Validation Passed
   - Analyzing repository
   - Applying changes to 1 files
   - PR Created

### Verification

- **Branch**: Check that `fix-issue-<N>` branch exists
- **PR**: Verify PR contains `src/utils/logger.py` with correct implementation
- **Dashboard**: Timeline shows all agent steps with icons

---

## Performance Metrics

10 algorithmic tasks tested (script: `experiments/benchmark.py`, model: gpt-4o-mini):

| Metric | Value | Comment |
| :--- | :--- | :--- |
| **Success Rate** | **100%** | 10/10 tasks solved correctly |
| **Avg. Time** | **~7.2s** | Generation time (excluding CI/CD) |
| **Iterations** | **1.0** | All tasks solved zero-shot |

### Bug Fix Experiment

**Scenario**: Calculator app with `ZeroDivisionError` when grade list is empty.

**Result**: Agent analyzed `main.py` and `calculator.py`, identified the bug, added empty list check. No other code modified.

*Full report*: `experiments/BUG_FIX_REPORT.md`

---

## Usage Options

### Option 1: Use Our Hosted Agent (Quickest)

1. Install GitHub App: [MegaSchool Agent](https://github.com/apps/megaschool-agent-sikion)
2. Select repositories to grant access
3. **IMPORTANT**: In repo `Settings` → `Actions` → `General` → `Workflow permissions`:
   - Enable **"Allow GitHub Actions to create and approve pull requests"**
4. Create Issue with label `ready-to-code`

*Note: Runs on our demo server.*

### Option 2: Run in Your GitHub Actions (Your API Keys)

1. Fork this repository
2. Add secrets in `Settings` → `Secrets and variables` → `Actions`:
   - `LLM_API_KEY`: Your OpenAI/Yandex API key
   - `YC_FOLDER_ID`: Yandex Cloud folder ID (if using YandexGPT)
   - `DASHBOARD_API_URL`: Your dashboard URL (optional, for logs)
3. Enable workflows in `Actions` tab

Agent runs in your fork using your keys.

### Option 3: Self-Hosted Server with Webhooks (Advanced)

For full control over webhooks and server infrastructure:

See [docs/github_app_setup.md](docs/github_app_setup.md) for GitHub App creation and configuration.

### Option 4: Docker / Docker Compose

**Docker:**
```bash
docker build -t megaschool-agent .
docker run -d -p 8000:8080 --env-file .env --name my-agent megaschool-agent
```

**Docker Compose** (recommended):
```bash
docker-compose up -d --build
```

Server runs on `http://localhost:8000`. Use ngrok for webhooks.

---

## Configuration

Supports any OpenAI-compatible LLM (including YandexGPT):

- `LLM_BASE_URL`: API endpoint (default: `https://api.openai.com/v1`)
- `LLM_MODEL`: Model name (e.g., `gpt-4o`, `yandexgpt-lite`)
- `MAX_ITERATIONS`: Max fix attempts (default: 5)

---

## Contact

Author: Nikita Muravya  
Telegram: [t.me/nmuravya](https://t.me/nmuravya)

*Developed for MegaSchool Competition.*
