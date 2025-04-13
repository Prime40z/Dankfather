"""
Discord embed creators for the Mafia game.
"""
import discord
from typing import List, Dict, Any, Optional
from utils.constants import *

def create_game_lobby_embed(game) -> discord.Embed:
    """Create an embed for the game lobby."""
    embed = discord.Embed(
        title="🎭 Mafia Game Lobby",
        description=f"Host: {game.host.mention}\nPlayers: {len(game.players)}/{MAX_PLAYERS}",
        color=COLOR_LOBBY
    )
    
    # List joined players
    players_text = ""
    for i, player in enumerate(game.players, 1):
        players_text += f"{i}. {player.member.mention}\n"
        
    if players_text:
        embed.add_field(name="Players", value=players_text, inline=False)
    else:
        embed.add_field(name="Players", value="None yet. Use `!mafia join` to join!", inline=False)
        
    # Show instructions
    instructions = (
        "• Use `!mafia join` to join the game\n"
        "• Use `!mafia leave` to leave the game\n"
        "• Host can use `!mafia start` to start the game\n"
        "• Use `!mafia help` to see all commands"
    )
    embed.add_field(name="Instructions", value=instructions, inline=False)
    
    # Show minimum players required
    if len(game.players) < MIN_PLAYERS:
        embed.set_footer(text=f"Need at least {MIN_PLAYERS} players to start | {MIN_PLAYERS - len(game.players)} more needed")
    else:
        embed.set_footer(text="Ready to start! Host can use !mafia start")
        
    return embed

def create_game_start_embed(game) -> discord.Embed:
    """Create an embed for game start announcement."""
    embed = discord.Embed(
        title="🎮 Mafia Game Started!",
        description="The game has begun! Check your DMs for your role.",
        color=COLOR_NIGHT
    )
    
    # List players
    players_text = ""
    for i, player in enumerate(game.players, 1):
        players_text += f"{i}. {player.member.mention}\n"
        
    embed.add_field(name="Players", value=players_text, inline=False)
    
    # Add note about night phase
    embed.add_field(
        name=f"{EMOJI_NIGHT} Night Phase",
        value="The first night has begun! Players with night actions should check their DMs.",
        inline=False
    )
    
    embed.set_footer(text="Good luck!")
    return embed

def create_role_pm_embed(player, teammates=None) -> discord.Embed:
    """Create an embed for role PM."""
    role = player.role
    
    # Set color based on alignment
    if role.alignment == "Mafia":
        color = COLOR_MAFIA
    elif role.alignment == "Town":
        color = COLOR_TOWN
    else:
        color = COLOR_NEUTRAL
        
    # Create embed
    embed = discord.Embed(
        title=f"Your Role: {role.name}",
        description=f"**Alignment**: {role.alignment}\n\n{role.description}",
        color=color
    )
    
    # Add emoji based on role
    role_emoji = EMOJI_VILLAGER
    if role.name == "Mafia":
        role_emoji = EMOJI_MAFIA
    elif role.name == "Detective":
        role_emoji = EMOJI_DETECTIVE
    elif role.name == "Doctor":
        role_emoji = EMOJI_DOCTOR
        
    embed.set_author(name=f"{role_emoji} {role.name}")
    
    # Add night action instructions if applicable
    if role.has_night_action():
        action_instructions = "**Night Action:**\n"
        
        if role.name == "Mafia":
            action_instructions += "Each night, you can vote to kill a player.\n"
            action_instructions += "Use `!mafia action @player` in DM to submit your kill target.\n"
            action_instructions += "The Mafia collectively decide on one target to kill."
        elif role.name == "Detective":
            action_instructions += "Each night, you can investigate a player to learn their alignment.\n"
            action_instructions += "Use `!mafia action @player` in DM to investigate them."
        elif role.name == "Doctor":
            action_instructions += "Each night, you can protect a player from being killed.\n"
            action_instructions += "Use `!mafia action @player` in DM to protect them."
            
        embed.add_field(name="Night Action", value=action_instructions, inline=False)
        
    # Add team information for Mafia
    if role.name == "Mafia" and teammates:
        team_text = "Your fellow Mafia members are:\n"
        for mate in teammates:
            team_text += f"• {mate.member.display_name}\n"
        embed.add_field(name="Your Team", value=team_text, inline=False)
        
    embed.set_footer(text="Remember to keep your role secret!")
    return embed

def create_day_phase_embed(game) -> discord.Embed:
    """Create an embed for day phase announcement."""
    embed = discord.Embed(
        title=f"{EMOJI_DAY} Day {game.day_num}",
        description="It's time to discuss and vote!",
        color=COLOR_DAY
    )
    
    # List alive players
    alive_players = [p for p in game.players if p.alive]
    alive_text = ""
    for i, player in enumerate(alive_players, 1):
        alive_text += f"{i}. {player.member.mention}\n"
        
    embed.add_field(name=f"Alive Players ({len(alive_players)})", value=alive_text, inline=False)
    
    # Instructions
    instructions = (
        "• Discuss and figure out who might be Mafia\n"
        "• Use `!mafia vote @player` to vote for someone\n"
        "• Use `!mafia unvote` to remove your vote\n"
        "• Use `!mafia vote` to see current votes\n"
        f"• You have {DAY_PHASE_DURATION // 60} minutes to vote"
    )
    embed.add_field(name="Instructions", value=instructions, inline=False)
    
    embed.set_footer(text=f"Player with the most votes will be lynched • Day {game.day_num}")
    return embed

