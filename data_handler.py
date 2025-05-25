import json
import os
import requests
import time
import random
import feedparser
import telebot
import xml.etree.ElementTree as ET
from translate import Translator
from gigachat_api import GIGACHAT_API_URL
from bot import bot
from gigachat_api import analyze_prompt_with_gigachat, query_gigachat_for_feedback
from wikipedia_api import get_wikipedia_summary, get_wikipedia_article_for_llama
from keyboard import create_test_keyboard
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import re
# data file
DATA_FILE = "user_history.json"
def extract_topic_from_prompt(prompt):
    system_prompt = (
        "Ты — анализатор промптов. Определи основную тему следующего запроса, "
        "выбрав одно главное ключевое слово или фразу. Не добавляй лишнего текста, "
        "просто укажи тему."
    )

    enriched_prompt = f"{system_prompt}\n\nПромпт пользователя: {prompt}"
    response = analyze_prompt_with_gigachat(enriched_prompt)

    return response.strip()

# themes
THEMES = [
    "Использование примеров в промптах — как улучшить результаты с помощью демонстрационных примеров",
    "Гибридные техники промпт-инжиниринга — комбинирование различных стратегий для повышения эффективности",
    "Этика и ограничения нейросетей — предвзятость, безопасность данных, корректность запросов",
    "Будущее профессии промпт-инженера — перспективы работы, развитие технологий",
    "Анализ ответа модели — разбор хода рассуждений модели, выявление ошибок",
    "Типы промптов",
    "Структура промпта",
    "RAG",
    "Основы промпт-инжиниринга",
    "Как правильно формулировать запросы",
    "Использование контекста в промптах",
    "Системные промпты и их настройка",
    "Продвинутые техники промптинга",
    "Работа с различными LLM-моделями",
    "Автоматизация с помощью промптов"
]

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







      




# Функция загрузки файла с тестами!

def load_tests():
        with open("tests.json", "r", encoding="utf-8") as file:
            return json.load(file)
        
    

def get_test_for_theme(user_id):
    data = load_data()
    user_data = data["users"].get(str(user_id))

    if not user_data:
        return "Сначала зарегистрируйтесь с помощью /start!"

    completed_themes = user_data["progress"]["completed_themes"]
    completed_tests = user_data["progress"].get("completed_tests", [])

    if not completed_themes:
        return "Вы еще не изучили ни одной темы! Начните с /theme."

    theme = random.choice(completed_themes)
    tests = load_tests()

    if theme not in tests or not tests[theme]:
        return "Для этой темы нет тестов."

    if theme in completed_tests:
        return "Вы уже прошли тест для этой темы!"  # Если тест был пройден    

    return theme, tests[theme]  # ✅ Гарантируем возврат кортежа






      


# Функция загрузки данных 
def load_data():
    if not os.path.exists(DATA_FILE):
        return{"users":{}}
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)
    
# Функция сохранения данных
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Функция регистрации пользователя
def register_user(user_id,username):
    data = load_data()
    if str(user_id) not in data["users"]:
        data["users"][str(user_id)] = {
            "username":username,
            "progress": {
                "completed_themes": [],
                "tests_passed": 0,
                "test_results": [], # Список результатов тестов
                "best_prompts": []
            },
            "level": 1,
            "experience": 0,
            "achievements":[],
            "feedback":[]
        }
        save_data(data)

        print(f"✅ Пользователь {user_id} зарегистрирован!")  # Отладочный вывод
    else:
        print(f"⚠️ Пользователь {user_id} уже зарегистрирован.")  # Отладочный вывод      

    if str(user_id) in data["users"]:
        return  # Пользователь уже зарегистрирован

          
        
    


# Функция обновления статистики пользователя после прохождения теста
def update_test_results(user_id, theme, correct_answers, total_questions):
    data = load_data()
    user_data = data["users"].get(str(user_id))

    # Проверяем, существует ли ключ "completed_tests" в "progress"
    if "completed_tests" not in user_data["progress"]:
        user_data["progress"]["completed_tests"] = []

    if user_data:
        user_data["progress"]["tests_passed"] += 1 # Увеличивает кол-во сданных тестов
        user_data["progress"]["completed_tests"].append(theme) 


        # Добавляем результаты теста
        user_data["progress"]["test_results"].append({
            "theme" : theme,
            "correct_answers" : correct_answers,
            "total_questions" : total_questions,
            "score":f"{(correct_answers / total_questions) * 100:.2f}%" # добавляем процент
        })
        save_data(data)
