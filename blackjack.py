import random
from discord.ext import commands

class BlackjackGame:
    def __init__(self):
        self.players = []
        self.hands = {}
        self.stands = {}
        self.active_hand = {}
        self.deck_mode = 'normal'  # 'normal' or 'stacked'
        self.house = []
        self.started = False
        self.turn_index = 0
        self.pending_action = None
        self.allow_double = True
        self.allow_split = True
        self.biased_starts = False  # <-- Toggle for biased starting hands

    def deal_card(self, who='player'):
        # Normal or stacked deck for in-game draws (not initial hands)
        if self.deck_mode == "normal":
            deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
            return random.choice(deck)
        else:
            if who == 'player':
                deck = [2]*1 + [3]*1 + [4]*1 + [5]*2 + [6]*2 + [7]*2 + [8]*2 + [9]*2 + [10]*8 + [11]*1
                return random.choice(deck)
            else:
                deck = [2]*5 + [3]*5 + [4]*5 + [5]*2 + [6]*2 + [7]*2 + [8]*1 + [9]*1 + [10]*2 + [11]*1
                return random.choice(deck)

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

    def generate_biased_start_hand(self):
        """
        Give a starting hand (2 cards) with total between 12 and 17 ~70% of the time,
        otherwise random normal hand.
        """
        hands_12_17 = []
        for c1 in [2,3,4,5,6,7]:
            for c2 in [5,6,7,8,9,10]:
                v = self.hand_value([c1, c2])
                if 12 <= v <= 17:
                    hands_12_17.append([c1, c2])
        if random.random() < 0.7:  # 70% chance
            return random.choice(hands_12_17)
        deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]
        return [random.choice(deck), random.choice(deck)]

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
        # Give players biased starting hands if enabled
        for player in game.players:
            if game.biased_starts:
                game.hands[player.id] = [game.generate_biased_start_hand()]
            else:
                deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]
                game.hands[player.id] = [[random.choice(deck), random.choice(deck)]]
            game.stands[player.id] = set()
            game.active_hand[player.id] = 0
        # Dealer/house hand is still random
        game.house = [game.deal_card('house'), game.deal_card('house')]
        game.started = True
        game.turn_index = 0
        game.pending_action = None
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
        if game.pending_action:
            p, action, _ = game.pending_action
            msg += f"\nAwaiting dealer approval: {p.mention} requests **{action.upper()}**"
        else:
            msg += f"{game.current_player().mention}, it's your turn! Type `!bj_hit`, `!bj_stand`, `!bj_double` or `!bj_split`."
        return msg

    def can_double(game, member):
        hand = game.current_hand(member)
        return game.allow_double and len(hand) == 2 and game.active_hand[member.id] not in game.stands[member.id]

    def can_split(game, member):
        hand = game.current_hand(member)
        return game.allow_split and len(hand) == 2 and hand[0] == hand[1] and len(game.hands[member.id]) < 4

    @bot.command()
    async def bj_hit(ctx):
        game = games.get(ctx.channel.id)
        if not game or not game.started or game.pending_action:
            await ctx.send("Cannot hit right now. (Game not started, or waiting on dealer approval for another action.)")
            return
        if ctx.author != game.current_player():
            await ctx.send("It's not your turn.")
            return
        hand = game.current_hand(ctx.author)
        idx = game.active_hand[ctx.author.id]
        hand.append(game.deal_card('player'))
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
        if not game or not game.started or game.pending_action:
            await ctx.send("Cannot stand right now. (Game not started, or waiting on dealer approval for another action.)")
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
        game = games.get(ctx.channel.id)
        if not game or not game.started:
            await ctx.send("No active blackjack game. Start one with `!bj_start`.")
            return
        if game.pending_action:
            await ctx.send("Another action is pending approval. Please wait.")
            return
        if ctx.author != game.current_player():
            await ctx.send("It's not your turn.")
            return
        if not can_double(game, ctx.author):
            await ctx.send("Double down is not allowed, or not possible at this time.")
            return
        idx = game.active_hand[ctx.author.id]
        game.pending_action = (ctx.author, "double", idx)
        await ctx.send(f"{ctx.author.mention} requests DOUBLE DOWN on hand {idx+1}. Dealer must approve with `!bj_approve` or deny with `!bj_deny`.")

    @bot.command()
    async def bj_split(ctx):
        game = games.get(ctx.channel.id)
        if not game or not game.started:
            await ctx.send("No active blackjack game. Start one with `!bj_start`.")
            return
        if game.pending_action:
            await ctx.send("Another action is pending approval. Please wait.")
            return
        if ctx.author != game.current_player():
            await ctx.send("It's not your turn.")
            return
        if not can_split(game, ctx.author):
            await ctx.send("Split is not allowed, or not possible at this time.")
            return
        idx = game.active_hand[ctx.author.id]
        game.pending_action = (ctx.author, "split", idx)
        await ctx.send(f"{ctx.author.mention} requests SPLIT on hand {idx+1}. Dealer must approve with `!bj_approve` or deny with `!bj_deny`.")

    @bot.command()
    async def bj_approve(ctx):
        game = games.get(ctx.channel.id)
        if not game or not game.started or not game.pending_action:
            await ctx.send("No action pending approval.")
            return
        player, action, idx = game.pending_action
        if action == "double":
            hand = game.hands[player.id][idx]
            hand.append(game.deal_card('player'))
            total = game.hand_value(hand)
            game.stands[player.id].add(idx)
            text = f"{player.mention} double down approved on hand {idx+1}! {hand} (Total: {total})"
            if total > 21:
                text += " — Busted!"
            await ctx.send(text)
            await advance_hand_or_turn(ctx, game, player)
        elif action == "split":
            hand = game.hands[player.id][idx]
            card = hand[0]
            game.hands[player.id].pop(idx)
            game.hands[player.id].insert(idx, [hand[1], game.deal_card('player')])
            game.hands[player.id].insert(idx, [card, game.deal_card('player')])
            game.stands[player.id] = set()
            await ctx.send(f"{player.mention} split approved! Now playing hand {idx+1}: {game.hands[player.id][idx]}")
            await ctx.send(await display_state(ctx, game))
        game.pending_action = None

    @bot.command()
    async def bj_deny(ctx):
        game = games.get(ctx.channel.id)
        if not game or not game.started or not game.pending_action:
            await ctx.send("No action pending approval.")
            return
        player, action, idx = game.pending_action
        await ctx.send(f"{player.mention}, your {action.upper()} on hand {idx+1} was denied by the dealer.")
        game.pending_action = None

    async def advance_hand_or_turn(ctx, game, member):
        hands = game.hands[member.id]
        stands = game.stands[member.id]
        idx = game.active_hand[member.id]
        for next_idx in range(idx+1, len(hands)):
            if next_idx not in stands:
                game.active_hand[member.id] = next_idx
                await ctx.send(f"{member.mention}, now playing hand {next_idx+1}.")
                await ctx.send(await display_state(ctx, game))
                return
        if game.turn_index < len(game.players) - 1:
            game.turn_index += 1
            next_player = game.current_player()
            await ctx.send(f"{next_player.mention}, it's your turn!")
            await ctx.send(await display_state(ctx, game))
        else:
            await finish_game(ctx, game)

    async def finish_game(ctx, game):
        house = game.house
        while game.hand_value(house) < 17 or (game.hand_value(house) == 17 and 11 in house):
            house.append(game.deal_card('house'))
        house_total = game.hand_value(house)
        result_msg = f"House hand: {house} (Total: {house_total})\n\n"
        for player in game.players:
            for i, hand in enumerate(game.hands[player.id]):
                total = game.hand_value(hand)
                if total > 21 and house_total > 21:
                    result = "Both busted! House wins."
                elif total > 21:
                    result = "Busted! House wins."
                elif house_total > 21:
                    result = "Dealer busted! You win!"
                elif total > house_total:
                    result = "You win!"
                elif total == house_total:
                    result = "House wins!"
                else:
                    result = "House wins!"
                result_msg += f"{player.mention}, Hand {i+1}: {hand} (Total: {total}) - **{result}**\n"
        await ctx.send(result_msg)
        del games[ctx.channel.id]

    @bot.command()
    async def bj_options(ctx, *args):
        game = games.setdefault(ctx.channel.id, BlackjackGame())
        msg = []
        args = list(args)
        if not args:
            msg.append(f"Current advanced table mode: **{game.deck_mode}**")
            msg.append(f"Double allowed: **{game.allow_double}**")
            msg.append(f"Split allowed: **{game.allow_split}**")
            msg.append(f"Biased starts: **{game.biased_starts}**")
        else:
            for arg in args:
                arg = arg.lower()
                if arg in ['shuffle', 'stacked', 'on']:
                    game.deck_mode = 'stacked'
                    game.biased_starts = True  # <-- Enable biased starting hands
                    msg.append("Advanced table mode: hand data tracking ENABLED")
                elif arg in ['off', 'normal']:
                    game.deck_mode = 'normal'
                    game.biased_starts = False  # <-- Disable biased starting hands
                    msg.append("Advanced table mode: hand data tracking DISABLED")
                elif arg.startswith('double:'):
                    val = arg.split(':', 1)[1]
                    if val == 'on':
                        game.allow_double = True
                        msg.append("Double down ENABLED.")
                    elif val == 'off':
                        game.allow_double = False
                        msg.append("Double down DISABLED.")
                elif arg.startswith('split:'):
                    val = arg.split(':', 1)[1]
                    if val == 'on':
                        game.allow_split = True
                        msg.append("Split ENABLED.")
                    elif val == 'off':
                        game.allow_split = False
                        msg.append("Split DISABLED.")
        await ctx.send("\n".join(msg))

    @bot.command()
    async def bj_reset(ctx):
        if ctx.channel.id in games:
            del games[ctx.channel.id]
        await ctx.send("Blackjack table reset.")
