"""Операции над коллекцией событий: добавление, удаление, поиск, группировка."""
from __future__ import annotations

from datetime import date, timedelta

from models import Event

# Результаты поиска — пары (номер в общем списке, событие), чтобы номера
# в выдаче совпадали с номерами в полном списке.
Found = list[tuple[int, Event]]


def add_event(events: list[Event], event: Event) -> None:
    """Добавляет событие и сохраняет порядок по дате (сортировка устойчивая)."""
    events.append(event)
    events.sort(key=lambda e: e.day)


def delete_event(events: list[Event], index: int) -> Event:
    """Удаляет событие по индексу и возвращает его."""
    return events.pop(index)


def find_on_date(events: list[Event], day: date) -> Found:
    """События на конкретную дату."""
    return [(i, e) for i, e in enumerate(events) if e.day == day]


def find_upcoming(events: list[Event], today: date, days: int) -> Found:
    """События от сегодняшнего дня до today + days включительно."""
    last = today + timedelta(days=days)
    return [(i, e) for i, e in enumerate(events) if today <= e.day <= last]


def find_by_title(events: list[Event], query: str) -> Found:
    """События, в названии которых встречается подстрока (без учёта регистра)."""
    query = query.casefold()
    return [(i, e) for i, e in enumerate(events) if query in e.title.casefold()]


def group_by_date(events: list[Event]) -> dict[date, Found]:
    """Группирует события по датам: дата -> список пар (номер, событие)."""
    groups: dict[date, Found] = {}
    for i, e in enumerate(events):
        groups.setdefault(e.day, []).append((i, e))
    return groups


def count_past(events: list[Event], today: date) -> int:
    """Сколько событий уже прошло (дата раньше сегодняшней)."""
    return sum(1 for e in events if e.day < today)


def remove_past(events: list[Event], today: date) -> int:
    """Удаляет прошедшие события на месте и возвращает, сколько удалено."""
    before = len(events)
    events[:] = [e for e in events if e.day >= today]
    return before - len(events)
