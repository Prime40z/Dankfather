"""
Voting system for the Mafia game.
"""
from typing import Dict, List, Set, Optional, Tuple

class VoteManager:
    """Manages voting during day phases."""
    
    def __init__(self):
        """Initialize the vote manager."""
        self.votes = {}  # voter_id -> target_id
        self.vote_records = {}  # target_id -> [voter_id, ...]
        
    def cast_vote(self, voter, target) -> None:
        """
        Cast a vote from a voter to a target.
        
        Args:
            voter: The Player casting the vote
            target: The Player being voted for
        """
        # Remove any existing vote
        self.remove_vote(voter)
        
        # Record the new vote
        self.votes[voter.id] = target.id
        
        # Update vote records
        if target not in self.vote_records:
            self.vote_records[target] = []
        self.vote_records[target].append(voter)
        
    def remove_vote(self, voter) -> bool:
        """
        Remove a vote from a voter.
        
        Args:
            voter: The Player whose vote should be removed
            
        Returns:
            bool: True if a vote was removed, False otherwise
        """
        if voter.id in self.votes:
            target_id = self.votes[voter.id]
            del self.votes[voter.id]
            
            # Find the target and remove the voter
            for target, voters in self.vote_records.items():
                if target.id == target_id:
                    self.vote_records[target] = [v for v in voters if v.id != voter.id]
                    if not self.vote_records[target]:
                        del self.vote_records[target]
                    return True
                    
        return False
        
    def get_vote(self, voter_id) -> Optional[int]:
        """Get the target ID that a voter has voted for."""
        return self.votes.get(voter_id)
        
    def get_vote_counts(self) -> Dict:
        """Get a dictionary of vote counts for each target."""
        return self.vote_records
        
    def clear_votes(self) -> None:
        """Clear all votes."""
        self.votes = {}
        self.vote_records = {}
        
    def all_votes_cast(self, alive_players) -> bool:
        """
        Check if all alive players have cast votes.
        
        Args:
            alive_players: List of alive Player objects
            
        Returns:
            bool: True if all alive players have voted, False otherwise
        """
        for player in alive_players:
            if player.id not in self.votes:
                return False
        return True
        
    def tally_votes(self) -> Dict:
        """
        Tally the votes and return vote counts for each target.
        
        Returns:
            Dict: Dictionary mapping target players to vote counts
        """
        vote_counts = {}
        for target, voters in self.vote_records.items():
            vote_counts[target] = len(voters)
        return vote_counts