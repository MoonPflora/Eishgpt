import os
import sys
import socket
import sqlite3
import logging
import random
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv
from telebot import TeleBot, types

# Local imports
from user_data.free_user_db import init_free_user_db, can_free_user_search
from handlers.payment_handler import init_payment_db, is_premium
from handlers import payment_handler, job_submission
from handlers.admin_panel import register_admin_handlers
from user_search import JobSearcher
from session import user_states

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Prevent multiple instances
def is_already_running(port=8877):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return False
    except OSError:
        return True
    finally:
        s.close()

if is_already_running():
    logger.error("🚫 Bot already running! Only one instance is allowed.")
    sys.exit(1)

# Load environment
load_dotenv("env/.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN = os.getenv("ADMIN")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN missing in .env!")
    sys.exit(1)

try:
    ADMIN = int(ADMIN)
except (ValueError, TypeError):
    logger.error("❌ ADMIN must be a valid integer Telegram user ID in .env")
    sys.exit(1)

PERMANENT_ADMINS = {ADMIN}

# Initialize bot and components
bot = TeleBot(BOT_TOKEN, parse_mode="HTML")
admin_sessions = set()
searcher = JobSearcher()
ADMIN_CODE = "787898rawa"
user_search_states = {}
captcha_states = {}  # ✅ Captcha user state

# Initialize databases
init_free_user_db()
init_payment_db()

# Register handlers
register_admin_handlers(bot, admin_sessions)
job_submission.register(bot)

# Admin functions
def is_admin(user_id):
    return user_id in PERMANENT_ADMINS or user_id in admin_sessions

def admin_only(func):
    def wrapper(message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "❌ تۆ ئەدمین نییت.")
            return
        return func(message, *args, **kwargs)
    return wrapper

@bot.message_handler(func=lambda msg: msg.text == ADMIN_CODE)
def handle_admin_code(message):
    admin_sessions.add(message.from_user.id)
    logger.info(f"✅ Admin verified by code: {message.from_user.id}")
    bot.send_message(message.chat.id, "✅ چوونەژوورەوەی ئەدمین سەرکەوتوو بوو.")

# Search state management
class UserSearchState:
    def __init__(self):
        self.category = None
        self.location = None
        self.normalized_location = None
        self.time_filter = 7
        self.current_job_index = 0
        self.results = []

def get_user_state(user_id):
    if user_id not in user_search_states:
        user_search_states[user_id] = UserSearchState()
    return user_search_states[user_id]

# UI keyboards
def create_time_filter_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("🚨 ئەمشەو / 24کاتژمێر", callback_data="time_filter:0"),
        types.InlineKeyboardButton("٢ ڕۆژ", callback_data="time_filter:2")
    )
    keyboard.row(
        types.InlineKeyboardButton("٤ ڕۆژ", callback_data="time_filter:4"),
        types.InlineKeyboardButton("٧ ڕۆژ", callback_data="time_filter:7")
    )
    return keyboard

def create_location_keyboard():
    keyboard = []
    for loc_key, loc_data in searcher.locations.items():
        name = loc_data.get("kurdish")
        if isinstance(name, str) and name.strip():
            keyboard.append([types.InlineKeyboardButton(name, callback_data=f"location:{loc_key}")])
    keyboard.append([types.InlineKeyboardButton("هەموو شوێنەکان", callback_data="location:all")])
    return types.InlineKeyboardMarkup(keyboard)

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📤 ناردنی هەلی کار"))
    keyboard.add(types.KeyboardButton("🔍 گەڕان بۆ کار"))
    keyboard.add(types.KeyboardButton("💎 بەشداریکردن"))
    keyboard.add(types.KeyboardButton("💎 خەزنکردنی CV"))
    bot.send_message(
        message.chat.id,
        "سڵاو 👋، من سارام👩‍💼\n🌟 بەخێربێیت بۆ Kurdistan Jobs Central 🌟\nچۆن دەتوانم یارمەتیت بدەم؟ 😊",
        reply_markup=keyboard
    )

# 📤 Job submission with CAPTCHA
@bot.message_handler(func=lambda msg: msg.text == "📤 ناردنی هەلی کار")
def handle_send_job(message):
    user_id = message.chat.id
    captcha_code = random.randint(1000, 9999)
    captcha_states[user_id] = captcha_code
    bot.send_message(user_id, f"🛡 تکایە ئەم ژمارەیە بنووسە بۆ دڵنیا بوونت: <b>{captcha_code}</b>", parse_mode='HTML')

