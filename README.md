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

flowchart TD
    subgraph Scheduler
        A[4-hour Pipeline Execution] -->|Run every 4 hours| B[Execute scheduled scripts]
        B --> C[telegram_scraper.py]
        C --> D[scrape_cleaner.py]
        D --> E[eishgpt_job_processor.py]
        E --> F[ocr.py]
        F --> G[image_processor.py]
        G --> H[admin_job_loader.py]
        H --> I[job_poster.py]
        I --> J[admin_poster.py]
        J --> K[poster.py]
        K --> L[master_cleaner.py]
    end

    subgraph Bot Capabilities
        UserCmd[User Commands] --> StartCmd[/start - Welcome]
        UserCmd --> SearchCmd[/search - Job search]
        UserCmd --> SubmitCmd[/submit - Job submission]
        UserCmd --> PremiumCmd[/premium - Subscription]
        AdminCmds[Admin Commands] --> AdminPanel[/admin - Panel access]
        AdminCmds --> ValidateCmd[/validate - Job validation]
        AdminCmds --> StatsCmd[/stats - System stats]
        AutoProcesses[Automated Processes] --> Captcha[CAPTCHA verification]
        AutoProcesses --> JobApproval[Job approval workflow]
        AutoProcesses --> PremiumMgmt[Premium subscription management]
    end

    subgraph Data Flow
        T[scraped_jobs.json] -->|Process| U[eishgpt_job_processor.py]
        V[processed_jobs.json] -->|Post| W[job_poster.py]
        X[user_submissions.json] -->|Load| Y[admin_job_loader.py]
        Z[processed.json] -->|Post| AA[admin_poster.py]
    end

    subgraph System Components
        AB[telegram_scraper.py] -->|Scrapes| AC[Channels]
        AD[eishgpt_job_processor.py] -->|Normalizes| AE[Jobs]
        AF[job_poster.py] -->|Posts| AG[Channels]
        AH[master_cleaner.py] -->|Cleans| AI[Data]
        AJ[payment_handler.py] -->|Processes| AK[Payments]
    end

    subgraph External Integrations
        AL[Telegram API] -->|Interacts| AM[Bot]
        AN[FastPay] -->|Processes| AO[Payments]
        AP[SQLite] -->|Stores| AQ[Data]
    end

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
