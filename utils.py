
import requests
import time
import random
import os
import json
from gigachat_api import analyze_prompt_with_gigachat, query_gigachat_for_feedback, GIGACHAT_API_URL
from wikipedia_api import get_wikipedia_summary, get_wikipedia_article_for_llama
from data_handler import load_data, save_data, register_user, update_progress, update_test_results, load_tests, THEMES



CACHE_DIR = "cache"
CACHE_EXPIRATION_TIME = 3600   # 1 HOURS






# Функция определения темы с помощью LLaMA
def extract_topic_from_prompt(prompt):
    system_prompt = (
        "Ты — анализатор промптов. Определи основную тему следующего запроса, "
        "выбрав одно главное ключевое слово или фразу. Не добавляй лишнего текста, "
        "просто укажи тему."
    )

    enriched_prompt = f"{system_prompt}\n\nПромпт пользователя: {prompt}"
    response = analyze_prompt_with_gigachat(enriched_prompt)

    return response.strip()


# Функция выбора темы(случайной)
def get_next_theme(user_id):
    data = load_data()
    user_data = data["users"].get(str(user_id))

    if not user_data:
        return "Сначало зарегиструйтесь с помощью /start!"
    
    completed_themes = user_data["progress"]["completed_themes"]

    # Фильтруем темы, которые пользователь еще не изучал

    available_themes = [theme for theme in THEMES if theme not in completed_themes]

    if not available_themes:
        return "Вы изучили все темы!🎉 Ожидайте новых материалов."
    
    next_theme = random.choice(available_themes) # Выводим случайную тему

    return f"📚 *Тема для изучения:*\n➡{next_theme}"


# Функция для получения доп материалов
def get_additional_materials_for_topic_with_llama(topic, lang="ru"):
    # Формируем запрос для LLaMA с темой
    prompt = f"Предоставь дополнительные материалы по теме: {topic}. Включи краткое описание, ключевые аспекты, ссылки на ресурсы, если они есть, и примерные разделы.\n\nОтвечай на русском языке."

    # Отправляем запрос в LLaMA API
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "language": lang
        }
    }

    try:
        response = requests.post(GIGACHAT_API_URL, json=payload, timeout=300)
        response_data = response.json()
        time.sleep(5)

        # Получаем ответ и возвращаем его
        llama_response = response_data.get("response", "Ошибка обработки запроса.")
        
        # Если в ответе есть структура, например, ссылки или разделы, можно их разделить
        return llama_response

    except Exception as e:
        return f"Ошибка запроса к Ollama: {e}"
    except requests.exceptions.ReadTimeout:
        return "Ошибка: запрос занял слишком много времени. Попробуйте позже."
    except requests.exceptions.RequestException as e:
        return f"Ошибка запроса: {e}"
    

# фУНКЦИЯ кэширования
def cache_prompt_analysis(user_prompt, analysis_result):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    cache_filename = os.path.join(CACHE_DIR, f"{hash(user_prompt)}.json")

    # save results
    with open(cache_filename, 'w') as f:
        json.dump({
            'timestamp':time.time(),
            'analysis_result': analysis_result
        }, f)
def get_cached_analysis(user_prompt):
    cache_filename = os.path.join(CACHE_DIR, f"{hash(user_prompt)}.json")

    if os.path.exists(cache_filename):
        with open(cache_filename, 'r') as f:
            cached_data = json.load(f)

        if time.time() - cached_data['timestamp'] < CACHE_EXPIRATION_TIME:
            return cached_data['analysis_result']

    return None            
