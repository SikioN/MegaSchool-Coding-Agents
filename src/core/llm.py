from abc import ABC, abstractmethod
from typing import Optional
import openai
import requests
from src.core.config import Config

class LLMProvider(ABC):
    """
    Абстрактный базовый класс для провайдеров LLM.
    Определяет единый интерфейс взаимодействия с различными языковыми моделями.
    """
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Генерирует текстовый ответ на основе системного и пользовательского промптов.
        """
        pass

class OpenAILLM(LLMProvider):
    """
    Реализация провайдера для работы с OpenAI API.
    """
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.LLM_BASE_URL
        )
        self.model = Config.LLM_MODEL

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Отправляет запрос к модели OpenAI и возвращает содержимое ответа.
        Возвращает пустую строку в случае ошибки API.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"Ошибка OpenAI: {e}")
            return ""

class YandexGPTLLM(LLMProvider):
    """
    Реализация провайдера для работы с YandexGPT через REST API.
    """
    def __init__(self):
        self.api_key = Config.OPENAI_API_KEY
        self.folder_id = Config.YC_FOLDER_ID
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        # modelUri формируется как: "gpt://<folder_id>/yandexgpt/latest"
        self.model_uri = f"gpt://{self.folder_id}/yandexgpt/latest"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Отправляет POST-запрос к API YandexGPT и возвращает сгенерированный текст.
        Использует синхронный режим генерации.
        """
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "x-folder-id": self.folder_id or ""
        }
        
        prompt = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": "8000"
            },
            "messages": [
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": user_prompt}
            ]
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=prompt)
            if response.status_code != 200:
                print(f"Ошибка YandexGPT: {response.text}")
                return ""
            
            result = response.json()
            return result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")
        except Exception as e:
            print(f"Исключение YandexGPT: {e}")
            return ""

def get_llm() -> LLMProvider:
    """
    Фабричная функция для получения экземпляра LLM провайдера.
    Выбирает YandexGPT, если URL или Folder ID указывают на Яндекс, иначе использует OpenAI.
    """
    if "api.cloud.yandex" in Config.LLM_BASE_URL or Config.YC_FOLDER_ID:
         if "yandex" in Config.LLM_MODEL.lower() or Config.YC_FOLDER_ID:
             return YandexGPTLLM()
    
    return OpenAILLM()
