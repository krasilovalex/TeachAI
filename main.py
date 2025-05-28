import telebot
from telebot import util
from gigachat_api import analyze_prompt_with_gigachat, query_gigachat_for_feedback
from wikipedia_api import get_wikipedia_summary, get_wikipedia_article_for_llama
from data_handler import load_data, save_data, register_user, update_progress, update_test_results, load_tests, THEMES, get_additional_materials_for_topic_with_llama, get_user_stats, get_test_for_theme, search_medium, search_arxiv, update_experince
from utils import get_next_theme, extract_topic_from_prompt, cache_prompt_analysis, get_cached_analysis
from keyboard import create_test_keyboard
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import re
import os
import json
from dotenv import load_dotenv
from bot import bot
import requests
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
CACHE_DIR = "cache"
CACHE_EXPIRATION_TIME = 3599   # 1 HOURS



# Команда /start
@bot.message_handler(commands=['start'])

def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    register_user(user_id,username)

    # create keyboard
    markup = InlineKeyboardMarkup()
    markup.row(
    InlineKeyboardButton("✅Мини-приложение✅", callback_data="mini"),
)
    markup.row(
    InlineKeyboardButton("📊Статистика📊", callback_data="stats"),
    InlineKeyboardButton("🚀Таблица лидеров🚀", callback_data="leaderboard")
)


    bot.send_message(
        message.chat.id,
        f"Привет, {username}! 👋\n"
        "TeachAI — твой персональный наставник в мире искусственного интеллекта.\n"
        "Учись создавать эффективные промпты, анализировать работу моделей, проходить интерактивные тесты и получать персональные рекомендации. \n"
        "Всё прямо в Telegram.! 🚀\n"
        "🚀 Преврати ИИ в инструмент своей силы.",
        reply_markup=markup
    )

    



# команда открытия приложения

@bot.message_handler(commands=['mini'])
def open_mini_app(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🚀 Открыть mini app", web_app=WebAppInfo(url='https://cmsxkl.ddns.net'))
    )
    bot.send_message(message.chat.id, "Нажми на кнопку ниже, чтобы открыть приложение 👇", reply_markup=keyboard)

# Команда /examples
@bot.message_handler(commands=['examples'])
def handle_examples(message):
    examples = [
        "Как лучше сформулировать запрос для создания изображения?",
        "Напиши промпт для генерации идеи для стартапа.",
        "Как задать вопрсоы, чтобы получить точный ответ?"
    ]
    bot.reply_to(message, "\n".join(examples))
# Команда /theme
@bot.message_handler(commands=['theme'])
def handle_themes(message):
    user_id = message.from_user.id
    theme_message = get_next_theme(user_id)
    bot.send_message(message.chat.id, theme_message, parse_mode="Markdown")

    # command /leaderboard
@bot.message_handler(commands=['leaderboard'])
def get_leaderboard(message):
    data = load_data()
    users = data["users"]

    leaderboard = sorted(users.items(), key=lambda x: x[1].get("experience", 0), reverse=True)

    top_users = leaderboard[:10]
    leaderboard_text = "\n".join([f"🏅 {i+1}. @{escape_markdown(user[1]['username'])} - {user[1].get('experience', 0)} XP"
                                  for i,user in enumerate(top_users)])
    
    bot.send_message(message.chat.id, f"📊 *Топ-пользователей*\n\n{leaderboard_text}", parse_mode="Markdown")





# Команда /done
@bot.message_handler(commands=["done"])
def theme_done(message):
    user_id = message.from_user.id
    theme = message.text.replace("/done","").strip()

    if not theme:
        bot.send_message(message.chat.id, "⚠ Укажите тему которую вы заверишили. Например: `/done Основы промпт-инжиниринга`", parse_mode="Markdown")
        return

    data = load_data()
    user_data = data["users"].get(str(user_id))

    if not user_data:
        bot.send_message(message.chat.id,"Сначала зарегиструйтесь с помощью /start")
        return

    if theme not in THEMES:
        bot.send_message(message.chat.id, "Такой темы нет в списке, используйте /theme чтобы получить список доступных тем", parse_mode="Markdown")
        return
    
    if theme in user_data["progress"]["completed_themes"]:
        bot.send_message(message.chat.id, "Вы уже завершили эту тему! 🎓", parse_mode="Markdown")
        return

    user_data["progress"]["completed_themes"].append(theme)
    save_data(data)

    bot.send_message(message.chat.id, f"✅ Тема \'{theme}' отмечена как изученная!", parse_mode="Markdown")
    update_experince(user_id, 10) # Начисляем 10XP

    # dop.mat
    ##additional_materials = get_additional_materials_for_topic_with_llama(theme)
   ## bot.send_message(message.chat.id, f"📚 Дополнительные материалы по теме:\n\n{additional_materials}", parse_mode="Markdown")