def create_night_phase_embed(game) -> discord.Embed:
    """Create an embed for night phase announcement."""
    embed = discord.Embed(
        title=f"{EMOJI_NIGHT} Night {game.day_num}",
        description="Night has fallen. Players with night actions should check their DMs.",
        color=COLOR_NIGHT
    )
    
    # List alive players
    alive_players = [p for p in game.players if p.alive]
    alive_text = ""
    for i, player in enumerate(alive_players, 1):
        alive_text += f"{i}. {player.member.mention}\n"
        
    embed.add_field(name=f"Alive Players ({len(alive_players)})", value=alive_text, inline=False)
    
    # Instructions
    instructions = (
        "• Players with night actions should submit them via DM\n"
        "• Use `!mafia action @player` in DM to submit your action\n"
        f"• You have {NIGHT_PHASE_DURATION // 60} minutes to submit your actions\n"
        "• Regular players should wait for the next day"
    )
    embed.add_field(name="Instructions", value=instructions, inline=False)
    
    embed.set_footer(text=f"Night {game.day_num} • Actions will be processed automatically")
    return embed

def create_vote_results_embed(lynched_player, vote_counts) -> discord.Embed:
    """Create an embed for vote results."""
    embed = discord.Embed(
        title="🗳️ Lynch Results",
        description=f"**{lynched_player.member.display_name}** has been lynched by the town!",
        color=COLOR_MAFIA
    )
    
    # Add role reveal
    embed.add_field(
        name="Role Revealed",
        value=f"**{lynched_player.member.display_name}** was a **{lynched_player.role.name}** ({lynched_player.role.alignment})!",
        inline=False
    )
    
    # Add vote breakdown
    votes_text = ""
    for player, count in vote_counts.items():
        votes_text += f"{player.member.display_name}: {count} votes\n"
        
    if votes_text:
        embed.add_field(name="Vote Breakdown", value=votes_text, inline=False)
        
    return embed

def create_game_over_embed(game, winner) -> discord.Embed:
    """Create an embed for game over announcement."""
    if winner == "Mafia":
        title = f"{EMOJI_MAFIA} Mafia Wins!"
        description = "The Mafia has taken control of the town!"
        color = COLOR_MAFIA
    else:  # Town wins
        title = f"{EMOJI_VILLAGER} Town Wins!"
        description = "The Town has eliminated all members of the Mafia!"
        color = COLOR_TOWN
        
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    
    # Count players by alignment
    mafia_players = [p for p in game.players if p.role.alignment == "Mafia"]
    town_players = [p for p in game.players if p.role.alignment == "Town"]
    
    # Add Mafia team
    mafia_text = ""
    for player in mafia_players:
        status = EMOJI_ALIVE if player.alive else EMOJI_DEAD
        mafia_text += f"{status} {player.member.display_name} - {player.role.name}\n"
        
    embed.add_field(name=f"Mafia Team ({len(mafia_players)})", value=mafia_text or "None", inline=False)
    
    # Add Town team
    town_text = ""
    for player in town_players:
        status = EMOJI_ALIVE if player.alive else EMOJI_DEAD
        town_text += f"{status} {player.member.display_name} - {player.role.name}\n"
        
    embed.add_field(name=f"Town Team ({len(town_players)})", value=town_text or "None", inline=False)
    
    # Add game stats
    embed.add_field(name="Game Stats", value=f"Days: {game.day_num}\nPlayers: {len(game.players)}", inline=False)
    
    embed.set_footer(text="Thanks for playing! Use !mafia create to start a new game.")
    return embed

def create_help_embed() -> discord.Embed:
    """Create a help embed for Mafia commands."""
    embed = discord.Embed(
        title="🎭 Mafia Game Help",
        description="Here are all the commands for the Mafia game:",
        color=COLOR_LOBBY
    )
    
    # Game setup commands
    setup_commands = (
        "`!mafia create` - Create a new game\n"
        "`!mafia join` - Join an existing game\n"
        "`!mafia leave` - Leave the game lobby\n"
        "`!mafia start` - Start the game (host only)\n"
        "`!mafia end` - End the game (host only)"
    )
    embed.add_field(name="Game Setup", value=setup_commands, inline=False)
    
    # Game commands
    game_commands = (
        "`!mafia status` - Check game status\n"
        "`!mafia vote @player` - Vote to lynch a player\n"
        "`!mafia vote` - See current votes\n"
        "`!mafia unvote` - Remove your vote\n"
        "`!mafia action @player` - Use your night action (in DM)"
    )
    embed.add_field(name="Game Commands", value=game_commands, inline=False)
    
    # Information commands
    info_commands = (
        "`!mafia help` - Show this help message\n"
        "`!mafia roles` - Show all possible roles"
    )
    embed.add_field(name="Information", value=info_commands, inline=False)
    
    # Game rules
    rules = (
        "**Game Phases:**\n"
        "• Day: Discuss and vote to lynch a suspicious player\n"
        "• Night: Special roles use their night actions\n\n"
        "**Win Conditions:**\n"
        "• Town wins by eliminating all Mafia members\n"
        "• Mafia wins by outnumbering the Town"
    )
    embed.add_field(name="Game Rules", value=rules, inline=False)
    
    return embed