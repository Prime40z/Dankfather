import discord
from discord.ext import commands
from discord.ui import Select, View


class NightActions(commands.Cog):
    def __init__(self, bot, game_manager):
        self.bot = bot
        self.game_manager = game_manager

    async def start_night_phase(self):
        """Start the night phase and prompt roles with night actions."""
        for player in self.game_manager.players:
            if player.role.has_night_action:
                await self.prompt_night_action(player)

    async def prompt_night_action(self, player):
        """Send a dropdown menu to the player for selecting a target."""
        valid_targets = player.role.valid_targets(self.game_manager.get_alive_players())

        # Create dropdown options
        options = [
            discord.SelectOption(label=target.user.name, value=str(target.user.id))
            for target in valid_targets
        ]

        # Handle cases where there are no valid targets
        if not options:
            await player.user.send("You have no valid targets for your action tonight.")
            return

        # Create and send the dropdown
        select = Select(placeholder="Select a target", options=options)
        view = View()
        view.add_item(select)

        async def callback(interaction: discord.Interaction):
            selected_target_id = select.values[0]
            selected_target = next(
                (p for p in self.game_manager.players if str(p.user.id) == selected_target_id),
                None
            )
            if selected_target:
                player.role.previous_target = selected_target
                await interaction.response.send_message(
                    f"You have selected {selected_target.user.name} as your target."
                )
            else:
                await interaction.response.send_message("Invalid target selected.")

        select.callback = callback
        await player.user.send("Choose your target for tonight:", view=view)


async def setup(bot):
    bot.add_cog(NightActions(bot))
