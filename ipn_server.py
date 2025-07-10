from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime, timedelta
import os
import requests
from handlers.payment_handler import parse_order_id

app = FastAPI()

# === Telegram Bot Info (from .env) ===
from dotenv import load_dotenv
load_dotenv("env/.env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise Exception("❌ BOT_TOKEN missing from .env")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# === FastPay IPN Payload ===
class FastPayIPN(BaseModel):
    merchant_order_id: str
    gw_transaction_id: str
    received_amount: str
    currency: str
    status: str
    customer_name: str | None = None
    customer_mobile_number: str | None = None
    received_at: str | None = None
    at: str | None = None

@app.post("/fastpay/ipn")
async def fastpay_ipn(ipn: FastPayIPN):
    if ipn.status.lower() != "success":
        raise HTTPException(status_code=400, detail="❌ Payment not successful")

    try:
        user_id, plan_days, _ = parse_order_id(ipn.merchant_order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="❌ Invalid order_id format")

    try:
        # === Mark payment as paid ===
        conn = sqlite3.connect("user_data/payments.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE payments SET status = 'paid' WHERE order_id = ?", (ipn.merchant_order_id,))
        conn.commit()

        # === Add or update user in premium_users.db ===
        now = datetime.utcnow()
        end_date = now + timedelta(days=plan_days)
        end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")

        conn2 = sqlite3.connect("user_data/premium_users.db")
        cur2 = conn2.cursor()
        cur2.execute("""
            CREATE TABLE IF NOT EXISTS premium_users (
                user_id INTEGER PRIMARY KEY,
                end_date TEXT NOT NULL
            )
        """)
        cur2.execute("""
            INSERT INTO premium_users (user_id, end_date)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET end_date = excluded.end_date
        """, (user_id, end_date_str))
        conn2.commit()
        conn2.close()

        # === Optional Cleanup ===
        cursor.execute("DELETE FROM payments WHERE order_id = ?", (ipn.merchant_order_id,))
        conn.commit()
        conn.close()

        # === Send Telegram confirmation ===
        message = (
            f"✅ پارەدان سەرکەوتوو بوو!\n"
            f"👤 ناسنامە: <code>{user_id}</code>\n"
            f"🗓 بەشداربوونەکەت بۆ {plan_days} ڕۆژە.\n"
            f"🔒 بەسەر دەچێت لە: <b>{end_date_str.split()[0]}</b>"
        )
        payload = {
            "chat_id": user_id,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(TELEGRAM_API, json=payload)

        return {"message": "✅ IPN processed and subscription activated."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Server error: {e}")