# Команда /stats
@bot.message_handler(commands=["stats"])
def stats(message):
    user_id = message.from_user.id
    stats_message = get_user_stats(user_id)
    bot.send_message(message.chat.id, stats_message, parse_mode="Markdown")


# Команда /test
@bot.message_handler(commands=["test"])
def test(message):
    user_id = message.from_user.id
    result = get_test_for_theme(user_id)

    if isinstance(result, str):  # Если функция вернула строку (ошибку)
        bot.send_message(message.chat.id, result)
        return

    theme, test = result

    if not test:  # Проверяем, что тест не пустой
        bot.send_message(message.chat.id, "Для этой темы пока нет тестов.")
        return

    question_index = 0
    user_sessions[user_id] = {"theme": theme, "test": test, "index": question_index}

    send_question(message.chat.id, user_id)
    update_experince(user_id, 10) # Начисляем 10XP

# Отправка вопроса пользователю
def send_question(chat_id, user_id):
    session = user_sessions.get(user_id)
    if not session:
        return

    theme = session["theme"]
    test = session["test"]
    index = session["index"]


    current_question = test[index]

    if not isinstance(current_question, dict):
        bot.send_message(chat_id, "Ошибка при загрузке вопроса. Попробуйте позже.")
        return

    question_text = f"📝 Тема: {theme}\n\n{current_question['question']}"
    keyboard = create_test_keyboard(current_question["options"])

    bot.send_message(chat_id, question_text, reply_markup=keyboard)

# Обработчик ответов
@bot.callback_query_handler(func=lambda call: True)
def universal_callback_handler(call):
    if call.data.startswith('opt_'):
        handle_answer(call)  # обработка ответов на тест

    elif call.data == 'mini':
        bot.answer_callback_query(call.id)
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("🚀 Открыть Mini App", web_app=WebAppInfo(url='https://cmsxkl.ddns.net'))
        )
        bot.send_message(call.message.chat.id, "Нажми на кнопку ниже 👇", reply_markup=keyboard)

    elif call.data == 'create_prompt':
        bot.answer_callback_query(call.id)
        fake_message = call.message  # это объект типа Message
        create_prompt(fake_message)  # вызываем обработчик вручную

    elif call.data == 'stats':
        bot.answer_callback_query(call.id)
        user_id = call.from_user.id
        stats_message = get_user_stats(user_id)
        bot.send_message(call.message.chat.id, stats_message, parse_mode="Markdown")

    elif call.data == 'leaderboard':
         bot.answer_callback_query(call.id)
         leaderboard_text = get_leaderboard(call.message)  # вызов функции
         bot.send_message(call.message.chat.id, leaderboard_text, parse_mode="Markdown")

    else:
        bot.answer_callback_query(call.id, "Неизвестная команда.")







    

    # Хранение сессий тестирования
user_sessions = {}


# Команда /create_prompt для создания и анализа собственного промпта
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
        f"📊 *Анализ с GigaChat:*\n{ollama_feedback}\n\n"
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

    save_best_prompt(user_id, user_prompt, "GigaChat")    
    update_experince(user_id, 10) # Начисляем 10XP   


def save_best_prompt(user_id, prompt, api_used):
    data = load_data()
    user_data = data["users"].get(str(user_id))

    if user_data:
        user_data["progress"]["best_prompts"].append({"prompt": prompt, "rating": 5, "api":api_used}) # Primer s reitingom
        save_data(data)

