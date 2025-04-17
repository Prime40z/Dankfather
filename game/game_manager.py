from discord.ext import commands
import discord
import logging
import asyncio  # Add asyncio for timers
from game.night_actions import NightActions  # Night phase logic
from game.roles import (
    ROLES, Mafia, Doctor, Detective, Villager, Jester, SerialKiller,
    Bodyguard, Spy, Witch, Arsonist, Mayor, Veteran, Escort, Consort,
    Framer, Forger, Executioner, Survivor, Amnesiac, Blackmailer,
    Disguiser, Godfather, Tracker, Lookout, Vigilante
)
from game.phases import NightPhase, DayPhase  # Phase logic
from game.win_conditions import WinConditions  # Win condition checks

# Set up logging
logging.basicConfig(level=logging.INFO)

class GameManager:
    def __init__(self, bot):
        self.bot = bot
        self.players = []  # List of Player objects
        self.night_actions = NightActions(bot, self)
        self.phase = None  # Represents the current phase
        self.win_conditions = WinConditions(self.players)

    async def start_game(self, channel):
        """Initialize and start the game."""
        try:
            logging.info("Game is starting...")
            self.assign_roles()

            # Notify players of their assigned roles
            for player in self.players:
                try:
                    await player.user.send(f"You have been assigned the role: {player.role}")
                    logging.info(f"Notified {player.user.name} of their role: {player.role}")
                except Exception as e:
                    logging.error(f"Could not notify {player.user.name} of their role. Error: {e}")

            logging.info("Roles have been assigned.")
            await self.start_night_phase(channel)
        except Exception as e:
            logging.error(f"Error during game start: {e}")

    def assign_roles(self):
        """Assign roles to players."""
        from random import shuffle

        # Define roles that must always appear in the game
        required_roles = [Godfather(), Doctor(), Detective()]  # Example of required roles
        if len(self.players) < len(required_roles):
            logging.warning("Not enough players to assign all required roles!")
            return

        # Shuffle the remaining roles
        remaining_roles = ROLES.copy()
        shuffle(remaining_roles)

        # Remove required roles from the remaining pool to avoid duplication
        for required_role in required_roles:
            remaining_roles = [role for role in remaining_roles if type(role) != type(required_role)]

        # Ensure required roles are assigned first
        for player, role in zip(self.players, required_roles):
            player.role = role
            logging.info(f"Assigned required role {role} to player {player.user.name}")

        # Assign the rest of the roles randomly
        for player, role in zip(self.players[len(required_roles):], remaining_roles):
            player.role = role
            logging.info(f"Assigned role {role} to player {player.user.name}")

    async def start_night_phase(self, channel):
        """Start the night phase with a timer."""
        try:
            logging.info("Starting night phase...")
            self.phase = NightPhase(channel, self.players)
            await self.phase.start()

            # Wait for the night phase duration (45 seconds)
            night_duration = 45
            logging.info(f"Night phase will last {night_duration} seconds.")
            await asyncio.sleep(night_duration)

            await self.night_actions.start_night_phase()
            await self.check_win_conditions(channel)

            # Automatically transition to the day phase
            await self.start_day_phase(channel)
        except Exception as e:
            logging.error(f"Error during night phase: {e}")

    async def start_day_phase(self, channel):
        """Start the day phase with a timer."""
        try:
            logging.info("Starting day phase...")
            self.phase = DayPhase(channel, self.players)
            await self.phase.start()

            # Day phase duration is 90 seconds
            day_duration = 90
            voting_menu_start = 25  # Voting menu appears in the last 25 seconds
            logging.info(f"Day phase will last {day_duration} seconds.")

            # Wait until voting menu appears
            await asyncio.sleep(day_duration - voting_menu_start)

            # Show voting menu
            logging.info("Opening voting menu.")
            await self.show_voting_menu(channel)

            # Wait for the remaining time
            await asyncio.sleep(voting_menu_start)

            # Tally votes and check win conditions
            await self.phase.tally_votes()
            await self.check_win_conditions(channel)

            # Automatically transition to the night phase
            await self.start_night_phase(channel)
        except Exception as e:
            logging.error(f"Error during day phase: {e}")

    async def show_voting_menu(self, channel):
        """Display a voting menu for players to place votes."""
        try:
            for player in self.players:
                if player.alive:
                    await channel.send(
                        f"{player.user.mention}, cast your vote using the `!vote @player` command!"
                    )
        except Exception as e:
            logging.error(f"Error displaying voting menu: {e}")

    async def check_win_conditions(self, channel):
        """Check and announce if any team has won."""
        result = self.win_conditions.check_win()
        if result:
            await channel.send(result)
            # Reset the game on win
            self.players = []
            logging.info("Game has ended. Players have been reset.")
        else:
            # Check if the Godfather is dead and promote a new one if needed
            await self.check_and_promote_godfather(channel)

    async def check_and_promote_godfather(self, channel):
        """Check if the Godfather is dead and promote a new one from Mafia-aligned roles."""
        godfather_dead = not any(player.alive and isinstance(player.role, Godfather) for player in self.players)
        if godfather_dead:
            # Find all alive Mafia-aligned players
            mafia_roles = (Mafia, Blackmailer, Consort, Framer)  # Add other Mafia roles if necessary
            alive_mafia_players = [player for player in self.players if player.alive and isinstance(player.role, mafia_roles)]

            if alive_mafia_players:
                # Promote the first Mafia-aligned player to Godfather
                new_godfather = alive_mafia_players[0]
                new_godfather.role = Godfather()  # Assign the new Godfather role
                await new_godfather.user.send("You have been promoted to the Godfather!")
                logging.info(f"{new_godfather.user.name} has been promoted to the new Godfather.")
                await channel.send(f"{new_godfather.user.mention} has been promoted to the new Godfather!")
            else:
                logging.info("No Mafia-aligned players remain to promote to Godfather.")

    def get_alive_players(self):
        """Return a list of all alive players."""
        return [player for player in self.players if player.alive]


class Player:
    def __init__(self, user):
        self.user = user
        self.role = None
        self.alive = True
        self.previous_target = None

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
    await game_manager.start_game(ctx.channel)
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

    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN environment variable is not set.")
    bot.run(TOKEN)