# Функция получения теста для темы с проверкой пройденных
                                     
 
# Функция обновления прогресса
def update_progress(user_id, completed_theme=None, test_passed=False, best_prompt=None):
    data = load_data()
    user_data = data["users"].get(str(user_id))

    if user_data:
        if completed_theme and completed_theme not in user_data["progress"]["completed_themes"]:
            user_data["progress"]["completed_themes"].append(completed_theme)
    if test_passed:
        user_data["progress"]["tests_passed"] += 1
    if best_prompt:
        user_data["progress"]["best_prompts"].append(best_prompt)
    save_data(data)    


# Функция получения статистики пользователя
def get_user_stats(user_id):
    data = load_data()
    user_data = data["users"].get(str(user_id))

    if not user_data:
        return "У вас пока нет сохранененных данных. Начните обучение с /theme!"
    
    stats = (
        f"📊 *Ваша статистика*\n"
        f"👤 *Имя:* {user_data['username']}\n"
        f"🏆 *Уровень:* {user_data['level']}\n"
        f"📚 *Пройденные темы:* {len(user_data['progress']['completed_themes'])}\n"
        f"✅ *Сданные тесты:* {user_data['progress']['tests_passed']}\n"
    )

    if user_data["progress"]["test_results"]:
        stats += "\n🎓 *Результаты тестов:*\n"
        for result in user_data["progress"]["test_results"][:3]:
            stats += f"- Тема : {result['theme']} | {result['score']} ({result['correct_answers']}/{result['total_questions']})\n"

    if user_data["progress"]["best_prompts"]:
        stats += "\n✨ *Лучшие промпты:*\n"
        for prompt in user_data["progress"]["best_prompts"][:3]: # TOP 3
            stats += f"- _{prompt["prompt"]}_(⭐ {prompt["rating"]})\n"
    return stats 


# Функция translate

def translate_to_english(text):
    translator = Translator(to_lang="en")
    return translator.translate(text)



# Функции запроса материалов

def search_arxiv(topic):
    """Ищет наученые статьи в ArXiv"""
    url = f"http://export.arxiv.org/api/query?search_query={topic}&start=0&max_results=1"
    response = requests.get(url)

    if response.status_code != 200:
        return "Ошибка при запросе ArXiv"
    
    root =  ET.fromstring(response.text)

    entry = root.find("{https://www.w3.org/2005/Atom}entry")
    if entry is None:
        return "Статья не найдена."
    
    title = entry.find("{http://www.w3.org/2005/Atom}title").text
    summary =  entry.find("{http://www.w3.org/2005/Atom}summary").text
    link = entry.find("{http://www.w3.org/2005/Atom}link").attrib['href']

    authors  = [author.find("{http://www.w3.org/2005/Atom}name").text for author in entry.findall("{http://www.w3.org/2005/Atom}author")]

    authors_text = ",".join(authors)
    
    return f"**Название:** {title}\n**Авторы:** {authors_text}\n**Ссылка:** [ArXiv]({link})\n\n**Описание:** {summary}"






def search_medium(topic):
    """Ищет наученые статьи в Medium через RSS"""

    translated_topic = translate_to_english(topic)

    rss_url = f"https://medium.com/feed/tag/{translated_topic.replace(' ', '-')}"
    feed = feedparser.parse(rss_url)

    if not feed.entries:
        return "🔸 Нет доступных статей на Medium по этой теме"
    
    results = []
    for entry in feed.entries[:3]:
        results.append(f"🔹[{entry.title}]({entry.link})")

    return "\n".join(results)    


# обновление опыта юзера
def update_experince(user_id, points):

    data = load_data()
    user_data = data["users"].get(str(user_id))
    user_data["progress"].setdefault("experience", 0) # Опыт по умолчанию

    if not user_data:
        return
    
    user_data["progress"]["experience"] += points

    # Определение уровня(например 100XP = 1lvl)
    user_data["progress"]["level"] = user_data["progress"]["experience"] // 100

    save_data(data)



