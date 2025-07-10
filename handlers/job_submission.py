import os
import json
import re
from telebot import types
from session import user_states, user_data

CANCEL_COMMANDS = ["cancel", "گەڕانەوە"]
cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
cancel_markup.add("گەڕانەوە")

def start_submission(bot, message):
    user_id = message.chat.id
    user_states[user_id] = "title"  # Start directly with title
    user_data[user_id] = {}
    print(f"[DEBUG] Start submission for {user_id}")
    bot.send_message(
        user_id,
        "📝(دکتۆر ،مەندوب ، کرێکار هتد..) ناونیشانی هەلی کار بنووسە:",  # First prompt is now title
        reply_markup=cancel_markup
    )

def register(bot):

    def reset_user(user_id):
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)

    def save_job(user_id, message=None):
        job = user_data[user_id]

        # Convert types
        if 'cv_method' in job:
            job['cv_method'] = int(job['cv_method'])
        if 'cv_delivery_method' in job:
            job['cv_delivery_method'] = int(job['cv_delivery_method'])
        if 'messaging_app' in job:
            try:
                job['messaging_app'] = int(job['messaging_app'])
            except ValueError:
                job['messaging_app'] = 2  # default Telegram

        job["user_id"] = user_id
        if message:
            job["username"] = message.from_user.username or "نەدۆزرایەوە"
        job.pop("_next", None)

        os.makedirs("user_data", exist_ok=True)
        path = "user_data/user_submissions.json"

        try:
            with open(path, "r", encoding="utf-8") as f:
                jobs = json.load(f)
        except Exception:
            jobs = []

        jobs.append(job)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
            print(f"✅ Job saved for user {user_id}")
        except Exception as e:
            print(f"[❌ JSON write failed] {e}")

        reset_user(user_id)

    def ask(user_id, step):
        prompts = {
            "title": "📝 ناونیشانی هەلی کار بنووسە:",
            "location": "📍 شوێنی کار بنووسە:",
            "salary": "💰 مووچە بنووسە (تکایە بنووسە . یان 0 بۆ بەتاڵ جێهێشتن):",
            "requirements": "🧾 پێداویستیەکان بنووسە:",
            "description": "📋 ناوەرۆکی ڕوون بنووسە:",
            "cv_method": "❓ دەتەوێت سیڤی وەربگریت یان تەنها پەیوەندی؟\n1️⃣ سیڤی وەربگرە\n2️⃣ تەنها پەیوەندی",
            "cv_delivery_method": "📩 چۆن دەتەوێت سیڤی وەربگریت؟\n1️⃣ تەنها ئیمەیڵ\n2️⃣ تەنها ژمارە\n3️⃣ هەردوو",
            "email": "📧 ئیمەیڵەکەت بنووسە:",
            "contact": "📞 ژمارەی پەیوەندی بنووسە:",
            "messaging_app": "📲 ئەپێک دیاری بکە:\n1️⃣ WhatsApp\n2️⃣ Telegram\n3️⃣ Viber",
            "image": "🖼️ تکیە وێنەی شوێنی کارەکە ، بیناکە، کۆمپانیاکە بنێرە بؤ پشت ڕاسکەدنەوەیە. لە پۆستەکەیا بڵاو نەکرێتەوە."
        }
        bot.send_message(user_id, prompts.get(step, "⚠️ هەڵەیەک روویدا."), reply_markup=cancel_markup)

    @bot.message_handler(func=lambda msg: msg.chat.id in user_states, content_types=["text"])
    def handle_text(msg):
        user_id = msg.chat.id
        text = msg.text.strip()
        state = user_states.get(user_id)

        if text in CANCEL_COMMANDS:
            reset_user(user_id)
            bot.send_message(user_id, "❌ پڕۆسەی ناردنەوە بەتاڵ کرا.", reply_markup=types.ReplyKeyboardRemove())
            return

        if state == "title":
            user_data[user_id]["title"] = text
            user_states[user_id] = "location"
            ask(user_id, "location")

        elif state == "location":
            user_data[user_id]["location"] = text
            user_states[user_id] = "salary"
            ask(user_id, "salary")

        elif state == "salary":
            if text in [".", "0"]:
                user_data[user_id]["salary"] = ""
            elif not re.fullmatch(r"\d{3,}(\s*(دینار|هەزار|IQD|USD|\$|hazar|dinars)?)", text, re.IGNORECASE):
                bot.send_message(user_id, "💰 مووچەکە پێویستە بە شێوەیەکی دروست بنووسرێت (400$, 400 دینار). یان . / 0 بۆ بەتاڵ جێهێشتن.")
                return
            else:
                user_data[user_id]["salary"] = text
            user_states[user_id] = "requirements"
            ask(user_id, "requirements")

        elif state == "requirements":
            user_data[user_id]["requirements"] = text
            user_states[user_id] = "description"
            ask(user_id, "description")

        elif state == "description":
            user_data[user_id]["description"] = text
            user_states[user_id] = "cv_method"
            ask(user_id, "cv_method")

        elif state == "cv_method":
            if text not in ["1", "2"]:
                bot.send_message(user_id, "❗️تکایە 1 یان 2 بنووسە.")
                return
            user_data[user_id]["cv_method"] = text
            if text == "2":
                user_states[user_id] = "contact"
                ask(user_id, "contact")
            else:
                user_states[user_id] = "cv_delivery_method"
                ask(user_id, "cv_delivery_method")

        elif state == "cv_delivery_method":
            if text not in ["1", "2", "3"]:
                bot.send_message(user_id, "❗️تکایە 1، 2، یان 3 بنووسە.")
                return
            user_data[user_id]["cv_delivery_method"] = text
            if text == "1":
                user_states[user_id] = "email"
                ask(user_id, "email")
            elif text == "2":
                user_states[user_id] = "contact"
                ask(user_id, "contact")
            else:
                user_data[user_id]["_next"] = "both"
                user_states[user_id] = "email"
                ask(user_id, "email")

        elif state == "email":
            if text not in [".", "0"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", text):
                bot.send_message(user_id, "📧 ئیمەیڵەکە دروست نییە.")
                return
            user_data[user_id]["email"] = text
            if user_data[user_id].get("_next") == "both":
                user_states[user_id] = "contact"
                ask(user_id, "contact")
            else:
                user_states[user_id] = "image"
                ask(user_id, "image")

        elif state == "contact":
            if not re.search(r"\d{7,}", text):
                bot.send_message(user_id, "📞 ژمارەی دروست بنووسە.")
                return
            user_data[user_id]["contact"] = text
            if user_data[user_id].get("_next") == "both" or user_data[user_id].get("cv_delivery_method") == "2":
                user_states[user_id] = "messaging_app"
                ask(user_id, "messaging_app")
            else:
                user_states[user_id] = "image"
                ask(user_id, "image")

        elif state == "messaging_app":
            apps = {"1": "WhatsApp", "2": "Telegram", "3": "Viber"}
            if text not in apps:
                bot.send_message(user_id, "📲 تکایە ژمارەیەک دیاری بکە (1، 2، یان 3).")
                return
            user_data[user_id]["messaging_app"] = text
            user_states[user_id] = "image"
            ask(user_id, "image")

    @bot.message_handler(func=lambda msg: msg.chat.id in user_states, content_types=["photo", "document"])
    def handle_image(msg):
        user_id = msg.chat.id
        state = user_states.get(user_id)
        if state != "image":
            bot.send_message(user_id, "⚠️ تکایە لە کاتی دروست وەستایەوە و پەیامەکان پێشکەش بکە.")
            return

        file_id = None
        if msg.content_type == "photo":
            file_id = msg.photo[-1].file_id
            file_name = f"{file_id}.jpg"
        elif msg.content_type == "document" and msg.document.mime_type.startswith("image/"):
            file_id = msg.document.file_id
            file_name = msg.document.file_name or f"{file_id}.jpg"
        else:
            bot.send_message(user_id, "⚠️ تکایە وێنەیەک بنێرە (photo یان document image).")
            return

        user_data[user_id]["image"] = file_id

        try:
            file_info = bot.get_file(file_id)
            downloaded = bot.download_file(file_info.file_path)
            os.makedirs("user_data/images", exist_ok=True)
            with open(f"user_data/images/{file_name}", "wb") as f:
                f.write(downloaded)
            print(f"✅ Image saved to user_data/images/{file_name}")
        except Exception as e:
            print(f"[Image Download Error] {e}")
            bot.send_message(user_id, "⚠️ نەتوانرا وێنەکە داگرتن، دووبارە هەوڵ بدە.")
            return

        try:
            save_job(user_id, msg)
            bot.send_message(user_id, "سوپاس بۆ ناردنەکەت ✅.", reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            print(f"[Save Error] {e}")
            bot.send_message(user_id, "⚠️ هەڵەیەک ڕوویدا لە کاتی پاشەکەوت.")