from bot_instance import bot  # Import the shared bot instance
import logging
import asyncio
from aiohttp import web  # For health-check server
from random import shuffle
from game.night_actions import NightActions
from game.roles import (
    ROLES, Mafia, Doctor, Detective, Villager, Jester, SerialKiller,
    Bodyguard, Spy, Witch, Arsonist, Mayor, Veteran, Escort, Consort,
    Framer, Forger, Executioner, Survivor, Amnesiac, Blackmailer,
    Disguiser, Godfather, Tracker, Lookout, Vigilante
)
from game.phases import NightPhase
from game.win_conditions import WinConditions

# Set up logging
logging.basicConfig(level=logging.INFO)

# Constants
MAX_PLAYERS = 20  # Maximum number of players per game

class GameManager:
    def __init__(self):
        self.players = []
        self.host = None
        self.night_actions = NightActions(bot, self)
        self.phase = None
        self.win_conditions = WinConditions(self.players)
        self.game_started = False  # To prevent joins/leaves after game starts
        self.night_kills = []  # Stores nightly kills for updates

    async def start_game(self, channel, user):
        """Start the game."""
        if len(self.players) < 4:
            await channel.send("Not enough players to start the game. At least 4 players are required.")
            return

        self.game_started = True
        await channel.send(f"{user.mention} has started the game!")
        await self.assign_roles()
        await channel.send("Roles have been assigned. The game is now starting!")
        self.phase = NightPhase(channel, self.players)
        await self.phase.start()
    
    async def assign_roles(self):
        """Assign roles to players."""
        shuffle(ROLES)
        for i, player in enumerate(self.players):
            player.role = ROLES[i % len(ROLES)]
            await player.user.send(f"You are a {player.role.name}.")

# Initialize the GameManager
game_manager = GameManager()
