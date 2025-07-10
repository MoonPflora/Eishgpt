import sqlite3
import requests
from datetime import datetime
import os
import uuid
from dotenv import load_dotenv

# Load .env file from project root or specify your path here
load_dotenv("env/.env")

FASTPAY_STORE_ID = os.getenv("FASTPAY_STORE_ID", "").strip()
FASTPAY_STORE_PASSWORD = os.getenv("FASTPAY_STORE_PASSWORD", "").strip()
FASTPAY_API_URL = "https://qr.fast-pay.iq/api/v1/public/vending/qr"  # Production endpoint

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "user_data", "payments.db")

def init_payment_db():
    """Initialize the payments database and table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            plan_days INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def generate_order_id(user_id: int, plan_days: int) -> str:
    """
    Generate order_id encoding user_id, plan_days, and current UTC timestamp.
    Format: {user_id}_{plan_days}_{YYYYMMDDTHHMMSS}
    """
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    return f"{user_id}_{plan_days}_{timestamp}"

def parse_order_id(order_id: str):
    """
    Parse order_id string back into components.
    Returns tuple (user_id:int, plan_days:int, timestamp:datetime) or raises ValueError.
    """
    try:
        parts = order_id.split("_")
        user_id = int(parts[0])
        plan_days = int(parts[1])
        timestamp = datetime.strptime(parts[2], "%Y%m%dT%H%M%S")
        return user_id, plan_days, timestamp
    except Exception as e:
        raise ValueError(f"Invalid order_id format: {order_id}") from e

def create_payment_order(user_id: int, plan_days: int, amount: int) -> str:
    """
    Create a payment order record in DB and request QR code URL from FastPay.
    Returns the QR code URL string.
    Raises Exception on failure.
    """
    if not FASTPAY_STORE_ID or not FASTPAY_STORE_PASSWORD:
        raise Exception("FastPay credentials are not set in environment variables.")

    order_id = generate_order_id(user_id, plan_days)
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Save the order to DB with 'pending' status
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO payments (order_id, user_id, plan_days, amount, created_at) VALUES (?, ?, ?, ?, ?)",
        (order_id, user_id, plan_days, amount, created_at)
    )
    conn.commit()
    conn.close()

    payload = {
        "storeId": FASTPAY_STORE_ID,
        "storePassword": FASTPAY_STORE_PASSWORD,
        "orderID": order_id,
        "billAmount": amount,
        "currency": "IQD"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.post(FASTPAY_API_URL, json=payload, headers=headers, timeout=15)

    if response.status_code != 200:
        raise Exception(f"HTTP error {response.status_code} from FastPay API: {response.text}")

    data = response.json()

    if data.get("code") != 200:
        raise Exception(f"FastPay API error: {data.get('message') or data.get('messages')}")

    # data['data'] should contain the QR code URL string
    qr_url = data.get("data")
    if not qr_url:
        raise Exception("FastPay API response missing QR code URL")

    return qr_url

def update_payment_status(order_id: str, new_status: str):
    """
    Update the payment status in the database.
    Typically called upon receiving IPN webhook.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE payments SET status = ? WHERE order_id = ?", (new_status, order_id))
    conn.commit()
    conn.close()
def is_premium(user_id):
    """Simple premium check that won't break existing functionality"""
    try:
        conn = sqlite3.connect("user_data/premium_users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM premium_users WHERE user_id = ?", (user_id,))
        return bool(cursor.fetchone())
    except:
        return False
    """Check if user has an active premium subscription"""
    try:
        conn = sqlite3.connect("user_data/premium_users.db")
        c = conn.cursor()
        
        # First check if user exists in premium database
        c.execute("SELECT end_date FROM premium_users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return False
            
        # Check if subscription is still valid
        end_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        current_time = datetime.now()
        
        conn.close()
        return current_time < end_date
        
    except Exception as e:
        print(f"[Premium Check Error] User ID: {user_id} - {str(e)}")
        return False
    try:
        conn = sqlite3.connect(PREMIUM_DB_PATH)
        c = conn.cursor()
        c.execute("SELECT end_date FROM premium_users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()

        if row:
            end_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            return datetime.utcnow() < end_date
        return False
    except Exception as e:
        print(f"[is_premium ERROR] {e}")
        return False
    try:
        conn = sqlite3.connect(PREMIUM_DB_PATH)
        c = conn.cursor()
        c.execute("SELECT end_date FROM premium_users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()

        if row:
            end_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            return datetime.utcnow() < end_date
        return False
    except Exception as e:
        print(f"[is_premium ERROR] {e}")
        return False

if __name__ == "__main__":
    init_payment_db()
    print("✅ payments.db and payments table created.")

    # Example test - will fail without valid credentials
    try:
        test_user_id = 123456789
        test_plan_days = 30
        test_amount = 2000

        print("🚀 Creating test payment order (will fail without real credentials)...")
        qr_url = create_payment_order(test_user_id, test_plan_days, test_amount)
        print(f"✅ QR code URL: {qr_url}")

        # Example parsing order_id:
        user_id, plan_days, ts = parse_order_id(generate_order_id(test_user_id, test_plan_days))
        print(f"Parsed order_id -> user_id: {user_id}, plan_days: {plan_days}, timestamp: {ts}")

    except Exception as e:
        print(f"❌ Failed to create payment order: {e}")
