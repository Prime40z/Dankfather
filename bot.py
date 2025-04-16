import os
import asyncio
import logging
from aiohttp import web
import discord
from discord.ext import commands

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize intents for the bot
intents = discord.Intents.all()

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")

# HTTP health check handler
async def health_check(request):
    logging.info("Received health check request")
    return web.Response(text="OK")

# Function to start the aiohttp server
async def start_aiohttp_server():
    # Logging to confirm the server starts
    logging.info("Starting aiohttp health check server...")
    app = web.Application()
    app.router.add_get("/", health_check)  # Route for health check

    # Run the aiohttp server on port 8080
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)
    await site.start()
    logging.info("Health check server is running on http://0.0.0.0:8080")

# Main function to run both the bot and the health check server
async def main():
    # Start the aiohttp server in the background
    await start_aiohttp_server()

    # Fetch the bot token from environment variables
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN environment variable is not set.")
    
    # Run the Discord bot
    await bot.start(token)

# Run the main function using asyncio
if __name__ == "__main__":
    asyncio.run(main())
