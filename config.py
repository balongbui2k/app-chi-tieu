# Telegram Expense Tracking Bot Configuration
import os

# Telegram Bot Token from @BotFather
# Set this in Render Environment Variables or use default for local testing
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# List of authorized User IDs
# Set AUTHORIZED_USER_IDS in environment as comma-separated values: "123,456,789"
user_ids_env = os.getenv("AUTHORIZED_USER_IDS", "12345678")
AUTHORIZED_USER_IDS = [int(uid.strip()) for uid in user_ids_env.split(",")]

# Default fallback to example if not set
WEB_APP_URL = os.getenv("WEB_APP_URL", "")

# Data storage settings
DATA_DIR = "data"

# Currency symbol
CURRENCY = "vnd"

# Monthly report day
REPORT_DAY = 5
