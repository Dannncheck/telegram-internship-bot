import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

async def handle_any_message(update: Update, context):
    chat_id = update.effective_chat.id
    print(f"\n{'='*50}")
    print(f"✅ ВАШ CHAT_ID: {chat_id}")
    print(f"{'='*50}\n")
    print(f"Добавьте в .env:\nTELEGRAM_CHAT_ID={chat_id}\n")
    await update.message.reply_text(f"Ваш chat_id: {chat_id}")

async def main():
    app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    app.add_handler(MessageHandler(filters.ALL, handle_any_message))
    print("🤖 Бот запущен! Напишите ему ЛЮБОЕ сообщение в Telegram...")
    await app.run_polling()

asyncio.run(main())cat > get_my_id.py << 'EOF'
import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

async def handle_any_message(update: Update, context):
    chat_id = update.effective_chat.id
    print(f"\n{'='*50}")
    print(f"✅ ВАШ CHAT_ID: {chat_id}")
    print(f"{'='*50}\n")
    print(f"Добавьте в .env:\nTELEGRAM_CHAT_ID={chat_id}\n")
    await update.message.reply_text(f"Ваш chat_id: {chat_id}")

async def main():
    app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    app.add_handler(MessageHandler(filters.ALL, handle_any_message))
    print("🤖 Бот запущен! Напишите ему ЛЮБОЕ сообщение в Telegram...")
    await app.run_polling()

asyncio.run(main())
EOF
