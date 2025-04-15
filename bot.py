import discord
from discord.ext import commands
import random
import sqlite3
import os

# Initialize the bot with the specified prefix
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="mm.", intents=intents)

# Database setup for persistent storage
DB_FILE = "player_stats.db"

def setup_database():
    """Create the database and tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            user_id TEXT PRIMARY KEY,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def update_stat(user_id, column):
    """Update a specific stat for a user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO stats (user_id, {column})
        VALUES (?, 1)
        ON CONFLICT(user_id) DO UPDATE SET {column} = {column} + 1
    """, (user_id,))
    conn.commit()
    conn.close()

def get_stats(user_id):
    """Retrieve stats for a specific user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT games_played, games_won FROM stats WHERE user_id = ?", (user_id,))
    stats = cursor.fetchone()
    conn.close()
    return stats if stats else (0, 0)

# Game state
game_state = {
    "players": [],
    "roles": [],
    "is_active": False,
    "game_mode": "Classic"
}

# Available roles including the new ones
available_roles = [
    "Villager", "Mafia", "Doctor", "Sheriff", "Jailor", "Survivor", "Serial Killer"
]

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.command()
async def join(ctx):
    """Join the Mafia game."""
    if ctx.author not in game_state["players"]:
        game_state["players"].append(ctx.author)
        await ctx.send(f"{ctx.author.mention} has joined the game!")
    else:
        await ctx.send(f"{ctx.author.mention}, you have already joined the game!")

@bot.command()
async def leave(ctx):
    """Leave the Mafia game."""
    if ctx.author in game_state["players"]:
        game_state["players"].remove(ctx.author)
        await ctx.send(f"{ctx.author.mention} has left the game.")
    else:
        await ctx.send(f"{ctx.author.mention}, you are not in the game.")

@bot.command()
async def start(ctx):
    """Start the Mafia game."""
    if len(game_state["players"]) < 5:
        await ctx.send("You need at least 5 players to start the game.")
        return

    game_state["is_active"] = True
    game_state["roles"]
