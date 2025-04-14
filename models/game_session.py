"""
GameSession class to manage the state of a Mafia game.
"""
import discord
import random
import asyncio
from typing import List, Dict, Optional, Any, Tuple

from .player import Player
from .roles import ALL_ROLES, Villager, Mafia, Detective, Doctor
from .phases import PhaseManager
from .voting import VoteManager
from utils.constants import *
from utils.helpers import get_random_death_message, get_random_lynch_message
from utils.embeds import (
    create_game_lobby_embed, create_game_start_embed, 
    create_day_phase_embed, create_night_phase_embed,
    create_vote_results_embed, create_game_over_embed
)

class GameSession:
    """Represents a single game session of Mafia."""
    
    def __init__(self, channel, host):
        """Initialize a new game session."""
        self.channel = channel
        self.host = host
        self.players = []
        self.phase_manager = PhaseManager()
        self.vote_manager = VoteManager()
        self.started = False
        self.day_num = 0
        self.night_actions = {}  # Player ID -> target ID
        self.protected_player = None  # Player protected by doctor
        
    def add_player(self, member) -> bool:
        """Add a player to the game."""
        # Check if game is already started
        if self.started:
            return False
            
        # Check if player is already in the game
        if any(p.id == member.id for p in self.players):
            return False
            
        # Check if the game is full
        if len(self.players) >= MAX_PLAYERS:
            return False
            
        # Add the player
        player = Player(member)
        self.players.append(player)
        return True
        
    def remove_player(self, member_id) -> bool:
        """Remove a player from the game."""
        # Check if game is already started
        if self.started:
            return False
            
        # Check if player is in the game
        for i, player in enumerate(self.players):
            if player.id == member_id:
                self.players.pop(i)
                return True
                
        return False
        
    def get_player(self, member_id) -> Optional[Player]:
        """Get a player by their Discord member ID."""
        for player in self.players:
            if player.id == member_id:
                return player
        return None
        
    def get_player_by_member(self, member) -> Optional[Player]:
        """Get a player by their Discord member object."""
        return self.get_player(member.id)
        
    async def start_game(self):
        """Start the game by assigning roles to players."""
        if self.started or len(self.players) < MIN_PLAYERS:
            return False
            
        self.started = True
        self.day_num = 0
        
        # Shuffle players for random role assignment
        random.shuffle(self.players)
        
        # Get role distribution based on player count
        num_players = len(self.players)
        role_counts = ROLE_DISTRIBUTION.get(num_players, {})
        
        # Create role instances based on counts
        roles = []
        for role_name, count in role_counts.items():
            for _ in range(count):
                if role_name == "Mafia":
                    roles.append(Mafia())
                elif role_name == "Detective":
                    roles.append(Detective())
                elif role_name == "Doctor":
                    roles.append(Doctor())
                elif role_name == "Villager":
                    roles.append(Villager())
        
        # Assign roles to players
        for i, player in enumerate(self.players):
            player.role = roles[i]
        
        # Send role PMs to each player
        mafia_players = [p for p in self.players if p.role.name == "Mafia"]
        
        for player in self.players:
            teammates = None
            if player.role.name == "Mafia":
                teammates = [p for p in mafia_players if p.id != player.id]
                
            # Create and send role PM embed
            embed = create_role_pm_embed(player, teammates)
            try:
                await player.member.send(embed=embed)
            except discord.Forbidden:
                # Unable to DM the player
                await self.channel.send(f"⚠️ {player.member.mention}, I couldn't send you a DM with your role! " 
                                      "Please enable DMs from server members and use !mafia role to see your role.")
        
        # Start the first night phase
        await self.start_night_phase()
        return True
        
    async def start_day_phase(self):
        """Start the day phase of the game."""
        self.day_num += 1
        
        # Clear night actions and votes from previous phases
        self.night_actions = {}
        self.vote_manager.clear_votes()
        self.protected_player = None
        
        # Create day phase embed
        embed = create_day_phase_embed(self)
        await self.channel.send(embed=embed)
        
        # Start the day phase with a timer
        await self.phase_manager.start_phase("day", DAY_PHASE_DURATION)
        
        # Set up timeout to end the day phase
        await self._end_day_after_timeout(DAY_PHASE_DURATION)
        
    async def start_night_phase(self):
        """Start the night phase of the game."""
        # Clear votes from previous phases
        self.vote_manager.clear_votes()
        
        # Create night phase embed
        embed = create_night_phase_embed(self)
        await self.channel.send(embed=embed)
        
        # Start the night phase with a timer
        await self.phase_manager.start_phase("night", NIGHT_PHASE_DURATION)
        
        # DM players with night actions
        alive_players = [p for p in self.players if p.alive]
        for player in alive_players:
            if player.role.has_night_action():
                # Send action instructions
                targets = "\n".join([f"{i+1}. {p.member.display_name}" for i, p in enumerate(alive_players) 
                                    if (p.id != player.id or player.role.can_target_self())])
                
                action_description = ""
                if player.role.name == "Mafia":
                    action_description = "kill"
                elif player.role.name == "Detective":
                    action_description = "investigate"
                elif player.role.name == "Doctor":
                    action_description = "protect"
                
                instructions = (
                    f"**Night {self.day_num}**\n"
                    f"Use your role ability to {action_description} a player.\n"
                    f"Use `!mafia action <player_number>` to select your target.\n\n"
                    f"**Available Targets:**\n{targets}"
                )
                
                try:
                    await player.member.send(instructions)
                except discord.Forbidden:
                    # Unable to DM the player
                    pass
        
        # Set up timeout to end the night phase
        await self._end_night_after_timeout(NIGHT_PHASE_DURATION)
        
    async def _end_day_after_timeout(self, seconds):
        """End the day phase after a timeout."""
        try:
            await asyncio.sleep(seconds)
            
            # Only process if we're still in day phase (might have ended early)
            if self.phase_manager.current_phase == "day":
                await self.process_day_votes()
                
                # Check if game is over
                game_over = await self.check_game_over()
                if not game_over:
                    await self.start_night_phase()
        except asyncio.CancelledError:
            # Timer was cancelled (day ended early)
            pass
            
    async def _end_night_after_timeout(self, seconds):
        """End the night phase after a timeout."""
        try:
            await asyncio.sleep(seconds)
            
            # Only process if we're still in night phase (might have ended early)
            if self.phase_manager.current_phase == "night":
                await self.process_night_actions()
                
                # Check if game is over
                game_over = await self.check_game_over()
                if not game_over:
                    await self.start_day_phase()
        except asyncio.CancelledError:
            # Timer was cancelled (night ended early)
            pass
            
    def register_vote(self, voter, target):
        """Register a vote from a player for a target."""
        self.vote_manager.cast_vote(voter, target)
        
    def remove_vote(self, voter):
        """Remove a vote from a player."""
        return self.vote_manager.remove_vote(voter)
        
    def check_all_votes_cast(self):
        """Check if all alive players have cast votes."""
        alive_players = [p for p in self.players if p.alive]
        return self.vote_manager.all_votes_cast(alive_players)
        
    def get_vote_counts(self):
        """Get the current vote counts."""
        return self.vote_manager.tally_votes()
        
    async def process_day_votes(self):
        """Process the votes cast during the day phase."""
        vote_counts = self.vote_manager.tally_votes()
        
        # No votes cast
        if not vote_counts:
            await self.channel.send("📊 No votes were cast today. Nobody was lynched.")
            return None
            
        # Find the player with the most votes
        max_votes = 0
        targets_with_max = []
        
        for target, count in vote_counts.items():
            if count > max_votes:
                max_votes = count
                targets_with_max = [target]
            elif count == max_votes:
                targets_with_max.append(target)
                
        # Handle tie by random selection
        if len(targets_with_max) > 1:
            await self.channel.send(f"📊 There was a tie! A random player among those with {max_votes} votes will be lynched.")
            lynched_player = random.choice(targets_with_max)
        else:
            lynched_player = targets_with_max[0]
            
        # Kill the lynched player
        lynched_player.alive = False
        
        # Send lynch results
        embed = create_vote_results_embed(lynched_player, vote_counts)
        await self.channel.send(embed=embed)
        
        return lynched_player
        
    def register_night_action(self, actor, target=None):
        """Register a night action from a player."""
        if target:
            self.night_actions[actor.id] = target.id
            return True
        return False
        
    def check_all_night_actions_submitted(self):
        """Check if all night actions have been submitted."""
        awaiting_actions = []
        
        for player in self.players:
            if player.alive and player.role.has_night_action():
                if player.id not in self.night_actions:
                    awaiting_actions.append(player)
                    
        return len(awaiting_actions) == 0, awaiting_actions
        
    async def process_night_actions(self):
        """Process all night actions."""
        # First, determine who the Mafia wants to kill
        mafia_alive = [p for p in self.players if p.alive and p.role.name == "Mafia"]
        mafia_targets = {}
        
        for mafia in mafia_alive:
            if mafia.id in self.night_actions:
                target_id = self.night_actions[mafia.id]
                mafia_targets[target_id] = mafia_targets.get(target_id, 0) + 1
                
        # Find the most voted mafia target
        mafia_kill_target = None
        max_votes = 0
        
        for target_id, votes in mafia_targets.items():
            if votes > max_votes:
                max_votes = votes
                mafia_kill_target = self.get_player(target_id)
                
        # Process Doctor protection
        doctor_alive = [p for p in self.players if p.alive and p.role.name == "Doctor"]
        for doctor in doctor_alive:
            if doctor.id in self.night_actions:
                protected_id = self.night_actions[doctor.id]
                self.protected_player = self.get_player(protected_id)
                
        # Process Detective investigations
        detective_alive = [p for p in self.players if p.alive and p.role.name == "Detective"]
        for detective in detective_alive:
            if detective.id in self.night_actions:
                investigated_id = self.night_actions[detective.id]
                investigated_player = self.get_player(investigated_id)
                
                # Send investigation results
                if investigated_player:
                    alignment = investigated_player.role.alignment
                    try:
                        await detective.member.send(
                            f"🔎 **Investigation Results (Night {self.day_num}):**\n"
                            f"You investigated **{investigated_player.member.display_name}**.\n"
                            f"They are aligned with the **{alignment}**."
                        )
                    except discord.Forbidden:
                        # Unable to DM the player
                        pass
                        
        # Process Mafia kill
        if mafia_kill_target and mafia_kill_target != self.protected_player:
            mafia_kill_target.alive = False
            death_message = get_random_death_message()
            
            await self.channel.send(
                f"☀️ **Day {self.day_num+1} Begins**\n"
                f"The town wakes up to tragic news...\n"
                f"**{mafia_kill_target.member.display_name}** {death_message}.\n"
                f"They were a **{mafia_kill_target.role.name}**!"
            )
        else:
            if mafia_kill_target:
                # Target was protected
                await self.channel.send(
                    f"☀️ **Day {self.day_num+1} Begins**\n"
                    f"The town wakes up... Everything seems quiet. Nobody died last night!"
                )
            else:
                # No kill target
                await self.channel.send(
                    f"☀️ **Day {self.day_num+1} Begins**\n"
                    f"The town wakes up... The Mafia was inactive. Nobody died last night!"
                )
                
    async def check_game_over(self) -> bool:
        """
        Check if the game is over and determine the winner.
        Returns True if the game is over, False otherwise.
        """
        alive_players = [p for p in self.players if p.alive]
        alive_mafia = [p for p in alive_players if p.role.alignment == "Mafia"]
        alive_town = [p for p in alive_players if p.role.alignment == "Town"]
        
        game_over = False
        winner = None
        
        # Game is over if all mafia are dead
        if len(alive_mafia) == 0:
            game_over = True
            winner = "town"
            await self.channel.send(embed=create_game_over_embed(self, "Town"))
            
        # Game is over if mafia outnumber or equal town
        elif len(alive_mafia) >= len(alive_town):
            game_over = True
            winner = "mafia"
            await self.channel.send(embed=create_game_over_embed(self, "Mafia"))
        
        if game_over:
            # Record game outcome in database
            try:
                from utils.db_utils import end_game_record
                from main import app
                
                with app.app_context():
                    if hasattr(self, 'db_game'):
                        end_game_record(self, self.db_game, winner)
                    else:
                        import logging
                        logging.warning("Game ended but no db_game attribute found")
                
                # Clean up
                if self.channel.id in self.bot.active_games:
                    del self.bot.active_games[self.channel.id]
            except Exception as e:
                import logging
                logging.error(f"Error recording game end in database: {e}")
                
            return True
            
        # Game continues
        return False
