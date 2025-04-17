from discord.ext import commands
import discord

# Define intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.presences = False
intents.typing = False

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)
