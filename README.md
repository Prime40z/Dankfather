# Discord Mafia Bot

A Discord bot that runs a Mafia-style game with role assignments, day/night cycles, and voting mechanics.

## Features

- Create and manage Mafia game sessions in Discord channels
- Supports 4-15 players per game
- Role assignments (Mafia, Detective, Doctor, Villager)
- Day/night cycle gameplay
- Voting system for lynching suspected Mafia members
- Special role abilities during night phases
- Web interface for bot status monitoring

## Game Roles

- **Villager (Town)** - A regular town citizen with no special abilities. Win by eliminating all Mafia.
- **Mafia (Mafia)** - Member of the Mafia. Can kill one player each night. Win by outnumbering the Town.
- **Detective (Town)** - Can investigate one player each night to learn their alignment (Town or Mafia).
- **Doctor (Town)** - Can protect one player each night from being killed.

## Commands

- `!mafia help` - Display help information
- `!mafia create` - Create a new game in the current channel
- `!mafia join` - Join an active game
- `!mafia leave` - Leave the game lobby
- `!mafia start` - Start the game (host only)
- `!mafia vote @player` - Vote to lynch a player during day phase
- `!mafia unvote` - Remove your vote
- `!mafia action @player` - Use your night ability (in DM)
- `!mafia end` - End the current game (host only)
- `!mafia status` - Check the current game status
- `!mafia roles` - Show information about all roles

## Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up a Discord bot in the Discord Developer Portal
4. Add the bot token to an environment variable named `DISCORD_TOKEN`
5. Run the bot: `python main.py`

## Project Structure

- `main.py` - Entry point that runs the bot and web interface
- `bot.py` - Main bot class definition and event handlers
- `cogs/game_commands.py` - Discord commands implementation
- `game/` - Core game logic components
  - `game_session.py` - Game session management
  - `player.py` - Player representation
  - `roles.py` - Role definitions and abilities
  - `phases.py` - Day/night phase handling
  - `voting.py` - Voting system
- `utils/` - Utility modules
  - `constants.py` - Game constants
  - `embeds.py` - Discord embed formatters
  - `helpers.py` - Helper functions

## Requirements

- Python 3.8+
- discord.py
- Flask (for web interface)

## License

MIT License