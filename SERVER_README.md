# Telegram Userbot Bot Server

## 🚀 Полнофункциональный сервер управления Telegram аккаунтами с Gemini AI

### Особенности

- ✅ Управление аккаунтами Telegram
- ✅ Встроенный Telegram бот
- ✅ Интеграция с Gemini AI для генерации ответов
- ✅ Анализ сообщений с помощью AI
- ✅ RESTful API для управления
- ✅ Система сессий и авторизации
- ✅ История сообщений
- ✅ Автоматические ответы
- ✅ Управление настройками

### Установка

1. Установите зависимости:
```bash
pip install -r requirements_server.txt
```

2. Создайте `.env` файл с вашими ключами (см. `.env.example`)

3. Запустите сервер:
```bash
python bot_server.py
```

### Конфигурация

Необходимо установить следующие переменные окружения или отредактировать `bot_server.py`:

```python
GEMINI_API_KEY = 'AIzaSyAzngAoNLb4D3aC-fmH_kB9Fox9DIHcSvM'
TELEGRAM_BOT_TOKEN = '8911412500:AAGuZSZ4NlgT46GKLpB8Ppu8ILuwBURenvg'
API_TOKEN = 'bot-secret-token'
```

### API Endpoints

#### Управление аккаунтами

- `GET /api/accounts` - Получить все аккаунты
- `GET /api/accounts/<id>` - Получить аккаунт
- `POST /api/accounts` - Создать аккаунт
- `PUT /api/accounts/<id>` - Обновить аккаунт
- `DELETE /api/accounts/<id>` - Удалить аккаунт

#### Сессии

- `POST /api/accounts/<id>/login` - Авторизация
- `POST /api/accounts/<id>/logout` - Выход
- `GET /api/accounts/<id>/sessions` - Получить сессии

#### Действия

- `POST /api/accounts/<id>/send-message` - Отправить сообщение
- `GET /api/accounts/<id>/settings` - Получить настройки
- `PUT /api/accounts/<id>/settings` - Обновить настройки
- `GET /api/accounts/<id>/conversation-history` - История

#### AI Функции

- `POST /api/accounts/<id>/ai/generate-reply` - Сгенерировать ответ
- `POST /api/accounts/<id>/ai/analyze-message` - Анализировать сообщение
- `POST /api/ai/chat` - Чат с AI

#### Telegram

- `GET /api/telegram/users` - Список пользователей
- `POST /api/telegram/send-message` - Отправить сообщение

#### Статус

- `GET /api/status` - Статус сервера
- `GET /api/docs` - Документация API

### Использование Telegram Бота

#### Команды

```
/start - Начало работы
/help - Справка
/status - Статус сервера
/accounts - Список аккаунтов
/ai [вопрос] - Спросить у AI
/analyze [текст] - Анализировать текст
```

### Примеры API запросов

#### Создание аккаунта

```bash
curl -X POST http://localhost:5000/api/accounts \
  -H "Authorization: Bearer bot-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "phone": "+1234567890",
    "ai_enabled": true,
    "telegram_enabled": true
  }'
```

#### Генерация ответа с помощью AI

```bash
curl -X POST http://localhost:5000/api/accounts/acc_0/ai/generate-reply \
  -H "Authorization: Bearer bot-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Привет! Как дела?"
  }'
```

#### Анализ сообщения

```bash
curl -X POST http://localhost:5000/api/accounts/acc_0/ai/analyze-message \
  -H "Authorization: Bearer bot-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Это отличное решение!"
  }'
```

#### Отправка сообщения через Telegram

```bash
curl -X POST http://localhost:5000/api/telegram/send-message \
  -H "Authorization: Bearer bot-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "text": "Привет! Это сообщение от сервера"
  }'
```

### Использование Client

```python
from bot_client import BotServerClient

client = BotServerClient()

# Создать аккаунт
result = client.create_account(
    username='test_user',
    phone='+1234567890'
)

acc_id = result['account_id']

# Авторизоваться
client.login(acc_id)

# Сгенерировать ответ
reply = client.ai_generate_reply(acc_id, 'Привет!')

# Отправить сообщение
client.send_message(acc_id, 'user123', 'Привет!')

# Чат с AI
response = client.ai_chat('What is Python?')

# Выйти
client.logout(acc_id)
```

### Архитектура

```
bot_server.py
├── Flask приложение
├── Telegram Bot (pyTelegramBotAPI)
├── Gemini AI (google-generativeai)
├── Account Management
├── Session Management
├── Message History
└── API Endpoints
```

### Требования

- Python 3.8+
- Flask 2.3.2+
- pyTelegramBotAPI 4.14.0+
- google-generativeai 0.3.0+
- requests 2.31.0+

### Порты

- API сервер: `5000`
- Telegram Bot: Использует Telegram Bot API

### Логирование

Логи выводятся в консоль с уровнем INFO.

### Лицензия

MIT

### Поддержка

Для проблем и вопросов создавайте Issues в репозитории.
