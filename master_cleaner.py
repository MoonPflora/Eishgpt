import os
import shutil
import json
from pathlib import Path

# ===== Configuration ===== (Modify if needed)

BASE_DIR = Path(__file__).resolve().parent

PATHS_TO_CLEAN = [
    BASE_DIR / "image" / "image_only",
    BASE_DIR / "image" / "fjkurdistan10",
    BASE_DIR / "image" / "allkurdistanjobs",
    BASE_DIR / "user_data" / "images",
]

ADMIN_JOBS_DIR = BASE_DIR / "admin_jobs"
JOB_FOLDER_PREFIX = "job_"

JSON_FILES_TO_CLEAN = [
    BASE_DIR / "admin_jobs" / "ocr_status.json",
    BASE_DIR / "admin_jobs" / "processed.json",
    BASE_DIR / "scraped_data" / "scraped_jobs.json",
    BASE_DIR / "scraped_data" / "junk.json",
    BASE_DIR / "scraped_data" / "cleaned_scraped.json",
    BASE_DIR / "processed_data" / "processed_jobs.json",
]

# ===== Functions =====
def clean_directory(dir_path: Path) -> None:
    """Delete all files/subfolders inside a directory but keep the directory."""
    if not dir_path.exists():
        print(f"⚠️ Directory not found: {dir_path}")
        return

    for item in dir_path.glob("*"):
        try:
            if item.is_file():
                item.unlink()  # Delete file
            elif item.is_dir():
                shutil.rmtree(item)  # Delete folder recursively
            print(f"🗑️ Deleted: {item}")
        except Exception as e:
            print(f"❌ Failed to delete {item}: {e}")

def delete_job_folders(root_dir: Path, prefix: str) -> None:
    """Delete folders starting with 'job_[number]' in the given directory."""
    if not root_dir.exists():
        print(f"⚠️ Directory not found: {root_dir}")
        return

    for folder in root_dir.glob(f"{prefix}*"):
        if folder.is_dir() and folder.name.startswith(prefix):
            try:
                shutil.rmtree(folder)
                print(f"🔥 Deleted job folder: {folder}")
            except Exception as e:
                print(f"❌ Failed to delete {folder}: {e}")

def clean_json_file(file_path: Path) -> None:
    """Empty a JSON file (reset to empty list/dict)."""
    if not file_path.exists():
        print(f"⚠️ JSON file not found: {file_path}")
        return

    try:
        with open(file_path, "w") as f:
            if "status" in file_path.name.lower():
                json.dump({}, f)  # Reset status files to {}
            else:
                json.dump([], f)  # Reset data files to []
        print(f"🧹 Cleaned JSON: {file_path}")
    except Exception as e:
        print(f"❌ Failed to clean {file_path}: {e}")

# ===== Main Execution =====
if __name__ == "__main__":
    print("🚀 Starting MASTER CLEANER...")

    # 1. Clean specified directories (delete contents)
    for path in PATHS_TO_CLEAN:
        print(f"\n🔍 Cleaning directory: {path}")
        clean_directory(path)

    # 2. Delete 'job_[number]' folders in admin_jobs
    print(f"\n🔍 Deleting job folders in: {ADMIN_JOBS_DIR}")
    delete_job_folders(ADMIN_JOBS_DIR, JOB_FOLDER_PREFIX)

    # 3. Clean JSON files (empty them)
    print("\n🔍 Cleaning JSON files...")
    for json_file in JSON_FILES_TO_CLEAN:
        clean_json_file(json_file)

    print("\n✨ MASTER CLEANER finished! ✨")