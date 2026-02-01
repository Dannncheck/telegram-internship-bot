import os
from telegram import Bot
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def find_channel():
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    
    # Получаем информацию о боте
    me = await bot.get_me()
    print(f"🤖 Бот: @{me.username}")
    print("\nТеперь:")
    print("1. Добавьте бота админом в канал")
    print("2. Опубликуйте в канале тестовый пост")
    print("3. Перешлите этот пост боту в личку")
    print("4. Бот покажет ID канала\n")

asyncio.run(find_channel())