#   функция достижений
def check_achievements(user_id):
    data = load_data()
    user_data = ["users"].get(str(user_id))

    if not user_data:
        return
    
    achievements = user_data["progress"].setdefault("achievements", [])

    # Примеры достижений
    if user_data["progress"].get("tests_completed", 0) >= 5 and "Тестовый гуру" not in achievements:
        achievements.append("Тестовый гуру")
        bot.send_message(user_id, "🎉 Поздравляем! Вы получили достижение: Тестовый гуру 🏆")

    if user_data["progress"].get("prompts_tested",0) >= 10 and "Промпт-Мастер" not in achievements:
        achievements.append("Промпт-Мастер")
        bot.send_message(user_id, "🎉 Поздравляем! Вы получили достижение: Промпт-Мастер 🏆")

    save_data()

def escape_markdown(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f"([{re.escape(escape_chars)}])", r'\\\1', text)   

@bot.message_handler(commands=['create_prompt'])
def create_prompt(message):
    user_id = message.from_user.id
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Использовать GigaChat", callback_data='use_llama'))
    bot.send_message(message.chat.id, "Выберите какой сервис использовать для анализа промпта:", reply_markup=markup)

    # обработчик выбора API
def handle_api_choice(call):
    user_id = call.from_user.id
    if call.data == "use_llama":
        msg = bot.send_message(call.message.chat.id, "Введите свой промпт для анализа с помощью LLaMA")
        bot.register_next_step_handler(msg, process_user_prompt_llama)


def evaluate_prompt(prompt):
    """"1. Четкость, 2. Полнота, 3. Специфичность"""
    clarity = min(10, max(3, len(prompt.split())/ 5))
    completeness = 10 if "детали" in prompt.lower() or "описание" in prompt.lower() else 7
    specificity = 10 if any(word in prompt.lower() for word in ["конкретный", "пример", "детализируй"]) else 6

    suggestions = []
    if clarity < 7:
        suggestions.append("Попробуй сформулировать запрос проще и конкретнее.")
    if completeness < 8:
        suggestions.append("Добавь больше деталей или условий.")
    if specificity < 7:
        suggestions.append("Уточни параметры запроса, чтобы избежать общих ответов.")

    return {
        "clarity": clarity,
        "completeness": completeness,
        "specificity": specificity,
        "suggestions": suggestions
    }
    

def process_user_prompt_llama(message):
    user_id = message.from_user.id
    user_prompt = message.text.strip()

    if not user_prompt:
        bot.reply_to(message, "Вы не ввели промпт. Пожалуйста, попробуйте снова.")
        return


    waiting_message = bot.send_message(message.chat.id, "⏳ Анализирую ваш промпт, пожалуйста, подождите...")
    

    # Определяем ключевую тему промпта
    topic = extract_topic_from_prompt(user_prompt)

    if not topic:
        bot.reply_to(message, "⚠️Не удалось определить тему запроса. Попробуйте сформулировать его иначе.",
                               message.chat.id, waiting_message.message_id)
        return

    # Пробуем найти инфо в wiki
    wikipedia_info = get_wikipedia_article_for_llama(topic) if topic else "Контекст не найден."

    enriched_prompt = (
        f"Контекстная информация:\n{wikipedia_info}\n\n"
        f"Промпт пользователя:\n{user_prompt}"
    )



    # Анализируем промпт с помощью LLaMA

    ollama_feedback = analyze_prompt_with_gigachat(enriched_prompt)

    prompt_evaluation = evaluate_prompt(user_prompt)

    feedback_message = escape_markdown(
         f"📌 *Ваш промпт:*\n{user_prompt}\n\n"
        f"📖 *Определённая тема:* {topic}\n\n"
        f"📊 *Анализ с LLaMA:*\n{ollama_feedback}\n\n"
        f"📈 *Оценка промпта:*\n"
        f"🔹 Четкость: {prompt_evaluation['clarity']}/10\n"
        f"🔹 Полнота: {prompt_evaluation['completeness']}/10\n"
        f"🔹 Специфичность: {prompt_evaluation['specificity']}/10\n\n"

    )

    # Обновляем сообщение с итоговым ответом
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=waiting_message.message_id,
        text=feedback_message,
        parse_mode="Markdown")

    save_best_prompt(user_id, user_prompt, "LLaMA")    
    update_experince(user_id, 10) # Начисляем 10XP   


def save_best_prompt(user_id, prompt, api_used):
    data = load_data()
    user_data = data["users"].get(str(user_id))

    if user_data:
        user_data["progress"]["best_prompts"].append({"prompt": prompt, "rating": 5, "api":api_used}) # Primer s reitingom
        save_data(data)


