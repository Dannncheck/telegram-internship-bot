# Дайджест стажировок в Telegram

Бот один раз в день проверяет страницы стажировок крупных компаний и отправляет в Telegram одно сообщение с новыми стажировками или обновлениями статуса.

## Стек

- Python 3.11
- Playwright (динамические страницы)
- requests + BeautifulSoup (где возможно)
- SQLite
- python-telegram-bot
- Markdown/HTML для сообщений

## Источники

1. **T-Bank** — https://education.tbank.ru/start/ (Playwright)
2. **Сбер** — https://sberstudent.ru/internship/ (requests + BeautifulSoup)
3. **Wildberries Tech** — https://tech.wildberries.ru/courses?status_id=2&status_id=5 (Playwright)
4. **Яндекс** — https://yandex.ru/yaintern/internship (Playwright)
5. **VK** — https://internship.vk.company/vacancy (Playwright)

## Установка

Требуется **Python 3.11+**. Если обновили Python — пересоздайте venv:

```bash
# Если был старый venv (например, под Python 3.9) — удалите его
rm -rf .venv

python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
# Отредактируйте .env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

- **TELEGRAM_BOT_TOKEN** — токен от [@BotFather](https://t.me/BotFather).
- **TELEGRAM_CHAT_ID** — ID чата или канала:
  - Личные сообщения: числовой ID (узнать можно у [@userinfobot](https://t.me/userinfobot)).
  - Канал: `@channel_username` или числовой ID вида `-100xxxxxxxxxx` (бот должен быть админом с правом публикации).

## Запуск локально

Один прогон (проверить источники, при изменениях отправить дайджест):

```bash
python main.py
```

**Получить сводку в любой момент** (даже если изменений нет):

```bash
python main.py --send
```

Бот проверит источники, обновит базу и **всегда** отправит сообщение: либо дайджест изменений, либо краткую сводку «изменений нет, всего отслеживается N стажировок».

## Запуск по cron (раз в день)

Пример — каждый день в 9:00 по локальному времени:

```bash
crontab -e
```

Добавьте строку (подставьте свой путь к проекту и venv):

```cron
0 9 * * * /path/to/internship/.venv/bin/python /path/to/internship/main.py >> /path/to/internship/cron.log 2>&1
```

Или через обёртку-скрипт:

```bash
#!/bin/bash
cd /path/to/internship
source .venv/bin/activate
python main.py >> cron.log 2>&1
```

И в cron:

```cron
0 9 * * * /path/to/internship/run.sh
```

## Запуск через GitHub Actions (раз в день)

1. В репозитории: **Settings → Secrets and variables → Actions**.
2. Добавьте секреты:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Создайте файл `.github/workflows/digest.yml`:

```yaml
name: Internship digest

on:
  schedule:
    - cron: '0 6 * * *'   # 06:00 UTC каждый день (9:00 МСК)
  workflow_dispatch:      # ручной запуск

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium --with-deps

      - name: Run digest
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python main.py
```

После push workflow будет запускаться по расписанию и при ручном запуске.

## Добавление нового источника

1. **Новый файл парсера** в `parsers/`, например `parsers/company.py`:

```python
from parsers.base import Internship

def parse_company(url: str) -> list[Internship]:
    # requests + BeautifulSoup или Playwright
    result = []
    # ... парсинг ...
    result.append(Internship(company="Компания", title="...", url="...", status="..."))
    return result
```

2. **Регистрация** в `parsers/__init__.py`:

- Импорт: `from parsers.company import parse_company`
- В список `SOURCES` добавить: `("Компания", "https://...", parse_company)`

После этого новый источник будет участвовать в общем прогоне и дайджесте.

## Структура проекта

```
main.py           # Точка входа
config.py         # Настройки из .env
db.py             # SQLite: схема, upsert, определение изменений
telegram_bot.py   # Формирование и отправка дайджеста в Telegram
parsers/
  __init__.py     # Регистрация источников и collect_all_internships()
  base.py         # Internship, контракт парсера
  tbank.py        # T-Bank (Playwright)
  sber.py         # Сбер (requests + BeautifulSoup)
  wildberries.py  # Wildberries Tech (Playwright)
  yandex.py       # Яндекс (Playwright)
  vk.py           # VK (Playwright)
.env.example
requirements.txt
README.md
```

## Логика работы

- Для каждого источника вызывается своя функция парсинга.
- Все стажировки сохраняются в SQLite с уникальным ключом `company|title`.
- При каждом запуске определяются **новые** стажировки и те, у которых **изменился статус**.
- Если есть такие изменения — в Telegram отправляется **одно** сообщение-дайджест; если нет — ничего не отправляется.
