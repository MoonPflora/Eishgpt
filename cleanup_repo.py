import os
import shutil

def cleanup_repository():
    # Remove sensitive data files
    sensitive_files = [
        'Mistral_api.txt',
        'Telegram_api.txt',
        'Telegram_bot_api.txt',
        'Bot.log',
        'Job_poster.log',
        'Job_poster.lock',
        'Free_user_id.db',
        'Payment.jpg'
    ]

    for file in sensitive_files:
        try:
            os.remove(file)
            print(f"Removed sensitive file: {file}")
        except FileNotFoundError:
            print(f"File not found: {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")

    # Remove __pycache__ directories
    for root, dirs, files in os.walk('.'):
        for dir in dirs:
            if dir == '__pycache__':
                pycache_path = os.path.join(root, dir)
                try:
                    shutil.rmtree(pycache_path)
                    print(f"Removed __pycache__ directory: {pycache_path}")
                except Exception as e:
                    print(f"Error removing {pycache_path}: {e}")

    # Remove collected data files
    data_files = [
        'Scraped_data/scraped_jobs.json',
        'Scraped_data/cleaned_scraped_jobs.json',
        'Scraped_data/junk.json',
        'Scraped_data/last_scraped.json',
        'Processed_data/processed_jobs.json',
        'Processed_data/posted_jobs.json',
        'Processed_data/posted_jobs.json.backup_1751319053',
        'Processed_data/processed_jobs.json.backup_1751319053',
        'Admin_jobs/ocr_status.json',
        'Admin_jobs/processed.json',
        'User_data/search_history.json',
        'User_data/user_submissions.json'
    ]

    for file in data_files:
        try:
            os.remove(file)
            print(f"Removed data file: {file}")
        except FileNotFoundError:
            print(f"File not found: {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")

    # Remove images and other media files
    image_dirs = [
        'User_data/images',
        'Scraped_data/images',
        'Linkedin_data/images'
    ]

    for dir in image_dirs:
        try:
            shutil.rmtree(dir)
            print(f"Removed image directory: {dir}")
        except Exception as e:
            print(f"Error removing {dir}: {e}")

    # Remove session files
    session_files = [
        'Scraper/anon.session',
        'Scraper/session_name.session',
        'Scraper/telegram_scraper_session.session'
    ]

    for file in session_files:
        try:
            os.remove(file)
            print(f"Removed session file: {file}")
        except Exception as e:
            print(f"Error removing {file}: {e}")

    print("Repository cleanup completed.")

if __name__ == "__main__":
    cleanup_repository()