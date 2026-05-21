from flask import Flask, jsonify, request
from functools import wraps
import logging
import json
from datetime import datetime
import google.generativeai as genai
import telebot
from telebot import types

app = Flask(__name__)

# Конф��гурация
app.config['SECRET_KEY'] = 'your-secret-key-here'
API_TOKEN = 'bot-secret-token'
GEMINI_API_KEY = 'AIzaSyAzngAoNLb4D3aC-fmH_kB9Fox9DIHcSvM'
TELEGRAM_BOT_TOKEN = '8911412500:AAGuZSZ4NlgT46GKLpB8Ppu8ILuwBURenvg'

# Настройка Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Настройка Telegram Bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище данных аккаунта
accounts_db = {
    'default': {
        'username': 'default_user',
        'phone': '+1234567890',
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'sessions': [],
        'settings': {
            'auto_reply': False,
            'proxy': None,
            'privacy': 'friends',
            'ai_enabled': True,
            'telegram_enabled': True
        }
    }
}

# Хранилище сессий
active_sessions = {}

# История сообщений для контекста AI
conversation_history = {}

# Хранилище пользователей Telegram
telegram_users = {}


def require_token(f):
    """Декоратор для пр��верки токена API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token != API_TOKEN:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ===== TELEGRAM BOT HANDLERS =====

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    telegram_users[user_id] = {
        'username': username,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name,
        'connected_account': None,
        'created_at': datetime.now().isoformat()
    }
    
    reply_text = f"👋 Добро пожаловать, {username}!\n\n"
    reply_text += "🤖 Это бот управления Telegram аккаунтами с поддержкой Gemini AI.\n\n"
    reply_text += "📋 Команды:\n"
    reply_text += "/help - Справка\n"
    reply_text += "/status - Статус бота\n"
    reply_text += "/accounts - Список аккаунтов\n"
    reply_text += "/ai - Помощь AI\n"
    
    bot.reply_to(message, reply_text)
    logger.info(f'New user connected: {username} ({user_id})')


@bot.message_handler(commands=['help'])
def send_help(message):
    """Обработчик команды /help"""
    help_text = "📚 Справка по командам:\n\n"
    help_text += "/start - Начало\n"
    help_text += "/status - Статус сервера\n"
    help_text += "/accounts - Список аккаунтов\n"
    help_text += "/ai [вопрос] - Спросить у AI\n"
    help_text += "/analyze [текст] - Анализировать текст\n"
    
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['status'])
def send_status(message):
    """Обработчик команды /status"""
    active_acc = len([a for a in accounts_db.values() if a['status'] == 'active'])
    status_text = f"🟢 Статус сервера: ОНЛАЙН\n\n"
    status_text += f"👥 Активных аккаунтов: {active_acc}\n"
    status_text += f"📊 Всего а��каунтов: {len(accounts_db)}\n"
    status_text += f"👤 Активных сессий: {len(active_sessions)}\n"
    status_text += f"🤖 Gemini AI: Включена\n"
    status_text += f"⏰ Время сервера: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    bot.reply_to(message, status_text)


@bot.message_handler(commands=['accounts'])
def send_accounts(message):
    """Обработчик команды /accounts"""
    accounts_text = "📋 Список аккаунтов:\n\n"
    for acc_id, acc_data in accounts_db.items():
        accounts_text += f"👤 {acc_data['username']} (@{acc_id})\n"
        accounts_text += f"   📱 {acc_data['phone']}\n"
        accounts_text += f"   🟢 Статус: {acc_data['status']}\n\n"
    
    bot.reply_to(message, accounts_text)


@bot.message_handler(commands=['ai'])
def handle_ai_command(message):
    """Обработчик команды /ai"""
    if len(message.text) <= 4:
        bot.reply_to(message, "Использование: /ai [вопрос]\nПример: /ai Что такое Python?")
        return
    
    question = message.text[4:].strip()
    bot.send_message(message.chat.id, "⏳ Генерирую ответ от Gemini AI...")
    
    try:
        response = generate_ai_response(question)
        bot.send_message(message.chat.id, f"🤖 AI Ответ:\n\n{response}")
        logger.info(f'AI response generated for user {message.from_user.id}')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")


@bot.message_handler(commands=['analyze'])
def handle_analyze_command(message):
    """Обработчик команды /analyze"""
    if len(message.text) <= 9:
        bot.reply_to(message, "Использование: /analyze [текст]\nПример: /analyze Отличное решение!")
        return
    
    text = message.text[9:].strip()
    bot.send_message(message.chat.id, "📊 Анализирую текст...")
    
    try:
        analysis = analyze_message(text)
        analysis_text = "📊 Анализ текста:\n\n"
        if isinstance(analysis, dict):
            for key, value in analysis.items():
                analysis_text += f"{key}: {value}\n"
        else:
            analysis_text += str(analysis)
        
        bot.send_message(message.chat.id, analysis_text)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Обработчик обычных сообщений"""
    user_id = message.from_user.id
    
    if message.chat.type == 'private':
        # Личные сообщения
        bot.send_message(message.chat.id, 
            "📝 Сообщение получено!\n\n"
            "Используйте /help для справки по командам."
        )
        logger.info(f'Message from {user_id}: {message.text}')


