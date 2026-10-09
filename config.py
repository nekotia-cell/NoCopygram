import pytz
import os

# Bot settings
BOT_TOKEN = 'токен тута'
ADMIN_ID = 6639427571

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), 'players.db')

# Game settings
GAME_TIMEOUT = 120  # 2 minutes in seconds
SPAM_DELAY = 3

# VIP settings
VIP_PRICE = 500
VIP_DURATION = 69 * 24 * 3600  # 69 days in seconds
CROWN_EMOJI = "👑 VIP | "

# Clan settings
CLAN_CREATION_COST = 50000
CLAN_NAME_MAX_LENGTH = 25
CLAN_MIN_DEPOSIT = 10000
CLAN_MAX_MEMBERS = 40
CLAN_RATING_UPDATE_INTERVAL = 3 * 24 * 3600  # 3 days

# Other
LOG_LENGTH = 10
TIMEZONE = pytz.timezone('Europe/Moscow')
