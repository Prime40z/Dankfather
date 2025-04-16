import discord
from discord.ext import commands


class NightActions(commands.Cog):
    def __init__(self, bot, game):
        self.bot = bot
        self.game = game  # Reference to the current game
        self.actions = []  # Store submitted actions for the night

    async def start_night_phase(self):
        """Start the night phase and send drop-down menus to all players with abilities."""
        # Iterate over players with abilities
        for player in self.game.players:
            if player.role and player.role.has_night_action:
                await self.send_action_menu(player)

    async def send_action_menu(self, player):
        """Send a private drop-down menu to the player for their night action."""
        # Build the list of valid targets dynamically based on the player's role
        target_options = self.get_valid_targets(player)

        # If no valid targets, notify the player
        if not target_options:
            await player.user.send(
                f"As a {player.role.name}, you have no valid targets for tonight."
            )
            return

        # Define the select menu
        class TargetSelect(discord.ui.Select):
            def __init__(self):
                super().__init__(
                    placeholder="Choose your target...",
                    options=target_options,
                    custom_id=f"{player.role.name.lower()}_action"
                )

            async def callback(self, interaction: discord.Interaction):
                # Handle the player's selection
                target_id = int(self.values[0])
                target_player = next(p for p in self.game.players if p.user.id == target_id)

                # Log the action
                self.view.cog.actions.append({
                    "role": player.role.name,
                    "player": player.user,
                    "target": target_player.user
                })
                await interaction.response.send_message(
                    f"You have chosen to target {target_player.user.name}.", ephemeral=True
                )

        # Define the view that contains the select menu
        class TargetSelectView(discord.ui.View):
            def __init__(self, cog):
                super().__init__()
                self.cog = cog  # Pass the cog for access to actions
                self.add_item(TargetSelect())

        # Send the select menu as an ephemeral message in the game channel
        await player.user.send(
            f"As a {player.role.name}, choose your target for tonight:",
            view=TargetSelectView(self)
        )

    def get_valid_targets(self, player):
        """Get a list of valid targets based on the player's role and game rules."""
        valid_targets = []

        # Example rule: Mafia can't kill other Mafia members
        if player.role.name == "Mafia":
            valid_targets = [
                discord.SelectOption(label=p.user.name, value=str(p.user.id))
                for p in self.game.players if p.alive and p.user != player.user and p.role.name != "Mafia"
            ]

        # Example rule: Doctor can't heal the same person twice in a row
        elif player.role.name == "Doctor":
            previous_target = player.role.previous_target
            valid_targets = [
                discord.SelectOption(label=p.user.name, value=str(p.user.id))
                for p in self.game.players if p.alive and p.user != previous_target
            ]

        # Default for other roles: All alive players except the player themselves
        else:
            valid_targets = [
                discord.SelectOption(label=p.user.name, value=str(p.user.id))
                for p in self.game.players if p.alive and p.user != player.user
            ]

        return valid_targets
