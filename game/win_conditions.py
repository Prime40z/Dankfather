class WinConditions:
    def __init__(self, players):
        self.players = players

    def check_win(self):
        """Check if any team or role has won."""
        mafia_alive = any(player.alive and isinstance(player.role, Mafia) for player in self.players)
        town_alive = any(player.alive and not isinstance(player.role, Mafia) for player in self.players)
        jester_wins = any(not player.alive and isinstance(player.role, Jester) for player in self.players)

        if jester_wins:
            return "Jester has won the game by being lynched!"
        if mafia_alive and not town_alive:
            return "Mafia has won the game!"
        if not mafia_alive and town_alive:
            return "Town has won the game!"
        return None