@bot.message_handler(func=lambda m: m.chat.id in captcha_states)
def verify_captcha(m):
    user_id = m.chat.id
    if m.text.strip() == str(captcha_states[user_id]):
        del captcha_states[user_id]
        bot.send_message(user_id, "✅ سەرکاوتوو بوویت، بنوسە cancel بۆ پاشگەزبوونەوە:")
        job_submission.start_submission(bot, m)
    else:
        bot.send_message(user_id, "❌ ژمارە هەڵە بوو. تکایە دووبارە هەوڵ بدە.")

# CV placeholder
@bot.message_handler(func=lambda msg: msg.text == "💎 خەزنکردنی CV")
def handle_save_cv(message):
    bot.send_message(message.chat.id, "🛠 ئەم کارە لەم ساتەدا بەردەست نییە. بەم زوانە دێتەوە!")

@bot.callback_query_handler(func=lambda call: call.data == "auto_apply")
def handle_auto_apply(call):
    bot.answer_callback_query(call.id, "🛠 ئەم کارە لەم ساتەدا بەردەست نییە.", show_alert=True)

# 🔍 Job search
@bot.message_handler(func=lambda msg: msg.text == "🔍 گەڕان بۆ کار")
def start_search(message):
    user_id = message.chat.id
   # if not is_premium(user_id) and not can_free_user_search(user_id):
    #    bot.send_message(user_id, "🚫 تەنها جارێک دەتوانی گەڕان بکەیت بەبێ بەشداربوون.")
    #    return

    keyboard = []
    for cat_key, cat_data in searcher.categories.items():
        kurdish_name = cat_data.get("kurdish")
        if isinstance(kurdish_name, str):
            keyboard.append([types.InlineKeyboardButton(kurdish_name, callback_data=f"search_cat:{cat_key}")])

    bot.send_message(message.chat.id, "📌 تکایە بەشی کار هەڵبژێرە:", reply_markup=types.InlineKeyboardMarkup(keyboard))

@bot.callback_query_handler(func=lambda call: call.data.startswith("search_cat:"))
def select_category(call):
    user_state = get_user_state(call.from_user.id)
    user_state.category = call.data.split(":")[1]
    user_state.current_job_index = 0
    user_state.results = []
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="📍 تکایە شوێن هەڵبژێرە:", reply_markup=create_location_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("location:"))
def select_location(call):
    user_state = get_user_state(call.from_user.id)
    location_key = call.data.split(":")[1]
    if location_key == "all":
        user_state.location = None
        user_state.normalized_location = None
    else:
        loc_obj = searcher.locations.get(location_key)
        if not loc_obj:
            bot.answer_callback_query(call.id, "❌ شوێنەکە نەدۆزرایەوە.")
            return
        user_state.location = loc_obj.get("kurdish")
        user_state.normalized_location = loc_obj.get("normalized")

    user_state.current_job_index = 0
    user_state.results = []
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="⏳ ماوەی گەڕان هەڵبژێرە:", reply_markup=create_time_filter_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("time_filter:"))
def select_time_filter(call):
    user_state = get_user_state(call.from_user.id)
    days = int(call.data.split(":")[1])
    user_state.time_filter = days

    results = searcher.search(category_key=user_state.category,
                              location_input=user_state.normalized_location,
                              max_days=user_state.time_filter)

    user_state.results = results
    user_state.current_job_index = 0

    if not results:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="❌ هیچ کارێک نەدۆزرایەوە بەپێی هەڵبژاردنەکانت!")
        return

    show_job_result(call.message, user_state)

def show_job_result(message, user_state):
    try:
        job = user_state.results[user_state.current_job_index]
        cat_data = searcher.categories.get(user_state.category, {})
        cat_kurdish = cat_data.get("kurdish", "بێ بەش")
        contact_display = f"📧 ئیمەیڵ: {job['email']}" if job.get("email") else f"📞 پەیوەندی: {job.get('contact', 'نادیار')}"

        text = (
            f"<b>{job.get('title', 'بێ ناونیشان')}</b>\n\n"
            f"📌 <b>بەش:</b> {cat_kurdish}\n"
            f"📍 <b>شوێن:</b> {job.get('location', 'نادیار')}\n"
            f"⏳ <b>کات:</b> {searcher._format_posted_time(job.get('posted_at', 0))}\n\n"
            f"📋 <b>پێداویستیەکان:</b>\n{job.get('requirements', '')}\n\n"
            f"📝 <b>ناوەرۆک:</b>\n{job.get('description', '')}\n\n"
            f"{contact_display}"
        )

        keyboard = types.InlineKeyboardMarkup()
        if user_state.current_job_index > 0:
            keyboard.add(types.InlineKeyboardButton("⬅️ پێشوو", callback_data="nav:prev"))
        if user_state.current_job_index < len(user_state.results) - 1:
            keyboard.add(types.InlineKeyboardButton("دواتر ➡️", callback_data="nav:next"))

        keyboard.add(types.InlineKeyboardButton("🔁 گەڕانەوە", callback_data="new_search"))
        keyboard.add(types.InlineKeyboardButton("📝 ناردنی CV", callback_data="auto_apply"))

        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error in show_job_result: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "new_search")
