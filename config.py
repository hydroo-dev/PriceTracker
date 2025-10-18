# config.py - Configuration Settings

# ================================
# TELEGRAM BOT SETTINGS
# ================================
# Get bot token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN = "8494042393:AAHGzXMWDJ3Jo5-afpjETYmWyKh0hkJJCYg"

# Get chat ID from @userinfobot on Telegram
# Or visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
# For single user: TELEGRAM_CHAT_ID = "8216346390"
# For multiple users (dono ko notification jayegi):
TELEGRAM_CHAT_ID = [8216346390, 7764354682]  # Pushpa & Hydroo

# ================================
# TRACKING SETTINGS
# ================================
# How often to check prices (in seconds)
CHECK_INTERVAL = 6000  # 100 minutes (original: 3600 = 1 hour)

# ================================
# DATABASE SETTINGS
# ================================
# JSON file to store tracked products
DATABASE_FILE = "tracked_products.json"

# ================================
# SCRAPING SETTINGS
# ================================
# Delay between requests (in seconds) to avoid blocking
REQUEST_DELAY = 3

# Maximum retries for failed requests
MAX_RETRIES = 3