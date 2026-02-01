import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

async def handle_forwarded(update: Update, context):
    if update.message and update.message.forward_origin:
        origin = update.message.forward_origin
        
        # Проверяем тип источника
        if hasattr(origin, 'chat'):
            chat = origin.chat
            print(f"\n{'='*60}")
            print(f"✅ ID КАНАЛА: {chat.id}")
            print(f"📢 Название: {chat.title}")
            if hasattr(chat, 'username') and chat.username:
                print(f"🔗 Username: @{chat.username}")
            print(f"{'='*60}\n")
            print(f"Используйте в .env:")
            if hasattr(chat, 'username') and chat.username:
                print(f"TELEGRAM_CHAT_ID=@{chat.username}")
            else:
                print(f"TELEGRAM_CHAT_ID={chat.id}")
            print()
            
            await update.message.reply_text(
                f"✅ ID канала: {chat.id}\n"
                f"📢 {chat.title}"
            )

async def main():
    app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    app.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded))
    
    print("🤖 Бот @interrn_bot готов!")
    print("📱 Теперь:")
    print("   1. Опубликуйте пост в канале")
    print("   2. Перешлите его боту @interrn_bot в личку\n")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
