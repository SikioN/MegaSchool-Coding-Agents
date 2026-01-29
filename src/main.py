import argparse
import sys
from src.core.config import Config
from src.agents.code_agent import CodeAgent
from src.agents.reviewer_agent import ReviewerAgent

def main():
    """
    Точка входа CLI приложения.
    Обрабатывает аргументы командной строки и запускает соответствующих агентов.
    """
    parser = argparse.ArgumentParser(description="Coding Agents CLI")
    subparsers = parser.add_subparsers(dest="command", help="Команда для запуска")

    # Команда запуска Code Agent
    code_parser = subparsers.add_parser("code", help="Запустить Code Agent")
    code_parser.add_argument("--issue", required=True, help="URL GitHub Issue")

    # Команда запуска Reviewer Agent
    review_parser = subparsers.add_parser("review", help="Запустить Reviewer Agent")
    review_parser.add_argument("--pr", required=True, help="URL Pull Request")
    review_parser.add_argument("--issue", required=True, help="URL оригинального Issue")

    # Команда запуска Исправления (Code Agent Fix Mode)
    fix_parser = subparsers.add_parser("fix", help="Запустить исправление Code Agent по ревью")
    fix_parser.add_argument("--pr", required=True, help="URL Pull Request")
    fix_parser.add_argument("--issue", required=True, help="URL оригинального Issue")

    args = parser.parse_args()

    # Валидация конфигурации при запуске
    Config.validate()

    if args.command == "code":
        agent = CodeAgent()
        agent.run(args.issue)
    
    elif args.command == "fix":
        agent = CodeAgent()
        agent.run_fix(args.pr, args.issue)

    elif args.command == "review":
        agent = ReviewerAgent()
        agent.run(args.pr, args.issue)
        
    elif args.command == "init":
        print("Инициализация...")
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
