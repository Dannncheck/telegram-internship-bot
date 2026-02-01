"""
Работа с SQLite: хранение стажировок и определение новых/изменённых.
"""
import sqlite3
from pathlib import Path
from typing import NamedTuple

from parsers.base import Internship


# Таблица: уникальный ключ (company|title), все поля, дата последнего обновления
SCHEMA = """
CREATE TABLE IF NOT EXISTS internships (
    id TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_internships_updated ON internships(updated_at);
"""


class Change(NamedTuple):
    """Изменение: новая запись или обновлённый статус."""
    internship: Internship
    is_new: bool  # True = новая, False = изменился статус


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Подключение к SQLite с включённым foreign_keys и row_factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    """Создать таблицы, если их нет."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


def get_internships_count(db_path: Path) -> int:
    """Вернуть количество стажировок в базе."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM internships").fetchone()
        return row[0] if row else 0


def _row_to_internship(row: sqlite3.Row) -> Internship:
    return Internship(
        company=row["company"],
        title=row["title"],
        url=row["url"],
        status=row["status"] or "",
    )


def upsert_and_get_changes(
    db_path: Path,
    internships: list[Internship],
) -> list[Change]:
    """
    Сохранить стажировки в БД. Вернуть список изменений:
    - новые стажировки (is_new=True);
    - стажировки с изменившимся статусом (is_new=False).
    """
    init_db(db_path)
    changes: list[Change] = []
    now = __import__("datetime").datetime.utcnow().isoformat() + "Z"

    with get_connection(db_path) as conn:
        for i in internships:
            uid = i.unique_key()
            row = conn.execute(
                "SELECT company, title, url, status FROM internships WHERE id = ?",
                (uid,),
            ).fetchone()

            if row is None:
                conn.execute(
                    "INSERT INTO internships (id, company, title, url, status, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (uid, i.company, i.title, i.url, i.status, now),
                )
                changes.append(Change(internship=i, is_new=True))
            else:
                prev = _row_to_internship(row)
                if prev.status != i.status:
                    conn.execute(
                        "UPDATE internships SET url = ?, status = ?, updated_at = ? WHERE id = ?",
                        (i.url, i.status, now, uid),
                    )
                    changes.append(Change(internship=i, is_new=False))

        conn.commit()

    return changes
