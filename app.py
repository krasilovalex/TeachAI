from flask import Flask, jsonify, send_from_directory, request, render_template
import json
import os
from datetime import datetime, timedelta
import logging
from yandexgpt import query_yandexgpt
import hashlib
import time
import random
from ai_mentor import generate_response  # Твоя логика

app = Flask(__name__, static_folder="public")
DATA_FILE = 'user_history.json'
logging.basicConfig(level=logging.INFO)


LEVEL_ACHIEVEMENTS = {
    1: "Ученики ИИ",
    5: "Подмастерье TeachAI",
    10: "Инженер Промптов",
    15: "Архитектор Разума",
    20: "Мастер ИИ",
    25: "Повелитель Моделей",
    30: "TeachAI: Легенда",
    35: "Алхимик Алгоритмов",
    40: "Повелитель Знаний",
    45: "Грандмастер Генерации",
    50: "Создатель Сознаний",
    55: "Навигатор Нейросетей",
    60: "Вершитель Промптов",
    65: "Демистификатор ИИ",
    70: "Бессмертный Разума",
    75: "TeachAI: Бессмертная Сингулярность"
}

LEVEL_THRESHOLDS = [
     0,     # Уровень 1
   350,     # Уровень 2
   750,     # Уровень 3
  1200,     # Уровень 4
  1700,     # Уровень 5
  2200,     # Уровень 6
  2750,     # Уровень 7
  3300,     # Уровень 8
  3900,     # Уровень 9
  4500,     # Уровень 10
  5150,     # Уровень 11
  5800,     # Уровень 12
  6500,     # Уровень 13
  7200,     # Уровень 14
  7950,     # Уровень 15
  8700,     # Уровень 16
  9500,     # Уровень 17
 10300,     # Уровень 18
 11100,     # Уровень 19
 11950,     # Уровень 20
 12800,     # Уровень 21
 13700,     # Уровень 22
 14650,     # Уровень 23
 15600,     # Уровень 24
 16600,     # Уровень 25
 17600,     # Уровень 26
 18650,     # Уровень 27
 19700,     # Уровень 28
 20800,     # Уровень 29
 21900,     # Уровень 30
 23050,     # Уровень 31
 24200,     # Уровень 32
 25400,     # Уровень 33
 26600,     # Уровень 34
 27850,     # Уровень 35
 29100,     # Уровень 36
 30400,     # Уровень 37
 31700,     # Уровень 38
 33050,     # Уровень 39
 34400,     # Уровень 40
 35800,     # Уровень 41
 37200,     # Уровень 42
 38650,     # Уровень 43
 40100,     # Уровень 44
 41600,     # Уровень 45
 43100,     # Уровень 46
 44650,     # Уровень 47
 46200,     # Уровень 48
 47800,     # Уровень 49
 49400,     # Уровень 50
 51050,     # Уровень 51
 52700,     # Уровень 52
 54400,     # Уровень 53
 56100,     # Уровень 54
 57850,     # Уровень 55
 59600,     # Уровень 56
 61400,     # Уровень 57
 63200,     # Уровень 58
 65050,     # Уровень 59
 66900,     # Уровень 60
 68800,     # Уровень 61
 70700,     # Уровень 62
 72650,     # Уровень 63
 74600,     # Уровень 64
 76600,     # Уровень 65
 78600,     # Уровень 66
 80650,     # Уровень 67
 82700,     # Уровень 68
 84800,     # Уровень 69
 86900,     # Уровень 70
 89050,     # Уровень 71
 91200,     # Уровень 72
 93400,     # Уровень 73
 95600,     # Уровень 74
 97850      # Уровень 75
]

TASK_TO_LESSON = {
    "1-1": "1.1", "1-2": "1.1", "1-3": "1.1", "1-4": "1.1", "1-5": "1.1", "1-6": "1.1", "1-7": "1.1",
    "1-8": "1.2", "1-9": "1.2", "1-10": "1.2",
    "1-11": "1.3",
    # добавляй дальше по мере разработки
}

def update_lesson_progress(user_data, task_id):
    new_progress = TASK_TO_LESSON.get(task_id)
    if new_progress and new_progress != user_data["progress"].get("lesson_progress"):
        user_data["progress"]["lesson_progress"] = new_progress



