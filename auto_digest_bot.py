"""
Telegram бот с автоматической отправкой дайджестов каждые 4 часа.
Также доступны команды для ручного запроса.
"""
import os
import asyncio
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import sqlite3
from pathlib import Path
import sys

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers import collect_all_internships
from db import upsert_and_get_changes, get_internships_count
from telegram_bot import build_digest_message, build_no_changes_message

load_dotenv()

# Настройки
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_PATH = Path(os.getenv("DB_PATH", "./internships.db"))

# Интервал проверки (в часах)
CHECK_INTERVAL_HOURS = 4


def get_open_internships():
    """Получить открытые стажировки."""
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT company, title, status, url 
        FROM internships 
        WHERE status LIKE '%Открыт%' 
           OR status LIKE '%набор%'
           OR status LIKE '%Идет%'
           OR status LIKE '%Прием заявок%'
           OR status LIKE '%Приём заявок%'
        ORDER BY company, title
    """)
    results = cursor.fetchall()
    conn.close()
    return results


def get_stats():
    """Получить статистику."""
    if not DB_PATH.exists():
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM internships")
    total = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM internships 
        WHERE status LIKE '%Открыт%' 
           OR status LIKE '%набор%'
           OR status LIKE '%Идет%'
           OR status LIKE '%Прием заявок%'
           OR status LIKE '%Приём заявок%'
    """)
    open_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT company) FROM internships")
    companies = cursor.fetchone()[0]
    
    conn.close()
    return {'total': total, 'open': open_count, 'companies': companies}


def escape_html(text):
    """Экранировать HTML."""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


async def check_and_send_digest(context: ContextTypes.DEFAULT_TYPE):
    """Проверить источники и отправить дайджест если есть изменения."""
    print(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Проверка стажировок...")
    
    try:
        # Собираем данные в отдельном потоке (т.к. Playwright синхронный)
        loop = asyncio.get_event_loop()
        internships = await loop.run_in_executor(None, collect_all_internships)
        
        if not internships:
            print("⚠️ Не удалось получить данные")
            return
        
        # Сохраняем в БД и получаем изменения
        changes = await loop.run_in_executor(None, upsert_and_get_changes, DB_PATH, internships)
        new_list = [c.internship for c in changes if c.is_new]
        updated_list = [c.internship for c in changes if not c.is_new]
        
        if changes:
            # Есть изменения - отправляем дайджест
            text = build_digest_message(new_list, updated_list)
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=text,
                parse_mode='HTML'
            )
            print(f"✅ Дайджест отправлен: {len(new_list)} новых, {len(updated_list)} обновлений")
        else:
            print("ℹ️ Изменений нет")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")


async def send_digest_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для принудительной отправки дайджеста."""
    await update.message.reply_text("🔄 Проверяю источники...")
    
    try:
        loop = asyncio.get_event_loop()
        internships = await loop.run_in_executor(None, collect_all_internships)
        
        if not internships:
            await update.message.reply_text("⚠️ Не удалось получить данные")
            return
        
        changes = await loop.run_in_executor(None, upsert_and_get_changes, DB_PATH, internships)
        new_list = [c.internship for c in changes if c.is_new]
        updated_list = [c.internship for c in changes if not c.is_new]
        
        if changes:
            text = build_digest_message(new_list, updated_list)
            await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
            await update.message.reply_text(
                f"✅ Дайджест отправлен в канал!\n"
                f"🆕 Новых: {len(new_list)}\n"
                f"🔄 Обновлений: {len(updated_list)}"
            )
        else:
            total = await loop.run_in_executor(None, get_internships_count, DB_PATH)
            text = build_no_changes_message(total)
            await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
            await update.message.reply_text("✅ Сводка отправлена (изменений нет)")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def show_open_internships(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать открытые стажировки."""
    internships = get_open_internships()
    
    if not internships:
        await update.message.reply_text(
            "😔 Сейчас нет открытых стажировок.\n"
            "Используйте /stats для статистики."
        )
        return
    
    message_parts = [f"🆕 <b>Открытые стажировки ({len(internships)}):</b>\n"]
    
    for company, title, status, url in internships:
        block = f"\n🏢 <b>{escape_html(company)}</b> — {escape_html(title)}"
        if status:
            block += f"\n🔓 {escape_html(status)}"
        block += f'\n🔗 <a href="{escape_html(url)}">Ссылка</a>\n'
        message_parts.append(block)
    
    full_message = "".join(message_parts)
    
    if len(full_message) > 4000:
        chunks = []
        current = message_parts[0]
        for part in message_parts[1:]:
            if len(current) + len(part) < 4000:
                current += part
            else:
                chunks.append(current)
                current = part
        if current:
            chunks.append(current)
        
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode='HTML', disable_web_page_preview=True)
    else:
        await update.message.reply_text(full_message, parse_mode='HTML', disable_web_page_preview=True)


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику."""
    stats = get_stats()
    
    if not stats:
        await update.message.reply_text("📭 База данных пуста")
        return
    
    message = f"""
📊 <b>Статистика:</b>

📚 Всего стажировок: <b>{stats['total']}</b>
🟢 Открыт набор: <b>{stats['open']}</b>
🔴 Набор закрыт: <b>{stats['total'] - stats['open']}</b>
🏢 Компаний: <b>{stats['companies']}</b>

⏰ Автопроверка: каждые {CHECK_INTERVAL_HOURS} часа
"""
    
    await update.message.reply_text(message, parse_mode='HTML')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие."""
    text = f"""
👋 <b>Привет! Бот для отслеживания стажировок.</b>

🤖 <b>Автоматический режим:</b>
Каждые {CHECK_INTERVAL_HOURS} часа бот проверяет источники и отправляет дайджест в канал при появлении новых стажировок.

📋 <b>Команды:</b>

/check - проверить сейчас и отправить дайджест
/internships - показать открытые стажировки
/stats - статистика

Бот работает 24/7! ⚡
"""
    await update.message.reply_text(text, parse_mode='HTML')


async def post_init(application: Application):
    """Действия после инициализации бота."""
    # Настраиваем периодическую проверку каждые 4 часа
    job_queue = application.job_queue
    
    # Запускаем сразу при старте
    await check_and_send_digest(application)
    
    # И потом каждые 4 часа
    job_queue.run_repeating(
        check_and_send_digest,
        interval=CHECK_INTERVAL_HOURS * 3600,  # в секундах
        first=CHECK_INTERVAL_HOURS * 3600
    )
    
    print(f"✅ Автопроверка настроена: каждые {CHECK_INTERVAL_HOURS} часа")


async def main():
    """Запуск бота."""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Ошибка: установите TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env")
        return
    
    print("🤖 Запуск бота с автоматической проверкой...")
    print(f"📊 База данных: {DB_PATH}")
    print(f"📢 Канал: {CHAT_ID}")
    print(f"⏰ Интервал проверки: каждые {CHECK_INTERVAL_HOURS} часа\n")
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("check", send_digest_now))
    app.add_handler(CommandHandler("internships", show_open_internships))
    app.add_handler(CommandHandler("stats", show_stats))
    
    # Запускаем
    await app.initialize()
    await post_init(app)
    await app.start()
    await app.updater.start_polling()
    
    print("✅ Бот запущен и работает!")
    print("\nДоступные команды:")
    print("  /start - информация")
    print("  /check - проверить сейчас")
    print("  /internships - открытые стажировки")
    print("  /stats - статистика\n")
    
    # Ждем
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")