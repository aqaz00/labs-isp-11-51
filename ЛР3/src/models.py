"""Модель данных: одно событие календаря."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Event:
    """Контейнер данных одного события (без логики и наследования)."""

    day: date
    title: str
    note: str = ""

    def to_dict(self) -> dict:
        """Превращает событие в словарь для сохранения в JSON."""
        return {"date": self.day.isoformat(), "title": self.title, "note": self.note}

    @staticmethod
    def from_dict(data: dict) -> "Event":
        """Создаёт событие из словаря; при некорректных данных бросает ValueError."""
        if not isinstance(data, dict):
            raise ValueError("запись не является объектом")
        try:
            day = date.fromisoformat(str(data["date"]))
            title = str(data["title"]).strip()
        except KeyError as err:
            raise ValueError(f"нет поля {err}") from None
        except ValueError:
            raise ValueError("неверная дата") from None
        if not title:
            raise ValueError("пустое название события")
        return Event(day, title, str(data.get("note", "")))
