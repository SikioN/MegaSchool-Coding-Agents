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
    def __init__(self):
        self.llm = get_llm()
        self.git = GitProvider()

    def run(self, issue_url: str):
        """
        Запускает процесс выполнения задачи (Initial Flow).
        """
        print(f"Code Agent запущен для задачи: {issue_url}")
        
        # 1. Чтение задачи
        issue_content = self.git.get_issue(issue_url)
        print("Содержимое задачи получено.")
        
        # 2. Сбор контекста
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
        response = self.llm.generate(system_prompt, user_prompt)
        
        # 4. Обработка ответа и создание PR
        self._apply_and_push(response, f"Решение задачи {issue_url.split('/')[-1]}", issue_url)

    def run_fix(self, pr_url: str, issue_url: str):
        """
        Запускает цикл исправления на основе ревью.
        """
        print(f"Code Agent запущен в режиме FIX для PR: {pr_url}")
        
        # 1. Проверка лимита итераций
        comments = self.git.get_pr_comments(pr_url)
        request_changes_count = comments.count("[REQUEST_CHANGES]")
        
        if request_changes_count >= Config.MAX_ITERATIONS:
             print(f"CRITICAL: Достигнут лимит итераций ({Config.MAX_ITERATIONS}). Остановка.")
             self.git.post_comment(pr_url, f"❌ Code Agent остановил работу: превышен лимит итераций ({Config.MAX_ITERATIONS}). Требуется вмешательство человека.")
             return

        # 2. Checkout ветки PR
        self.git.checkout_pr(pr_url)
        
        # 3. Сбор информации
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
        response = self.llm.generate(system_prompt, user_prompt)
        
        # 4. Применение и пуш
        self._apply_and_push(response, "Исправления по замечаниям ревью", issue_url, is_fix=True)

    def _apply_and_push(self, llm_response: str, title: str, issue_url: str, is_fix: bool = False):
        """
        Парсит ответ, применяет изменения, коммитит и пушит (создает PR если нужно).
        """
        changes = parse_code_blocks(llm_response)
        if not changes:
            print("LLM не сгенерировала изменений.")
            return

        # Если это новая задача, создаем ветку (если не fix mode, где мы уже на ветке)
        if not is_fix:
            timestamp = int(time.time())
            branch_name = f"fix/issue-{timestamp}"
            self.git.create_branch(branch_name)
        
        apply_file_changes(changes)
        
        # Коммит
        self.git.commit_changes(title)
        
        # Если fix mode, мы просто пушим в текущую ветку (pr обновляется автоматически)
        if is_fix:
            # Коммит
            self.git.commit_changes(title)
            # Просто пуш
            self.git.create_pr("Update", "Fixes", "main") # create_pr делает push
            print(f"Изменения отправлены в PR.")
        else:
            # 6. Коммит и создание PR
            self.git.commit_changes(f"Решение задачи {issue_url}")
            
            issue_number = issue_url.split('/')[-1]
            
            pr_url = self.git.create_pr(
                title=f"Fix: Issue {issue_number}", 
                body=f"Реализованы изменения на основе описания задачи.\n\nCloses #{issue_number}"
            )
            
            print(f"Code Agent завершил работу. PR создан: {pr_url}")

    def _get_context(self) -> str:
        """
        Считывает Python файлы, игнорируя мусор.
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
