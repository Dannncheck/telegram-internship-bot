"""
Интерактивный Telegram бот для просмотра стажировок по команде.
Команды:
  /start - приветствие и список команд
  /internships или /стажировки - показать открытые стажировки
  /all - показать все стажировки (включая закрытые)
  /stats - статистика
"""
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import sqlite3
from pathlib import Path

load_dotenv()

# Настройки
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_PATH = Path(os.getenv("DB_PATH", "./internships.db"))


def get_open_internships():
    """Получить стажировки со статусом 'Открыт набор' или похожим."""
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ищем стажировки где в статусе есть слова о наборе
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


def get_all_internships():
    """Получить все стажировки."""
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT company, title, status, url 
        FROM internships 
        ORDER BY company, title
    """)
    results = cursor.fetchall()
    conn.close()
    return results


def get_stats():
    """Получить статистику по стажировкам."""
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
    return {
        'total': total,
        'open': open_count,
        'companies': companies
    }


def escape_html(text):
    """Экранировать HTML символы."""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    welcome_text = """
👋 <b>Привет! Я бот для отслеживания стажировок.</b>

📋 <b>Доступные команды:</b>

/internships или /стажировки - показать открытые стажировки
/all - показать все стажировки
/stats - статистика по базе данных

Бот автоматически проверяет источники и присылает обновления в канал!
"""
    await update.message.reply_text(welcome_text, parse_mode='HTML')


async def internships_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /internships - показать открытые стажировки."""
    internships = get_open_internships()
    
    if not internships:
        await update.message.reply_text(
            "😔 К сожалению, сейчас нет открытых стажировок.\n\n"
            "Используйте /all чтобы увидеть все стажировки."
        )
        return
    
    # Формируем сообщение
    message_parts = [f"🆕 <b>Открытые стажировки ({len(internships)}):</b>\n"]
    
    for company, title, status, url in internships:
        block = f"\n🏢 <b>{escape_html(company)}</b> — {escape_html(title)}"
        if status:
            block += f"\n🔓 {escape_html(status)}"
        block += f'\n🔗 <a href="{escape_html(url)}">Ссылка</a>\n'
        message_parts.append(block)
    
    full_message = "".join(message_parts)
    
    # Telegram ограничение 4096 символов
    if len(full_message) > 4000:
        # Разбиваем на части
        chunks = []
        current_chunk = message_parts[0]
        
        for part in message_parts[1:]:
            if len(current_chunk) + len(part) < 4000:
                current_chunk += part
            else:
                chunks.append(current_chunk)
                current_chunk = part
        
        if current_chunk:
            chunks.append(current_chunk)
        
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode='HTML', disable_web_page_preview=True)
    else:
        await update.message.reply_text(full_message, parse_mode='HTML', disable_web_page_preview=True)


async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /all - показать все стажировки."""
    internships = get_all_internships()
    
    if not internships:
        await update.message.reply_text("📭 База данных пуста. Запустите main.py для сбора данных.")
        return
    
    message_parts = [f"📋 <b>Все стажировки ({len(internships)}):</b>\n"]
    
    for company, title, status, url in internships:
        block = f"\n🏢 <b>{escape_html(company)}</b> — {escape_html(title)}"
        if status:
            block += f"\n📊 {escape_html(status)}"
        block += f'\n🔗 <a href="{escape_html(url)}">Ссылка</a>\n'
        message_parts.append(block)
    
    full_message = "".join(message_parts)
    
    # Разбиваем на части если слишком длинное
    if len(full_message) > 4000:
        chunks = []
        current_chunk = message_parts[0]
        
        for part in message_parts[1:]:
            if len(current_chunk) + len(part) < 4000:
                current_chunk += part
            else:
                chunks.append(current_chunk)
                current_chunk = part
        
        if current_chunk:
            chunks.append(current_chunk)
        
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode='HTML', disable_web_page_preview=True)
    else:
        await update.message.reply_text(full_message, parse_mode='HTML', disable_web_page_preview=True)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats - показать статистику."""
    stats = get_stats()
    
    if not stats:
        await update.message.reply_text("📭 База данных пуста.")
        return
    
    message = f"""
📊 <b>Статистика базы данных:</b>

📚 Всего стажировок: <b>{stats['total']}</b>
🟢 Открыт набор: <b>{stats['open']}</b>
🔴 Набор закрыт: <b>{stats['total'] - stats['open']}</b>
🏢 Компаний: <b>{stats['companies']}</b>
"""
    
    await update.message.reply_text(message, parse_mode='HTML')


async def main():
    """Запуск бота."""
    if not BOT_TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден в .env")
        return
    
    print("🤖 Запуск интерактивного бота...")
    print(f"📊 База данных: {DB_PATH}")
    print("✅ Бот готов к работе!\n")
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("internships", internships_command))
    app.add_handler(CommandHandler("all", all_command))
    app.add_handler(CommandHandler("stats", stats_command))
    
    # Запускаем бота
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    print("Доступные команды:")
    print("  /start - приветствие")
    print("  /internships - открытые стажировки")
    print("  /all - все стажировки")
    print("  /stats - статистика\n")
    
    # Ждем
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")