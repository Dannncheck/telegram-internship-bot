
"""
Парсер стажировок Сбера: requests + BeautifulSoup.
Страница: https://sberstudent.ru/internship/
Умное определение статусов - множество формулировок.
"""
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from parsers.base import Internship


def smart_status_detection(text: str) -> str:
    """
    Умное определение статуса стажировки по тексту.
    Возвращает: "Открыт набор", "Набор закрыт", "Скоро откроется", или пустую строку.
    """
    text_lower = text.lower()
    
    # Признаки ОТКРЫТОГО набора
    open_patterns = [
        r'набор\s+открыт',
        r'открыт\s+набор',
        r'прием\s+заявок',
        r'приём\s+заявок',
        r'идет\s+набор',
        r'идёт\s+набор',
        r'принимаем\s+заявки',
        r'подать\s+заявку',
        r'registration\s+open',
        r'applications\s+open',
        r'recruiting',
        r'apply\s+now',
    ]
    
    for pattern in open_patterns:
        if re.search(pattern, text_lower):
            return "Открыт набор"
    
    # Признаки СКОРО
    soon_patterns = [
        r'скоро',
        r'ближайшее\s+время',
        r'весна\s+\d{4}',
        r'лето\s+\d{4}',
        r'осень\s+\d{4}',
        r'зима\s+\d{4}',
        r'coming\s+soon',
        r'opens\s+soon',
    ]
    
    for pattern in soon_patterns:
        if re.search(pattern, text_lower):
            return "Скоро откроется"
    
    # Признаки ЗАКРЫТОГО набора
    closed_patterns = [
        r'набор\s+закрыт',
        r'закрыт\s+набор',
        r'прием\s+завершен',
        r'приём\s+завершен',
        r'завершен',
        r'applications\s+closed',
        r'closed',
    ]
    
    for pattern in closed_patterns:
        if re.search(pattern, text_lower):
            return "Набор закрыт"
    
    return ""


def parse_sber(url: str) -> list[Internship]:
    """
    Парсит страницу стажировок Сбера с умным определением статусов.
    """
    from config import REQUESTS_TIMEOUT_SEC

    try:
        resp = requests.get(url, timeout=REQUESTS_TIMEOUT_SEC)
        resp.raise_for_status()
    except Exception:
        return [Internship(
            company="Сбер",
            title="Стажировки в Сбере",
            url=url,
            status="Ошибка загрузки"
        )]

    soup = BeautifulSoup(resp.text, "html.parser")
    company = "Сбер"
    base_url = "https://sberstudent.ru"
    apply_url = "https://sberstudent.fut.ru/"
    
    result: list[Internship] = []
    seen_titles: set[str] = set()
    
    # Ищем все карточки/блоки с направлениями
    # На сайте Сбера каждая стажировка обычно в отдельном блоке с заголовком h3-h5
    
    # Способ 1: Найти все заголовки стажировок
    for heading in soup.find_all(['h3', 'h4', 'h5']):
        title = heading.get_text(strip=True)
        
        # Фильтры - пропускаем служебные заголовки
        if not title or len(title) < 3:
            continue
        
        skip_words = [
            'стажировк', 'что тебя ждет', 'часто задаваемые', 
            'проверь статус', 'познакомься', 'будь в курсе',
            'все этапы', 'готов получить', 'сбер',
        ]
        
        if any(word in title.lower() for word in skip_words):
            continue
        
        if title in seen_titles:
            continue
        
        # Получаем родительский блок
        parent = heading.find_parent(['div', 'section', 'article'])
        if not parent:
            continue
        
        # Проверяем статус в родительском блоке
        block_text = parent.get_text()
        status = smart_status_detection(block_text)
        
        # Ищем ссылку
        link_el = parent.find('a', href=True)
        link = urljoin(base_url, link_el['href']) if link_el else apply_url
        
        seen_titles.add(title)
        result.append(
            Internship(
                company=company,
                title=title,
                url=link,
                status=status or "Уточните на сайте"
            )
        )
    
    # Способ 2: Если ничего не нашли - ищем по всему тексту статусы
    if not result:
        # Проверяем общий статус набора на странице
        page_text = soup.get_text()
        general_status = smart_status_detection(page_text)
        
        result.append(
            Internship(
                company=company,
                title="Стажировки в Сбере",
                url=url,
                status=general_status or "Проверьте на сайте"
            )
        )
    
    return result