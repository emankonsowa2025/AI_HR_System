import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "asktech.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT
        )
        """
    )
    # table for storing user skills
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            skill TEXT NOT NULL,
            created_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_message(role: str, text: str, created_at: str = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO chats (role, message, created_at) VALUES (?, ?, ?)", (role, text, created_at))
    conn.commit()
    conn.close()


def get_history(limit: int = 100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, role, message, created_at FROM chats ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
