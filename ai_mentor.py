import os
import json
import requests
from dotenv import load_dotenv

load_dotenv("as.env")

YANDEXGPT_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
IAM_TOKEN = os.getenv("IAM_TOKEN")
FOLDER_ID = os.getenv("FOLDER_ID")
MODEL_URI = f"gpt://{FOLDER_ID}/yandexgpt/latest"

USER_HISTORY_PATH = "user_history.json"

LESSONS = {
    "1.1": {
        "title": "Что такое ИИ и нейросети",
        "theory_id": "theory-1-1",
        "practice_id": "practice-1-1"
    },
    "1.2": {
        "title": "Где мы сталкиваемся с ИИ",
        "theory_id": "theory-1-2",
        "practice_id": "practice-1-2"
    },
    "1.3": {
        "title": "Возможности и ограничения ИИ",
        "theory_id": "theory-1-3",
        "practice_id": "practice-1-3"
    }
}

def load_user_history():
    try:
        with open(USER_HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_history(history):
    with open(USER_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def build_prompt(user_profile, message):
    return f"""
Тебя зовут — TeachAI-Mentor. Ты — дружелюбный, внимательный ИИ-наставник по обучению ИИ, Python и машинному обучению. Пиши красиво, с использованием эмодзи 🤖📘 и понятными абзацами. Отвечай живо, вдохновляй, как реальный человек. Стиль — поддерживающий и образовательный. Используй цепочку размышлений (chain-of-thought), софистический метод (socratic questioning), дружелюбный тон и Markdown-стиль форматирования (жирный, курсив, списки).

🧠 Уровень ученика: {user_profile.get('level', 'начальный')}
🎯 Цель ученика: {user_profile.get('goal', 'научиться работать с ИИ')}
⚠️ Недавние ошибки: {', '.join(user_profile.get('weaknesses', [])) or 'не указаны'}

📩 Сообщение от ученика:
\"{message}\"

Ответь структурированно, с примерами, вопросами и рекомендациями, что делать дальше.
"""

def query_yandexgpt(prompt):
    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "modelUri": MODEL_URI,
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": 400
        },
        "messages": [
            {"role": "system", "text": "Ты — ИИ-наставник, говоришь с учениками в дружелюбной и воодушевляющей манере, используя эмодзи и абзацы."},
            {"role": "user", "text": prompt}
        ]
    }
    response = requests.post(YANDEXGPT_API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["result"]["alternatives"][0]["message"]["text"]

def generate_response(user_id, message):
    history = load_user_history()
    
    # Гарантированно получить или создать структуру с полями
    user_data = history.get(user_id, {})
    user_data.setdefault("level", "начальный")
    user_data.setdefault("goal", "изучить основы ИИ")
    user_data.setdefault("weaknesses", [])
    user_data.setdefault("chat", [])
    user_data.setdefault("lesson_progress", "1.1")
    user_data.setdefault("progress", {})
    user_data["progress"].setdefault("lesson_progress", user_data["lesson_progress"])
    
    # Построение промпта и получение ответа
    prompt = build_prompt(user_data, message)
    reply = query_yandexgpt(prompt)
    
    # Добавление рекомендации
    lesson_id = user_data["progress"].get("lesson_progress", "1.1")
    lesson = LESSONS.get(lesson_id)
    if lesson:
        title = lesson["title"]
        theory_link = f"#{lesson['theory_id']}"
        practice_link = f"#{lesson['practice_id']}"
        reply += (
            f"\n\n📘 _Следующий шаг_: перейди к [теории по уроку «{title}»]({theory_link}) "
            f"и выполни [практику]({practice_link}). У тебя получится! 🚀"
        )
    
    # Обновление истории диалога
    user_data["chat"].append({"q": message, "a": reply})
    history[user_id] = user_data
    save_user_history(history)

    return reply
