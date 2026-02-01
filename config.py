"""
Настройки приложения из переменных окружения.
Требуется Python 3.11+.
"""
import os
from pathlib import Path

# Загрузка .env при наличии python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


# Telegram
TELEGRAM_BOT_TOKEN: str | None = _env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str | None = _env("TELEGRAM_CHAT_ID")  # ID чата или @channel_username

# База данных
BASE_DIR = Path(__file__).resolve().parent
DB_PATH: Path = Path(_env("DB_PATH") or str(BASE_DIR / "internships.db"))

# Playwright
PLAYWRIGHT_HEADLESS: bool = (_env("PLAYWRIGHT_HEADLESS", "true").lower() in ("1", "true", "yes"))
PLAYWRIGHT_TIMEOUT_MS: int = int(_env("PLAYWRIGHT_TIMEOUT_MS", "15000"))

# Requests
REQUESTS_TIMEOUT_SEC: int = int(_env("REQUESTS_TIMEOUT_SEC", "15"))
