from flask import Flask, jsonify, send_from_directory, request, render_template
import json
import os
from datetime import datetime, timedelta
import logging
from gigachat_api import query_gigachat_for_feedback
import hashlib
import time

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

        # Анализ промпта (например, через GigaChat API)
        result = query_gigachat_for_feedback(prompt)

        return jsonify({'analysis': result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
def get_user_league(level: int):
    leagues = [
        {"name": "Искатели Искры", "emoji": "🪙", "color": "#a58c6f", "min": 1, "max": 4},
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
    try:
        with open('user_history.json', 'r', encoding='utf-8') as f:
            users = json.load(f)

        user_data = users.get("users", {}).get(str(user_id))
        app.logger.info(f"Запрошен user_id: {user_id}")

        if user_data:
            level = user_data.get('level', 1)
            league = get_user_league(level)

            # Добавляем лигу в ответ
            user_data['league'] = league
            return jsonify(user_data)
        else:
            return jsonify({
                'level': 1,
                'experience': 0,
                'achievements': [],
                'league': get_user_league(1)
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
    try:
        data = request.get_json()
        user_id = str(data.get('user_id'))
        task_id = data.get('task_id')

        if not user_id or not task_id:
            return jsonify({'success': False, 'message': 'user_id или task_id отсутствует'}), 400

        users = load_users()
        if user_id not in users:
            return jsonify({'success': False, 'message': 'Пользователь не найден'}), 404

        user_data = users[user_id]

        # Обязательно инициализируем поля
        if 'completed_tasks' not in user_data:
            user_data['completed_tasks'] = []

        if 'experience' not in user_data:
            user_data['experience'] = 0

        # Проверка на повтор
        if task_id in user_data['completed_tasks']:
            return jsonify({'success': False, 'message': 'Задача уже выполнена'}), 400

        # Обновление данных
        
        user_data['completed_tasks'].append(task_id)
        logging.info(f"[{user_id}] Before XP: {user_data.get('experience')}")
        user_data['experience'] += 50
        logging.info(f"[{user_id}] After XP: {user_data.get('experience')}")

        update_level(users, user_id)  # важно, чтобы эта функция тоже меняла users[user_id]

        save_users(users)  # обязательно сохранить

        return jsonify({'success': True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
@app.route('/api/get_completed_tasks', methods=['GET'])
def get_completed_tasks():
    user_id = request.args.get('userId')  # передай userId с фронта
    course_id = request.args.get('courseId')

    with open('user_history.json', 'r') as f:
        user_history = json.load(f)

    user_data = user_history.get(user_id, {'completed_tasks': [], 'exp': 0, 'level': 1})
    completed = [t for t in user_data['completed_tasks'] if t.startswith(course_id)]

    return jsonify({'completedTasks': completed})














@app.route('/<path:path>')
def static_files(path):
    response = send_from_directory(app.static_folder, path)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(debug=True, port=3000)
    
