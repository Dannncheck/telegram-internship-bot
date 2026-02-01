import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

async def handle_channel_post(update: Update, context):
    if update.channel_post:
        chat_id = update.channel_post.chat.id
        chat_title = update.channel_post.chat.title
        print(f"\n{'='*50}")
        print(f"✅ ID КАНАЛА: {chat_id}")
        print(f"📢 Название: {chat_title}")
        print(f"{'='*50}\n")
        print(f"Добавьте в .env:\nTELEGRAM_CHAT_ID={chat_id}\n")

async def main():
    app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    app.add_handler(MessageHandler(filters.ALL, handle_channel_post))
    print("🤖 Бот запущен!")
    print("📢 Опубликуйте ЛЮБОЙ пост в канале (где бот админ)...")
    await app.run_polling(allowed_updates=['channel_post'])

asyncio.run(main())
