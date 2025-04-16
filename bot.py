import os
import discord
from discord.ext import commands
from game.game_manager import GameManager

# Initialize intents for the bot
intents = discord.Intents.all()

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize the game manager
game_manager = GameManager(bot)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def start(ctx):
    """Command to start the game."""
    await game_manager.start_game()

# Fetch the token from the environment variable
token = os.getenv("BOT_TOKEN")
if not token:
    raise ValueError("DISCORD_BOT_TOKEN environment variable not set.")

# Run the bot
bot.run(token)
