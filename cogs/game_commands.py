"""
Discord.py cog containing commands for the Mafia game.
"""
import discord
from discord.ext import commands
from discord import app_commands

from game.game_session import GameSession
from game.player import Player
from utils.embeds import create_game_lobby_embed, create_help_embed
from utils.constants import MIN_PLAYERS, MAX_PLAYERS

class GameCommands(commands.Cog):
    """Commands for managing Mafia game sessions."""
    
    def __init__(self, bot):
        """Initialize the cog with a reference to the bot."""
        self.bot = bot
        
    @commands.group(name="mafia", invoke_without_command=True)
    async def mafia(self, ctx):
        """Main command group for Mafia game commands."""
        await self.help(ctx)
        
    @mafia.command(name="help")
    async def help(self, ctx):
        """Display help information for the Mafia game."""
        embed = create_help_embed()
        await ctx.send(embed=embed)
        
    @mafia.command(name="create")
    async def create(self, ctx):
        """Create a new Mafia game in the current channel."""
        # Check if there's already a game in this channel
        if ctx.channel.id in self.bot.active_games:
            await ctx.send("⚠️ There is already an active game in this channel. Use `!mafia join` to join it.")
            return
            
        # Create new game
        game = GameSession(ctx.channel, ctx.author)
        self.bot.active_games[ctx.channel.id] = game
        
        # Add the host to the game
        game.add_player(ctx.author)
        
        # Send game lobby embed
        embed = create_game_lobby_embed(game)
        await ctx.send(embed=embed)
        
    @mafia.command(name="join")
    async def join(self, ctx):
        """Join the active Mafia game in the current channel."""
        # Check if there's a game in this channel
        if ctx.channel.id not in self.bot.active_games:
            await ctx.send("⚠️ There is no active game in this channel. Use `!mafia create` to start one.")
            return
            
        game = self.bot.active_games[ctx.channel.id]
        
        # Try to add the player
        if game.add_player(ctx.author):
            embed = create_game_lobby_embed(game)
            await ctx.send(embed=embed)
        else:
            if game.started:
                await ctx.send("⚠️ The game has already started. You cannot join now.")
            elif any(p.id == ctx.author.id for p in game.players):
                await ctx.send("⚠️ You are already in the game.")
            elif len(game.players) >= MAX_PLAYERS:
                await ctx.send(f"⚠️ The game is full ({MAX_PLAYERS} players maximum).")
            else:
                await ctx.send("⚠️ You cannot join the game for an unknown reason.")
                
    @mafia.command(name="leave")
    async def leave(self, ctx):
        """Leave the active Mafia game in the current channel."""
        # Check if there's a game in this channel
        if ctx.channel.id not in self.bot.active_games:
            await ctx.send("⚠️ There is no active game in this channel.")
            return
            
        game = self.bot.active_games[ctx.channel.id]
        
        # Try to remove the player
        if game.remove_player(ctx.author.id):
            # If the game is now empty, delete it
            if not game.players:
                del self.bot.active_games[ctx.channel.id]
                await ctx.send("Game ended because all players left.")
                return
                
            # If the host left, assign a new host
            if game.host.id == ctx.author.id:
                game.host = game.players[0].member
                await ctx.send(f"The host left. {game.host.mention} is now the host.")
                
            embed = create_game_lobby_embed(game)
            await ctx.send(embed=embed)
        else:
            if game.started:
                await ctx.send("⚠️ The game has already started. You cannot leave now.")
            else:
                await ctx.send("⚠️ You are not in the game.")
                
    @mafia.command(name="start")
    async def start(self, ctx):
        """Start the Mafia game if enough players have joined."""
        # Check if there's a game in this channel
        if ctx.channel.id not in self.bot.active_games:
            await ctx.send("⚠️ There is no active game in this channel. Use `!mafia create` to start one.")
            return
            
        game = self.bot.active_games[ctx.channel.id]
        
        # Check if the user is the host
        if game.host.id != ctx.author.id:
            await ctx.send("⚠️ Only the game host can start the game.")
            return
            
        # Check if the game has already started
        if game.started:
            await ctx.send("⚠️ The game has already started.")
            return
            
        # Check if there are enough players
        if len(game.players) < MIN_PLAYERS:
            await ctx.send(f"⚠️ Not enough players to start. Need at least {MIN_PLAYERS} players (currently {len(game.players)}).")
            return
            
        # Start the game
        await game.start_game()
        
        # Record the game in the database
        try:
            from utils.db_utils import create_game_record
            from flask import current_app
            from main import app
            
            with app.app_context():
                game.db_game = create_game_record(game)
        except Exception as e:
            import logging
            logging.error(f"Error recording game start in database: {e}")
            # Continue even if database recording fails
            
        await ctx.send("🎮 The Mafia game has started! Check your DMs for your role.")
        
    @mafia.command(name="vote")
    async def vote(self, ctx, target_mention = None):
        """Vote for a player during the day phase."""
        # Extract the target member from the mention
        target = None
        if target_mention:
            try:
                # Extract user ID from the mention string
                user_id = int(target_mention.strip('<@!>'))
                target = ctx.guild.get_member(user_id)
            except (ValueError, TypeError):
                pass
        # Check if there's a game in this channel
        if ctx.channel.id not in self.bot.active_games:
            await ctx.send("⚠️ There is no active game in this channel.")
            return
            
        game = self.bot.active_games[ctx.channel.id]
        
        # Check if the game has started
        if not game.started:
            await ctx.send("⚠️ The game hasn't started yet.")
            return
            
        # Check if it's the day phase
        if game.phase_manager.current_phase != "day":
            await ctx.send("⚠️ You can only vote during the day phase.")
            return
            
        # If no target provided, show current votes
        if target is None:
            vote_counts = game.get_vote_counts()
            if not vote_counts:
                await ctx.send("📊 No votes have been cast yet.")
                return
                
            # Format vote counts
            vote_text = "**Current Votes:**\n"
            for target_player, count in vote_counts.items():
                vote_text += f"{target_player.member.display_name}: {count} votes\n"
                
            await ctx.send(vote_text)
            return
            
        # Get the voter player object
        voter = game.get_player_by_member(ctx.author)
        if not voter:
            await ctx.send("⚠️ You are not in the game.")
            return
            
        # Check if the voter is alive
        if not voter.alive:
            await ctx.send("⚠️ Dead players cannot vote.")
            return
            
        # Get the target player object
        target_player = game.get_player_by_member(target)
        if not target_player:
            await ctx.send("⚠️ That player is not in the game.")
            return
            
        # Check if the target is alive
        if not target_player.alive:
            await ctx.send("⚠️ You cannot vote for a dead player.")
            return
            
        # Register the vote
        game.register_vote(voter, target_player)
        await ctx.send(f"✅ {voter.member.mention} voted for {target_player.member.mention}.")
        
        # Check if all players have voted
        if game.check_all_votes_cast():
            await ctx.send("Everyone has voted! Processing votes...")
            await game.process_day_votes()
            
            # Check if game is over
            game_over = await game.check_game_over()
            if not game_over:
                await game.start_night_phase()
                
    @mafia.command(name="unvote")
    async def unvote(self, ctx):
        """Remove your vote during the day phase."""
        # Check if there's a game in this channel
        if ctx.channel.id not in self.bot.active_games:
            await ctx.send("⚠️ There is no active game in this channel.")
            return
            
        game = self.bot.active_games[ctx.channel.id]
        
        # Check if the game has started
        if not game.started:
            await ctx.send("⚠️ The game hasn't started yet.")
            return
            
        # Check if it's the day phase
        if game.phase_manager.current_phase != "day":
            await ctx.send("⚠️ You can only unvote during the day phase.")
            return
            
        # Get the voter player object
        voter = game.get_player_by_member(ctx.author)
        if not voter:
            await ctx.send("⚠️ You are not in the game.")
            return
            
        # Check if the voter is alive
        if not voter.alive:
            await ctx.send("⚠️ Dead players cannot vote or unvote.")
            return
            
        # Remove the vote
        if game.remove_vote(voter):
            await ctx.send(f"✅ {voter.member.mention} removed their vote.")
        else:
            await ctx.send("⚠️ You don't have an active vote to remove.")
            
    @mafia.command(name="action")
    async def action(self, ctx, target_mention = None):
        """Perform your role's night action."""
        # Extract the target member from the mention
        target = None
        if target_mention:
            try:
                # Extract user ID from the mention string
                user_id = int(target_mention.strip('<@!>'))
                target = ctx.guild.get_member(user_id)
            except (ValueError, TypeError):
                pass
        # Check if this is a DM
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("⚠️ Night actions must be sent via DM for secrecy.")
            return
            
        # Find the game this player is in
        player_games = []
        for channel_id, game in self.bot.active_games.items():
            player = game.get_player_by_member(ctx.author)
            if player:
                player_games.append((game, player))
                
        if not player_games:
            await ctx.send("⚠️ You are not in any active games.")
            return
            
        if len(player_games) > 1:
            await ctx.send("⚠️ You are in multiple games. Please specify a game.")
            return
            
        game, player = player_games[0]
        
        # Check if the game has started
        if not game.started:
            await ctx.send("⚠️ The game hasn't started yet.")
            return
            
        # Check if it's the night phase
        if game.phase_manager.current_phase != "night":
            await ctx.send("⚠️ You can only use your action during the night phase.")
            return
            
        # Check if the player is alive
        if not player.alive:
            await ctx.send("⚠️ Dead players cannot use actions.")
            return
            
        # Check if the player has a night action
        if not player.role.has_night_action():
            await ctx.send("⚠️ Your role doesn't have a night action.")
            return
            
        # Check if a target is required
        if player.role.requires_target() and target is None:
            await ctx.send("⚠️ Your role requires a target. Use `!mafia action @player`.")
            return
            
        # If target is provided, get the target player
        target_player = None
        if target:
            target_player = game.get_player_by_member(target)
            if not target_player:
                await ctx.send("⚠️ That player is not in the game.")
                return
                
            # Check if the target is alive
            if not target_player.alive:
                await ctx.send("⚠️ You cannot target a dead player.")
                return
                
            # Check if the player can target themselves
            if target_player.id == player.id and not player.role.can_target_self():
                await ctx.send("⚠️ You cannot target yourself with this action.")
                return
                
        # Register the night action
        if game.register_night_action(player, target_player):
            action_desc = ""
            if player.role.name == "Mafia":
                action_desc = "kill"
            elif player.role.name == "Detective":
                action_desc = "investigate"
            elif player.role.name == "Doctor":
                action_desc = "protect"
                
            if target_player:
                await ctx.send(f"✅ You will {action_desc} {target_player.member.display_name} tonight.")
            else:
                await ctx.send(f"✅ Your action has been registered for tonight.")
                
            # Check if all actions submitted
            all_submitted, _ = game.check_all_night_actions_submitted()
            if all_submitted:
                await game.channel.send("All night actions have been submitted! Processing actions...")
                await game.process_night_actions()
                
                # Check if game is over
                game_over = await game.check_game_over()
                if not game_over:
                    await game.start_day_phase()
        else:
            await ctx.send("⚠️ Failed to register your action.")
            
    @mafia.command(name="end")
    async def end(self, ctx):
        """End the current Mafia game (host only)."""
        # Check if there's a game in this channel
        if ctx.channel.id not in self.bot.active_games:
            await ctx.send("⚠️ There is no active game in this channel.")
            return
            
        game = self.bot.active_games[ctx.channel.id]
        
        # Check if the user is the host
        if game.host.id != ctx.author.id:
            await ctx.send("⚠️ Only the game host can end the game.")
            return
            
        # End the game
        del self.bot.active_games[ctx.channel.id]
        await ctx.send("🎮 The game has been ended by the host.")
        
    @mafia.command(name="status")
    async def status(self, ctx):
        """Display the current status of the game."""
        # Check if there's a game in this channel
        if ctx.channel.id not in self.bot.active_games:
            await ctx.send("⚠️ There is no active game in this channel.")
            return
            
        game = self.bot.active_games[ctx.channel.id]
        
        if not game.started:
            embed = create_game_lobby_embed(game)
            await ctx.send(embed=embed)
            return
            
        # Display game status
        alive_players = [p for p in game.players if p.alive]
        dead_players = [p for p in game.players if not p.alive]
        
        status_text = f"**Game Status (Day {game.day_num})**\n"
        status_text += f"Phase: {game.phase_manager.current_phase.capitalize()}\n"
        status_text += f"Alive Players ({len(alive_players)}):\n"
        
        for i, player in enumerate(alive_players, 1):
            status_text += f"{i}. {player.member.mention}\n"
            
        if dead_players:
            status_text += f"\nDead Players ({len(dead_players)}):\n"
            for i, player in enumerate(dead_players, 1):
                status_text += f"{i}. {player.member.mention} - was {player.role.name}\n"
                
        await ctx.send(status_text)
        
    @mafia.command(name="roles")
    async def roles(self, ctx):
        """Display information about all possible roles."""
        roles_text = "**Mafia Game Roles**\n\n"
        
        # Villager
        roles_text += "**Villager** (Town)\n"
        roles_text += "A regular town citizen with no special abilities. Win by eliminating all Mafia.\n\n"
        
        # Mafia
        roles_text += "**Mafia** (Mafia)\n"
        roles_text += "Member of the Mafia. Can kill one player each night. Win by outnumbering the Town.\n\n"
        
        # Detective
        roles_text += "**Detective** (Town)\n"
        roles_text += "Can investigate one player each night to learn their alignment (Town or Mafia).\n\n"
        
        # Doctor
        roles_text += "**Doctor** (Town)\n"
        roles_text += "Can protect one player each night from being killed.\n\n"
        
        await ctx.send(roles_text)
        
    @vote.error
    async def vote_error(self, ctx, error):
        """Error handler for the vote command."""
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("⚠️ Player not found. Make sure to @mention them.")
        else:
            await ctx.send(f"⚠️ An error occurred: {error}")
            
    @action.error
    async def action_error(self, ctx, error):
        """Error handler for the action command."""
        if isinstance(error, commands.MemberNotFound):
            await ctx.send("⚠️ Player not found. Make sure to @mention them.")
        else:
            await ctx.send(f"⚠️ An error occurred: {error}")
            
async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(GameCommands(bot))