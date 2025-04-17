from discord.ext import commands
import discord
import logging
from health_check import start_health_check_server
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)  # Suppress logs below WARNING from discord library

# Configure intents
intents = discord.Intents.default()
intents.messages = True  # Enable message-related events
intents.guilds = True  # Enable guild-related events
intents.message_content = True  # Enable Message Content Intent to allow command processing
intents.members = False  # Disable member-related events (if not needed)
intents.presences = False  # Disable presence updates

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    """Simple ping command to test bot responsiveness."""
    await ctx.send("Pong!")

if __name__ == "__main__":
    import os

    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN environment variable is not set.")

    # Start health check server
    start_health_check_server()

    # Run the bot
    asyncio.run(bot.start(TOKEN))
