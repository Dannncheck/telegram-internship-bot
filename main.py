"""
Точка входа: запуск парсеров, сравнение с БД, отправка дайджеста в Telegram.
По умолчанию сообщение отправляется только при изменениях.
С флагом --send сводка отправляется всегда (по запросу).
"""
import argparse
import sys

import config
from db import get_internships_count, upsert_and_get_changes
from parsers import collect_all_internships
from telegram_bot import build_digest_message, build_no_changes_message, send_digest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Проверить источники стажировок и отправить дайджест в Telegram."
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Всегда отправить сводку (даже если изменений нет). Удобно для запроса по желанию.",
    )
    args = parser.parse_args()
    force_send = args.send

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("Задайте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env", file=sys.stderr)
        sys.exit(1)

    # Собрать стажировки со всех источников
    internships = collect_all_internships()
    if not internships:
        print("Не удалось получить ни одной стажировки.", file=sys.stderr)
        sys.exit(0)

    # Сохранить в БД и получить список изменений (новые + с изменённым статусом)
    changes = upsert_and_get_changes(config.DB_PATH, internships)
    new_list = [c.internship for c in changes if c.is_new]
    updated_list = [c.internship for c in changes if not c.is_new]

    if changes:
        text = build_digest_message(new_list, updated_list)
        send_digest(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, text)
        print(f"Отправлен дайджест: {len(new_list)} новых, {len(updated_list)} обновлений.")
    elif force_send:
        total = get_internships_count(config.DB_PATH)
        text = build_no_changes_message(total)
        send_digest(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, text)
        print("Отправлена сводка: изменений нет.")
    else:
        print("Изменений нет, сообщение не отправляется.")


if __name__ == "__main__":
    main()
