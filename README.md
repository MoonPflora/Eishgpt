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

```
Eishgpt System Flowchart

1. [Scheduler]
   - Daily Scraping: 03:00 AM
     - Scrape job postings from configured channels
     - Save raw data to Scraped_data/scraped_jobs.json
   - Weekly Cleanup: Sunday 02:00 AM
     - Remove jobs older than MAX_JOB_AGE
     - Clean Scraped_data/junk.json
     - Update Admin_jobs/ocr_status.json
   - Monthly Maintenance: 1st of month 01:00 AM
     - Backup databases
     - Run premium_id_cleaner.py
     - Update Processed_data/posted_jobs.json.backup

2. [Bot Capabilities]
   - User Commands:
     - /start - Welcome message
     - /search - Job search interface
     - /submit - Job submission form
     - /premium - Subscription options
   - Admin Commands:
     - /admin - Admin panel access
     - /validate - Job validation interface
     - /stats - System statistics
   - Automated Processes:
     - CAPTCHA verification for submissions
     - Job approval workflow
     - Premium subscription management

3. [Data Flow]
   - Scraped_data/scraped_jobs.json -> Eichgpt_job_processor.py
   - Processed_data/processed_jobs.json -> Job_poster.py
   - User_data/user_submissions.json -> Admin_job_loader.py
   - Admin_jobs/processed.json -> Admin_poster.py

4. [System Components]
   - Telegram_scraper.py - Handles channel scraping
   - Eichgpt_job_processor.py - Normalizes and processes jobs
   - Job_poster.py - Posts approved jobs to channels
   - Master_cleaner.py - Manages scheduled cleanup
   - Payment_handler.py - Processes premium subscriptions

5. [External Integrations]
   - Telegram API - For bot interactions
   - FastPay - For payment processing
   - SQLite - For database storage
```

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
- Job scraping from multiple channels
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