import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "user_data/free_user_id.db"

def init_free_user_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS free_user_search (
            user_id INTEGER PRIMARY KEY,
            last_search TEXT
        )
    """)
    conn.commit()
    conn.close()

def can_free_user_search(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT last_search FROM free_user_search WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    now = datetime.now()
    if row:
        last_search = datetime.fromisoformat(row[0])
        if now < last_search + timedelta(hours=48):
            conn.close()
            return False
    cursor.execute(
        "REPLACE INTO free_user_search (user_id, last_search) VALUES (?, ?)",
        (user_id, now.isoformat()),
    )
    conn.commit()
    conn.close()
    return True
