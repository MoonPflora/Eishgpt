import subprocess
import time
import os
import sys
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import threading
import signal

# --- Config ---
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Script execution order (runs every 4 hours)
SCHEDULED_SCRIPTS = [
    "scraper/telegram_scraper.py",
    "scrape_cleaner.py",
    "eishgpt_job_processor.py",
    "ocr.py",
    "image_processor.py",
    "admin_job_loader.py",
    "job_poster.py",
    "admin_poster.py",
    "poster.py",
    "master_cleaner.py"  # Cleanup always last
]
MAX_RETRIES = 4
RETRY_DELAY = 30  # seconds
INTER_SCRIPT_DELAY = 60  # seconds between scripts

# --- Minimal Logging ---
logging.basicConfig(
    handlers=[
        RotatingFileHandler(
            LOG_DIR / "runner.log",
            maxBytes=1_000_000,
            backupCount=2,
            delay=True  # Lazy file creation
        ),
        logging.StreamHandler()
    ],
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# --- Utilities ---
def clear_console():
    """Cross-platform console clearing."""
    os.system("cls" if sys.platform == "win32" else "clear")

def run_script(script_path: Path) -> bool:
    """Execute script with retries and minimal logging."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Executing: {script_path.name} (Attempt {attempt}/{MAX_RETRIES})")
            result = subprocess.run(
                [sys.executable, str(script_path)],
                check=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                logger.debug(f"Output: {result.stdout[:200]}...")  # Truncate long outputs
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"Attempt {attempt} failed: {e.stderr.strip() or 'Unknown error'}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    logger.error(f"Max retries reached for {script_path.name}")
    return False

# --- Core Functions ---
def run_scheduled_tasks():
    """Execute scripts sequentially every 4 hours."""
    while True:
        logger.info("Starting scheduled task cycle")
        for script in SCHEDULED_SCRIPTS:
            script_path = BASE_DIR / script
            if not script_path.exists():
                logger.error(f"Script missing: {script_path}")
                continue
            
            if run_script(script_path):
                logger.info(f"Completed: {script_path.name}")
            time.sleep(INTER_SCRIPT_DELAY)
        
        logger.info("Task cycle completed. Next run in 4 hours")
        time.sleep(4 * 3600 - (INTER_SCRIPT_DELAY * len(SCHEDULED_SCRIPTS)))

def run_bot():
    """Maintain bot_main.py 24/7 with daily restarts."""
    while True:
        try:
            logger.info("Initializing bot_main.py")
            bot_process = subprocess.Popen(
                [sys.executable, str(BASE_DIR / "bot_main.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Stream output to logs
            def stream_output(stream, log_func):
                for line in iter(stream.readline, ''):
                    log_func(line.strip())

            threading.Thread(
                target=stream_output,
                args=(bot_process.stdout, logger.info),
                daemon=True
            ).start()
            threading.Thread(
                target=stream_output,
                args=(bot_process.stderr, logger.error),
                daemon=True
            ).start()

            # Monitor for 24 hours
            start_time = time.time()
            while time.time() - start_time < 86400:  # 24 hours
                if bot_process.poll() is not None:
                    logger.warning("Bot process terminated unexpectedly")
                    break
                time.sleep(60)

            bot_process.terminate()
            clear_console()
            logger.info("Bot restarting after 24-hour cycle")

        except Exception as e:
            logger.critical(f"Bot supervisor error: {str(e)}")
            time.sleep(60)

def shutdown_handler(signum, frame):
    """Handle graceful shutdown."""
    logger.info("Shutdown signal received")
    sys.exit(0)

# --- Main Execution ---
if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Start components
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=run_scheduled_tasks, daemon=True).start()

    # Keep alive
    while True:
        time.sleep(3600)