@app.route("/mentor", methods=["POST"])
def mentor_reply():

    data = request.get_json()
    user_id = str(data["user_id"])
    message = data["message"]
    reply = generate_response(user_id, message)
    return jsonify({"reply": reply})

def update_level(users, user_id):
    xp = users[user_id]['experience']
    current_level = users[user_id]['level']
    new_level = 1
    new_achievements = []

    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if xp >= threshold:
            new_level = i + 1
        else:
            break

    if new_level > current_level:
        users[user_id]['level'] = new_level

        for lvl, achievement in LEVEL_ACHIEVEMENTS.items():
            if new_level >= lvl and achievement not in users[user_id]['achievements']:
                users[user_id]['achievements'].append(achievement)
                new_achievements.append(achievement)

    return new_achievements  # 👈 Вернём список новых достижений

def get_level_by_experience(exp):
    for i in reversed(range(len(LEVEL_THRESHOLDS))):
        if exp >= LEVEL_THRESHOLDS[i]:
            return i + 1
    return 1

def get_user_id_by_username(username):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for user_id, user_data in data['users'].items():
        if user_data.get('username') == username:
            return user_id
    return None


@app.route('/courses/<username>')
def courses(username):
    user_id = get_user_id_by_username(username)
    if not user_id:
        return f"Пользователь {username} не найден", 404
    return render_template('courses.html', user_id=user_id)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')



def load_users():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("users", {})  # <-- вот ключевой момент

def save_users(users):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({"users": users}, f, ensure_ascii=False, indent=4)

def save_all_users(users):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({"users": users}, f, ensure_ascii=False, indent=4)

