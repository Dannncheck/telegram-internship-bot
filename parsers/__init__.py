"""
Регистрация и запуск всех парсеров источников стажировок.
"""
from parsers.base import Internship
from parsers.sber import parse_sber
from parsers.tbank import parse_tbank
from parsers.vk import parse_vk
from parsers.wildberries import parse_wildberries
from parsers.yandex import parse_yandex

# URL источников (строго по ТЗ): (название, URL, функция парсинга)
SOURCES = [
    ("T-Bank", "https://education.tbank.ru/start/", parse_tbank),
    ("Сбер", "https://sberstudent.ru/internship/", parse_sber),
    ("Wildberries Tech", "https://tech.wildberries.ru/courses?status_id=2&status_id=5", parse_wildberries),
    ("Яндекс", "https://yandex.ru/yaintern/internship", parse_yandex),
    ("VK", "https://internship.vk.company/vacancy", parse_vk),
]


def collect_all_internships() -> list[Internship]:
    """Запустить все парсеры и собрать объединённый список стажировок."""
    result: list[Internship] = []
    for company, url, parse_fn in SOURCES:
        try:
            items = parse_fn(url)
            result.extend(items)
        except Exception as e:
            # Логируем и продолжаем со следующими источниками
            import sys
            print(f"[{company}] Ошибка парсинга: {e}", file=sys.stderr)
    return result
