import os
import asyncio
import logging
import discord
from bot_instance import bot  # Import the shared bot instance
from health_check import start_health_check_server
from game.game_manager import game_manager  # Import the GameManager
from game.player import Player  # Import the Player class

from blackjack import setup_blackjack_commands
setup_blackjack_commands(bot)

# Set up logging
logging.basicConfig(level=logging.INFO)
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)

@bot.command()
async def join(ctx):
    if game_manager.game_started:
        await ctx.send("The game has already started. You cannot join now.")
        return

    if any(player.user == ctx.author for player in game_manager.players):
        await ctx.send(f"{ctx.author.mention}, you are already in the game.")
    else:
        player = Player(ctx.author)
        game_manager.players.append(player)
        if not game_manager.host:
            game_manager.host = ctx.author
            await ctx.send(f"{ctx.author.mention} has joined the game and is now the host!")
        else:
            await ctx.send(f"{ctx.author.mention} has joined the game!")

@bot.command()
async def leave(ctx):
    if game_manager.game_started:
        await ctx.send("The game has already started. You cannot leave now.")
        return

    for player in game_manager.players:
        if player.user == ctx.author:
            game_manager.players.remove(player)
            if game_manager.host == ctx.author:
                if game_manager.players:
                    game_manager.host = game_manager.players[0].user
                    await ctx.send(f"{ctx.author.mention} has left the game. The new host is {game_manager.host.mention}!")
                else:
                    game_manager.host = None
                    await ctx.send(f"{ctx.author.mention} has left the game. There are no players left.")
            else:
                await ctx.send(f"{ctx.author.mention} has left the game.")
            return
    await ctx.send(f"{ctx.author.mention}, you are not in the game.")

@bot.command()
async def start(ctx):
    if ctx.author != game_manager.host:
        await ctx.send("Only the host can start the game.")
        return

    await game_manager.start_game(ctx.channel, ctx.author)

@bot.command()
async def reset(ctx):
    if ctx.author != game_manager.host:
        await ctx.send("Only the host can reset the game.")
        return

    game_manager.players = []
    game_manager.host = None
    game_manager.game_started = False
    game_manager.night_kills = []
    await ctx.send("The game has been reset.")

@bot.command()
async def kick(ctx, member: discord.Member):
    if ctx.author != game_manager.host:
        await ctx.send("Only the host can kick players.")
        return

    for player in game_manager.players:
        if player.user == member:
            game_manager.players.remove(player)
            await ctx.send(f"{member.mention} has been kicked from the game.")
            return
    await ctx.send(f"{member.mention} is not in the game.")

@bot.command()
async def party(ctx):
    if not game_manager.players:
        await ctx.send("There are no players in the game.")
        return

    player_list = "\n".join([f"{player.user.mention}" for player in game_manager.players])
    await ctx.send(f"Current players in the game:\n{player_list}")

@bot.event
async def on_ready():
    try:
        logging.info(f"Logged in as {bot.user}")
        logging.info(f"Registered Commands: {[command.name for command in bot.commands]}")
    except Exception as e:
        logging.error(f"Error in on_ready: {e}")

async def run_bot_forever():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set.")
    while True:
        try:
            logging.info("Starting bot...")
            await bot.start(TOKEN)
        except Exception as e:
            logging.error(f"Bot crashed with error: {e}. Restarting in 5 seconds...")
            await asyncio.sleep(5)

async def run_health_check():
    logging.info("Starting health check server...")
    runner, site = await start_health_check_server()
    logging.info("Health check server running. Blocking forever...")
    await asyncio.Event().wait()  # Block forever

async def main():
    logging.info("Main starting. Running bot and health check concurrently.")
    await asyncio.gather(
        run_bot_forever(),
        run_health_check()
    )
    logging.info("Main exited! This should never happen unless both tasks stopped.")

if __name__ == "__main__":
    print("Launching async main()...")
    asyncio.run(main())
    print("asyncio.run(main()) exited! This should never print!")
