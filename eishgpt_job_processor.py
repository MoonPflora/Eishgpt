import os
import json
import time
import re
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv("env/.env")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Constants
INPUT_FILE = "scraped_data/cleaned_scraped_jobs.json"
OUTPUT_FILE = "processed_data/processed_jobs.json"
PROMPT_FILE = "prompt.txt"  # New prompt file path
MAX_TOKENS_PER_BATCH = 3500
MAX_RETRIES = 3
SLEEP_BETWEEN_BATCHES = 60  # 1 minute
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"⚠️ Corrupted JSON in {path}: {e}")
            tmp_path = path + ".tmp"
            if os.path.exists(tmp_path):
                try:
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        print(f"🧯 Recovering from {tmp_path}")
                        return json.load(f)
                except Exception as e:
                    print(f"❌ Recovery from .tmp also failed: {e}")
            corrupted_path = path + ".corrupted"
            os.rename(path, corrupted_path)
            print(f"🛑 Renamed corrupted file to {corrupted_path}")
            return []
    return []

def save_json(path, data):
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception as e:
        print(f"❌ Failed to save {path}: {e}")

def load_prompt(path):
    """Load prompt template from file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise Exception(f"🚨 Critical: Prompt file not found at {path}")

def is_duplicate(text, processed):
    return any(job.get("raw_text", "") == text for job in processed)

def estimate_tokens(text):
    return max(1, len(text) // 4)

def split_batches(jobs, max_tokens=MAX_TOKENS_PER_BATCH):
    batches = []
    current = []
    token_count = 0

    for job in jobs:
        text = job.get("text", "").strip()
        tokens = estimate_tokens(text)

        if token_count + tokens > max_tokens and current:
            batches.append(current)
            current = []
            token_count = 0

        current.append(job)
        token_count += tokens

    if current:
        batches.append(current)

    return batches

def build_prompt(text):
    """Inject job text into the template."""
    prompt_template = load_prompt(PROMPT_FILE)
    return prompt_template.replace("{input_text}", text.strip())

def call_mistral(prompt, system="You are a job extractor."):
    payload = {
        "model": "mistral-medium",
        "temperature": 0.3,
        "top_p": 1,
        "max_tokens": 800,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Retry {attempt+1}/{MAX_RETRIES} failed: {e}")
            time.sleep(5)
    return None

def extract_job_info(text):
    content = call_mistral(build_prompt(text))
    if not content:
        return None

    # Remove JSON markdown if present
    content = re.sub(r"^```(?:json)?\n?|```$", "", content.strip(), flags=re.MULTILINE)
    
    # Extract JSON
    try:
        extracted = json.loads(content)
        
        # Enforce empty image field and validate contact
        extracted["image"] = ""
        if not extracted.get("contact"):
            print("⚠️ Ignored job (no valid contact)")
            return None
            
        return extracted
    except Exception as e:
        print(f"⚠️ Invalid JSON from AI: {e}\nRaw content:\n{content}")
        return None

def main():
    raw_jobs = load_json(INPUT_FILE)
    processed_jobs = load_json(OUTPUT_FILE)
    unprocessed_jobs = [j for j in raw_jobs if not is_duplicate(j.get("text", ""), processed_jobs)]

    print(f"🔍 Found {len(unprocessed_jobs)} new jobs to process.")
    if not unprocessed_jobs:
        return

    batches = split_batches(unprocessed_jobs)
    for i, batch in enumerate(batches):
        print(f"⚙️ Processing batch {i+1}/{len(batches)} with {len(batch)} jobs...")
        for job in batch:
            text = job.get("text", "").strip()
            if not text:
                continue

            extracted = extract_job_info(text)
            if not extracted:
                continue

            # Preserve original metadata
            extracted.update({
                "raw_text": text,
                "channel": job.get("channel"),
                "date": job.get("date")
            })
            processed_jobs.append(extracted)
            print(f"✅ Processed: {extracted.get('title', 'Unknown')}")

        save_json(OUTPUT_FILE, processed_jobs)
        print(f"💾 Saved {len(processed_jobs)} total jobs so far.")
        time.sleep(SLEEP_BETWEEN_BATCHES)

    print("✅ All jobs processed successfully. Script finished.")

if __name__ == "__main__":
    main()