# ===== AI FUNCTIONS =====

def generate_ai_response(prompt: str, account_id: str = None) -> str:
    """Генерировать ответ используя Gemini AI"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f'Gemini API error: {e}')
        return f'Error generating response: {str(e)}'


def generate_auto_reply(message_text: str, account_id: str) -> str:
    """Сгенерировать автоматический ответ на сообщение"""
    prompt = f"""You are a helpful Telegram bot assistant. Someone sent you this message: "{message_text}"
    
Generate a natural, friendly, and concise auto-reply message in the same language as the original message. 
Keep it short (1-2 sentences max). Be professional but warm."""
    
    return generate_ai_response(prompt, account_id)


def analyze_message(message_text: str) -> dict:
    """Анализировать сообщение используя AI"""
    prompt = f"""Analyze this message and provide:
1. Sentiment (positive/negative/neutral)
2. Intent (what the user wants)
3. Language (detected language)

Message: "{message_text}"

Respond in JSON format."""
    
    response = generate_ai_response(prompt)
    try:
        return json.loads(response)
    except:
        return {'response': response}


# ===== ACCOUNT MANAGEMENT =====

@app.route('/api/accounts', methods=['GET'])
@require_token
def get_accounts():
    """Получить список всех аккаунтов"""
    accounts = []
    for acc_id, acc_data in accounts_db.items():
        accounts.append({
            'id': acc_id,
            'username': acc_data['username'],
            'status': acc_data['status'],
            'created_at': acc_data['created_at']
        })
    return jsonify({
        'status': 'success',
        'accounts': accounts,
        'count': len(accounts)
    })


@app.route('/api/accounts/<acc_id>', methods=['GET'])
@require_token
def get_account(acc_id):
    """Получить информацию о конкретном аккаунте"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    acc = accounts_db[acc_id]
    return jsonify({
        'status': 'success',
        'account': {
            'id': acc_id,
            'username': acc['username'],
            'phone': acc['phone'],
            'status': acc['status'],
            'created_at': acc['created_at'],
            'settings': acc['settings'],
            'sessions_count': len(acc['sessions'])
        }
    })


@app.route('/api/accounts', methods=['POST'])
@require_token
def create_account():
    """Создать новый аккаунт"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'phone' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    acc_id = f"acc_{len(accounts_db)}"
    
    accounts_db[acc_id] = {
        'username': data['username'],
        'phone': data['phone'],
        'status': 'inactive',
        'created_at': datetime.now().isoformat(),
        'sessions': [],
        'settings': {
            'auto_reply': data.get('auto_reply', False),
            'proxy': data.get('proxy', None),
            'privacy': data.get('privacy', 'friends'),
            'ai_enabled': data.get('ai_enabled', True),
            'telegram_enabled': data.get('telegram_enabled', True)
        }
    }
    
    conversation_history[acc_id] = []
    logger.info(f'New account created: {acc_id}')
    
    return jsonify({
        'status': 'success',
        'account_id': acc_id,
        'message': 'Account created'
    }), 201


@app.route('/api/accounts/<acc_id>', methods=['PUT'])
@require_token
def update_account(acc_id):
    """Обновить данные аккаунта"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.get_json()
    acc = accounts_db[acc_id]
    
    if 'username' in data:
        acc['username'] = data['username']
    if 'phone' in data:
        acc['phone'] = data['phone']
    if 'settings' in data:
        acc['settings'].update(data['settings'])
    
    logger.info(f'Account updated: {acc_id}')
    
    return jsonify({
        'status': 'success',
        'message': 'Account updated'
    })


