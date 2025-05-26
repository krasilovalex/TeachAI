from flask import Flask, jsonify, send_from_directory, request, render_template
import json
import os
from datetime import datetime, timedelta
import logging
from gigachat_api import query_gigachat_for_feedback

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
    30: "TeachAI: Легенда"
}

LEVEL_THRESHOLDS = [
    0,     # Уровень 1
    100,   # Уровень 2
    250,   # Уровень 3
    450,   # Уровень 4
    700,   # Уровень 5
    950,   # Уровень 6
    1150,  # Уровень 7
    1300,  # Уровень 8
    1400,  # Уровень 9
    1500,  # Уровень 10
    1700,  # Уровень 11
    1900,  # Уровень 12
    2150,  # Уровень 13
    2400,  # Уровень 14
    2700,  # Уровень 15
    3000,  # Уровень 16
    3400,  # Уровень 17
    3800,  # Уровень 18
    4200,  # Уровень 19
    4600,  # Уровень 20
    5100,  # Уровень 21
    5600,  # Уровень 22
    6200,  # Уровень 23
    6800,  # Уровень 24
    7500,  # Уровень 25
    8200,  # Уровень 26
    9000,  # Уровень 27
    9800,  # Уровень 28
    10700, # Уровень 29
    11700  # Уровень 30
]

def update_level(users, user_id):
    xp = users[user_id]['experience']
    current_level = users[user_id]['level']

    # Индекс соответствует уровню (0 = уровень 1, 1 = уровень 2, ...)
    new_level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if xp >= threshold:
            new_level = i + 1  # i=0 -> уровень 1, i=1 -> уровень 2
        else:
            break

    if new_level > current_level:
        users[user_id]['level'] = new_level
        # Добавим достижения за новые уровни
        for lvl, achievement in LEVEL_ACHIEVEMENTS.items():
            if new_level >= lvl and achievement not in users[user_id]['achievements']:
                users[user_id]['achievements'].append(achievement)

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
        user_id = str(data.get('user_id'))  # приведение к строке — обязательно

        if not prompt:
            return jsonify({'error': 'Пустой промпт'}), 400

        if not user_id:
            return jsonify({'error': 'Не указан user_id'}), 400

        # Загружаем пользователей
        users = load_users()
        print(users.keys())

        if user_id not in users:
            return jsonify({'error': f'Пользователь {user_id} не найден'}), 404

        # Увеличиваем опыт
        users[user_id]['experience'] += 20

        update_level(users, user_id)

        # Сохраняем обратно
        save_users(users)

        # Анализируем промпт (например, через GigaChat API)
        result = query_gigachat_for_feedback(prompt)

        return jsonify({'analysis': result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>')
def get_user_data(user_id):
    try:
        with open('user_history.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
        user_data = users.get("users", {}).get(str(user_id))
        app.logger.info(f"Запрошен user_id: {user_id}")
        if user_data:
            return jsonify(user_data)
        else:
            return jsonify({
                'level': 1,
                'experience': 0,
                'achievements': []
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
                "experience": info.get("experience", 0)
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
    