def analyze_prompt_full(user_prompt: str):
    topic = extract_topic_from_prompt(user_prompt)
    if not topic:
        return {"error": "Тема не определена"}

    wikipedia_info = get_wikipedia_article_for_llama(topic)
    enriched_prompt = f"Контекстная информация:\n{wikipedia_info}\n\nПромпт пользователя:\n{user_prompt}"

    ollama_feedback = analyze_prompt_with_gigachat(enriched_prompt)
    prompt_evaluation = evaluate_prompt(user_prompt)

    return {
        "prompt": user_prompt,
        "topic": topic,
        "llm_feedback": ollama_feedback,
        "evaluation": prompt_evaluation
    }

      

# Команда /best_prompts для просмотра лучших промптов
@bot.message_handler(commands=['best_prompts'])
def best_prompts(message):
    user_id = message.from_user.id
    data = load_data()
    user_data = data["users"].get(str(user_id))

    if not user_data or not user_data["progress"]["best_prompts"]:
        bot.send_message(message.chat.id, "У вас нет сохранненых лучших промптов.")
        return
    
    prompts = user_data["progress"]["best_prompts"]
    best_prompts_message = "✨ Ваши лучшие промпты:\n"
    for prompt in prompts:
        best_prompts_message += f"- _{prompt['prompt']}_(⭐ {prompt['rating']})\n"

    bot.send_message(message.chat.id, best_prompts_message)



# Команда /materials
@bot.message_handler(commands=["materials"])
def handle_materials(message):
    user_id = message.from_user.id
    data = load_data()
    user_data = data["users"].get(str(user_id))

    if not user_data or not user_data["progress"]["completed_themes"]:
        bot.send_message(message.chat.id, "Сначала изучите хотя бы одну тему через /theme")
        return

    last_theme = user_data["progress"]["completed_themes"][-1]  # Определяем тему
    bot.send_message(message.chat.id, f"🔍 Ищу материалы по теме: *{last_theme}*...", parse_mode="Markdown")

    arxiv_papers = search_arxiv(last_theme)
    medium_articles = search_medium(last_theme)  # Получаем статьи по теме
    

    materials_message = f"📚 *Дополнительные материалы по теме:* {last_theme}\n\n"

    if arxiv_papers:
        materials_message = f"🔹 *ArXiv:*\n{arxiv_papers}\n\n"
    if medium_articles:
        materials_message = f"🔹 *Medium:*\n{medium_articles}\n\n"

    bot.send_message(message.chat.id, materials_message, parse_mode="Markdown")            


@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = message.from_user.id
    data = load_data()
    user_data = data["users"].get(str(user_id))

    if not user_data:
        bot.send_message(message.chat.id, "Вы еще не зарегистрованы. Используйте /start.")
        return
    
    exp = user_data.get("experience",0)
    level = user_data.get("level",1)
    achievements = user_data.get("achievements", [])

    achievements_text = "\n".join([f"🏅 {ach} " for ach in achievements]) if achievements else "Пока нет достижений."

    bot.send_message(message.chat.id, f"🎖 *Ваш профиль*\n\n"
                                      f"⭐ Уровень: {level}\n"
                                      f"🔹Опыт: {exp} XP\n"
                                      f"🏆Достижения:\n{achievements_text}",
                    parse_mode="Markdown")

def escape_markdown(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f"([{re.escape(escape_chars)}])", r'\\\1', text)




# command /search
@bot.message_handler(commands=['search'])
def search_materials(message):
    user_query = message.text.replace("/search", "").strip()

    if not user_query:
        bot.send_message(message.chat.id, "⚠ Введите ключевые слова для поиска, например `/search нейросети`", parse_mode="Markdown")
        return
    
    bot.send_message(message.chat.id, f"🔍 Ищу материалы по запросу: *{user_query}*...")

    additional_materials = get_additional_materials_for_topic_with_llama(user_query)
    bot.send_message(message.chat.id, f"📚 Дополнительные материалы по теме:\n\n{additional_materials}", parse_mode="Markdown") 

















# Запуск бота
if __name__ == '__main__':
    bot.polling(timeout=30, long_polling_timeout=30)
while True:
    try:
        bot.polling(timeout=30, long_polling_timeout=30)
    except requests.exceptions.ReadTimeout:
        print("Read timeout error, retrying...")
        time.sleep(5)  # Задержка перед повторной попыткой
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(5)  # Задержка перед повторной попыткой

