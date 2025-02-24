import discord
from discord.ext import commands
import asyncio
from config import Config
from utils.logger import setup_logger
from webserver import keep_alive

logger = setup_logger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$$", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")
    try:
        await bot.load_extension("cogs.lottery")
        logger.info("Lottery cog loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load lottery cog: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.send(f"⌛ Please wait {error.retry_after:.1f}s before using this command again.")
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Please check command usage.")
    else:
        logger.error(f"Unhandled error: {str(error)}")
        await ctx.send("❌ An error occurred while processing your command.")

async def run_bot():
    retries = 0
    max_retries = 5
    retry_delay = 5  # seconds

    while retries < max_retries:
        try:
            async with bot:
                await bot.start(Config.TOKEN)
        except discord.ConnectionClosed:
            retries += 1
            logger.warning(f"Connection closed. Attempting reconnection {retries}/{max_retries}")
            await asyncio.sleep(retry_delay)
        except discord.LoginFailure:
            logger.error("Invalid token provided")
            return
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            retries += 1
            await asyncio.sleep(retry_delay)
        else:
            retries = 0  # Reset retries on successful connection

    logger.critical("Max reconnection attempts reached. Bot shutting down.")

if __name__ == "__main__":
    if not Config.TOKEN:
        logger.error("Discord token not found in environment variables")
        exit(1)

    # Start the webserver
    keep_alive()

    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")