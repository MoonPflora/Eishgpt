import os
import sqlite3

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
    print(f"Initialized database and table at {DB_PATH}")

if __name__ == "__main__":
    init_free_user_db()
