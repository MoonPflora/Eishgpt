import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "premium_users.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS premium_users (
    user_id INTEGER PRIMARY KEY,
    end_date TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("✅ DB and table ready!")
