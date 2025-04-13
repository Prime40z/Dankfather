"""
Player class to represent a player in the Mafia game.
"""
import discord
from typing import Optional, Any

class Player:
    """Represents a player in the game."""
    
    def __init__(self, member: discord.Member):
        """Initialize a player with their Discord member."""
        self.member = member
        self.id = member.id
        self.role = None  # Will be assigned when the game starts
        self.alive = True
        self.vote = None  # Current vote during day phase
        
    @property
    def name(self) -> str:
        """Get the player's display name."""
        return self.member.display_name
        
    def __str__(self) -> str:
        """String representation of the player."""
        role_str = f" ({self.role.name})" if self.role else ""
        status = "Alive" if self.alive else "Dead"
        return f"{self.name}{role_str} - {status}"