@app.route('/api/accounts/<acc_id>', methods=['DELETE'])
@require_token
def delete_account(acc_id):
    """Удалить аккаунт"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    del accounts_db[acc_id]
    if acc_id in conversation_history:
        del conversation_history[acc_id]
    
    logger.info(f'Account deleted: {acc_id}')
    
    return jsonify({
        'status': 'success',
        'message': 'Account deleted'
    })


# ===== SESSION MANAGEMENT =====

@app.route('/api/accounts/<acc_id>/login', methods=['POST'])
@require_token
def login_account(acc_id):
    """Авторизовать аккаунт"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    session_id = f"session_{datetime.now().timestamp()}"
    
    session_data = {
        'session_id': session_id,
        'account_id': acc_id,
        'created_at': datetime.now().isoformat(),
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    
    active_sessions[session_id] = session_data
    accounts_db[acc_id]['sessions'].append(session_id)
    accounts_db[acc_id]['status'] = 'active'
    
    logger.info(f'Account logged in: {acc_id}, session: {session_id}')
    
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'message': 'Logged in successfully'
    })


@app.route('/api/accounts/<acc_id>/logout', methods=['POST'])
@require_token
def logout_account(acc_id):
    """Выйти из аккаунта"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    accounts_db[acc_id]['sessions'].clear()
    accounts_db[acc_id]['status'] = 'inactive'
    
    logger.info(f'Account logged out: {acc_id}')
    
    return jsonify({
        'status': 'success',
        'message': 'Logged out successfully'
    })


@app.route('/api/accounts/<acc_id>/sessions', methods=['GET'])
@require_token
def get_sessions(acc_id):
    """Получить все сессии аккаунта"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    sessions = []
    for session_id in accounts_db[acc_id]['sessions']:
        if session_id in active_sessions:
            sessions.append(active_sessions[session_id])
    
    return jsonify({
        'status': 'success',
        'sessions': sessions,
        'count': len(sessions)
    })


# ===== ACCOUNT ACTIONS =====

@app.route('/api/accounts/<acc_id>/send-message', methods=['POST'])
@require_token
def send_message(acc_id):
    """Отправить сообщение от аккаунта"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    if accounts_db[acc_id]['status'] != 'active':
        return jsonify({'error': 'Account is not active'}), 400
    
    data = request.get_json()
    
    if not data or 'to' not in data or 'text' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    message = {
        'from': acc_id,
        'to': data['to'],
        'text': data['text'],
        'timestamp': datetime.now().isoformat(),
        'status': 'sent'
    }
    
    # Сохранить в историю
    if acc_id not in conversation_history:
        conversation_history[acc_id] = []
    conversation_history[acc_id].append(message)
    
    logger.info(f'Message sent from {acc_id} to {data["to"]}')
    
    return jsonify({
        'status': 'success',
        'message': message,
        'result': 'Message sent'
    })


@app.route('/api/accounts/<acc_id>/settings', methods=['GET'])
@require_token
def get_settings(acc_id):
    """Получить настройки аккаунта"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    return jsonify({
        'status': 'success',
        'settings': accounts_db[acc_id]['settings']
    })


@app.route('/api/accounts/<acc_id>/settings', methods=['PUT'])
@require_token
def update_settings(acc_id):
    """Обновить настройки аккаунта"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.get_json()
    accounts_db[acc_id]['settings'].update(data)
    
    logger.info(f'Settings updated for account: {acc_id}')
    
    return jsonify({
        'status': 'success',
        'settings': accounts_db[acc_id]['settings'],
        'message': 'Settings updated'
    })


@app.route('/api/accounts/<acc_id>/conversation-history', methods=['GET'])
@require_token
def get_conversation_history(acc_id):
    """Получить историю сообщений для аккаунта"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    history = conversation_history.get(acc_id, [])
    
    return jsonify({
        'status': 'success',
        'account_id': acc_id,
        'history': history,
        'count': len(history)
    })


# ===== AI FEATURES =====

