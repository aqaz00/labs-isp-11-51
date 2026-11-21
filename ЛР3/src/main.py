"""Точка входа: календарь событий."""
from pathlib import Path

from ui import run

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "events.json"

if __name__ == "__main__":
    run(DATA_FILE)
