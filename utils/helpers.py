"""
Helper functions for the Mafia bot.
"""
import discord
import random
from typing import List, Dict, Any, Optional

def format_list(items: List[str], conjunction: str = "and") -> str:
    """
    Format a list of items as a comma-separated string with a conjunction.
    
    Args:
        items: List of strings to format
        conjunction: The conjunction to use (default: "and")
        
    Returns:
        Formatted string
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])}, {conjunction} {items[-1]}"

def get_random_death_message() -> str:
    """Get a random death message for Mafia kills."""
    messages = [
        "was found dead in their home",
        "was brutally murdered during the night",
        "was silenced permanently by the Mafia",
        "was stabbed in the back - literally",
        "will not be waking up this morning",
        "met a grisly end at the hands of the Mafia",
        "was eliminated by the Mafia's hit squad",
        "is sleeping with the fishes now",
        "has been taken out by the Mafia"
    ]
    return random.choice(messages)

def get_random_lynch_message() -> str:
    """Get a random lynch message."""
    messages = [
        "was dragged to the town square and hanged",
        "was voted out by the angry mob",
        "was executed for their alleged crimes",
        "faced the town's justice",
        "was eliminated by town vote",
        "met their fate at the gallows",
        "was found guilty by town consensus"
    ]
    return random.choice(messages)

def pluralize(count: int, singular: str, plural: str = "") -> str:
    """
    Return singular or plural form based on count.
    
    Args:
        count: The count to check
        singular: Singular form of the word
        plural: Plural form of the word (defaults to singular + 's')
        
    Returns:
        Appropriate form of the word
    """
    if count == 1:
        return singular
    return plural if plural else f"{singular}s"

def truncate_text(text: str, max_length: int = 1024) -> str:
    """
    Truncate text to fit within Discord embed field limits.
    
    Args:
        text: The text to truncate
        max_length: Maximum allowed length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def mention_list(members: List[discord.Member]) -> str:
    """
    Create a list of mentions from Discord members.
    
    Args:
        members: List of Discord members
        
    Returns:
        String of mentions separated by commas
    """
    return ", ".join([m.mention for m in members])