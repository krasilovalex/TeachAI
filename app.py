from flask import Flask, jsonify, send_from_directory, request, render_template
import json
import os
from datetime import datetime, timedelta
import logging
from gigachat_api import query_gigachat_for_feedback

app = Flask(__name__, static_folder="public")
DATA_FILE = 'user_history.json'
logging.basicConfig(level=logging.INFO)

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



@app.route('/api/analyze', methods=['POST'])
def analyze_prompt():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return jsonify({'error': 'Пустой промпт'}), 400

        result = query_gigachat_for_feedback(prompt)
        return jsonify({'analysis': result})
    except Exception as e:
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
    
LEVEL_THRESHOLDS = {
    1: 0,
    2: 10,
    3: 25,
    4: 50,
    5: 80,
    6: 120
    # и т.д.
}

ACHIEVEMENTS = {
    1: "Первый шаг",
    3: "Наставник новичков",
    5: "Продвинутый инженер"
}

def load_user_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

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

@app.route('/api/complete_task', methods=['POST'])
def complete_task():
    try:
        data = request.get_json()
        user_id = str(data.get('userId'))
        task_id = data.get('taskId')

        app.logger.info(f"Получен userId={user_id}, taskId={task_id}")

        if not user_id or not task_id:
            return jsonify({'status': 'error', 'message': 'userId и taskId обязательны'}), 400

        user_data = load_user_data()
        users = user_data.setdefault('users', {})

        # Инициализация пользователя, если он ещё не существует
        user = users.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'Пользователь не найден'}), 404

        # Обеспечим наличие вложенного progress
        user.setdefault('progress', {})
        progress = user['progress']

        # Обновляем структуру, если каких-то полей нет
        progress.setdefault('completed_themes', [])
        progress.setdefault('tests_passed', 0)
        progress.setdefault('test_results', [])
        progress.setdefault('best_prompts', [])
        progress.setdefault('completed_tests', [])

        # Добавляем taskId, если он ещё не зафиксирован
        if task_id not in progress['completed_tests']:
            progress['completed_tests'].append(task_id)
            save_user_data(user_data)
            app.logger.info(f"Пользователь {user_id} выполнил задачу {task_id}")

        return jsonify({
            'status': 'ok',
            'completedTests': progress['completed_tests']
        })

    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'Файл user_history.json не найден'}), 500
    except json.JSONDecodeError:
        return jsonify({'status': 'error', 'message': 'Ошибка разбора JSON'}), 500
    except Exception as e:
        app.logger.exception("Неожиданная ошибка при выполнении задачи")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
    
