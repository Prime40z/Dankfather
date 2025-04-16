import os
import asyncio
from aiohttp import web
import discord
from discord.ext import commands

# Initialize intents for the bot
intents = discord.Intents.all()

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# HTTP health check handler
async def health_check(request):
    return web.Response(text="OK")

# Function to run the aiohttp server
def run_aiohttp_server():
    app = web.Application()
    app.router.add_get("/", health_check)

    # Run the aiohttp web server
    web.run_app(app, host="0.0.0.0", port=8000)

# Fetch the bot token from environment variables
token = os.getenv("BOT_TOKEN")
if not token:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is not set.")

# Run the aiohttp server in a separate asyncio task
loop = asyncio.get_event_loop()
loop.create_task(asyncio.to_thread(run_aiohttp_server))

# Run the bot
bot.run(token)
