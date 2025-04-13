"""
Role classes for the Mafia game.
"""
from typing import Callable, Optional, List, Dict, Any

class Role:
    """Base class for all roles in the game."""
    
    def __init__(self):
        """Initialize the role with default values."""
        self.name = "Unknown"
        self.alignment = "Unknown"
        self.description = "Unknown role"
        
    def has_night_action(self) -> bool:
        """Check if this role has a night action."""
        return False
        
    def get_night_action(self) -> Optional[Callable]:
        """Get the night action function for this role."""
        return None
        
    def requires_target(self) -> bool:
        """Check if this role's night action requires a target."""
        return False
        
    def can_target_self(self) -> bool:
        """Check if this role can target themselves with their action."""
        return False
        
    def __str__(self) -> str:
        """String representation of the role."""
        return f"{self.name} ({self.alignment})"


class Villager(Role):
    """
    The basic Town role with no special abilities.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Villager"
        self.alignment = "Town"
        self.description = "A regular town citizen with no special abilities. Win by eliminating all Mafia."


class Mafia(Role):
    """
    The Mafia role that can kill one player each night.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Mafia"
        self.alignment = "Mafia"
        self.description = "Member of the Mafia. Can kill one player each night. Win by outnumbering the Town."
        
    def has_night_action(self) -> bool:
        return True
        
    def get_night_action(self) -> Callable:
        def kill_action(target):
            # This is a placeholder - actual killing is handled in game_session.py
            return target
        return kill_action
        
    def requires_target(self) -> bool:
        return True


class Detective(Role):
    """
    The Detective role that can investigate one player each night.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Detective"
        self.alignment = "Town"
        self.description = "Can investigate one player each night to learn their alignment (Town or Mafia)."
        
    def has_night_action(self) -> bool:
        return True
        
    def get_night_action(self) -> Callable:
        def investigate_action(target):
            # Actual investigation logic is in game_session.py
            return target
        return investigate_action
        
    def requires_target(self) -> bool:
        return True


class Doctor(Role):
    """
    The Doctor role that can protect one player each night.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Doctor"
        self.alignment = "Town"
        self.description = "Can protect one player each night from being killed."
        
    def has_night_action(self) -> bool:
        return True
        
    def get_night_action(self) -> Callable:
        def protect_action(target):
            # Actual protection logic is in game_session.py
            return target
        return protect_action
        
    def requires_target(self) -> bool:
        return True
        
    def can_target_self(self) -> bool:
        return True


# All available roles for role assignment
ALL_ROLES = [Villager, Mafia, Detective, Doctor]