@app.route('/api/accounts/<acc_id>/ai/generate-reply', methods=['POST'])
@require_token
def ai_generate_reply(acc_id):
    """Сгенерировать ответ на сообщение используя AI"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    if not accounts_db[acc_id]['settings'].get('ai_enabled', True):
        return jsonify({'error': 'AI is disabled for this account'}), 400
    
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing message field'}), 400
    
    try:
        reply = generate_auto_reply(data['message'], acc_id)
        return jsonify({
            'status': 'success',
            'original_message': data['message'],
            'generated_reply': reply
        })
    except Exception as e:
        logger.error(f'AI reply generation error: {e}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/accounts/<acc_id>/ai/analyze-message', methods=['POST'])
@require_token
def ai_analyze_message(acc_id):
    """Анализировать сообщение используя AI"""
    if acc_id not in accounts_db:
        return jsonify({'error': 'Account not found'}), 404
    
    if not accounts_db[acc_id]['settings'].get('ai_enabled', True):
        return jsonify({'error': 'AI is disabled for this account'}), 400
    
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing message field'}), 400
    
    try:
        analysis = analyze_message(data['message'])
        return jsonify({
            'status': 'success',
            'message': data['message'],
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f'AI analysis error: {e}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/ai/chat', methods=['POST'])
@require_token
def ai_chat():
    """General AI chat endpoint"""
    data = request.get_json()
    
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Missing prompt field'}), 400
    
    try:
        response = generate_ai_response(data['prompt'])
        return jsonify({
            'status': 'success',
            'prompt': data['prompt'],
            'response': response
        })
    except Exception as e:
        logger.error(f'AI chat error: {e}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ===== TELEGRAM FEATURES =====

@app.route('/api/telegram/users', methods=['GET'])
@require_token
def get_telegram_users():
    """Получить список пользователей Telegram"""
    users = []
    for user_id, user_data in telegram_users.items():
        users.append({
            'user_id': user_id,
            'username': user_data['username'],
            'first_name': user_data['first_name'],
            'connected_account': user_data['connected_account'],
            'created_at': user_data['created_at']
        })
    
    return jsonify({
        'status': 'success',
        'users': users,
        'count': len(users)
    })


@app.route('/api/telegram/send-message', methods=['POST'])
@require_token
def telegram_send_message():
    """Отправить сообщение через Telegram"""
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'text' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        bot.send_message(data['user_id'], data['text'])
        logger.info(f'Message sent via Telegram to {data["user_id"]}')
        return jsonify({
            'status': 'success',
            'message': 'Message sent'
        })
    except Exception as e:
        logger.error(f'Telegram send error: {e}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ===== SERVER STATUS =====

@app.route('/api/status', methods=['GET'])
def server_status():
    """Проверить статус сервера"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'active_accounts': len([a for a in accounts_db.values() if a['status'] == 'active']),
        'active_sessions': len(active_sessions),
        'telegram_users': len(telegram_users),
        'ai_enabled': True,
        'gemini_model': 'gemini-pro',
        'telegram_bot': 'active'
    })


@app.route('/', methods=['GET'])
def home():
    """Главная страница"""
    return jsonify({
        'status': 'success',
        'message': 'Telegram Userbot Account Manager Server with Gemini AI',
        'version': '3.0',
        'api_docs': '/api/docs',
        'features': {
            'ai_powered': True,
            'telegram_integrated': True,
            'account_management': True
        }
    })


@app.route('/api/docs', methods=['GET'])
def api_docs():
    """Документация API"""
    return jsonify({
        'status': 'success',
        'version': '3.0',
        'api_endpoints': {
            'accounts': {
                'GET /api/accounts': 'Получить список всех аккаунтов',
                'GET /api/accounts/<id>': 'Получить информацию об аккаунте',
                'POST /api/accounts': 'Создать новый аккаунт',
                'PUT /api/accounts/<id>': 'Обновить аккаунт',
                'DELETE /api/accounts/<id>': 'Удалить аккаунт'
            },
            'sessions': {
                'POST /api/accounts/<id>/login': 'Авторизовать аккаунт',
                'POST /api/accounts/<id>/logout': 'Выйти из аккаунта',
                'GET /api/accounts/<id>/sessions': 'Получить сессии'
            },
            'actions': {
                'POST /api/accounts/<id>/send-message': 'Отправить сообщение',
                'GET /api/accounts/<id>/settings': 'Получить настройки',
                'PUT /api/accounts/<id>/settings': 'Обновить настройки',
                'GET /api/accounts/<id>/conversation-history': 'Получить историю'
            },
            'ai_features': {
                'POST /api/accounts/<id>/ai/generate-reply': 'Сгенерировать ответ',
                'POST /api/accounts/<id>/ai/analyze-message': 'Анализировать сообщение',
                'POST /api/ai/chat': 'Чат с AI'
            },
            'telegram': {
                'GET /api/telegram/users': 'Получить пользователей Telegram',
                'POST /api/telegram/send-message': 'Отправить сообщение в Telegram'
            },
            'status': {
                'GET /api/status': 'Статус сервера'
            }
        }
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal error: {error}')
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    logger.info('🚀 Starting Telegram Userbot Account Manager Server')
    logger.info('🤖 Gemini AI enabled and ready')
    logger.info('📱 Telegram Bot active')
    logger.info('📝 API Documentation available at http://localhost:5000/api/docs')
    
    # Запустить Flask в отдельном потоке
    from threading import Thread
    
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запустить Telegram Bot
    logger.info('Starting Telegram bot polling...')
    bot.infinity_polling()
