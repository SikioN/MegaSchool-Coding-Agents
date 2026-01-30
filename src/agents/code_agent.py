import os
import time
from src.core.llm import get_llm
from src.core.config import Config
from src.core.git_provider import GitProvider
from src.core.utils import parse_code_blocks, apply_file_changes

class CodeAgent:
    """
    Агент-разработчик.
    Отвечает за анализ задач, генерацию кода и создание Pull Requests.
    """
    def __init__(self, git_provider: GitProvider | None = None):
        self.llm = get_llm()
        self.git = git_provider or GitProvider()

    def _log_step(self, message: str, details: dict = None, icon: str = "ℹ️"):
        """
        Logs a granular step to the DB for the Dashboard.
        """
        try:
            from src.core.db import log_event
            repo_name = self.git._get_repo_name_from_remote() or "unknown"
            
            payload = {"message": message, "icon": icon}
            if details:
                payload.update(details)
                
            log_event("agent_step", repo_name, payload)
            print(f"[{icon}] {message}")
        except Exception as e:
            print(f"Log Error: {e}")

    def run(self, issue_url: str):
        """
        Запускает процесс выполнения задачи (Initial Flow).
        """
        self.current_issue_url = issue_url
        print(f"Code Agent запущен для задачи: {issue_url}")
        
        self._log_step(f"Started working on Issue {issue_url.split('/')[-1]}", icon="🏁")
        
        # 1. Чтение задачи
        self._log_step("Fetching Issue content...", icon="📥")
        issue_content = self.git.get_issue(issue_url)
        
        # 1.a Добавляем комментарии (User Refinement)
        comments = self.git.get_issue_comments(issue_url)
        if comments:
            print(f"Найдены комментарии к задаче ({len(comments)} chars). Добавляем в контекст.")
            issue_content += f"\n\nUPDATES (Comments):\n{comments}"
            self._log_step("Attached user comments to context", icon="🗣️")
            
        print("Содержимое задачи получено (с учетом комментариев).")
        
        # 1.1 ВАЛИДАЦИЯ ЗАДАЧИ
        self._log_step("Validating Issue description...", icon="🛡")
        is_valid, reason = self._validate_issue(issue_content)
        if not is_valid:
            self._log_step(f"Task Rejected: {reason}", icon="❌")
            print(f"❌ Задача отклонена: {reason}")
            rejection_comment = (
                f"❌ **Task Rejected**\n\n"
                f"I cannot process this request because the description is insufficient.\n"
                f"**Reason**: {reason}\n\n"
                f"Please update the issue with clear requirements, file names, and acceptance criteria."
            )
            self.git.post_comment(issue_url, rejection_comment)
            
            # Remove Label
            self.git.remove_label(issue_url, "ready-to-code")
            
            # Log failure to DB
            from src.core.db import log_event
            repo_name = self.git._get_repo_name_from_remote() or "unknown"
            log_event("agent_error", repo_name, {"error": "Validation Failed", "reason": reason})
            return
            
        self._log_step("Validation Passed. Starting pipeline.", icon="✅")

        # 2. Сбор контекста
        self._log_step("Analyzing repository context...", icon="🔍")
        context = self._get_context()
        
        # 3. Генерация плана и кода
        system_prompt = self._get_system_prompt()
        user_prompt = f"""
Текущие файлы проекта:
{context}

Задача:
{issue_content}

Задание:
Проанализируй задачу и перепиши необходимые файлы для её решения или реализации фичи.
Верни ПОЛНОЕ содержимое модифицированных файлов.
"""
        print("Запрос к LLM...")
        self._log_step("Thinking... (Querying LLM)", icon="🧠")
        response = self.llm.generate(system_prompt, user_prompt)
        
        # 4. Обработка ответа и создание PR
        self._apply_and_push(response, f"Решение задачи {issue_url.split('/')[-1]}", issue_url)

    def _validate_issue(self, content: str) -> tuple[bool, str]:
        """
        Проверяет качество описания задачи.
        Возвращает (Passed, Reason).
        """
        # Попытка извлечь чистое тело задачи (убираем Title: ...)
        body = content
        if "Description:" in content:
            body = content.split("Description:", 1)[1].strip()
        
        # 1. Heuristic: Length Check
        if len(body) < 30:
            return False, "Insufficient description. Please provide more details."
            
        # 2. Heuristic: Keyword Check
        keywords = ["create", "add", "implement", "fix", "update", "refactor", "change", "delete", "remove"]
        if not any(word in body.lower() for word in keywords):
            return False, "No actionable keywords found (e.g., 'create', 'fix', 'implement'). What should I do?"
            
        return True, "OK"


    def run_fix(self, pr_url: str, issue_url: str):
        """
        Запускает цикл исправления на основе ревью.
        """
        print(f"Code Agent запущен в режиме FIX для PR: {pr_url}")
        self._log_step(f"Starting Fix Loop for PR {pr_url.split('/')[-1]}", icon="🔧", details={"pr_url": pr_url})
        
        # 1. Проверка лимита итераций
        comments = self.git.get_pr_comments(pr_url)
        request_changes_count = comments.count("[REQUEST_CHANGES]")
        
        if request_changes_count >= Config.MAX_ITERATIONS:
             print(f"CRITICAL: Достигнут лимит итераций ({Config.MAX_ITERATIONS}). Остановка.")
             self._log_step("Max iterations reached. Stopping.", icon="🛑")
             self.git.post_comment(pr_url, f"❌ Code Agent остановил работу: превышен лимит итераций ({Config.MAX_ITERATIONS}). Требуется вмешательство человека.")
             return

        # 2. Checkout ветки PR
        self._log_step("Checking out PR branch...", icon="🌿")
        self.git.checkout_pr(pr_url)
        
        # 3. Сбор информации
        self._log_step("Reading PR comments and diff...", icon="📖")
        issue_content = self.git.get_issue(issue_url)
        pr_comments = self.git.get_pr_comments(pr_url)
        pr_diff = self.git.get_pr_diff(pr_url)
        context = self._get_context() # Текущее состояние файлов
        
        # 3. Генерация исправлений
        system_prompt = self._get_system_prompt()
        user_prompt = f"""
МЫ НАХОДИМСЯ НА ИТЕРАЦИИ ИСПРАВЛЕНИЙ.

Код проекта:
{context}

Изменения в PR (Diff):
{pr_diff}

Оригинальная задача:
{issue_content}

ЗАМЕЧАНИЯ РЕВЬЮЕРА (Comments):
{pr_comments}

Задание:
Исправь код согласно замечаниям ревьюера.
Верни ПОЛНОЕ содержимое исправленных файлов.
"""
        print("Запрос к LLM для исправлений...")
        self._log_step("Analyzing Reviewer feedback...", icon="🧐")
        self._log_step("Thinking... (Generating Fix)", icon="🧠")
        response = self.llm.generate(system_prompt, user_prompt)
        
        # 4. Применение и пуш
        self._apply_and_push(response, "Исправления по замечаниям ревью", issue_url, is_fix=True)

    def _apply_and_push(self, llm_response: str, title: str, issue_url: str, is_fix: bool = False):
        """
        Парсит ответ, примененияет изменения, коммитит и пушит (создает PR если нужно).
        """
        from src.core.db import log_event
        
        changes = parse_code_blocks(llm_response)
        repo_name = self.git._get_repo_name_from_remote() or "unknown/repo"
        
        if not changes:
            print("LLM не сгенерировала изменений.")
            self._log_step("LLM did not return any code changes.", icon="⚠️")
            log_event("agent_error", repo_name, {"error": "LLM returned no code changes", "issue": issue_url})
            return

        # Если это новая задача, создаем ветку (если не fix mode, где мы уже на ветке)
        if not is_fix:
            timestamp = int(time.time())
            branch_name = f"fix/issue-{timestamp}"
            self.git.create_branch(branch_name)
            self._log_step(f"Created branch `{branch_name}`", icon="🌿")
        
        # LOGGING FILE CHANGES
        file_list = [c.get('path', c.get('file', 'unknown')) for c in changes]
        self._log_step(f"Applying changes to {len(file_list)} files: {', '.join(file_list)}", icon="📝")
        
        apply_file_changes(changes)
        
        # Коммит
        self.git.commit_changes(title)
        
        # Если fix mode, мы просто пушим в текущую ветку (pr обновляется автоматически)
        if is_fix:
            # Коммит
            self.git.commit_changes(title)
            # Просто пуш
            self._log_step("Pushing fix to remote...", icon="📤")
            self.git.create_pr("Update", "Fixes", "main") # create_pr делает push
            print(f"Изменения отправлены в PR.")
            self._log_step("Fix pushed to PR successfully", icon="✅")
            log_event("agent_action", repo_name, {"action": "changes_pushed", "pr": issue_url}) # issue_url here is PR url in fix mode
        else:
            # 6. Коммит и создание PR
            self.git.commit_changes(f"Решение задачи {issue_url}")
            
            issue_number = issue_url.split('/')[-1]
            
            self._log_step("Creating Pull Request...", icon="🚀")
            
            pr_url = self.git.create_pr(
                title=f"Fix: Issue {issue_number}", 
                body=f"Реализованы изменения на основе описания задачи.\n\nCloses #{issue_number}"
            )
            
            print(f"Code Agent завершил работу. PR создан: {pr_url}")
            
            self._log_step(f"Pull Request Created: {pr_url}", icon="🎉", details={"pr_url": pr_url})
            
            # LOG SUCCESS TO DB (For Dashboard)
            log_event("pull_request", repo_name, {
                "action": "opened_by_agent", 
                "title": title, 
                "html_url": pr_url,
                "issue_url": issue_url
            })
            
            # COMMENT ON ISSUE
            if "Error creating PR" in pr_url:
                 comment_body = (
                    f"⚠️ **Task Completed but PR Failed**\n\n"
                    f"I implemented the changes, but could not create a Pull Request.\n"
                    f"**Error Details:**\n`{pr_url}`\n\n"
                    f"Please check GitHub App Permissions (Pull Requests: Read & Write)."
                )
            else:
                comment_body = (
                    f"🚀 **Task Completed!**\n\n"
                    f"I have created a Pull Request with the solution: {pr_url}\n\n"
                    f"Please review the changes."
                )
            self.git.post_comment(issue_url, comment_body)

    def _get_context(self) -> str:
        """
        Считывает файлы, используя Smart Context (Repo Map + LLM Selection).
        """
        try:
            from src.core.repo_scanner import RepoMapGenerator
        except ImportError:
            print("RepoMapGenerator not found. Falling back to naive scan.")
            return self._get_context_legacy()

        # 1. Generate Map
        print("Генерация карты репозитория...")
        self._log_step("Scanning repository structure (Smart Context)...", icon="📡")
        repo_map = RepoMapGenerator.generate_map(".")
        print(f"Карта создана ({len(repo_map)} chars).")

        # 2. Select Files via LLM
        issue_content = self.git.get_issue(self.current_issue_url) if hasattr(self, 'current_issue_url') else "Task"
        relevant_files = self._select_relevant_files(issue_content, repo_map)
        
        self._log_step(f"AI Selected {len(relevant_files)} relevant files", icon="🎯", details={"files": relevant_files})
        print(f"LLM выбрала файлы: {relevant_files}")
        
        # 3. Read Files
        context = ""
        for path in relevant_files:
            if os.path.exists(path) and os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    context += f"\nFile: `{path}`\n```\n{content}\n```\n"
                except Exception as e:
                    print(f"Failed to read {path}: {e}")
            else:
                 # File might be new (to be created), so we just skip reading it
                 pass
                 
        return context

    def _select_relevant_files(self, issue: str, repo_map: str) -> list[str]:
        """
        Asks LLM to select relevant files based on the map.
        """
        system_prompt = """You are a Principal Software Architect.
Your task is to identify which files in the repository are relevant to a specific Issue/Task.
You must return a raw JSON list of file paths.

Example Output:
["src/main.py", "src/auth/login.py"]

Do not output ANY explanation. Just the JSON list.
"""
        user_prompt = f"""
REPO MAP:
{repo_map}

TASK:
{issue}

Which files should I read or modify to solve this task?
Includes files that need to be modified and files that provide necessary context (definitions, helpers).
If the task requires creating a new file, do not list it here (as it doesn't exist yet), unless you need to check if it conflicts.
Return JSON list of paths.
"""
        try:
            response = self.llm.generate(system_prompt, user_prompt)
            # Cleanup Markdown wrappers
            clean_json = response.replace("```json", "").replace("```", "").strip()
            import json
            files = json.loads(clean_json)
            if isinstance(files, list):
                return files
            return []
        except Exception as e:
            print(f"Error selecting files: {e}")
            return [] # Fallback to empty or legacy?

    def _get_context_legacy(self) -> str:
        """
        Legacy: Reads all Python files.
        """
        context = ""
        exclude_dirs = {'.git', '.venv', '__pycache__', 'venv', 'env'}
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith(".py") or file in ["Dockerfile", "pyproject.toml"]:
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r") as f:
                            content = f.read()
                        context += f"\nFile: `{path}`\n```python\n{content}\n```\n"
                    except:
                        pass
        return context

    def _get_system_prompt(self) -> str:
        return """Ты опытный Python разработчик ПО.
Твоя задача — прочитать GitHub Issue и модифицировать кодовую базу для её решения.

Формат вывода:
Ты должен вывести изменения в строгом формате для автоматического применения.
Для каждого измененного (или созданного) файла предоставь ПОЛНОЕ содержимое файла.

Формат:
File: `path/to/file.py`
```python
... полный код файла ...
```

Не выводи diff. Выводи полное содержимое файла.
Используй идиоматичный Python 3.11+.
"""
