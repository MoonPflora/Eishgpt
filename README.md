# Eishgpt - AI-Powered Job Scraper and Posting System

## System Overview

Eishgpt is a comprehensive job management system that:
- Scrapes job postings from various channels
- Normalizes and transforms structured job data
- Posts jobs to preferred channels
- Handles user submissions with admin validation
- Includes scheduled cleanup and self-maintenance
- Features an AI-powered pipeline
- Has a premium subscription system (disabled by default)

## System Flowchart
+---------------------------+
|         SCHEDULER         |
+---------------------------+
  4‑hour Pipeline Execution
       │
       ▼
  Execute scheduled scripts
       │
       ▼
  telegram_scraper.py
       │
       ▼
  scrape_cleaner.py
       │
       ▼
  eishgpt_job_processor.py
       │
       ▼
  ocr.py
       │
       ▼
  image_processor.py
       │
       ▼
  admin_job_loader.py
       │
       ▼
  job_poster.py
       │
       ▼
  admin_poster.py
       │
       ▼
  poster.py
       │
       ▼
  master_cleaner.py

+---------------------------+
|      BOT CAPABILITIES     |
+---------------------------+
  User Commands
    ├── /start – Welcome
    ├── /search – Job search
    ├── /submit – Job submission
    └── /premium – Subscription

  Admin Commands
    ├── /admin – Panel access
    ├── /validate – Job validation
    └── /stats – System stats

  Automated Processes
    ├── CAPTCHA verification
    ├── Job approval workflow
    └── Premium subscription management

+---------------------------+
|        DATA FLOW          |
+---------------------------+
  scraped_jobs.json  ──Process──►  eishgpt_job_processor.py
  processed_jobs.json ──Post───►  job_poster.py
  user_submissions.json ──Load──►  admin_job_loader.py
  processed.json ──Post───────►  admin_poster.py

+---------------------------+
|     SYSTEM COMPONENTS     |
+---------------------------+
  telegram_scraper.py  ──Scrapes──►  Channels
  eishgpt_job_processor.py ──Normalizes──►  Jobs
  job_poster.py  ──Posts──►  Channels
  master_cleaner.py  ──Cleans──►  Data
  payment_handler.py  ──Processes──►  Payments

+---------------------------+
|   EXTERNAL INTEGRATIONS   |
+---------------------------+
  Telegram API  ──Interacts──►  Bot
  FastPay  ──Processes──►  Payments
  SQLite  ──Stores──►  Data
## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your values
3. Install dependencies: `pip install -r Requirements.txt`
4. Run: `python Bot_main.py`

## Environment Variables

| Variable | Description |
|----------|-------------|
| BOT_TOKEN | Your Telegram bot token |
| ADMIN | Admin user ID |
| ADMIN_CODE | Admin verification code |
| PAYMENT_PHONE_NUMBER | Payment phone number |
| PAYMENT_IMAGE_PATH | Path to payment image |
| FREE_USER_DB_PATH | Path to free user database |
| PREMIUM_USER_DB_PATH | Path to premium user database |
| LOG_FILE | Path to log file |
| CHANNEL_ID | Target channel ID for job postings |
| SCRAPE_INTERVAL | Interval for job scraping (in minutes) |
| MAX_JOB_AGE | Maximum age of jobs to process (in days) |

## Security

Never commit `.env` files or sensitive data. All credentials must be loaded from environment variables.

## Features

### Core Functionality
- Job scraping from multiple channels (every 4 hours)
- Data normalization and transformation
- AI-powered job processing pipeline
- Scheduled job cleanup and maintenance

### User Features
- Job posting with CAPTCHA verification
- Job searching with filters
- User submission system with admin validation
- Premium subscription system (disabled by default)

### Admin Features
- Admin panel for system management
- Job validation and approval workflow
- System monitoring and maintenance tools

## Dependencies

- Python 3.7+
- telebot
- python-dotenv
- sqlite3
- BeautifulSoup (for scraping)
- requests (for HTTP requests)
- schedule (for scheduled tasks)
- python-crontab (for cron job management)

## Configuration

The system can be configured through environment variables to:
- Set scraping intervals
- Define target channels
- Configure job processing rules
- Manage subscription settings

## License

AGPL-3.0 License

Copyright (c) 2023 MoonPflora

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
