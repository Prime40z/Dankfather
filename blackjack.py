import random
from discord.ext import commands

class BlackjackGame:
    def __init__(self):
        self.players = []  # list of discord.Member
        self.hands = {}    # member.id -> list of cards
        self.stands = set()
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        self.house = []
        self.started = False
        self.turn_index = 0  # index in self.players

    def deal_card(self):
        return random.choice(self.deck)

    def hand_value(self, hand):
        total = sum(hand)
        aces = hand.count(11)
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    def current_player(self):
        if self.turn_index < len(self.players):
            return self.players[self.turn_index]
        return None

# Map channel ID to game instance
games = {}

def setup_blackjack_commands(bot):
    @bot.command()
    async def bj_join(ctx):
        """Join the blackjack game in this channel."""
        game = games.setdefault(ctx.channel.id, BlackjackGame())
        if game.started:
            await ctx.send("Game already started! Wait for the next round.")
            return
        if ctx.author in game.players:
            await ctx.send(f"{ctx.author.mention}, you are already in the game.")
            return
        game.players.append(ctx.author)
        await ctx.send(f"{ctx.author.mention} joined the blackjack table! ({len(game.players)} players)")

    @bot.command()
    async def bj_start(ctx):
        """Start the blackjack game in this channel."""
        game = games.get(ctx.channel.id)
        if not game or game.started:
            await ctx.send("No game to start, or game already started.")
            return
        if len(game.players) < 1:
            await ctx.send("Need at least 1 player to start.")
            return
        # Deal cards
        for player in game.players:
            game.hands[player.id] = [game.deal_card(), game.deal_card()]
        game.house = [game.deal_card(), game.deal_card()]
        game.started = True
        game.turn_index = 0
        await ctx.send("Blackjack started!\n" + await display_state(ctx, game))

    async def display_state(ctx, game):
        msg = ""
        for player in game.players:
            hand = game.hands[player.id]
            msg += f"{player.mention}: {hand} (Total: {game.hand_value(hand)})\n"
        msg += f"House shows: [{game.house[0]}, ?]\n"
        msg += f"{game.current_player().mention}, it's your turn! Type `!bj_hit` or `!bj_stand`."
        return msg

    @bot.command()
    async def bj_hit(ctx):
        game = games.get(ctx.channel.id)
        if not game or not game.started:
            await ctx.send("No active blackjack game. Start one with `!bj_start`.")
            return
        if ctx.author != game.current_player():
            await ctx.send("It's not your turn.")
            return
        hand = game.hands[ctx.author.id]
        hand.append(game.deal_card())
        total = game.hand_value(hand)
        if total > 21:
            await ctx.send(f"{ctx.author.mention} busted! Hand: {hand} (Total: {total})")
            game.stands.add(ctx.author.id)
            game.turn_index += 1
        else:
            await ctx.send(f"{ctx.author.mention}: {hand} (Total: {total})\nType `!bj_hit` or `!bj_stand`.")
            return  # Still player's turn
        await advance_turn(ctx, game)

    @bot.command()
    async def bj_stand(ctx):
        game = games.get(ctx.channel.id)
        if not game or not game.started:
            await ctx.send("No active blackjack game. Start one with `!bj_start`.")
            return
        if ctx.author != game.current_player():
            await ctx.send("It's not your turn.")
            return
        game.stands.add(ctx.author.id)
        game.turn_index += 1
        await ctx.send(f"{ctx.author.mention} stands.")
        await advance_turn(ctx, game)

    async def advance_turn(ctx, game):
        # Skip players who already stood or busted
        while (game.turn_index < len(game.players) and
               game.players[game.turn_index].id in game.stands):
            game.turn_index += 1
        if game.turn_index >= len(game.players):
            await finish_game(ctx, game)
        else:
            await ctx.send(f"{game.current_player().mention}, it's your turn! Type `!bj_hit` or `!bj_stand`.")

    async def finish_game(ctx, game):
        # Dealer plays
        house = game.house
        while game.hand_value(house) < 17:
            house.append(game.deal_card())
        house_total = game.hand_value(house)
        result_msg = f"House hand: {house} (Total: {house_total})\n\n"
        for player in game.players:
            hand = game.hands[player.id]
            total = game.hand_value(hand)
            if total > 21:
                result = "Busted! House wins."
            elif house_total > 21 or total > house_total:
                result = "You win!"
            elif total == house_total:
                result = "It's a tie!"
            else:
                result = "House wins!"
            result_msg += f"{player.mention}: {hand} (Total: {total}) - **{result}**\n"
        await ctx.send(result_msg)
        # Reset game for next round
        del games[ctx.channel.id]

    @bot.command()
    async def bj_reset(ctx):
        """Reset the blackjack table in this channel."""
        if ctx.channel.id in games:
            del games[ctx.channel.id]
        await ctx.send("Blackjack table reset.")
