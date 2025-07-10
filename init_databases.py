# init_databases.py
import sqlite3
import os

# Create user_data folder if it doesn't exist
os.makedirs("user_data", exist_ok=True)

# Initialize premium_users.db
with sqlite3.connect("user_data/premium_users.db") as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS premium_users (
            telegram_id INTEGER PRIMARY KEY,
            subscription_end TEXT  -- Format: YYYY-MM-DD
        )
    """)
    print("✅ premium_users.db initialized")

# Initialize payments.db
with sqlite3.connect("user_data/payments.db") as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payment_sessions (
            telegram_id INTEGER PRIMARY KEY,
            order_id TEXT UNIQUE,      -- FastPay order_id (8-32 chars)
            bill_amount INTEGER,       -- Amount in IQD
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ payments.db initialized")

print("🎉 All databases ready!")