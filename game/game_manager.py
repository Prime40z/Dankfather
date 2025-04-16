from discord.ext import commands
from game.roles import RoleFactory
from game.phases import DayPhase, NightPhase

class GameManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # Dictionary to store games by channel ID

    @commands.command()
    async def create_game(self, ctx):
        """Creates a new game in the current channel."""
        if ctx.channel.id in self.games:
            await ctx.send("A game is already active in this channel.")
        else:
            self.games[ctx.channel.id] = Game(ctx.channel)
            await ctx.send("Game created! Players can now join with `!join`.")

    @commands.command()
    async def join(self, ctx):
        """Allows a player to join the game."""
        game = self.games.get(ctx.channel.id)
        if game:
            if ctx.author in game.players:
                await ctx.send(f"{ctx.author.name}, you are already in the game!")
            else:
                game.add_player(ctx.author)
                await ctx.send(f"{ctx.author.name} joined the game!")
        else:
            await ctx.send("No active game in this channel.")

    @commands.command()
    async def start(self, ctx):
        """Starts the game."""
        game = self.games.get(ctx.channel.id)
        if game:
            if len(game.players) < 4:
                await ctx.send("At least 4 players are needed to start the game.")
            else:
                await game.start()
        else:
            await ctx.send("No active game in this channel.")

    @commands.command()
    async def vote(self, ctx, voted_player: commands.MemberConverter):
        """Casts a vote during the day phase."""
        game = self.games.get(ctx.channel.id)
        if game and isinstance(game.phase, DayPhase):
            response = await game.phase.cast_vote(ctx.author, voted_player)
            await ctx.send(response)
        else:
            await ctx.send("You cannot vote right now. Voting is only allowed during the day phase.")

    @commands.command()
    async def tally(self, ctx):
        """Tally votes and proceed to the next phase."""
        game = self.games.get(ctx.channel.id)
        if game and isinstance(game.phase, DayPhase):
            result = await game.phase.tally_votes()
            await ctx.send(result)
            game.end_day_phase()


class Game:
    def __init__(self, channel):
        self.channel = channel
        self.players = []
        self.phase = None
        self.roles = []

    def add_player(self, player):
        self.players.append(Player(player))

    async def start(self):
        self.assign_roles()
        self.phase = DayPhase(self.channel, self.players)
        await self.phase.start()

    def assign_roles(self):
        # Assign roles to players randomly
        from random import shuffle
        self.roles = list(RoleFactory.ROLES.keys())
        shuffle(self.roles)
        for i, player in enumerate(self.players):
            player.role = RoleFactory.create_role(self.roles[i])

    def end_day_phase(self):
        self.phase = NightPhase(self.channel, self.players)


class Player:
    def __init__(self, user):
        self.user = user
        self.role = None
        self.alive = True
