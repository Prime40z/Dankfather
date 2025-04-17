from discord.ext import commands
import discord
import logging
import asyncio
from aiohttp import web  # For health-check server
from game.night_actions import NightActions
from game.roles import (
    ROLES, Mafia, Doctor, Detective, Villager, Jester, SerialKiller,
    Bodyguard, Spy, Witch, Arsonist, Mayor, Veteran, Escort, Consort,
    Framer, Forger, Executioner, Survivor, Amnesiac, Blackmailer,
    Disguiser, Godfather, Tracker, Lookout, Vigilante
)
from game.phases import NightPhase, DayPhase
from game.win_conditions import WinConditions

# Set up logging
logging.basicConfig(level=logging.INFO)

# Constants
MAX_PLAYERS = 20  # Maximum number of players per game

class GameManager:
    def __init__(self, bot):
        self.bot = bot
        self.players = []
        self.host = None
        self.night_actions = NightActions(bot, self)
        self.phase = None
        self.win_conditions = WinConditions(self.players)
        self.game_started = False  # To prevent joins/leaves after game starts
        self.night_kills = []  # Stores nightly kills for updates

    async def start_game(self, channel, author):
        """Initialize and start the game."""
        if self.host != author:
            await channel.send("Only the host can start the game.")
            return

        if len(self.players) < 2:
            await channel.send("You need at least 2 players to start the game!")
            return

        try:
            self.game_started = True
            logging.info("Game is starting...")
            await channel.send("The game is starting! Roles are being assigned...")

            self.assign_roles()

            for player in self.players:
                try:
                    await player.user.send(f"You have been assigned the role: {player.role}")
                    logging.info(f"Notified {player.user.name} of their role: {player.role}")
                except Exception as e:
                    logging.error(f"Could not notify {player.user.name} of their role. Error: {e}")

            logging.info("Roles have been assigned.")
            await channel.send("Roles have been assigned. The game is beginning!")
            await self.start_night_phase(channel)
        except Exception as e:
            logging.error(f"Error during game start: {e}")

    def assign_roles(self):
        """Assign roles to players."""
        from random import shuffle

        required_roles = [Godfather(), Doctor(), Detective()]
        if len(self.players) < len(required_roles):
            logging.warning("Not enough players to assign all required roles!")
            return

        remaining_roles = ROLES.copy()
        shuffle(remaining_roles)

        for required_role in required_roles:
            remaining_roles = [role for role in remaining_roles if type(role) != type(required_role)]

        for player, role in zip(self.players, required_roles):
            player.role = role
            logging.info(f"Assigned required role {role} to player {player.user.name}")

        for player, role in zip(self.players[len(required_roles):], remaining_roles):
            player.role = role
            logging.info(f"Assigned role {role} to player {player.user.name}")

    async def start_night_phase(self, channel):
        """Start the night phase with a timer."""
        try:
            logging.info("Starting night phase...")
            await channel.send("The game is now in the **Night Phase**. Players with night actions, please act now.")

            self.phase = NightPhase(channel, self.players)
            await self.phase.start()

            night_duration = 45
            logging.info(f"Night phase will last {night_duration} seconds.")
            await asyncio.sleep(night_duration)

            self.night_kills = await self.night_actions.start_night_phase()
            await self.send_nightly_update(channel)

            await self.check_win_conditions(channel)
            await self.start_day_phase(channel)
        except Exception as e:
            logging.error(f"Error during night phase: {e}")

    async def send_nightly_update(self, channel):
        """Send a summary of the night's events."""
        if not self.night_kills:
            await channel.send("No one was killed during the night.")
        else:
            messages = []
            for kill in self.night_kills:
                victim = kill.get("victim")
                killer = kill.get("killer")
                healed = kill.get("healed", False)

                if healed:
                    messages.append(f"{victim.user.mention} was attacked by {killer}, but they were healed by the Doctor!")
                else:
                    messages.append(f"{victim.user.mention} was killed by {killer}!")

            await channel.send("\n".join(messages))

    async def start_day_phase(self, channel):
        """Start the day phase with a timer."""
        try:
            logging.info("Starting day phase...")
            await channel.send("The game is now in the **Day Phase**. Discuss and prepare to vote.")

            self.phase = DayPhase(channel, self.players)
            await self.phase.start()

            day_duration = 90
            voting_menu_start = 25
            logging.info(f"Day phase will last {day_duration} seconds.")

            await asyncio.sleep(day_duration - voting_menu_start)

            logging.info("Opening voting menu.")
            await self.show_voting_menu(channel)

            await asyncio.sleep(voting_menu_start)
            await self.phase.tally_votes()
            await self.check_win_conditions(channel)
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
            await self.end_game(channel, result)

    async def end_game(self, channel, result):
        """End the game and display the results."""
        await channel.send(f"**Game Over!**\n\n{result}")

        winners = []
        losers = []
        for player in self.players:
            if player.role.win_condition_met():
                winners.append(f"{player.user.mention} ({player.role})")
            else:
                losers.append(f"{player.user.mention} ({player.role})")

        winner_message = "**Winners:**\n" + "\n".join(winners) if winners else "No winners!"
        loser_message = "**Losers:**\n" + "\n".join(losers) if losers else "No losers!"

        await channel.send(f"{winner_message}\n\n{loser_message}")

        self.players = []
        self.host = None
        self.game_started = False
        self.night_kills = []

    async def join(self, ctx):
        """Command to join the game."""
        if self.game_started:
            await ctx.send("The game has already started, and no new players can join.")
            return

        if len(self.players) >= MAX_PLAYERS:
            await ctx.send("The game is full. A maximum of 20 players are allowed.")
            return

        if any(player.user == ctx.author for player in self.players):
            await ctx.send(f"{ctx.author.mention}, you are already in the game.")
        else:
            player = Player(ctx.author)
            self.players.append(player)
            if not self.host:
                self.host = ctx.author
                await ctx.send(f"{ctx.author.mention} has joined the game and is now the host!")
            else:
                await ctx.send(f"{ctx.author.mention} has joined the game!")

    async def leave(self, ctx):
        """Command to leave the game."""
        if self.game_started:
            await ctx.send("The game has already started, and players cannot leave.")
            return

        for player in self.players:
            if player.user == ctx.author:
                self.players.remove(player)
                if self.host == ctx.author:
                    if self.players:
                        self.host = self.players[0].user
                        await ctx.send(f"{ctx.author.mention} has left the game. The new host is {self.host.mention}!")
                    else:
                        self.host = None
                        await ctx.send(f"{ctx.author.mention} has left the game. There are no players left.")
                else:
                    await ctx.send(f"{ctx.author.mention} has left the game.")
                return
        await ctx.send(f"{ctx.author.mention}, you are not in the game.")

# Health-check server
async def health_check(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.add_routes([web.get('/', health_check)])

if __name__ == "__main__":
    import os

    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN environment variable is not set.")

    loop = asyncio.get_event_loop()
    loop.create_task(web._run_app(app, port=8080))
    bot.run(TOKEN)
