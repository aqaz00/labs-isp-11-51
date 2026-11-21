"""Работа с файлом: чтение и запись календаря в формате JSON."""
from __future__ import annotations

import json
import os
from pathlib import Path

from models import Event


def load_events(path: Path) -> tuple[list[Event], list[str]]:
    """Читает события из файла.

    Возвращает (список событий, список предупреждений). Если файла нет или он
    пустой — начинаем с пустого набора. Битый файл переименовывается в .bak,
    некорректные записи пропускаются.
    """
    if not path.exists():
        return [], []

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [], [f"не удалось прочитать файл {path.name}: {err}"]

    if not text.strip():
        return [], []

    try:
        raw = json.loads(text)
        if not isinstance(raw, list):
            raise ValueError("в файле ожидается список событий")
    except ValueError as err:  # JSONDecodeError наследуется от ValueError
        return [], [_backup_broken_file(path, err)]

    events: list[Event] = []
    warnings: list[str] = []
    for number, item in enumerate(raw, start=1):
        try:
            events.append(Event.from_dict(item))
        except ValueError as err:
            warnings.append(f"запись №{number} пропущена: {err}")
    events.sort(key=lambda e: e.day)
    return events, warnings


def _backup_broken_file(path: Path, reason: Exception) -> str:
    """Сохраняет копию битого файла рядом и возвращает текст предупреждения."""
    backup = path.with_suffix(".bak")
    try:
        os.replace(path, backup)
        return f"файл повреждён ({reason}); копия сохранена как {backup.name}, начинаем с пустого календаря"
    except OSError:
        return f"файл повреждён ({reason}); начинаем с пустого календаря"


def save_events(path: Path, events: list[Event]) -> None:
    """Записывает все события в файл. При ошибке ввода-вывода бросает OSError.

    Пишем во временный файл и подменяем им основной, чтобы сбой посреди записи
    не испортил старые данные.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    payload = [e.to_dict() for e in events]
    with open(tmp_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
