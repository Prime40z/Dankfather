from discord.ext import commands
import discord
from game.night_actions import NightActions
from game.roles import ROLES


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


# Example player class
class Player:
    def __init__(self, user):
        self.user = user
        self.role = None
        self.alive = True

    def __str__(self):
        return self.user.name


# Initialize bot and game manager
intents = discord.Intents.default()  # Use `discord.Intents.all()` if your bot needs all intents
intents.messages = True  # Enable specific intents (e.g., message handling)
intents.guilds = True
intents.members = True  # Enable member-related events (important for some bots)

bot = commands.Bot(command_prefix="!", intents=intents)
game_manager = GameManager(bot)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def start(ctx):
    """Command to start the game."""
    await game_manager.start_game()
