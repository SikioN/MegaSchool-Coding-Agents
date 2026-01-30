from src.core.llm import get_llm
from src.core.git_provider import GitProvider

class ReviewerAgent:
    """
    Агент-ревьюер.
    Отвечает за анализ Pull Requests и предоставление обратной связи.
    """
    def __init__(self, git_provider: GitProvider | None = None):
        self.llm = get_llm()
        self.git = git_provider or GitProvider()

    def run(self, pr_url: str, issue_url: str):
        """
        Запускает процесс ревью.
        1. Получает требования из задачи.
        2. Получает diff изменений из PR.
        3. Запрашивает анализ у LLM.
        4. Публикует результат в Pull Request.
        """
        print(f"Reviewer Agent запущен для PR: {pr_url}")
        
        # 1. Получение информации
        issue_content = self.git.get_issue(issue_url)
        print("Получение изменений PR...")
        pr_diff = self.git.get_pr_diff(pr_url)
        
        if not pr_diff or "Mock" in pr_diff:
             print("Warning: Could not fetch PR diff.")
        
        # 2. Анализ
        system_prompt = """Ты Старший Разработчик ПО (Senior Software Engineer), проводящий Code Review.
Твоя задача:
1. Проверить, соответствует ли реализация (Diff) требованиям задачи (Issue).
2. Найти потенциальные баги, уязвимости или проблемы с качеством кода.
3. Если код хорош и выполняет задачу, напиши строго первую строку: [APPROVE].
4. Если есть серьезные проблемы или недочеты, напиши строго первую строку: [REQUEST_CHANGES].

После первой строки напиши подробный отзыв. Будь конструктивен.
"""
        
        user_prompt = f"""
TASK REQUIREMENTS:
{issue_content}

CODE CHANGES (DIFF):
{pr_diff}

Review the changes above.
"""
        
        print("Запрос к LLM для ревью...")
        response = self.llm.generate(system_prompt, user_prompt)
        
        print("Результат ревью получен.")
        
        # 3. Публикация комментария
        self.git.post_comment(pr_url, response)
        
        status_line = response.split('\n')[0]
        if "[APPROVE]" in status_line:
            print(f"Review verdict: APPROVE ({status_line})")
        else:
            print(f"Review verdict: REQUEST_CHANGES ({status_line})")
