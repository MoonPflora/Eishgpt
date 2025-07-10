import os
import json
import asyncio
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.types import Message, MessageMediaPhoto

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'env', '.env')
load_dotenv(dotenv_path)

# Telegram credentials
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

# File paths
BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
SCRAPED_JOBS_FILE = os.path.join(BASE_DIR, 'scraped_data', 'scraped_jobs.json')
LAST_SCRAPED_FILE = os.path.join(BASE_DIR, 'scraped_data', 'last_scraped.json')
IMAGE_DIR = os.path.join(BASE_DIR, 'image')
IMAGE_ONLY_DIR = os.path.join(IMAGE_DIR, 'image_only')

# Channels to scrape
CHANNELS = ["allkurdistanjobs", "fjkurdistan10"]

# Ensure directories exist
os.makedirs(os.path.dirname(SCRAPED_JOBS_FILE), exist_ok=True)
os.makedirs(IMAGE_ONLY_DIR, exist_ok=True)


def safe_load_json(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default


def safe_write_json(data, path):
    temp_path = path + ".temp"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)


async def scrape():
    last_scraped = safe_load_json(LAST_SCRAPED_FILE, {})
    scraped_jobs = safe_load_json(SCRAPED_JOBS_FILE, [])
    new_last_scraped = {}

    async with TelegramClient("anon", API_ID, API_HASH) as client:
        for channel in CHANNELS:
            print(f"\n🔍 Scraping channel: {channel}")
            try:
                last_time = datetime.fromtimestamp(last_scraped.get(channel, 0), tz=timezone.utc)
                new_messages = []

                async for message in client.iter_messages(channel, limit=100):
                    if not isinstance(message, Message):
                        continue
                    if message.date <= last_time:
                        break

                    text = message.text or ""
                    timestamp = message.date.isoformat()

                    job_data = {
                        "channel": channel,
                        "text": text,
                        "date": timestamp
                    }

                    # Handle image saving only for allowed channel
                    if isinstance(message.media, MessageMediaPhoto):
                        if channel == "allkurdistanjobs":
                            image_name = f"{channel}_{message.id}.jpg"
                            if text.strip():
                                channel_img_dir = os.path.join(IMAGE_DIR, channel)
                                os.makedirs(channel_img_dir, exist_ok=True)
                                image_path = os.path.join(channel_img_dir, image_name)
                            else:
                                image_path = os.path.join(IMAGE_ONLY_DIR, image_name)

                            try:
                                await client.download_media(message.media, file=image_path)
                                job_data["image_path"] = image_path
                            except Exception as e:
                                print(f"⚠️ Failed to download image for message {message.id}: {e}")

                    # Add job to batch
                    new_messages.append(job_data)

                if new_messages:
                    print(f"✅ Found {len(new_messages)} new messages in {channel}")
                    scraped_jobs.extend(new_messages)
                    new_last_scraped[channel] = int(datetime.now(tz=timezone.utc).timestamp())
                else:
                    new_last_scraped[channel] = last_scraped.get(channel, 0)

            except FloodWaitError as e:
                print(f"⏳ Flood wait error for {channel}, sleeping {e.seconds}s...")
                time.sleep(e.seconds)
                continue
            except SessionPasswordNeededError:
                print("🔐 Two-step verification required. Check your Telegram setup.")
                break
            except Exception as e:
                print(f"❌ Error scraping {channel}: {e}")
                continue

    # Save results only if we scraped successfully
    try:
        safe_write_json(scraped_jobs, SCRAPED_JOBS_FILE)
        safe_write_json(new_last_scraped, LAST_SCRAPED_FILE)
        print("\n✅ Scraping complete and saved.")
    except Exception as e:
        print(f"❌ Failed to write JSON files: {e}")


if __name__ == "__main__":
    asyncio.run(scrape())
