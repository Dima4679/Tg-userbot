"""
Альтернативный User Bot с использованием Pyrogram
Более простой и легкий вариант
"""

from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
import logging
import google.generativeai as genai

# Конфигурация
API_ID = 36091784  # Получить на https://my.telegram.org/apps
API_HASH = 'e20c0f30be3031c9549b84f3451390ad'  # Получить на https://my.telegram.org/apps
PHONE_NUMBER = '+1234567890'  # Ваш номер телефона (с кодом страны)
GEMINI_API_KEY = 'AIzaSyAzngAoNLb4D3aC-fmH_kB9Fox9DIHcSvM'

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Создание клиента
app = Client("userbot", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER)

# Конфигурация
AUTO_REPLY = True
USE_AI = True
REPLY_DELAY = 1  # сек


def generate_reply(text: str) -> str:
    """Генерировать ответ через AI"""
    try:
        prompt = f"""Respond naturally and briefly to: "{text}"
Keep it 1-2 sentences. Same language. NO prefix."""
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Thanks for the message! 👋"


@app.on_message(filters.private & filters.incoming)
async def auto_reply(client: Client, message: Message):
    """Автоматический ответ на приватные сообщения"""
    
    if not AUTO_REPLY:
        return
    
    try:
        sender = message.from_user
        logger.info(f"📨 Message from {sender.first_name}: {message.text}")
        
        # Генерировать ответ
        if USE_AI and message.text:
            reply_text = generate_reply(message.text)
        else:
            reply_text = "Thanks! 👋"
        
        # Задержка
        await asyncio.sleep(REPLY_DELAY)
        
        # Отправить ответ
        await message.reply(reply_text)
        logger.info(f"✅ Replied: {reply_text}")
        
    except Exception as e:
        logger.error(f"Error: {e}")


@app.on_message(filters.command("stop"))
async def stop_cmd(client: Client, message: Message):
    """Остановить бот"""
    await message.reply("🛑 Bot stopped!")
    await client.stop()


@app.on_message(filters.command("status"))
async def status_cmd(client: Client, message: Message):
    """Статус бота"""
    status_text = (
        "🟢 User Bot Active!\n\n"
        f"Auto-reply: {'✅ ON' if AUTO_REPLY else '❌ OFF'}\n"
        f"AI: {'✅ ON' if USE_AI else '❌ OFF'}\n"
    )
    await message.reply(status_text)


async def main():
    """Запуск"""
    logger.info("🚀 Starting User Bot...")
    async with app:
        me = await app.get_me()
        logger.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        logger.info(f"👂 Listening for messages...\n")
        logger.info(f"Auto-reply: {'✅ ON' if AUTO_REPLY else '❌ OFF'}")
        logger.info(f"AI: {'✅ ON' if USE_AI else '❌ OFF'}\n")
        
        await app.listen()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
