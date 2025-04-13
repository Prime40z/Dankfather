"""
Constants used across the Mafia bot.
"""

# Game settings
MIN_PLAYERS = 4
MAX_PLAYERS = 15

# Role distribution
ROLE_DISTRIBUTION = {
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

# Phase durations in seconds
DAY_PHASE_DURATION = 300  # 5 minutes
NIGHT_PHASE_DURATION = 180  # 3 minutes

# Emoji constants
EMOJI_MAFIA = "🔪"
EMOJI_DETECTIVE = "🔎"
EMOJI_DOCTOR = "💉"
EMOJI_VILLAGER = "👨‍🌾"
EMOJI_ALIVE = "✅"
EMOJI_DEAD = "💀"
EMOJI_DAY = "☀️"
EMOJI_NIGHT = "🌙"

# Command prefix
COMMAND_PREFIX = "!"

# Colors for embeds
COLOR_LOBBY = 0x3498db  # Blue
COLOR_DAY = 0xf1c40f    # Yellow
COLOR_NIGHT = 0x34495e  # Dark Blue
COLOR_MAFIA = 0xe74c3c  # Red
COLOR_TOWN = 0x2ecc71   # Green
COLOR_NEUTRAL = 0x95a5a6  # Gray