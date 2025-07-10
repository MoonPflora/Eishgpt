import os
import json
import logging
from datetime import datetime

# === Configuration ===
TRACKER_FILE = "processed_data/posting_tracker.json"
INPUT_FILE = "processed_data/ready_to_post.json" 
POSTED_FILE = "processed_data/posted_jobs.json"
LOCK_FILE = "poster.lock"

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("job_poster.log"),
        logging.StreamHandler()
    ]
)

# === Core Functions ===
def load_json(file_path):
    """Safely load JSON file with empty list fallback"""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Corrupted file: {file_path}")
        return []

def atomic_save(file_path, data):
    """Atomic write with temp file replacement"""
    temp_path = f"{file_path}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, file_path)
    except Exception as e:
        logging.error(f"Failed to save {file_path}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)

def load_tracker():
    """Load or initialize tracking data"""
    try:
        return load_json(TRACKER_FILE) or {"last_processed_id": None, "in_progress_ids": []}
    except Exception as e:
        logging.error(f"Tracker load failed: {e}")
        return {"last_processed_id": None, "in_progress_ids": []}

def update_tracker(last_id=None, in_progress=None):
    """Update progress tracking"""
    tracker = load_tracker()
    if last_id is not None:
        tracker["last_processed_id"] = last_id
    if in_progress is not None:
        tracker["in_progress_ids"] = in_progress
    atomic_save(TRACKER_FILE, tracker)

def clear_stale_jobs():
    """Cleanup any stuck in-progress jobs"""
    tracker = load_tracker()
    if tracker.get("in_progress_ids"):
        logging.warning(f"Clearing {len(tracker['in_progress_ids'])} stuck jobs")
        tracker["in_progress_ids"] = []
        update_tracker(in_progress=[])

# === Job Processing ===
def post_to_api(job_data):
    """IMPLEMENT YOUR ACTUAL POSTING LOGIC HERE"""
    # Example: Telegram/Slack/DB posting
    # Return (success, message) tuple
    return True, "Posted successfully"

def process_jobs():
    """Main processing pipeline with resume capability"""
    tracker = load_tracker()
    jobs_to_process = load_json(INPUT_FILE)
    posted_jobs = load_json(POSTED_FILE)
    
    # Filter already posted jobs
    posted_ids = {j.get("unique_id") for j in posted_jobs}
    unposted = [
        j for j in jobs_to_process
        if j.get("unique_id") not in posted_ids
    ]
    
    # Respect last processed ID for resume
    if tracker.get("last_processed_id"):
        try:
            last_pos = next(i for i,j in enumerate(unposted) 
                          if j.get("unique_id") == tracker["last_processed_id"])
            unposted = unposted[last_pos+1:]
        except StopIteration:
            pass

    # Process with tracking
    for job in unposted:
        job_id = job.get("unique_id", "unknown")
        try:
            update_tracker(last_id=job_id, in_progress=[job_id])
            
            success, msg = post_to_api(job)
            if success:
                job["posted_at"] = datetime.now().isoformat()
                posted_jobs.append(job)
                atomic_save(POSTED_FILE, posted_jobs)
                logging.info(f"✅ {job_id[:8]} - {msg}")
            else:
                logging.error(f"❌ {job_id[:8]} - {msg}")
                
        except Exception as e:
            logging.critical(f"💥 {job_id[:8]} - Crash: {str(e)}")
            raise
        finally:
            update_tracker(in_progress=[])

    # Cleanup processed jobs
    if unposted:
        remaining = [j for j in jobs_to_process 
                    if j.get("unique_id") not in {p.get("unique_id") for p in posted_jobs}]
        atomic_save(INPUT_FILE, remaining)

# === Main Execution ===
if __name__ == "__main__":
    try:
        # Lockfile check
        if os.path.exists(LOCK_FILE):
            logging.warning("⚠️ Existing lockfile - recovering from crash")
            clear_stale_jobs()
        
        # Create lockfile
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        
        # Run processing
        process_jobs()
        
    except KeyboardInterrupt:
        logging.info("🛑 Graceful shutdown")
    except Exception as e:
        logging.critical(f"💥 Fatal error: {e}")
    finally:
        # Cleanup
        clear_stale_jobs()
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)