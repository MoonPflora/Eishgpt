import os
import json
import time
import uuid
from session import user_states
from pathlib import Path
from datetime import datetime, timedelta
import requests
from telebot import types

# Globals & Paths
admin_sessions_ref = set()
job_sessions = {}
pending_rejections = {}
pending_approvals = {}

BASE_DIR = Path(__file__).resolve().parent.parent
ADMIN_JOBS_DIR = BASE_DIR / "admin_jobs"
SUBMISSIONS_FILE = BASE_DIR / "user_data" / "user_submissions.json"
POSTED_FILE = BASE_DIR / "processed_data" / "posted_jobs.json"
CATEGORIES_JSON_PATH = BASE_DIR / "categories.json"  # <--- New: path to categories.json

CHANNEL_ID = "@KurdistanJobsCentral"  # Ideally move this to .env

# --- Removed static JOB_CATEGORIES dict -- we load categories dynamically from json file now ---

# Ensure directories exist
ADMIN_JOBS_DIR.mkdir(exist_ok=True)
POSTED_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_categories():
    try:
        with open(CATEGORIES_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading categories.json: {e}")
        return {}

# Load once on import or first use
CATEGORIES_DATA = load_categories()

def is_admin(user_id):
    return user_id in admin_sessions_ref

def load_jobs():
    if not SUBMISSIONS_FILE.exists():
        return []
    with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_jobs(jobs):
    SUBMISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SUBMISSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

def save_posted_job(job, category=None, message_id=None):
    job_data = {k: v for k, v in job.items() if k not in ("verification", "image")}
    job_data.update({
        "posted_at": int(time.time()),
        "posted": True,
        "channel_message_id": message_id
    })
    if category:
        job_data["category"] = category
        # Use Kurdish name from loaded categories instead of static dict
        job_data["category_kurdish"] = CATEGORIES_DATA.get(category, {}).get("kurdish", "هی تر")

    try:
        jobs = []
        if POSTED_FILE.exists():
            with open(POSTED_FILE, "r", encoding="utf-8") as f:
                jobs = json.load(f)
        jobs.append(job_data)
        with open(POSTED_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving posted job: {e}")
        return False

def post_to_channel(bot_token, job):
    try:
        clean_job = {
            'title': job.get('title', ''),
            'location': job.get('location', ''),
            'salary': job.get('salary', '0'),
            'requirements': job.get('requirements', ''),
            'description': job.get('description', ''),
            'cv_method': int(job.get('cv_method', 2)),
            'cv_delivery_method': int(job.get('cv_delivery_method', 1)),
            'email': job.get('email', ''),
            'contact': job.get('contact', ''),
            'messaging_app': job.get('messaging_app', 2),
            'category': job.get('category_kurdish', '')  # Use Kurdish name in post
        }

        message_parts = [
            f"<b>{clean_job['title']}-هەلی کار❗️</b>",
            f"📍 {clean_job['location']}-ناونیشان",
            f"💰 {clean_job['salary']}-موچە",
            f"🧾 {clean_job['requirements']}-پێداویستی",
            f"📋 {clean_job['description']}-ناوەرۆک"
        ]

        if clean_job['category']:
            message_parts.insert(1, f"🏷️ بەش: {clean_job['category']}")

        if clean_job['cv_method'] == 1:
            methods = []
            if clean_job['cv_delivery_method'] in [1, 3]:
                methods.append(f"📧 ئیمەیڵ: {clean_job['email']}")
            if clean_job['cv_delivery_method'] in [2, 3]:
                app_map = {1: "WhatsApp", 2: "Telegram", 3: "Viber"}
                app = app_map.get(clean_job['messaging_app'], "Telegram")
                methods.append(f"📱 {app}: {clean_job['contact']}")
            contact_info = "📩 سیڤی بنێرە بۆ: " + " / ".join(methods)
        else:
            contact_info = f"📞 پەیوەندی بکە بۆ: {clean_job['contact']}"

        message_parts.append(contact_info)
        message = "\n".join(message_parts)

        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
        )

        if resp.status_code == 200:
            result = resp.json().get("result", {})
            return True, result.get("message_id")
        else:
            print(f"Telegram API error: {resp.status_code} {resp.text}")
            return False, None

    except Exception as e:
        print(f"Error posting to channel: {e}")
        return False, None

def notify_user_approved(bot, user_id):
    try:
        bot.send_message(user_id, "سڵاو بەکارهێنەر، ئەدمین ڕەزامەندیی لە پۆستەکەت کردووە و دواتر بڵاو دەکرێتەوە ✅")
    except Exception as e:
        print(f"Couldn't notify approval: {e}")

def notify_user_rejected(bot, user_id, reason):
    try:
        bot.send_message(user_id, f"سڵاو بەکارهێنەر، پۆستەکەت ڕەتکرایەوە ❌\nهۆکار: {reason}")
    except Exception as e:
        print(f"Couldn't notify rejection: {e}")

def register_admin_handlers(bot, admin_sessions):
    global admin_sessions_ref, job_sessions, pending_rejections, pending_approvals

    @bot.message_handler(func=lambda m: m.text == "787898rawa")
    def handle_admin_code(message):
        admin_sessions_ref.add(message.from_user.id)
        bot.send_message(message.chat.id, "✅ چوونەژوورەوەی ئەدمین سەرکەوتوو بوو.")

    @bot.message_handler(commands=["review_jobs"])
    def handle_review_jobs(msg):
        if not is_admin(msg.from_user.id):
            return bot.send_message(msg.chat.id, "⛔ تۆ ئەدمین نیت.")
        jobs = load_jobs()
        if not jobs:
            return bot.send_message(msg.chat.id, "🚫 هیچ پۆستێک نەماوە.")
        job = jobs[0]
        username = job.get("username", "نەدۆزرایەوە")
        text = (
            f"📋 هەلی کار:\n📝 ناونیشان: {job.get('title', '')}\n"
            f"📍 شوێن: {job.get('location', '')}\n💰 مووچە: {job.get('salary', '')}\n"
            f"🧾 پێداویستی: {job.get('requirements', '')}\n📋 ناوەرۆک: {job.get('description', '')}\n"
            f"📞 پەیوەندی: {job.get('contact', '')}\n📧 ئیمەیڵ: {job.get('email', '')}\n👤 بەکارهێنەر: @{username}"
        )
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✅ پەسەند", callback_data="approve_job"),
            types.InlineKeyboardButton("❌ ڕەتکردنەوە", callback_data="reject_job")
        )
        if job.get("image"):
            try:
                bot.send_photo(msg.chat.id, photo=job["image"], caption=text, reply_markup=markup)
                return
            except Exception as e:
                print(f"Failed to send photo: {e}")
        bot.send_message(msg.chat.id, text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data in ["approve_job", "reject_job"])
    def handle_decision(call):
        if not is_admin(call.from_user.id):
            return bot.answer_callback_query(call.id, "⛔ ئەم فرمانە تەنها بۆ ئەدمینە.")
        jobs = load_jobs()
        if not jobs:
            return bot.answer_callback_query(call.id, "🚫 هیچ پۆستێک نەماوە.")
        job = jobs.pop(0)
        save_jobs(jobs)

        if call.data == "approve_job":
            pending_approvals[call.from_user.id] = job
            markup = types.InlineKeyboardMarkup(row_width=2)

            # --- Changed here: use loaded categories to create buttons with Kurdish text ---
            buttons = [
                types.InlineKeyboardButton(text=val.get("kurdish", key), callback_data=f"cat_{key}")
                for key, val in CATEGORIES_DATA.items()
            ]
            markup.add(*buttons)
            bot.send_message(call.message.chat.id, "📌 تکایە بەشی کار هەڵبژێرە:", reply_markup=markup)
            bot.answer_callback_query(call.id)

        else:
            pending_rejections[call.from_user.id] = job
            bot.answer_callback_query(call.id, "❌ ڕەتکرا، هۆکار بنووسە")
            bot.send_message(call.message.chat.id, "❌ تکایە هۆکاری ڕەتکردنەوە بنووسە:")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
    def handle_category_selection(call):
        if not is_admin(call.from_user.id):
            return bot.answer_callback_query(call.id, "⛔ ئەم فرمانە تەنها بۆ ئەدمینە.")
        job = pending_approvals.pop(call.from_user.id, None)
        if not job:
            return bot.answer_callback_query(call.id, "⚠️ هیچ کارێک بۆ پەسەندکردن نییە")
        category_key = call.data.split("_", 1)[1]  # Get main category key

        success, message_id = post_to_channel(bot.token, job)
        if success:
            if save_posted_job(job, category_key, message_id):
                notify_user_approved(bot, job.get("user_id"))
                bot.answer_callback_query(call.id, "✅ پەسەندکرا و بڵاوکرایەوە")
                bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
                
                # Show Kurdish category name in confirmation
                kurdish_name = CATEGORIES_DATA.get(category_key, {}).get("kurdish", "")
                bot.edit_message_text(
                    f"✅ پەسەندکرا و بڵاوکرایەوە!\n🏷️ بەش: {kurdish_name}",
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id
                )
            else:
                bot.answer_callback_query(call.id, "⚠️ پەسەندکرا بەڵام نەتوانرا پاشەکەوت بکرێت")
        else:
            bot.answer_callback_query(call.id, "⚠️ نەتوانرا بڵاوبکرێتەوە، تکایە دووبارە بکەرەوە")

        if load_jobs():
            handle_review_jobs(call.message)

    @bot.message_handler(func=lambda msg: msg.from_user.id in pending_rejections)
    def handle_rejection_reason(message):
        job = pending_rejections.pop(message.from_user.id)
        reason = message.text.strip()
        notify_user_rejected(bot, job.get("user_id"), reason)
        bot.send_message(message.chat.id, "❌ هۆکار نێردرا بۆ بەکارهێنەر.")
        if load_jobs():
            handle_review_jobs(message)

    @bot.message_handler(commands=["list_jobs"])
    def handle_list_jobs(message):
        if not is_admin(message.from_user.id):
            return bot.send_message(message.chat.id, "⛔ تۆ ئەدمین نیت.")
        jobs = load_jobs()
        if not jobs:
            return bot.send_message(message.chat.id, "🚫 هیچ پۆستێک نەماوە.")
        lines = ["📋 لیستی پۆستە چاوەڕوانەکان:"]
        for i, job in enumerate(jobs, 1):
            lines.append(f"{i}. {job.get('title', 'ناونیشان نییە')} — {job.get('location', 'شوێن نییە')}")
        bot.send_message(message.chat.id, "\n".join(lines))

    @bot.message_handler(commands=["enter_job"])
    def handle_enter_job(message):
        if not is_admin(message.from_user.id):
            return bot.send_message(message.chat.id, "⛔ تۆ ئەدمین نیت.")
        user_id = message.from_user.id
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        job_folder = ADMIN_JOBS_DIR / job_id
        job_sessions[user_id] = {
            "images": [],
            "awaiting_method": False,
            "start_time": datetime.now(),
            "job_folder": job_folder
        }
        job_folder.mkdir(exist_ok=True)
        bot.send_message(message.chat.id, "📸 تکایە وێنەکانی کارەکە بنێرە (یەک بە یەک)، پاشان /confirm_image بنێرە")

    @bot.message_handler(
        func=lambda msg: is_admin(msg.from_user.id) and
        msg.from_user.id in job_sessions and
        not job_sessions[msg.from_user.id]["awaiting_method"],
        content_types=["photo"]
    )
    def handle_job_images(message):
        user_id = message.from_user.id
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            job_sessions[user_id]["images"].append({
                "file_id": message.photo[-1].file_id,
                "data": downloaded_file
            })
            bot.reply_to(message, f"🖼️ وێنە {len(job_sessions[user_id]['images'])} وەرگیرا")
        except Exception as e:
            print(f"Error handling image: {e}")
            bot.reply_to(message, "⚠️ هەڵە لە هەڵگرتنی وێنە")

    @bot.message_handler(commands=["confirm_image"])
    def handle_confirm_image(message):
        user_id = message.from_user.id
        session = job_sessions.get(user_id)
        if not session or not session["images"]:
            return bot.send_message(message.chat.id, "⚠️ هیچ وێنەیەک وەرنەگیراوە")
        if datetime.now() - session["start_time"] > timedelta(minutes=30):
            job_sessions.pop(user_id, None)
            return bot.send_message(message.chat.id, "⌛ کاتی سێشەن تەواو بوو، تکایە دەستپێبکەرەوە")
        job_sessions[user_id]["awaiting_method"] = True
        bot.send_message(message.chat.id, "📨 تکایە ڕێگای پەیوەندی بنووسە (ئیمەیڵ/ژمارە/لینک):")

    @bot.message_handler(
        func=lambda msg: is_admin(msg.from_user.id) and
        msg.from_user.id in job_sessions and
        job_sessions[msg.from_user.id]["awaiting_method"]
    )
    def handle_application_method(message):
        user_id = message.from_user.id
        application_method = message.text.strip()
        session = job_sessions[user_id]
        try:
            for i, img_data in enumerate(session["images"], 1):
                with open(session["job_folder"] / f"image_{i}.jpg", "wb") as f:
                    f.write(img_data["data"])
            with open(session["job_folder"] / "application_method.txt", "w", encoding="utf-8") as f:
                f.write(application_method)
            bot.send_message(message.chat.id, f"✅ کارەکە پاشەکەوت کرا لە {session['job_folder']}")
        except Exception as e:
            print(f"Error saving job session data: {e}")
            bot.send_message(message.chat.id, "⚠️ هەڵە لە پاشەکەوتکردنەوە")
        job_sessions.pop(user_id, None)

    @bot.message_handler(commands=['enter_user'])
    def handle_enter_premium_ids(message):
        if not is_admin(message.from_user.id):
            return bot.send_message(message.chat.id, "⛔ تۆ ئەدمین نیت.")

        try:
            data_str = message.text.split(' ', 1)[1].strip()
        except IndexError:
            bot.send_message(message.chat.id, "❌ تکایە زانیاری بەشداربووان بەشێوەی `/enter_user id.days/id.days` بنووسە.")
            return

        try:
            import add_premium
            result = add_premium.add_premium_users(data_str)
            bot.send_message(message.chat.id, f"✅ {result}")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ کێشە لە زیادکردنی بەشداربووانەوە: {e}")
