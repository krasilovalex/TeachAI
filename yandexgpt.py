import requests
from dotenv import load_dotenv
import os

load_dotenv(as.env)

IAM_TOKEN = os.getenv("IAM_TOKEN")
FOLDER_ID = os.getenv("FOLDER_ID")
YANDEXGPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

def query_yandexgpt(prompt):
    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",  # Или "yandexgpt" для платной версии
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": 400
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты — дружелюбный, профессиональный помощник. Отвечай понятно, тепло и по делу."
            },
            {
                "role": "user",
                "text": f"Расскажи об этом. Отвечай только на русском языке.\n\n{prompt}"
            }
        ]
    }

    try:
        response = requests.post(YANDEXGPT_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()["result"]["alternatives"][0]["message"]["text"]
    except requests.exceptions.Timeout:
        return "⚠️ Запрос занял слишком много времени. Попробуйте позже."
    except requests.exceptions.RequestException as e:
        return f"⚠️ Ошибка запроса к YandexGPT: {e}"
    except Exception as e:
        return f"⚠️ Ошибка обработки ответа YandexGPT: {e}"

# 👀 Обёртка
def analyze_prompt_with_yandexgpt(prompt):
    return query_yandexgpt(prompt)
