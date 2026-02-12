# Telegram Expense Tracking Bot Configuration
import os
import json

# Telegram Bot Token from @BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Authorized User IDs
user_ids_env = os.getenv("AUTHORIZED_USER_IDS", "12345678")
AUTHORIZED_USER_IDS = [int(uid.strip()) for uid in user_ids_env.split(",")]

# Web App URL (Disabled for now)
WEB_APP_URL = os.getenv("WEB_APP_URL", "")

# Currency symbol
CURRENCY = "vnd"

# Monthly report day
REPORT_DAY = 5

# --- Google Sheets Configuration ---
# File name of the Google Sheet you created
GOOGLE_SHEET_NAME = "Quản lý chi tiêu"

# Path to service account JSON (for local testing)
# For Render: we will load from GOOGLE_CREDENTIALS_JSON environment variable
GOOGLE_CREDENTIALS_PATH = "service_account.json" 

def get_google_credentials():
    """Get Google Cloud Credentials from Env Var or File."""
    env_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if env_creds:
        return json.loads(env_creds)
    
    if os.path.exists(GOOGLE_CREDENTIALS_PATH):
        return GOOGLE_CREDENTIALS_PATH
        
    return None
