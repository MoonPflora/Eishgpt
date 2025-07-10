import os
from dotenv import load_dotenv
import requests

# Load bot token from env/.env
load_dotenv(dotenv_path="env/.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@KurdistanJobsCentral"

WELCOME_FILE = "welcome.txt"

def read_welcome_message():
    if not os.path.exists(WELCOME_FILE):
        print(f"❌ File {WELCOME_FILE} not found.")
        return None
    with open(WELCOME_FILE, "r", encoding="utf-8") as f:
        return f.read()

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("✅ Message sent successfully!")
    else:
        print(f"❌ Failed to send message. Status: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    message = read_welcome_message()
    if message:
        send_message(message)
