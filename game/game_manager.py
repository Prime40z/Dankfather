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


class Player:
    def __init__(self, user):
        self.user = user
        self.role = None
        self.alive = True

    def __str__(self):
        return self.user.name


# Initialize bot and game manager
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
game_manager = GameManager(bot)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def start(ctx):
    """Command to start the game."""
    await game_manager.start_game()


# Add the new commands here
@bot.command()
async def join(ctx):
    """Command to join the game."""
    if game_manager.get_alive_players():
        for player in game_manager.get_alive_players():
            if player.user == ctx.author:
                await ctx.send(f"{ctx.author.mention}, you are already in the game.")
                return

    new_player = Player(ctx.author)
    game_manager.players.append(new_player)
    await ctx.send(f"{ctx.author.mention} has joined the game!")

@bot.command()
async def leave(ctx):
    """Command to leave the game."""
    for player in game_manager.players:
        if player.user == ctx.author:
            game_manager.players.remove(player)
            await ctx.send(f"{ctx.author.mention} has left the game!")
            return
    await ctx.send(f"{ctx.author.mention}, you are not in the game.")

@bot.command()
async def kick(ctx, member: discord.Member):
    """Command to kick a player from the game."""
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
    if not game_manager.players:
        await ctx.send("No players have joined the game yet!")
    else:
        player_list = ", ".join([player.user.mention for player in game_manager.players])
        await ctx.send(f"Current players: {player_list}")

@bot.command()
async def reset(ctx):
    """Command to reset the game."""
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