@app.route('/api/analyze', methods=['POST'])
def analyze_prompt():
    try:
        print("Абсолютный путь к DATA_FILE:", os.path.abspath(DATA_FILE))
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        user_id = str(data.get('user_id'))

        if not prompt:
            return jsonify({'error': 'Пустой промпт'}), 400
        if not user_id:
            return jsonify({'error': 'Не указан user_id'}), 400

        users = load_users()
        print(users.keys())

        if user_id not in users:
            return jsonify({'error': f'Пользователь {user_id} не найден'}), 404

        # === АНТИСПАМ-ПРОВЕРКИ ===

        # 1. Ограничение по частоте (30 секунд между запросами)
        now = time.time()
        last_time = users[user_id].get('last_prompt_time', 0)
        if now - last_time < 10:
            return jsonify({'error': 'Слишком часто! Подождите немного.'}), 429
        users[user_id]['last_prompt_time'] = now

        # 2. Проверка на минимальную длину промпта
        if len(prompt) < 10:
            return jsonify({'error': 'Промпт слишком короткий, минимум 10 символов.'}), 400

        # 3. Проверка на повтор промпта
        def hash_prompt(text):
            return hashlib.sha256(text.encode()).hexdigest()
        prompt_hash = hash_prompt(prompt)
        last_prompt_hash = users[user_id].get('last_prompt_hash')
        if last_prompt_hash == prompt_hash:
            return jsonify({'error': 'Промпт повторяется, опыт не начислен.'}), 400
        users[user_id]['last_prompt_hash'] = prompt_hash

        # === Начисление опыта ===
        users[user_id]['experience'] += 20
        update_level(users, user_id)

        # Сохраняем обновления
        save_users(users)

        # Анализ промпта (например, через YandexGPT)
        result = query_yandexgpt(prompt)

        return jsonify({'analysis': result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
def get_user_league(level: int):
    leagues = [
        {"name": "Искатели Искры", "emoji": "🔥", "color": "#a58c6f", "min": 1, "max": 4},
        {"name": "Подмастерья Промптов", "emoji": "🧱", "color": "#bb7e5d", "min": 5, "max": 9},
        {"name": "Архитекторы Разума", "emoji": "⚙️", "color": "#6b7b8c", "min": 10, "max": 19},
        {"name": "Владыки Моделей", "emoji": "🧠", "color": "#a9a9a9", "min": 20, "max": 34},
        {"name": "Создатели Сознаний", "emoji": "🔥", "color": "#f4c542", "min": 35, "max": 49},
        {"name": "Легенды ИИ", "emoji": "💎", "color": "#4ecdc4", "min": 50, "max": 64},
        {"name": "Сингулярности", "emoji": "🌀", "color": "#9c27b0", "min": 65, "max": 75}
    ]

    for league in leagues:
        if league["min"] <= level <= league["max"]:
            return {
                "name": league["name"],
                "emoji": league["emoji"],
                "color": league["color"]
            }

    return {
        "league_name": "Неизвестная Лига",
        "emoji": "❓",
        "color": "#cccccc"
    }



@app.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    EMOJI_POOL = ['🏆', '🎯', '🚀', '💡', '📘', '🔍', '🧠', '🌐', '🛠️', '📈', '🧪', '👑', '🦾', '🌀', '🧭']

    LEVEL_ACHIEVEMENTS = {
        1: "Ученики ИИ",
        5: "Подмастерье TeachAI",
        10: "Инженер Промптов",
        15: "Архитектор Разума",
        20: "Мастер ИИ",
        25: "Повелитель Моделей",
        30: "TeachAI: Легенда",
        35: "Алхимик Алгоритмов",
        40: "Повелитель Знаний",
        45: "Грандмастер Генерации",
        50: "Создатель Сознаний",
        55: "Навигатор Нейросетей",
        60: "Вершитель Промптов",
        65: "Демистификатор ИИ",
        70: "Бессмертный Разума",
        75: "TeachAI: Бессмертная Сингулярность"
    }

    course_achievements = {
        "1": "🔍 Исследователь искусственного интеллекта",
        "2": "🧠 Архитектор нейросетей",
        "3": "🌐 AI-мастер повседневности"
    }

    try:
        with open('user_history.json', 'r+', encoding='utf-8') as f:
            users = json.load(f)
            user_data = users.get("users", {}).get(str(user_id))

            app.logger.info(f"Запрошен user_id: {user_id}")

            if not user_data:
                user_data = {'level': 1, 'experience': 0, 'completed_courses': [], 'achievements': []}

            level = user_data.get('level', 1)
            league = get_user_league(level)

            # Кэш достижений с эмодзи (добавляется в user_data)
            if "achievements_cache" not in user_data:
                user_data["achievements_cache"] = {}

            achievements = []

            # Уровневые ачивки
            for lvl, title in LEVEL_ACHIEVEMENTS.items():
                if level >= lvl:
                    achievements.append({'emoji': '🏆', 'label': title})

            # Курсовые ачивки
            for course_id in user_data.get("completed_courses", []):
                label = course_achievements.get(str(course_id))
                if label:
                    emoji, *rest = label.split(' ', 1)
                    label_text = rest[0] if rest else label
                    achievements.append({'emoji': emoji, 'label': label_text})

            # Пользовательские ачивки
            for ach in user_data.get("achievements", []):
                if ach not in user_data["achievements_cache"]:
                    user_data["achievements_cache"][ach] = random.choice(EMOJI_POOL)
                emoji = user_data["achievements_cache"][ach]
                achievements.append({'emoji': emoji, 'label': ach})

            # Сохраняем кэш обратно
            users["users"][str(user_id)] = user_data
            f.seek(0)
            json.dump(users, f, ensure_ascii=False, indent=2)
            f.truncate()

            unique_achievements = {}
            for ach in achievements:
                key = ach['label']
                if key not in unique_achievements:
                    unique_achievements[key] = ach

            return jsonify({
                'level': level,
                'experience': user_data.get('experience', 0),
                'league': league,
                'achievements': list(unique_achievements.values())
            })

    except FileNotFoundError:
        return jsonify({'error': 'Файл user_history.json не найден'}), 500
    except json.JSONDecodeError:
        return jsonify({'error': 'Ошибка разбора JSON'}), 500
    except Exception as e:
        app.logger.exception("Неожиданная ошибка")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leaderboard')
def get_leaderboard():
    try:
        with open('user_history.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            users = data.get("users", {})

        leaderboard = [
            {
                "user_id": user_id,
                "username": info.get("username", "unknown"),
                "level": info.get("level", 0),
                "experience": info.get("experience", 0),
                "league": get_user_league(info.get("level", 0))
            }
            for user_id, info in users.items()
        ]

        leaderboard.sort(key=lambda x: (-x["experience"], -x["level"]))
        return jsonify(leaderboard[:50])

    except Exception as e:
        app.logger.exception("Ошибка при создании таблицы лидеров")
        return jsonify({"error": str(e)}), 500
SUBSCRIPTION_COST = 500

@app.route('/api/user/<int:user_id>/subscribe', methods=['POST'])
def buy_subscription(user_id):
    try:
        data = request.get_json()
        payment_token = data.get("payment_token")

        if not payment_token:
            return jsonify({'error': 'Отсутствует токен оплаты'}), 400

        with open('user_history.json', 'r', encoding='utf-8') as f:
            data_file = json.load(f)

        users = data_file.setdefault("users", {})
        user = users.get(str(user_id))

        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        # Проверка существующей подписки
        expiry_str = user.get("subscription_expiry")
        if expiry_str:
            expiry_date = datetime.fromisoformat(expiry_str)
            if expiry_date > datetime.utcnow():
                return jsonify({'message': 'Подписка уже активна', 'subscription_expiry': expiry_str}), 200

        # TODO: Проверка токена оплаты (например, через сторонний сервис)
        # Временно просто считаем, что токен валиден

        # Активация подписки
        new_expiry = datetime.utcnow() + timedelta(days=30)
        user["is_subscribed"] = True
        user["subscription_expiry"] = new_expiry.isoformat()

        with open('user_history.json', 'w', encoding='utf-8') as f:
            json.dump(data_file, f, ensure_ascii=False, indent=2)

        return jsonify({
            'message': 'Подписка успешно активирована',
            'subscription_expiry': user["subscription_expiry"]
        })

    except FileNotFoundError:
        return jsonify({'error': 'Файл user_history.json не найден'}), 500
    except Exception as e:
        app.logger.exception("Ошибка при покупке подписки")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/payment-confirmed', methods=['POST'])
def confirm_payment(user_id):
    try:
        data = request.get_json()
        telegram_payment_charge_id = data.get("telegram_payment_charge_id")

        if not telegram_payment_charge_id:
            return jsonify({'error': 'Отсутствует Telegram Payment Charge ID'}), 400

        with open('user_history.json', 'r', encoding='utf-8') as f:
            data_file = json.load(f)

        users = data_file.setdefault("users", {})
        user = users.get(str(user_id))

        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404

        # Обновление подписки
        new_expiry = datetime.utcnow() + timedelta(days=30)
        user["is_subscribed"] = True
        user["subscription_expiry"] = new_expiry.isoformat()
        user["last_payment_id"] = telegram_payment_charge_id

        with open('user_history.json', 'w', encoding='utf-8') as f:
            json.dump(data_file, f, ensure_ascii=False, indent=2)

        return jsonify({
            'message': 'Подписка активирована',
            'subscription_expiry': user["subscription_expiry"]
        })

    except Exception as e:
        app.logger.exception("Ошибка при подтверждении оплаты")
        return jsonify({'error': str(e)}), 500


    


def save_user_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def calculate_level(experience):
    # Определяем максимальный уровень, соответствующий текущему опыту
    level = 1
    for lvl, exp_required in sorted(LEVEL_THRESHOLDS.items()):
        if experience >= exp_required:
            level = lvl
    return level

@app.route('/api/complete-task', methods=['POST'])
def complete_task():
    data = request.get_json()
    user_id = str(data.get('user_id'))
    task_id = data.get('task_id')

    if not user_id or not task_id:
        return jsonify({"success": False, "message": "user_id или task_id не указаны"}), 400

    users = load_users()

    # Создаём пользователя, если его ещё нет
    if user_id not in users:
        users[user_id] = {
            "username": "",
            "progress": {
                "completed_themes": [],
                "tests_passed": 0,
                "test_results": [],
                "best_prompts": []
            },
            "level": 1,
            "experience": 0,
            "achievements": [],
            "feedback": []
        }

    user = users[user_id]

    if task_id in user['progress'].get('completed_themes', []):
        return jsonify({"success": True, "message": "Задача уже выполнена"}), 200

    # Добавляем задачу и опыт
    user['progress']['completed_themes'].append(task_id)
    user['experience'] += 50

    # Обновляем уровень и получаем достижения
    new_achievements = update_level(users, user_id)

    save_user_data(users)

    return jsonify({
        "success": True,
        "message": "Опыт добавлен, задача отмечена",
        "new_level": users[user_id]["level"],
        "new_achievements": new_achievements
    }), 200

@app.route('/api/get_completed_tasks', methods=['GET'])
def get_completed_tasks():
    user_id = request.args.get('userId')  # передай userId с фронта
    course_id = request.args.get('courseId')

    with open('user_history.json', 'r') as f:
        user_history = json.load(f)

    user_data = user_history.get(user_id, {'completed_tasks': [], 'exp': 0, 'level': 1})
    completed = [t for t in user_data['completed_tasks'] if t.startswith(course_id)]

    return jsonify({'completedTasks': completed})

@app.route('/mark_task_complete', methods=['POST'])
def mark_task_complete():
    print("Абсолютный путь к DATA_FILE:", os.path.abspath(DATA_FILE))

    data = request.get_json()
    user_id = str(data.get('user_id'))
    task_id = data.get('task_id')
    answer = data.get('answer')  # новый параметр

    if not user_id or not task_id:
        return jsonify({"success": False, "message": "user_id или task_id не указаны"}), 400

    users = load_users()
    print("Загруженные пользователи:", users.keys())

    if user_id not in users:
        return jsonify({'success': False, 'message': f'Пользователь {user_id} не найден'}), 404

    user = users[user_id]

    # Проверка, было ли задание уже выполнено
    if task_id in user['progress'].get('completed_themes', []):
        return jsonify({
            "success": True,
            "was_already_completed": True,
            "message": "Задача уже выполнена",
            "current_level": user["level"]
        }), 200

    # Сохраняем ответ пользователя
    user['progress'].setdefault('task_answers', {})[task_id] = answer

    # Обновляем прогресс
    user['progress'].setdefault('completed_themes', []).append(task_id)
    user['experience'] += 50

    # 🧠 Обновляем lesson_progress
    update_lesson_progress(user, task_id)

    new_achievements = update_level(users, user_id)

    # Сохраняем изменения
    users[user_id] = user
    save_all_users(users)

    return jsonify({
        "success": True,
        "was_already_completed": False,
        "message": "Опыт добавлен, задача отмечена",
        "current_level": user["level"],
        "new_achievements": new_achievements
    }), 200

@app.route('/get_user_progress', methods=['POST'])
def get_user_progress():
    data = request.get_json()
    user_id = str(data.get('user_id'))

    users = load_users()
    user = users.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "Пользователь не найден"}), 404

    all_courses = {
        "1": 21,
        "2": 9,
        "3": 20
    }
    course_names = {
    "1": "Введение в нейросети и ИИ",
    "2": "Типы нейросетей",
    "3": "Как использовать нейросети в повседневной жизни"
}

    course_achievements = {
    "1": "🔍 Исследователь ИИ",
    "2": "🧠 Архитектор нейросетей",
    "3": "🌐 AI-мастер повседневности"
}

    completed_themes = user.get("progress", {}).get("completed_themes", [])
    course_progress = {}

    for course_id, total in all_courses.items():
        completed = sum(1 for theme in completed_themes if theme.startswith(f"{course_id}-"))
        percent = int((completed / total) * 100) if total else 0

        course_progress[course_id] = {
    "completed": completed,
    "total": total,
    "progress_percent": percent,
    "course_name": course_names.get(course_id, f"Курс {course_id}")
}

        

        # === 💡 Проверка 100% и награда ===
        if percent == 100:
            achievement_name = course_achievements.get(course_id, f"Курс {course_id} завершён")
            if achievement_name not in user.get("achievements", []):
                user["experience"] += 500
                user["achievements"].append(achievement_name)

    # ✅ Сохраняем обновления
    save_users(users)

    return jsonify({"success": True, "courses": course_progress})










@app.route('/<path:path>')
def static_files(path):
    response = send_from_directory(app.static_folder, path)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(debug=True, port=3000)
    
