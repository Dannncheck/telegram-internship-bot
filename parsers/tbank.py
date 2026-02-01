
"""
Парсер стажировок T-Bank (Тинькофф): Playwright.
Страница: https://education.tbank.ru/start/
Динамический контент.
"""
from parsers.base import Internship


def parse_tbank(url: str) -> list[Internship]:
    """
    Парсит страницу стажировок T-Bank через Playwright.
    Ищет карточки с направлениями стажировок.
    """
    from playwright.sync_api import sync_playwright
    from config import PLAYWRIGHT_HEADLESS, PLAYWRIGHT_TIMEOUT_MS

    company = "T-Bank"
    result: list[Internship] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
        try:
            page = browser.new_page()
            page.set_default_timeout(PLAYWRIGHT_TIMEOUT_MS)
            page.goto(url, wait_until="networkidle")
            
            # Ждем загрузки контента
            page.wait_for_timeout(2000)

            # Ищем все ссылки которые ведут на /start/* (это и есть стажировки)
            # Исключаем ссылки на соцсети, общие страницы и т.д.
            links = page.query_selector_all('a[href*="/start/"]')
            
            seen_urls = set()
            
            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    
                    # Пропускаем если это не стажировка
                    if not href or href == "/start/" or href == "/start":
                        continue
                    
                    # Формируем полный URL
                    if href.startswith("http"):
                        full_url = href
                    elif href.startswith("/"):
                        full_url = f"https://education.tbank.ru{href}"
                    else:
                        continue
                    
                    # Избегаем дубликатов
                    if full_url in seen_urls:
                        continue
                    
                    # Получаем заголовок (название стажировки)
                    # Обычно это h4 внутри ссылки или текст самой ссылки
                    title_el = link.query_selector("h4") or link.query_selector("h3") or link
                    title = (title_el.inner_text() or "").strip()
                    
                    if not title or len(title) < 3:
                        continue
                    
                    # Проверяем есть ли текст "Набор открыт" рядом с этой карточкой
                    # Ищем в родительском блоке
                    parent = link.evaluate("el => el.closest('div, section, article')")
                    status = ""
                    
                    # Проверяем текст перед ссылкой в том же блоке
                    try:
                        # Получаем весь текст родительского блока
                        parent_el = link.evaluate("el => el.parentElement")
                        if parent_el:
                            parent_text = page.evaluate("el => el.textContent", parent_el)
                            if "Набор открыт" in parent_text:
                                status = "Набор открыт"
                            elif "Набор закрыт" in parent_text:
                                status = "Набор закрыт"
                    except:
                        pass
                    
                    seen_urls.add(full_url)
                    result.append(
                        Internship(
                            company=company,
                            title=title,
                            url=full_url,
                            status=status
                        )
                    )
                    
                except Exception as e:
                    continue

        finally:
            browser.close()

    # Удаляем дубликаты по title
    unique_result = []
    seen_titles = set()
    for item in result:
        if item.title not in seen_titles:
            seen_titles.add(item.title)
            unique_result.append(item)

    if not unique_result:
        # Если ничего не нашли, добавляем заглушку
        unique_result.append(
            Internship(
                company=company,
                title="Т-Старт",
                url=url,
                status="Проверьте на сайте"
            )
        )
    
    return unique_result