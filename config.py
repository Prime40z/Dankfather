import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv('DISCORD_TOKEN')
    ENTRY_THRESHOLD = 10_000  # 1 entry per 10,000 Dank Memer coins donated
    TAX_RATE = 0.25  # 25% tax
    ADMIN_ROLES = os.getenv('ADMIN_ROLES', 'Admin,Moderator').split(',')
    LOTTERY_CHANNEL_ID = int(os.getenv('LOTTERY_CHANNEL_ID', '0'))  # Default to 0 if not set
    DANK_MEMER_ID = 270904126974590976  # Dank Memer's bot ID
    DB_PATH = "lottery.db"