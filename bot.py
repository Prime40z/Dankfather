from discord.ext import commands
import discord
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)  # Suppress logs below WARNING from discord library

class GameManager:
    def __init__(self, bot):
        self.bot = bot
        self.players = []  # List of Player objects

    async def start_game(self):
        """Initialize and start the game."""
        self.assign_roles()
        await self.start_night_phase()

    def assign_roles(self):
        """Assign roles to players."""
        from random import shuffle
        shuffle(ROLES)
        for player, role in zip(self.players, ROLES):
            player.role = role

    async def start_night_phase(self):
        """Start the night phase."""
        # Logic for night phase (placeholder)
        pass

    def get_alive_players(self):
        """Return a list of all alive players."""
        return [player for player in self.players if player.alive]


class Player:
    def __init__(self, user):
        self.user = user
        self.role = None
        self.alive = True

    def __str__(self):
        return self.user.name


# Configure intents
intents = discord.Intents.default()
intents.messages = True  # Enable message-related events
intents.guilds = True  # Enable guild-related events
intents.members = False  # Disable member-related events (if not needed)
intents.presences = False  # Disable presence updates

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)
game_manager = GameManager(bot)


@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")


@bot.command()
async def start(ctx):
    """Command to start the game."""
    logging.info("Start command invoked")
    if len(game_manager.players) < 2:
        await ctx.send("You need at least 2 players to start the game!")
        return
    await game_manager.start_game()
    await ctx.send("Game started!")


@bot.command()
async def join(ctx):
    """Command to join the game."""
    logging.info(f"Join command invoked by {ctx.author}")
    if any(player.user == ctx.author for player in game_manager.players):
        await ctx.send(f"{ctx.author.mention}, you are already in the game.")
    else:
        game_manager.players.append(Player(ctx.author))
        await ctx.send(f"{ctx.author.mention} has joined the game!")


@bot.command()
async def leave(ctx):
    """Command to leave the game."""
    logging.info(f"Leave command invoked by {ctx.author}")
    for player in game_manager.players:
        if player.user == ctx.author:
            game_manager.players.remove(player)
            await ctx.send(f"{ctx.author.mention} has left the game!")
            return
    await ctx.send(f"{ctx.author.mention}, you are not in the game.")


@bot.command()
async def kick(ctx, member: discord.Member):
    """Command to kick a player from the game."""
    logging.info(f"Kick command invoked by {ctx.author} for {member}")
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Only an administrator can kick players.")
        return

    for player in game_manager.players:
        if player.user == member:
            game_manager.players.remove(player)
            await ctx.send(f"{member.mention} has been kicked from the game!")
            return
    await ctx.send(f"{member.mention} is not in the game.")


@bot.command()
async def party(ctx):
    """Command to list all players in the game."""
    logging.info("Party command invoked")
    if not game_manager.players:
        await ctx.send("No players have joined yet!")
    else:
        members = ", ".join([player.user.mention for player in game_manager.players])
        await ctx.send(f"Current players: {members}")


@bot.command()
async def reset(ctx):
    """Command to reset the game."""
    logging.info(f"Reset command invoked by {ctx.author}")
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Only an administrator can reset the game.")
        return

    game_manager.players = []
    await ctx.send("The game has been reset. All players have been removed.")


# Run the bot
if __name__ == "__main__":
    import os

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN environment variable is not set.")
    bot.run(TOKEN)
