"""Консольный интерфейс: ввод данных, вывод таблиц и главное меню."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import planner
import storage
from models import Event

DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d")
WEEKDAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
YES_ANSWERS = ("д", "да", "y", "yes")

MENU = """
===== Календарь событий =====
1. Показать все события
2. Добавить событие
3. События на дату
4. Ближайшие события
5. Найти по названию
6. Удалить событие
7. Удалить прошедшие события
0. Выход"""


# ---------- ввод данных с проверкой ----------

def parse_date(text: str) -> date:
    """Разбирает дату в формате ДД.ММ.ГГГГ или ГГГГ-ММ-ДД."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError("неверный формат даты")


def ask_text(prompt: str, allow_empty: bool = False) -> str:
    """Спрашивает строку, пока пользователь не введёт непустую."""
    while True:
        value = input(prompt).strip()
        if value or allow_empty:
            return value
        print("Ошибка: строка не должна быть пустой.")


def ask_int(prompt: str, min_value: int, max_value: int, default: int | None = None) -> int:
    """Спрашивает целое число в границах; пустой ввод даёт default (если задан)."""
    while True:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        try:
            value = int(raw)
        except ValueError:
            print("Ошибка: нужно ввести целое число.")
            continue
        if min_value <= value <= max_value:
            return value
        print(f"Ошибка: число должно быть от {min_value} до {max_value}.")


def ask_date(prompt: str, default: date | None = None) -> date:
    """Спрашивает дату; пустой ввод означает значение по умолчанию (если оно есть)."""
    while True:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        try:
            return parse_date(raw)
        except ValueError:
            print("Ошибка: введите дату как ДД.ММ.ГГГГ или ГГГГ-ММ-ДД.")


# ---------- вывод ----------

def format_day(day: date) -> str:
    """Дата вида «24.11.2026 (вт)»."""
    return f"{day.strftime('%d.%m.%Y')} ({WEEKDAYS[day.weekday()]})"


def print_table(rows: planner.Found) -> None:
    """Печатает таблицу из пар (индекс в общем списке, событие)."""
    if not rows:
        print("Событий нет.")
        return
    title_width = max(len("Событие"), *(len(e.title) for _, e in rows))
    print(f"{'№':>3}  {'Дата':<15}  {'Событие':<{title_width}}  Заметка")
    for index, e in rows:
        print(f"{index + 1:>3}  {format_day(e.day):<15}  {e.title:<{title_width}}  {e.note}")


def save(events: list[Event], path: Path) -> bool:
    """Сохраняет календарь; при ошибке печатает сообщение и возвращает False."""
    try:
        storage.save_events(path, events)
        return True
    except OSError as err:
        print(f"Ошибка: не удалось записать файл ({err}).")
        return False


# ---------- пункты меню ----------

def show_all(events: list[Event]) -> None:
    """Печатает все события, сгруппированные по датам."""
    if not events:
        print("Календарь пуст.")
        return
    today = date.today()
    for day, rows in planner.group_by_date(events).items():
        mark = "  [прошло]" if day < today else ""
        print(f"{format_day(day)}{mark}")
        for index, e in rows:
            note = f" — {e.note}" if e.note else ""
            print(f"  {index + 1:>3}. {e.title}{note}")


def add_command(events: list[Event], path: Path) -> None:
    day = ask_date("Дата (ДД.ММ.ГГГГ, Enter — сегодня): ", default=date.today())
    title = ask_text("Название события: ")
    note = ask_text("Заметка (можно пропустить): ", allow_empty=True)
    planner.add_event(events, Event(day, title, note))
    if save(events, path):
        print("Событие добавлено и сохранено.")
    else:
        print("Событие добавлено в память, но в файл не записано.")


def on_date_command(events: list[Event]) -> None:
    day = ask_date("Дата (Enter — сегодня): ", default=date.today())
    print_table(planner.find_on_date(events, day))


def upcoming_command(events: list[Event]) -> None:
    days = ask_int("На сколько дней вперёд смотреть (Enter — 7): ", 0, 365, default=7)
    print_table(planner.find_upcoming(events, date.today(), days))


def search_title_command(events: list[Event]) -> None:
    query = ask_text("Что искать в названии: ")
    print_table(planner.find_by_title(events, query))


def delete_command(events: list[Event], path: Path) -> None:
    if not events:
        print("Нет событий для удаления.")
        return
    show_all(events)
    number = ask_int("Номер для удаления (0 — отмена): ", 0, len(events))
    if number == 0:
        return
    answer = ask_text("Удалить это событие? (д/н): ").lower()
    if answer not in YES_ANSWERS:
        print("Удаление отменено.")
        return
    planner.delete_event(events, number - 1)
    if save(events, path):
        print("Событие удалено.")


def remove_past_command(events: list[Event], path: Path) -> None:
    count = planner.count_past(events, date.today())
    if count == 0:
        print("Прошедших событий нет.")
        return
    answer = ask_text(f"Удалить прошедшие события ({count} шт.)? (д/н): ").lower()
    if answer not in YES_ANSWERS:
        print("Удаление отменено.")
        return
    removed = planner.remove_past(events, date.today())
    if save(events, path):
        print(f"Удалено событий: {removed}.")


# ---------- главный цикл ----------

def run(path: Path) -> None:
    """Загружает данные, показывает меню и обрабатывает выбор пользователя."""
    events, warnings = storage.load_events(path)
    for warning in warnings:
        print(f"Внимание: {warning}")
    print(f"Загружено событий: {len(events)}")

    actions = {
        "1": lambda: show_all(events),
        "2": lambda: add_command(events, path),
        "3": lambda: on_date_command(events),
        "4": lambda: upcoming_command(events),
        "5": lambda: search_title_command(events),
        "6": lambda: delete_command(events, path),
        "7": lambda: remove_past_command(events, path),
    }

    try:
        while True:
            print(MENU)
            choice = input("Выберите пункт: ").strip()
            if choice == "0":
                break
            action = actions.get(choice)
            if action is None:
                print("Ошибка: нет такого пункта меню.")
                continue
            action()
    except (KeyboardInterrupt, EOFError):
        print()  # Ctrl+C / Ctrl+D тоже завершают работу штатно

    if save(events, path):
        print("Данные сохранены. До свидания!")
