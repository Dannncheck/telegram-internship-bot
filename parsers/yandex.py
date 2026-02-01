

"""
Парсер стажировок Яндекса: Playwright.
Страница: https://yandex.ru/yaintern/internship
Умное определение статусов.
"""
from parsers.base import Internship
import re


def smart_status_detection(text: str) -> str:
    """Умное определение статуса."""
    text_lower = text.lower()
    
    open_patterns = [
        r'набор\s+открыт', r'открыт\s+набор', r'прием\s+заявок',
        r'приём\s+заявок', r'идет\s+набор', r'идёт\s+набор',
        r'принимаем\s+заявки', r'подать\s+заявку',
        r'registration\s+open', r'applications\s+open',
        r'recruiting', r'apply\s+now',
    ]
    
    for pattern in open_patterns:
        if re.search(pattern, text_lower):
            return "Открыт набор"
    
    soon_patterns = [
        r'скоро', r'ближайшее\s+время',
        r'весна\s+\d{4}', r'лето\s+\d{4}',
        r'coming\s+soon', r'opens\s+soon',
    ]
    
    for pattern in soon_patterns:
        if re.search(pattern, text_lower):
            return "Скоро откроется"
    
    closed_patterns = [
        r'набор\s+закрыт', r'закрыт\s+набор',
        r'прием\s+завершен', r'приём\s+завершен',
        r'applications\s+closed', r'closed',
    ]
    
    for pattern in closed_patterns:
        if re.search(pattern, text_lower):
            return "Набор закрыт"
    
    return ""


def parse_yandex(url: str) -> list[Internship]:
    """
    Парсит страницу стажировок Яндекса.
    """
    from playwright.sync_api import sync_playwright
    from config import PLAYWRIGHT_HEADLESS, PLAYWRIGHT_TIMEOUT_MS

    company = "Яндекс"
    result: list[Internship] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
        try:
            page = browser.new_page()
            page.set_default_timeout(PLAYWRIGHT_TIMEOUT_MS)
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(2000)

            # Ищем карточки или ссылки на стажировки
            cards = page.query_selector_all(
                'a[href*="yaintern"], a[href*="internship"], '
                '[class*="vacancy"], [class*="card"], [class*="program"]'
            )

            seen: set[str] = set()
            for card in cards:
                try:
                    # Получаем текст и ссылку
                    text = (card.inner_text() or "").strip()
                    href = card.get_attribute("href") or ""
                    
                    # Пропускаем если это не стажировка
                    if not text or len(text) < 3:
                        continue
                    
                    # Пропускаем навигационные элементы
                    if text in seen or text.lower() in ['главная', 'о компании', 'контакты']:
                        continue
                    
                    # Формируем URL
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        full_url = f"https://yandex.ru{href}"
                    else:
                        full_url = url
                    
                    # Получаем статус из родительского блока
                    parent_text = ""
                    try:
                        parent_text = page.evaluate(
                            "(el) => el.parentElement?.textContent || ''",
                            card
                        )
                    except:
                        pass
                    
                    status = smart_status_detection(text + " " + parent_text)
                    
                    seen.add(text)
                    result.append(
                        Internship(
                            company=company,
                            title=text,
                            url=full_url,
                            status=status or "Уточните на сайте"
                        )
                    )
                except Exception:
                    continue

        finally:
            browser.close()

    if not result:
        result.append(
            Internship(
                company=company,
                title="Стажировки Яндекс",
                url=url,
                status="Проверьте на сайте"
            )
        )
    
    return result
