"""
Скрипт для получения вашего chat_id.
Запустите этот скрипт, затем напишите боту /start в Telegram.
"""
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден в .env")
    exit(1)

print("🤖 Бот запущен!")
print("📱 Теперь откройте Telegram и напишите боту любое сообщение или /start")
print("💡 После этого вы увидите ваш chat_id здесь\n")

async def handle_message(update: Update, context):
    """Обработчик любого сообщения."""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    print("=" * 50)
    print(f"✅ Получено сообщение!")
    print(f"👤 От: {user.first_name} {user.last_name or ''} (@{user.username or 'нет username'})")
    print(f"💬 Chat ID: {chat_id}")
    print(f"📝 Текст: {update.message.text}")
    print("=" * 50)
    print(f"\n🎯 Используйте этот chat_id в .env:\nTELEGRAM_CHAT_ID={chat_id}\n")
    
    # Отправляем подтверждение
    await update.message.reply_text(
        f"✅ Отлично! Ваш chat_id: {chat_id}\n\n"
        f"Добавьте в .env файл:\nTELEGRAM_CHAT_ID={chat_id}"
    )

async def main():
    """Запуск бота."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики для любых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("start", handle_message))
    
    # Запуск
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
