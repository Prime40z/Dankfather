from collections import defaultdict

class Phase:
    def __init__(self, channel, players):
        self.channel = channel
        self.players = players

    async def start(self):
        pass


class NightPhase(Phase):
    async def start(self):
        await self.channel.send("Night has fallen. Everyone, perform your night actions!")

    # Implement night actions logic here (e.g., resolving role interactions)


class DayPhase(Phase):
    def __init__(self, channel, players):
        super().__init__(channel, players)
        self.votes = defaultdict(int)

    async def start(self):
        await self.channel.send("Day has dawned! Discuss and vote using `!vote @player`.")

    async def cast_vote(self, voter, voted_player):
        if voter not in [p.user for p in self.players if p.alive]:
            return f"{voter.name}, you are not part of the game or you are dead!"
        if voted_player not in [p.user for p in self.players if p.alive]:
            return f"{voted_player.name} is not a valid player!"

        self.votes[voted_player] += 1
        return f"{voter.name} has voted to lynch {voted_player.name}."

    async def tally_votes(self):
        if not self.votes:
            return "No votes were cast. The day ends with no lynching."

        max_votes = max(self.votes.values())
        lynched_players = [player for player, count in self.votes.items() if count == max_votes]

        if len(lynched_players) > 1:
            return f"It's a tie between {', '.join([player.name for player in lynched_players])}. No one is lynched."
        else:
            lynched_player = lynched_players[0]
            for player in self.players:
                if player.user == lynched_player:
                    player.alive = False
                    break
            return f"{lynched_player.name} has been lynched with {max_votes} votes!"
