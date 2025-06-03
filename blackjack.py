import random
from discord.ext import commands

class BlackjackGame:
    def __init__(self):
        self.players = []  # list of discord.Member
        self.hands = {}    # member.id -> list of hands (each hand is a list of cards)
        self.stands = {}   # member.id -> set of hand indexes that have stood/busted
        self.active_hand = {}  # member.id -> which hand they're playing now (for splits)
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

    def current_hand(self, member):
        idx = self.active_hand.get(member.id, 0)
        return self.hands[member.id][idx]

    def all_hands_done(self, member):
        return len(self.stands[member.id]) == len(self.hands[member.id])

games = {}

def setup_blackjack_commands(bot):
    @bot.command()
    async def bj_join(ctx):
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
        game = games.get(ctx.channel.id)
        if not game or game.started:
            await ctx.send("No game to start, or game already started.")
            return
        if len(game.players) < 1:
            await ctx.send("Need at least 1 player to start.")
            return
        # Deal cards
        for player in game.players:
            game.hands[player.id] = [[game.deal_card(), game.deal_card()]]  # List of hands
            game.stands[player.id] = set()
            game.active_hand[player.id] = 0
        game.house = [game.deal_card(), game.deal_card()]
        game.started = True
        game.turn_index = 0
        await ctx.send("Blackjack started!\n" + await display_state(ctx, game))

    async def display_state(ctx, game):
        msg = ""
        for player in game.players:
            hands = game.hands[player.id]
            msg += f"{player.mention}:\n"
            for i, hand in enumerate(hands):
                total = game.hand_value(hand)
                done = " (DONE)" if i in game.stands[player.id] else ""
                marker = " ←" if (player == game.current_player() and i == game.active_hand[player.id]) else ""
                msg += f"  Hand {i+1}: {hand} (Total: {total}){done}{marker}\n"
        msg += f"House shows: [{game.house[0]}, ?]\n"
        msg += f"{game.current_player().mention}, it's your turn! Type `!bj_hit`, `!bj_stand`, `!bj_double` or `!bj_split`."
        return msg

    def can_double(game, member):
        # Only if first action (exactly 2 cards), not already acted on this hand
        hand = game.current_hand(member)
        return len(hand) == 2 and game.active_hand[member.id] not in game.stands[member.id]

    def can_split(game, member):
        hand = game.current_hand(member)
        return (len(hand) == 2 and hand[0] == hand[1] 
                and len(game.hands[member.id]) < 4)  # Limit splits to 4 hands for sanity

    @bot.command()
    async def bj_hit(ctx):
        game = games.get(ctx.channel.id)
        if not game or not game.started:
            await ctx.send("No active blackjack game. Start one with `!bj_start`.")
            return
        if ctx.author != game.current_player():
            await ctx.send("It's not your turn.")
            return
        hand = game.current_hand(ctx.author)
        idx = game.active_hand[ctx.author.id]
        hand.append(game.deal_card())
        total = game.hand_value(hand)
        if total > 21:
            await ctx.send(f"{ctx.author.mention} busted on hand {idx+1}! {hand} (Total: {total})")
            game.stands[ctx.author.id].add(idx)
            await advance_hand_or_turn(ctx, game, ctx.author)
        else:
            await ctx.send(await display_state(ctx, game))

    @bot.command()
    async def bj_stand(ctx):
        game = games.get(ctx.channel.id)
        if not game or not game.started:
            await ctx.send("No active blackjack game. Start one with `!bj_start`.")
            return
        if ctx.author != game.current_player():
            await ctx.send("It's not your turn.")
            return
        idx = game.active_hand[ctx.author.id]
        game.stands[ctx.author.id].add(idx)
        await ctx.send(f"{ctx.author.mention} stands on hand {idx+1}.")
        await advance_hand_or_turn(ctx, game, ctx.author)

    @bot.command()
    async def bj_double(ctx):
        """Double down: double bet, one card, then stand."""
        game = games.get(ctx.channel.id)
        if not game or not game.started:
            await ctx.send("No active blackjack game. Start one with `!bj_start`.")
            return
        if ctx.author != game.current_player():
            await ctx.send("It's not your turn.")
            return
        if not can_double(game, ctx.author):
            await ctx.send("You can only double down on your first move with two cards.")
            return
        hand = game.current_hand(ctx.author)
        idx = game.active_hand[ctx.author.id]
        hand.append(game.deal_card())
        total = game.hand_value(hand)
        game.stands[ctx.author.id].add(idx)
        text = f"{ctx.author.mention} doubles down on hand {idx+1}! {hand} (Total: {total})"
        if total > 21:
            text += " — Busted!"
        await ctx.send(text)
        await advance_hand_or_turn(ctx, game, ctx.author)

    @bot.command()
    async def bj_split(ctx):
        """Split your hand if your first two cards are the same."""
        game = games.get(ctx.channel.id)
        if not game or not game.started:
            await ctx.send("No active blackjack game. Start one with `!bj_start`.")
            return
        if ctx.author != game.current_player():
            await ctx.send("It's not your turn.")
            return
        if not can_split(game, ctx.author):
            await ctx.send("You can only split when your first two cards are the same.")
            return

        idx = game.active_hand[ctx.author.id]
        hand = game.current_hand(ctx.author)
        card = hand[0]
        # Remove current hand and add two new hands (each with one of the split cards)
        game.hands[ctx.author.id].pop(idx)
        game.hands[ctx.author.id].insert(idx, [hand[1], game.deal_card()])
        game.hands[ctx.author.id].insert(idx, [card, game.deal_card()])
        # Reset stands for these hands
        game.stands[ctx.author.id] = set()
        await ctx.send(f"{ctx.author.mention} splits! Now playing hand {idx+1}: {game.hands[ctx.author.id][idx]}")
        await ctx.send(await display_state(ctx, game))

    async def advance_hand_or_turn(ctx, game, member):
        # Advance to next hand for this player, or next player if all hands done
        hands = game.hands[member.id]
        stands = game.stands[member.id]
        idx = game.active_hand[member.id]
        # Move to next hand that isn't stood/busted
        for next_idx in range(idx+1, len(hands)):
            if next_idx not in stands:
                game.active_hand[member.id] = next_idx
                await ctx.send(f"{member.mention}, now playing hand {next_idx+1}.")
                await ctx.send(await display_state(ctx, game))
                return
        # All hands done for this player
        if game.turn_index < len(game.players) - 1:
            game.turn_index += 1
            next_player = game.current_player()
            await ctx.send(f"{next_player.mention}, it's your turn!")
            await ctx.send(await display_state(ctx, game))
        else:
            await finish_game(ctx, game)

    async def finish_game(ctx, game):
        # Dealer plays
        house = game.house
        while game.hand_value(house) < 17:
            house.append(game.deal_card())
        house_total = game.hand_value(house)
        result_msg = f"House hand: {house} (Total: {house_total})\n\n"
        for player in game.players:
            for i, hand in enumerate(game.hands[player.id]):
                total = game.hand_value(hand)
                if total > 21:
                    result = "Busted! House wins."
                elif house_total > 21 or total > house_total:
                    result = "You win!"
                elif total == house_total:
                    result = "It's a tie!"
                else:
                    result = "House wins!"
                result_msg += f"{player.mention}, Hand {i+1}: {hand} (Total: {total}) - **{result}**\n"
        await ctx.send(result_msg)
        # Reset game for next round
        del games[ctx.channel.id]

    @bot.command()
    async def bj_reset(ctx):
        """Reset the blackjack table in this channel."""
        if ctx.channel.id in games:
            del games[ctx.channel.id]
        await ctx.send("Blackjack table reset.")
