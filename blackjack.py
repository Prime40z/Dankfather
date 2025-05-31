import discord
import random
from discord.ext import commands

deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4

games = {}

def deal_card():
    return random.choice(deck)

def hand_value(hand):
    total = sum(hand)
    aces = hand.count(11)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def setup_blackjack_commands(bot):
    @bot.command()
    async def blackjack(ctx):
        player = [deal_card(), deal_card()]
        house = [deal_card(), deal_card()]
        games[ctx.author.id] = {'player': player, 'house': house}

        await ctx.send(f"Your hand: {player} (Total: {hand_value(player)})\n"
                       f"House shows: [{house[0]}, ?]\n"
                       f"Type `!hit` to draw or `!stand` to hold.")

    @bot.command()
    async def hit(ctx):
        game = games.get(ctx.author.id)
        if not game:
            await ctx.send("Start a game first with `!blackjack`.")
            return

        game['player'].append(deal_card())
        total = hand_value(game['player'])
        if total > 21:
            await ctx.send(f"You busted! Your hand: {game['player']} (Total: {total})")
            del games[ctx.author.id]
        else:
            await ctx.send(f"Your hand: {game['player']} (Total: {total})\n"
                           "Type `!hit` or `!stand`.")

    @bot.command()
    async def stand(ctx):
        game = games.get(ctx.author.id)
        if not game:
            await ctx.send("Start a game first with `!blackjack`.")
            return

        while hand_value(game['house']) < 17:
            game['house'].append(deal_card())

        player_total = hand_value(game['player'])
        house_total = hand_value(game['house'])

        result = ""
        if house_total > 21 or player_total > house_total:
            result = "You win!"
        elif player_total == house_total:
            result = "It's a tie!"
        else:
            result = "House wins!"

        await ctx.send(f"Your hand: {game['player']} (Total: {player_total})\n"
                       f"House hand: {game['house']} (Total: {house_total})\n"
                       f"**{result}**")
        del games[ctx.author.id]
