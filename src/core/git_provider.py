from typing import List, Optional
import git
from github import Github, Auth
from github.Issue import Issue
from github.PullRequest import PullRequest
from src.core.config import Config

class GitProvider:
    """
    Провайдер для работы с Git репозиторием и GitHub API.
    Обеспечивает управление ветками, коммитами и Pull Request.
    """
    def __init__(self, repo_path: str = ".", token: Optional[str] = None):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)
        
        # Use provided token OR fallback to Config token
        api_token = token or Config.GITHUB_TOKEN
        
        if api_token:
            auth = Auth.Token(api_token)
            self.gh = Github(auth=auth)
        else:
            self.gh = None
            print("ВНИМАНИЕ: GitHub Token не предоставлен. Функции API будут недоступны.")

    def get_issue(self, issue_url: str) -> str:
        """
        Получает описание задачи (Issue) по её URL.
        Возвращает formatted string с заголовком и телом задачи.
        """
        if not self.gh:
            return "Тестовое описание задачи (Нет токена)"
            
        repo_name, issue_number = self._parse_issue_url(issue_url)
        repo = self.gh.get_repo(repo_name)
        issue = repo.get_issue(issue_number)
        return f"Title: {issue.title}\nDescription:\n{issue.body}"

    def create_branch(self, branch_name: str):
        """
        Создает новую ветку и переключает на нее.
        """
        # Если ветка уже есть, переключаемся на неё
        if branch_name in self.repo.heads:
            current = self.repo.heads[branch_name]
            current.checkout()
        else:
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
        print(f"Checkout branch: {branch_name}")

    def commit_changes(self, message: str):
        """
        Добавляет все изменения и делает коммит.
        """
        if self.repo.is_dirty(untracked_files=True):
            self.repo.git.add(A=True)
            self.repo.index.commit(message)
            print(f"Commit created: {message}")
        else:
            print("No changes to commit.")

    def create_pr(self, title: str, body: str, base: str = "main") -> str:
        """
        Push local branch and create Pull Request.
        """
        if not self.gh:
            return "Mock PR URL (No Token)"
            
        current_branch = self.repo.active_branch.name
        
        # Настройка remote с токеном для push
        origin = self.repo.remote(name='origin')
        remote_url = origin.url
        
        # Инъекция токена в URL для HTTPS push, если это HTTPS
        if "https://" in remote_url and "@" not in remote_url and Config.GITHUB_TOKEN:
            auth_url = remote_url.replace("https://", f"https://{Config.GITHUB_TOKEN}@")
            with self.repo.git.custom_environment(GIT_ASKPASS='echo'):
                 self.repo.git.push(auth_url, current_branch, set_upstream=True)
        else:
            # Пытаемся пушить как есть (SSH или уже настроенный cred helper)
            origin.push(current_branch, set_upstream=True)
        
        # Создание PR через API
        repo_name = self._get_repo_name_from_remote()
        if repo_name:
            repo = self.gh.get_repo(repo_name)
            try:
                # Проверяем, нет ли уже PR
                pulls = repo.get_pulls(state='open', head=f"{repo.owner.login}:{current_branch}", base=base)
                if pulls.totalCount > 0:
                    return pulls[0].html_url
                
                pr = repo.create_pull(title=title, body=body, head=current_branch, base=base)
                return pr.html_url
            except Exception as e:
                print(f"Error creating PR: {e}")
                return f"Error creating PR: {str(e)}"
            
        return "Could not determine repo name for PR creation"

    def get_pr_diff(self, pr_url: str) -> str:
        """
        Получает diff изменений в Pull Request.
        """
        if not self.gh:
            return "Mock Diff (No Token)"
            
        repo_name, pr_number = self._parse_issue_url(pr_url) # URL структура похожа
        repo = self.gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Простой способ получить файлы
        diff_output = ""
        for file in pr.get_files():
            diff_output += f"File: {file.filename}\nStatus: {file.status}\nPatch:\n{file.patch}\n---\n"
            
        return diff_output

    def post_comment(self, pr_url: str, body: str):
        """
        Публикует комментарий к Pull Request или Issue.
        """
        if not self.gh:
            print(f"Mock Comment on {pr_url}: {body[:50]}...")
            return

        repo_name, number = self._parse_issue_url(pr_url)
        repo = self.gh.get_repo(repo_name)
        issue = repo.get_issue(number) # PR is also an Issue in API implementation usually for comments
        issue.create_comment(body)
        print(f"Comment posted to {pr_url}")

    def remove_label(self, issue_url: str, label_name: str):
        """
        Удаляет лейбл с Issue.
        """
        if not self.gh:
             print(f"Mock Remove Label {label_name} from {issue_url}")
             return

        repo_name, number = self._parse_issue_url(issue_url)
        repo = self.gh.get_repo(repo_name)
        issue = repo.get_issue(number)
        try:
            issue.remove_from_labels(label_name)
            print(f"Label '{label_name}' removed from {issue_url}")
        except Exception as e:
            print(f"Error removing label: {e}")

    def get_pr_comments(self, pr_url: str) -> str:
        """
        Получает список комментариев к PR.
        """
        if not self.gh:
            return "Mock Comments"
            
        repo_name, number = self._parse_issue_url(pr_url)
        repo = self.gh.get_repo(repo_name)
        pr = repo.get_pull(number)
        
        comments_text = ""
        # Review comments (на код)
        for comment in pr.get_review_comments():
            comments_text += f"[Review Comment] {comment.path}:{comment.position}\n{comment.body}\n---\n"
            
        # Issue comments (общие)
        for comment in pr.get_issue_comments():
             comments_text += f"[General Comment] {comment.user.login}: {comment.body}\n---\n"
             
        return comments_text

    def checkout_pr(self, pr_url: str):
        """
        Переключается на ветку Pull Request.
        """
        if not self.gh:
             print("Mock Checkout PR")
             return
             
        repo_name, number = self._parse_issue_url(pr_url)
        repo = self.gh.get_repo(repo_name)
        pr = repo.get_pull(number)
        
        branch_name = pr.head.ref
        self.create_branch(branch_name) # Используем существующий метод, который чекаутит, если ветка есть

    def _parse_issue_url(self, url: str):
        """
        Helper: extracts (repo_name, number) from url.
        Example: https://github.com/owner/repo/issues/123 -> ("owner/repo", 123)
        """
        parts = url.rstrip("/").split("/")
        number = int(parts[-1])
        repo_name = f"{parts[-4]}/{parts[-3]}"
        return repo_name, number

    def _get_repo_name_from_remote(self) -> Optional[str]:
        origin = self.repo.remote(name='origin')
        url = origin.url
        # Покрываем HTTPS и SSH
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        if "github.com" in url:
            path = url.split("github.com")[-1].lstrip(":/")
            if path.endswith(".git"):
                path = path[:-4]
            return path
        return None
