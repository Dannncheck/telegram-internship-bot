"""
Базовые типы и контракт для парсеров.
"""
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Internship:
    """Одна стажировка / программа."""
    company: str
    title: str
    url: str
    status: str  # "открыт набор" / "скоро" / "закрыт" / "" если неизвестно

    def unique_key(self) -> str:
        """Ключ для дедупликации: company + title."""
        return f"{self.company}|{self.title}"


class ParserProtocol(Protocol):
    """Контракт парсера: имя источника и функция парсинга."""

    @property
    def source_name(self) -> str:
        ...

    def parse(self) -> list[Internship]:
        ...
