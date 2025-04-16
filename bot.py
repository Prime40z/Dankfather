import os
import discord
from discord.ext import commands
from game.game_manager import GameManager
from utils.database import setup_database
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Game Manager
game_manager = GameManager(bot)

# Database setup
DB_FILE = "mafia_game.db"
setup_database(DB_FILE)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")

# Add the GameManager as a bot cog
bot.add_cog(game_manager)

# Run the bot
if __name__ == "__main__":
    bot.run(os.getenv("BOT_TOKEN"))
