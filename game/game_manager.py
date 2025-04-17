from discord.ext import commands
import discord
import logging
from game.night_actions import NightActions
from game.roles import ROLES
import json

# Set up logging
logging.basicConfig(level=logging.INFO)

class GameManager:
    def __init__(self, bot):
        self.bot = bot
        self.players = []  # List of Player objects
        self.night_actions = NightActions(bot, self)

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
        await self.night_actions.start_night_phase()

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


# Initialize bot with only necessary intents
intents = discord.Intents.default()
intents.messages = True  # Enable message-related events
intents.guilds = True  # Enable guild-related events
intents.message_content = True  # Enable Message Content Intent
intents.presences = False  # Disable presence updates
intents.typing = False  # Disable typing events

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


@bot.event
async def on_socket_event_type(event_data):
    """Filter and log only relevant events."""
    try:
        # Parse event_data if it's a string
        if isinstance(event_data, str):
            event_data = json.loads(event_data)

        # Process the event if it's now a dictionary
        if "t" in event_data and event_data["t"] in ["MESSAGE_CREATE", "GUILD_CREATE"]:
            logging.debug(f"Relevant WebSocket Event: {event_data}")
    except Exception as e:
        logging.error(f"Error processing socket event: {e}")


# Run the bot
if __name__ == "__main__":
    import os

    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN environment variable is not set.")
    bot.run(TOKEN)
