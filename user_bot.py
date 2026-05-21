"""
Telegram User Bot - Отвечает от личного аккаунта
Использует Telethon для работы с личным аккаунтом
"""

import asyncio
import logging
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
import google.generativeai as genai

# Конфигурация
API_ID = 27434893  # Ваш API ID (получить на https://my.telegram.org/apps)
API_HASH = '02e9e3da6b67d89abdac1a836a6be12e'  # Ваш API Hash
GEMINI_API_KEY = 'AIzaSyAzngAoNLb4D3aC-fmH_kB9Fox9DIHcSvM'

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Создание клиента Telethon
client = TelegramClient('userbot_session', API_ID, API_HASH)

# Конфигурация автоответчика
AUTO_REPLY_ENABLED = True
AUTO_REPLY_DELAY = 0.5  # Задержка перед ответом (сек)
AUTHORIZED_USERS = []  # Пустой список = отвечать всем
USE_AI = True  # Использовать AI для генерации ответов


def generate_auto_reply(message_text: str) -> str:
    """Генерировать ответ используя Gemini AI"""
    try:
        prompt = f"""You are a helpful Telegram assistant. Someone sent you this message: "{message_text}"
        
Generate a natural, friendly, and concise reply in the same language as the original message. 
Keep it short (1-2 sentences max). Be professional but warm.
Do NOT include any prefix like 'AI:', just the reply text."""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f'AI error: {e}')
        return "Спасибо за сообщение! 👋"


@client.on(events.NewMessage(incoming=True, from_users=None))
async def handle_new_message(event):
    """Обработчик входящих сообщений"""
    
    # Пропустить сообщения от бота
    if event.from_id is None:
        return
    
    # Пропустить сообщения из групп (если нужно)
    if event.is_group:
        return
    
    # Проверить авторизованные пользователи
    if AUTHORIZED_USERS and event.sender_id not in AUTHORIZED_USERS:
        return
    
    # Получить информацию об отправителе
    sender = await event.get_sender()
    sender_name = sender.first_name or "User"
    
    logger.info(f"📨 Сообщение от {sender_name} (@{sender.username}): {event.text}")
    
    try:
        # Генерировать ответ
        if USE_AI and event.text:
            reply_text = generate_auto_reply(event.text)
        else:
            reply_text = "Спасибо за сообщение! 👋"
        
        # Задержка перед ответом (выглядит натурально)
        await asyncio.sleep(AUTO_REPLY_DELAY)
        
        # Отправить ответ
        await event.reply(reply_text)
        
        logger.info(f"✅ Ответ отправлен: {reply_text}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке: {e}")


@client.on(events.NewMessage(pattern='^/status'))
async def status_command(event):
    """Команда /status"""
    if event.is_private:
        await event.reply(
            "🟢 Userbot активен!\n\n"
            f"Auto-reply: {'✅ ВКЛ' if AUTO_REPLY_ENABLED else '❌ ВЫК'}\n"
            f"AI: {'✅ ВКЛ' if USE_AI else '❌ ВЫК'}\n"
        )


@client.on(events.NewMessage(pattern='^/ping'))
async def ping_command(event):
    """Команда /ping"""
    if event.is_private:
        await event.reply("🏓 Pong! Я онлайн!")


async def main():
    """Главная функция"""
    logger.info("🚀 Запуск User Bot...")
    
    try:
        # Подключение
        await client.start()
        
        me = await client.get_me()
        logger.info(f"✅ Авторизован как: {me.first_name} (@{me.username})")
        
        logger.info("👂 Прослушивание входящих сообщений...")
        logger.info(f"Auto-reply: {'✅ ВКЛ' if AUTO_REPLY_ENABLED else '❌ ВЫК'}")
        logger.info(f"AI: {'✅ ВКЛ' if USE_AI else '❌ ВЫК'}")
        
        # Бесконечный цикл
        await client.run_until_disconnected()
        
    except SessionPasswordNeededError:
        logger.error("❌ Требуется двухфакторная аутентификация!")
        logger.info("Пожалуйста, введите пароль вручную")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    asyncio.run(main())
