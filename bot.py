"""
Bot initialization and setup file for the Mafia Discord bot.
"""
import os
import logging
import discord
from discord.ext import commands
import asyncio

from config import PREFIX, DESCRIPTION

# Configure logging
logger = logging.getLogger('mafia_bot')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

class MafiaBot(commands.Bot):
    """Main bot class for the Mafia game."""
    
    def __init__(self):
        """Initialize the bot with necessary intents and command prefix."""
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True  # Needed to read message content
        
        # Note: We're disabling privileged intents for now
        # If these are needed later, they need to be enabled in the Discord Developer Portal
        # intents.members = True  # This is a privileged intent
        
        # Initialize the bot
        super().__init__(
            command_prefix=PREFIX,
            description=DESCRIPTION,
            intents=intents,
            case_insensitive=True
        )
        
        # Dictionary to track active games by channel ID
        self.active_games = {}
        
    async def setup_hook(self):
        """Load all cogs when the bot starts up."""
        await self.load_extension('cogs.game_commands')
        logger.info("Loaded game commands cog")
        
    async def on_ready(self):
        """Event triggered when the bot is ready."""
        logger.info(f'Logged in as {self.user.name} (ID: {self.user.id})')
        logger.info(f'Connected to {len(self.guilds)} guilds')
        logger.info(f'Bot is ready for use!')
        
        # Set activity to show help command
        await self.change_presence(activity=discord.Game(name=f"{PREFIX}mafia help"))
        
        # Register all guilds in the database
        try:
            from utils.db_utils import register_guild_if_new
            from main import app
            
            # Using app context to work with the database
            with app.app_context():
                for guild in self.guilds:
                    register_guild_if_new(guild)
                logger.info("Registered all guilds in the database")
        except Exception as e:
            logger.error(f"Error registering guilds in database: {e}")
        
    async def on_command_error(self, ctx, error):
        """Global error handler for command errors."""
        if isinstance(error, commands.CommandNotFound):
            # Ignore command not found errors
            return
            
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ Missing required argument: {error.param.name}. Use `{PREFIX}help mafia` for help.")
            return
            
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"⚠️ Invalid argument. Use `{PREFIX}help mafia` for help.")
            return
            
        # Log unexpected errors
        logger.error(f'Unhandled error in command {ctx.command}: {error}')
        await ctx.send(f"❌ An unexpected error occurred. Please try again later.")