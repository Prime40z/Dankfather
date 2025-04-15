import os
import discord
from discord.ext import commands
import random
import sqlite3

# Log bot startup
print("Bot is starting...")

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
    "game_mode": "Classic",
    "day_phase": False,  # False = Night, True = Day
    "votes": {}
}

# Available roles for the game
available_roles = [
    "Villager", "Mafia", "Doctor", "Sheriff", "Jailor", "Survivor", "Serial Killer",
    # Add more roles as needed
]

# Bot events and commands
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
    game_state["roles"] = random.sample(available_roles, len(game_state["players"]))
    game_state["day_phase"] = False  # Start with night phase

    for player, role in zip(game_state["players"], game_state["roles"]):
        try:
            await player.send(f"Your role is: {role}")
        except discord.Forbidden:
            await ctx.send(f"Unable to send DM to {player.mention}. Make sure your DMs are open.")
        except Exception as e:
            await ctx.send(f"An error occurred while assigning a role to {player.mention}: {str(e)}")

    await ctx.send(f"The game has started in {game_state['game_mode']} mode! Check your DMs for your role.")
    await ctx.send("It is now Night. All players with night actions, please DM the bot your actions!")

@bot.command()
async def end(ctx):
    """End the current Mafia game."""
    if game_state["is_active"]:
        game_state["is_active"] = False
        game_state["players"] = []
        game_state["roles"] = []
        game_state["votes"] = {}
        await ctx.send("The game has been ended.")
    else:
        await ctx.send("No game is currently active.")

@bot.command()
async def roles(ctx):
    """List all available roles."""
    try:
        await ctx.send("Available roles: " + ", ".join(available_roles))
    except Exception as e:
        await ctx.send(f"An error occurred while listing roles: {str(e)}")

@bot.command()
async def vote(ctx, target: discord.Member):
    """Vote to eliminate a player during the day phase."""
    if not game_state["is_active"]:
        await ctx.send("No active game to vote in.")
        return

    if not game_state["day_phase"]:
        await ctx.send("You can only vote during the day phase.")
        return

    if target not in game_state["players"]:
        await ctx.send(f"{target.mention} is not a valid player.")
        return

    game_state["votes"][ctx.author] = target
    await ctx.send(f"{ctx.author.mention} has voted to eliminate {target.mention}.")

@bot.command()
async def stats(ctx, member: discord.Member = None):
    """Show stats for a player."""
    member = member or ctx.author
    try:
        stats = get_stats(str(member.id))
        await ctx.send(f"{member.mention}'s Stats:\nGames Played: {stats[0]}\nGames Won: {stats[1]}")
    except Exception as e:
        await ctx.send(f"An error occurred while retrieving stats: {str(e)}")

@bot.command()
async def update_stats(ctx, winner: discord.Member):
    """Update stats after a game."""
    if not game_state["is_active"]:
        await ctx.send("No active game to update stats for.")
        return

    try:
        for player in game_state["players"]:
            update_stat(str(player.id), "games_played")

        update_stat(str(winner.id), "games_won")
        await ctx.send(f"Stats updated! {winner.mention} is the winner!")
    except Exception as e:
        await ctx.send(f"An error occurred while updating stats: {str(e)}")

# Run the bot
try:
    setup_database()
    bot.run(os.getenv("BOT_TOKEN"))
except Exception as e:
    print(f"An error occurred while running the bot: {str(e)}")
