import os
import json
import time
import re
import requests
from pathlib import Path
from dotenv import load_dotenv

# ======================
# CONFIGURATION
# ======================
ENV_PATH = Path(r"C:\Eishgpt\env\.env")
JOBS_DIR = Path(r"C:\Eishgpt\admin_jobs")
OUTPUT_FILE = JOBS_DIR / "processed.json"
MAX_RETRIES = 3
DELAY_SEC = 10
MAX_TOKENS = 8000
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

# ======================
# INITIALIZATION
# ======================
if not ENV_PATH.exists():
    raise FileNotFoundError(f"❌ .env file missing at {ENV_PATH}")

load_dotenv(ENV_PATH)
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    raise ValueError("❌ MISTRAL_API_KEY missing in .env file")

HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY.strip()}",
    "Content-Type": "application/json"
}

# ======================
# UTILITIES
# ======================
def estimate_tokens(text):
    return max(1, len(text) // 4)

def split_into_batches(texts, max_tokens=MAX_TOKENS):
    batches = []
    current_batch = []
    current_tokens = 0

    for text in texts:
        text_tokens = estimate_tokens(text)
        if current_tokens + text_tokens > max_tokens:
            if current_batch:
                batches.append(current_batch)
            current_batch = []
            current_tokens = 0
        current_batch.append(text)
        current_tokens += text_tokens

    if current_batch:
        batches.append(current_batch)

    return batches

def build_prompt(text_batch):
    numbered_batch = [
        f"=== JOB {i} ===\n{text.strip()}\n============"
        for i, text in enumerate(text_batch, 1)
    ]

    prompt_template = f"""
Extract job data from these OCR texts. Follow STRICT rules:
1. Process each JOB section separately
2. Output VALID JSON only
3. Keep original language for titles
4. Include salary only with numbers/currency
5. MUST include correct job_id matching the JOB number

{chr(10).join(numbered_batch)}

Output format (ONE JSON OBJECT PER JOB):
{{
  "jobs": [
    {{
      "title": "",
      "category": "",
      "location": "",
      "salary": "",
      "requirements": "",
      "description": "",
      "image": "",
      "job_id": 1
    }}
  ]
}}
"""
    return prompt_template

def call_mistral_api(prompt):
    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "You extract job data and output ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "max_tokens": 4000
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ API attempt {attempt+1}/{MAX_RETRIES} failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print("↳ Response snippet:", e.response.text[:200])
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY_SEC)
    return None

def process_batch(text_batch):
    prompt = build_prompt(text_batch)
    response = call_mistral_api(prompt)
    
    if not response:
        return []

    try:
        content = response["choices"][0]["message"]["content"]
        data = json.loads(content)
        jobs = data.get("jobs", [])
        processed = []

        for job in jobs:
            job_id = job.get("job_id", 0)
            if 1 <= job_id <= len(text_batch):
                job["raw_text"] = text_batch[job_id - 1]
                processed.append(job)
            else:
                print(f"⚠️ Invalid job_id {job_id} - expected between 1 and {len(text_batch)}")
        return processed
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"❌ Failed to parse API response: {e}")
        return []

# ======================
# MAIN FUNCTION
# ======================
def main():
    processed_jobs = []

    # Load previous processed jobs
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                processed_jobs = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to read processed.json: {e}. Starting fresh.")
            processed_jobs = []

    new_texts = []
    text_paths = []

    # Match only folders like "job_xxxxxx"
    for job_folder in sorted(JOBS_DIR.glob("job_*")):
        if not job_folder.is_dir():
            continue
        job_file = job_folder / "job.txt"
        if not job_file.exists():
            print(f"⛔ Skipped: {job_folder.name} (missing job.txt)")
            continue

        try:
            text = job_file.read_text(encoding='utf-8').strip()
            if text and not any(job.get("raw_text") == text for job in processed_jobs):
                new_texts.append(text)
                text_paths.append(job_folder.name)
        except Exception as e:
            print(f"⚠️ Could not read {job_file}: {e}")

    if not new_texts:
        print("✅ No new jobs to process.")
        return

    # Process in batches
    for batch_idx, batch in enumerate(split_into_batches(new_texts)):
        print(f"\n🔍 Processing batch {batch_idx+1} ({len(batch)} jobs)...")
        results = process_batch(batch)

        for result in results:
            try:
                idx = new_texts.index(result["raw_text"])
                result["source_folder"] = text_paths[idx]
                processed_jobs.append(result)
                print(f"✅ Extracted: {result.get('title', 'Untitled')} from {text_paths[idx]}")
            except ValueError:
                print("⚠️ Couldn't match result to source text")

        # Save progress incrementally
        try:
            temp_file = str(OUTPUT_FILE) + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(processed_jobs, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, OUTPUT_FILE)
        except Exception as e:
            print(f"❌ Failed to save progress: {e}")

        time.sleep(DELAY_SEC)

    print(f"\n🎉 Done! Total jobs processed: {len(processed_jobs)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"💥 Unhandled exception: {e}")
