import sqlite3
from datetime import datetime, timedelta

def add_premium_users(data_str):
    """
    Accepts a string like: '5703392732.30/123456789.60'
    and adds or updates entries in the premium_users database.
    """
    entries = data_str.split("/")
    conn = sqlite3.connect("user_data/premium_users.db")
    cursor = conn.cursor()

    now = datetime.now()
    count = 0

    for entry in entries:
        try:
            user_id_str, days_str = entry.split(".")
            user_id = int(user_id_str.strip())
            days = int(days_str.strip())

            end_date = now + timedelta(days=days)
            formatted_end_date = end_date.strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT OR REPLACE INTO premium_users (user_id, end_date)
                VALUES (?, ?)
            """, (user_id, formatted_end_date))

            count += 1
        except Exception as e:
            print(f"⚠️ Failed to add entry '{entry}': {e}")
            continue

    conn.commit()
    conn.close()
    return f"{count} بەکارهێنەر بەسەرکەوتوویی زیادکرا."
