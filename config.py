"""
Configuration for the Mafia Discord bot.
"""
import os
import logging

# Discord bot configuration
PREFIX = "!"
DESCRIPTION = "A Discord bot for playing the Mafia party game"

# Game settings
MIN_PLAYERS = 4
MAX_PLAYERS = 15

# Phase durations in seconds
DAY_PHASE_DURATION = 300  # 5 minutes
NIGHT_PHASE_DURATION = 180  # 3 minutes

# Role settings
DEFAULT_ROLES = {
    # Number of players: Role distribution
    4: {"Mafia": 1, "Detective": 1, "Villager": 2},
    5: {"Mafia": 1, "Detective": 1, "Villager": 3},
    6: {"Mafia": 1, "Detective": 1, "Doctor": 1, "Villager": 3},
    7: {"Mafia": 2, "Detective": 1, "Doctor": 1, "Villager": 3},
    8: {"Mafia": 2, "Detective": 1, "Doctor": 1, "Villager": 4},
    9: {"Mafia": 2, "Detective": 1, "Doctor": 1, "Villager": 5},
    10: {"Mafia": 3, "Detective": 1, "Doctor": 1, "Villager": 5},
    11: {"Mafia": 3, "Detective": 1, "Doctor": 1, "Villager": 6},
    12: {"Mafia": 3, "Detective": 1, "Doctor": 1, "Villager": 7},
    13: {"Mafia": 3, "Detective": 2, "Doctor": 1, "Villager": 7},
    14: {"Mafia": 4, "Detective": 2, "Doctor": 1, "Villager": 7},
    15: {"Mafia": 4, "Detective": 2, "Doctor": 1, "Villager": 8},
}

# Webhook configuration for logging (optional)
LOGGING_WEBHOOK_URL = os.getenv("LOGGING_WEBHOOK_URL", None)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Embed colors
COLORS = {
    "lobby": 0x3498db,   # Blue
    "day": 0xf1c40f,     # Yellow
    "night": 0x34495e,   # Dark Blue
    "mafia": 0xe74c3c,   # Red
    "town": 0x2ecc71,    # Green
    "neutral": 0x95a5a6, # Gray
    "error": 0xe74c3c,   # Red
}