def handle_new_search(call):
    start_search(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("nav:"))
def handle_nav(call):
    user_state = get_user_state(call.from_user.id)
    direction = call.data.split(":")[1]
    if direction == "prev" and user_state.current_job_index > 0:
        user_state.current_job_index -= 1
    elif direction == "next" and user_state.current_job_index < len(user_state.results) - 1:
        user_state.current_job_index += 1
    show_job_result(call.message, user_state)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_payment_plan(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    plan_days = call.data.split("_")[1]  # '30', '60', or '90'
    today = datetime.now().strftime("%d/%m/%Y")

    prices = {
        "30": "1000 IQD",
        "60": "2000 IQD",
        "90": "3000 IQD"
    }

    amount_text = prices.get(plan_days, "❓")
    message_code = f"{user_id}/{plan_days}/{today}"

    try:
        with open("payment.jpg", "rb") as photo:
            phone_number="\200E0770 039 8258"
            bot.send_photo(
                chat_id,
                photo,
                caption=(
                    f"💸 تکایە <b>{amount_text}</b> بنێرە بۆ پلانی {plan_days} ڕۆژ:\n\n"
                    f"📲 بۆ: <b>{phone_number}</b> لەسەر FastPay\n\n"
                    f"📝 لە خانەی نوسین، ئەم نامەیە بنووسە (بە تەواوی وەک خوارەوە):\n"
                    f"<code>{message_code}</code>\n\n"
                    f"⚠️ ئاگاداری! ئەگەر ئەم نامەیە نەتۆمار بکەیت یان هەڵەیەک لە ناوەوە بێت، ناتوانین پارەکەت بگرین.\n"
                    f"⏳ پڕۆسەکردن دەکرێت تا <b>12 کاتژمێر</b> بکات، تکایە بەرگەدار بە."
                ),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Couldn't send payment.jpg: {e}")
        bot.send_message(chat_id, "❌ ناتوانرێت وێنەی پارەدان بنێردرێت، تکایە پەیوەندیم پێوە بکە.")


@bot.message_handler(func=lambda msg: msg.text == "💎 بەشداریکردن")
def handle_subscription_check(message):
    user_id = message.chat.id
    try:
        conn = sqlite3.connect("user_data/premium_users.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT end_date FROM premium_users WHERE user_id = ? AND end_date > datetime('now')",
            (user_id,)
        )
        row = cursor.fetchone()

        if row:
            end_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            bot.send_message(user_id, f"👑 تۆ کراوی پرۆفیشناڵی بۆ کۆتایی: <b>{end_date.date()}</b> 🔒")
        else:
            msg = (
                "🚀 بە بەشداربوونت دەتوانی:\n"
                "- 🔍 گەڕانی بێ سنوور\n"
                "- 📤(بەم زوانە) ناردنی CV بۆ هەلی کار\n"
                "- 💾(بەم زوانە) خەزنکردنی CV\n\n"
                "💰 نرخەکان:\n"
                "- 30 ڕۆژ = 1,000 IQD\n"
                "- 60 ڕۆژ = 2,000 IQD\n"
                "- 90 ڕۆژ = 3,000 IQD\n\n"
                "🧾 بۆ کرین تکایە یەکێک هەڵبژێرە:"
            )
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("30 ڕۆژ - 1,000 IQD", callback_data="pay_30"))
            keyboard.add(types.InlineKeyboardButton("60 ڕۆژ - 2,000 IQD", callback_data="pay_60"))
            keyboard.add(types.InlineKeyboardButton("90 ڕۆژ - 3,000 IQD", callback_data="pay_90"))
            bot.send_message(user_id, msg, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error in subscription check: {e}")
        bot.send_message(user_id, "❌ کێشەیەک ڕوویدا لە کاتێک دا بەشداربوون دەبینرێت.")
    finally:
        conn.close()

# Main loop

if __name__ == "__main__":
    logger.info("✅ Initializing databases...")
    init_payment_db()
    init_free_user_db()
    logger.info("✅ Starting bot...")
    bot.polling(none_stop=True)
