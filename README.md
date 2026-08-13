# Eishgpt Bot

Telegram bot for job posting and management.

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

## Security

Never commit `.env` files or sensitive data. All credentials must be loaded from environment variables.

## Features

- Job posting with CAPTCHA verification
- Job searching with filters
- Premium subscription system
- Admin panel for management

## Dependencies

- Python 3.7+
- telebot
- python-dotenv
- sqlite3

## License

MIT