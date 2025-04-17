from discord.ext import commands
import discord
import logging
import asyncio
from health_check import start_health_check_server
from game.game_manager import bot  # Import the bot instance from game_manager.py

# Set up logging
logging.basicConfig(level=logging.INFO)
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)  # Suppress logs below WARNING from discord library

@bot.event
async def on_ready():
    try:
        logging.info(f"Logged in as {bot.user}")
        logging.info(f"Registered Commands: {[command.name for command in bot.commands]}")  # Log registered commands
    except Exception as e:
        logging.error(f"Error in on_ready: {e}")

async def main():
    # Start health check server first
    runner, site = await start_health_check_server()
    
    # Then start the bot
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set.")
    await bot.start(TOKEN)

if __name__ == "__main__":
    import os
    # Run both services in the same event loop
    asyncio.run(main())
