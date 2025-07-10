import os
import json
import re

# File paths
BASE_DIR = os.path.dirname(__file__)
SCRAPED_JOBS_FILE = os.path.join(BASE_DIR, 'scraped_data', 'scraped_jobs.json')
CLEANED_JOBS_FILE = os.path.join(BASE_DIR, 'scraped_data', 'cleaned_scraped_jobs.json')
JUNK_JOBS_FILE = os.path.join(BASE_DIR, 'scraped_data', 'junk.json')

# Akam name phrases to remove (Kurdish and English)
AKAM_PHRASES = [
    r"سڵاو کاک ئاكام[!؟]?",  # Kurdish
    r"کاک ئاكام\b",         # Kurdish
    r"ئاكام\b",             # Kurdish
    r"سڵاو\s*ئاكام",        # Kurdish
    r"Hello Akam",          # English
    r"Hi Akam",             # English
    r"Dear Akam",           # English
    r"Greetings Akam"       # English
]

# Job relevance keywords
JOB_KEYWORDS = [
    r"hiring", r"هەلی کار", r"کار", r"Hiring", r"position", r"job", r"vacancy",
    r"فرصة عمل", r"وظيفة", r"پۆست", r"وظائف", r"mocha", r"موچە",
    r"مۆزەف", r"کارمەند", r"سایەق", r"مەندوب", r"کاش ڤان", r"دکتۆر", r"پەرستار", r"سەیدەلانی"
]

# Enhanced contact keywords (added Arabic phrases)
CONTACT_KEYWORDS = [
    r"whatsapp", r"email", r"send cv", r"ژمارە", r"form", r"سی ڤی", r"ڕەقەم",
    r"gmail", r"ئیمێل", r"ئیمێڵ", r"پەیوەندی", r"viber", r"ڤایبەر", r"واتساپ",
    r"apply", r"submit", r"send", r"سیڤی", r"Apply", r"Submit", r"Send",
    r"إرسال السيرة الذاتية",  # Added Arabic phrase
    r"الواتساب"               # Added Arabic phrase
]

# Enhanced numeral conversion (Arabic to Western)
ARABIC_NUMERAL_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# --- Helper functions ---
def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_json(data, path):
    temp_path = path + '.temp'
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)

def clean_hashtags(text):
    return re.sub(r"#[\w_]+", "", text)

def clean_akam_chatter(text):
    """Safely remove Akam-related chatter without damaging job info"""
    for phrase in AKAM_PHRASES:
        text = re.sub(phrase, "", text, flags=re.IGNORECASE)
    return text.strip()

def has_required_fields(job):
    return bool(job.get("date")) and bool(job.get("channel"))

def normalize_numbers(text):
    """Convert all Arabic numerals to Western numerals"""
    return text.translate(ARABIC_NUMERAL_MAP)

def has_contact_info(text):
    normalized = normalize_numbers(text)

    # 1. Check enhanced contact keywords
    contact_keywords_present = any(
        re.search(kw, text, re.IGNORECASE) for kw in CONTACT_KEYWORDS
    )
    
    # 2. Check phone numbers (including Arabic numerals)
    phone_pattern = r"(?:\+?964|0)?[\s\-]*7\d{2}(?:[\s\-]*\d){7}"
    has_phone = re.search(phone_pattern, normalized)
    
    # 3. Check emails
    has_email = re.search(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", text)
    
    return contact_keywords_present or has_phone or has_email

# --- Main cleaning function ---
def clean_scraped_jobs():
    raw_jobs = load_json(SCRAPED_JOBS_FILE)
    cleaned_jobs = []
    junk_jobs = []

    for job in raw_jobs:
        if not isinstance(job, dict):
            job['__reason__'] = 'invalid format'
            junk_jobs.append(job)
            continue

        if not has_required_fields(job):
            job['__reason__'] = 'missing date or channel'
            junk_jobs.append(job)
            continue

        text = job.get("text", "").strip()
        
        # Clean text in this order:
        text = clean_hashtags(text)
        text = clean_akam_chatter(text)
        job["text"] = text

        if not has_contact_info(text):
            job['__reason__'] = 'no contact info'
            junk_jobs.append(job)
            continue

        cleaned_jobs.append(job)

    save_json(cleaned_jobs, CLEANED_JOBS_FILE)
    save_json(junk_jobs, JUNK_JOBS_FILE)

    print(f"🧹 Cleaned {len(raw_jobs)} jobs → kept {len(cleaned_jobs)} valid jobs, flagged {len(junk_jobs)} as junk")

if __name__ == "__main__":
    clean_scraped_jobs()