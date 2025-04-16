import os
import discord
from discord.ext import commands
from game.game_manager import GameManager
from aiohttp import web
import asyncio

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

# Minimal HTTP server for health checks
async def handle_health_check(request):
    print("Health check request received")
    return web.Response(text="OK")

async def run_http_server():
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    print("HTTP server is running on http://0.0.0.0:8000")
    await site.start()

# Run the bot and HTTP server
loop = asyncio.get_event_loop()
loop.create_task(run_http_server())  # Start the HTTP server
bot.run(token)  # Start the Discord bot
