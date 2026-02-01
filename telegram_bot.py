"""
Отправка дайджеста в Telegram (личка или канал).
Формат: HTML (надёжнее Markdown в Telegram API).
"""
from __future__ import annotations

import asyncio
from telegram import Bot
from telegram.constants import ParseMode

from parsers.base import Internship


def _escape_html(s: str) -> str:
    """Экранировать символы для HTML в Telegram."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_digest_message(new: list[Internship], updated: list[Internship]) -> str:
    """
    Собрать одно сообщение-дайджест: сначала новые стажировки, потом обновления статуса.
    Формат HTML для parse_mode=HTML.
    """
    parts: list[str] = []

    if new:
        parts.append("🆕 <b>Новые стажировки:</b>\n")
        for i in new:
            status_line = f"🔓 {_escape_html(i.status)}" if i.status else ""
            block = f"🏢 {_escape_html(i.company)} — {_escape_html(i.title)}"
            if status_line:
                block += f"\n{status_line}"
            block += f'\n🔗 <a href="{_escape_html(i.url)}">{_escape_html(i.url)}</a>\n'
            parts.append(block)

    if updated:
        parts.append("🔄 <b>Обновление статуса:</b>\n")
        for i in updated:
            status_line = f"🔓 {_escape_html(i.status)}" if i.status else ""
            block = f"🏢 {_escape_html(i.company)} — {_escape_html(i.title)}"
            if status_line:
                block += f"\n{status_line}"
            block += f'\n🔗 <a href="{_escape_html(i.url)}">{_escape_html(i.url)}</a>\n'
            parts.append(block)

    return "\n".join(parts).strip()


def build_no_changes_message(total: int) -> str:
    """Текст сводки, когда изменений нет (для принудительной отправки)."""
    return f"📋 <b>Проверка выполнена.</b>\n\nИзменений нет. Всего отслеживается стажировок: <b>{total}</b>."


def send_digest(bot_token: str, chat_id: str, text: str) -> None:
    """
    Отправить сообщение в Telegram.
    
    Args:
        bot_token: токен Telegram бота
        chat_id: ID чата или канала (может быть числом или @username)
        text: текст сообщения в формате HTML
    """
    try:
        bot = Bot(token=bot_token)
        
        # Определяем, число ли chat_id или строка
        try:
            chat_id_int = int(chat_id)
        except ValueError:
            chat_id_int = chat_id
        
        # Используем asyncio для отправки сообщения
        asyncio.run(_send_message_async(bot, chat_id_int, text))
        
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        raise


async def _send_message_async(bot: Bot, chat_id: int | str, text: str) -> None:
    """Вспомогательная async-функция для отправки сообщения."""
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
    )