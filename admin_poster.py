import requests
import time
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("C:/Eishgpt/env/.env"))

class JobPoster:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        self.channel_id = os.getenv("CHANNEL_ID")
        self.posted_file = Path("C:/Eishgpt/processed_data/posted_jobs.json")
        self.ensure_posted_file()

    def ensure_posted_file(self):
        """Ensure posted_jobs.json exists with empty list if not present"""
        self.posted_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.posted_file.exists():
            with open(self.posted_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def post_job(self, job):
        """Post job to channel (TEXT ONLY) with proper RTL formatting"""
        try:
            # Create clean job data with proper types
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
                'messaging_app': int(job.get('messaging_app', 2))
            }
            
            message = self._format_with_rtl(clean_job)
            resp = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": self.channel_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
            )
            
            if resp.status_code == 200:
                result = resp.json().get("result", {})
                return True, result.get("message_id")
            return False, None
        except Exception as e:
            print(f"Posting failed: {e}")
            return False, None

    def _format_with_rtl(self, job):
        """Format job with all Kurdish text properly right-aligned"""
        # Unicode directional formatting characters
        RLE = "\u202B"  # Right-to-Left Embedding
        PDF = "\u202C"  # Pop Directional Formatting
        
        # Format each line with consistent RTL
        message_lines = [
            f"{RLE}<b>{job['title']} - هەلی کار❗️{PDF}",
            f"{RLE}{job['location']} - ناونیشان📍{PDF}",
            f"{RLE}{job['salary']} - موچە💰{PDF}",
            f"{RLE}{job['requirements']} - پێداویستی🧾{PDF}",
            f"{RLE}{job['description']} - ناوەرۆک📋{PDF}"
        ]

        # Handle contact information
        if job['cv_method'] == 1:  # Receive CV
            methods = []
            if job['cv_delivery_method'] in [1, 3]:  # Email or both
                methods.append(f"{RLE}ئیمەیڵ: {job['email']} 📧{PDF}")
            if job['cv_delivery_method'] in [2, 3]:  # Number or both
                app_map = {1: "WhatsApp", 2: "Telegram", 3: "Viber"}
                app = app_map.get(job['messaging_app'], "Telegram")
                methods.append(f"{RLE}{app}: {job['contact']} 📱{PDF}")
            
            contact_line = f"{RLE}سیڤی بنێرە بۆ: {' / '.join(methods)} 📩{PDF}"
        else:  # Calls only
            contact_line = f"{RLE}پەیوەندی بکە بۆ: {job['contact']} 📞{PDF}"

        message_lines.append(contact_line)
        return "\n".join(message_lines)

    def save_posted_job(self, job, message_id=None):
        """Save with posted status and timestamp"""
        job_data = {
            **job,  # Keep all original data including image for admin review
            "posted": True,
            "posted_at": int(time.time()),
            "channel_message_id": message_id
        }
        
        try:
            with open(self.posted_file, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
            
            jobs.append(job_data)
            
            with open(self.posted_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving: {e}")
            return False