from typing import List
from backend.db.db import init_db, save_message as _save, get_history as _get_history


# Initialize DB on import (idempotent)
init_db()


def save_message(role: str, text: str, created_at: str = None):
    _save(role=role, text=text, created_at=created_at)


def get_history(limit: int = 100):
    rows = _get_history(limit=limit)
    return rows
