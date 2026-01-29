import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Класс конфигурации приложения.
    Загружает переменные окружения для работы с сервисами GitHub и LLM.
    """
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # Специфично для YandexGPT
    YC_FOLDER_ID = os.getenv("YC_FOLDER_ID")

    @classmethod
    def validate(cls):
        """
        Проверяет наличие обязательных переменных конфигурации.
        Выводит предупреждение в консоль, если отсутствуют критически важные токены.
        """
        if not cls.GITHUB_TOKEN:
            print("ВНИМАНИЕ: GITHUB_TOKEN не установлен.")
        if not cls.OPENAI_API_KEY:
             print("ВНИМАНИЕ: LLM_API_KEY не установлен.")
