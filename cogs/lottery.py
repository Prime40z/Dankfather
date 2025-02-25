import discord
from discord.ext import commands, tasks
import random
from datetime import datetime, timedelta
from typing import Optional
import re
from database import Database
from config import Config
from utils.logger import setup_logger
import os
from dotenv import load_dotenv, set_key

logger = setup_logger(__name__)

def is_admin(ctx):
    """Check if the user has an admin role"""
    return any(role.name in Config.ADMIN_ROLES for role in ctx.author.roles)

class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self._cooldowns = {}
        self.last_heartbeat = datetime.now()
        self.check_status.start()
        self._disconnected_time = None
        self.connection_monitor.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for Dank Memer donation messages"""
        if message.author.id != Config.DANK_MEMER_ID:  # Dank Memer's bot ID
            return

        if message.channel.id != Config.LOTTERY_CHANNEL_ID:
            return

        # Check for Dank Memer donation embed
        if message.embeds:
            embed = message.embeds[0]
            if "successfully donated" in embed.description.lower():
                try:
                    # Extract amount from embed description
                    amount_str = ''.join(filter(str.isdigit, embed.description))
                    amount = int(amount_str)
                    
                    # Get donor from message reference
                    if message.reference and message.reference.resolved:
                        donor = message.reference.resolved.author
                    else:
                        # Fallback to message author
                        donor = message.author

                    if not donor:
                        logger.error("Could not find donor")
                        return

                    new_entries, total_entries = self.db.add_donation(donor.id, amount)

                    embed = discord.Embed(title="🎉 Donation Tracked!", color=discord.Color.green())
                    embed.add_field(name="Donor", value=donor.mention, inline=True)
                    embed.add_field(name="Amount", value=f"{amount:,} coins", inline=True)
                    embed.add_field(name="New Entries", value=str(new_entries), inline=True)
                    embed.add_field(name="Total Entries", value=str(total_entries), inline=True)
                    embed.set_footer(text=f"1 entry per {Config.ENTRY_THRESHOLD:,} coins donated")

                    await message.channel.send(embed=embed)
                    logger.info(f"Automatically tracked donation: {donor.id} donated {amount} coins")

                except Exception as e:
                    logger.error(f"Error processing donation message: {str(e)}")

    def cog_unload(self):
        self.check_status.cancel()
        self.connection_monitor.cancel()

    async def check_lottery_channel(self, ctx) -> bool:
        """Check if the command is being used in the lottery channel"""
        if Config.LOTTERY_CHANNEL_ID == 0:
            await ctx.send("❌ Lottery channel hasn't been set up. Admins, please use $$setlotterychannel to set it up.")
            return False
        if ctx.channel.id != Config.LOTTERY_CHANNEL_ID:
            await ctx.send(f"❌ Please use lottery commands in <#{Config.LOTTERY_CHANNEL_ID}>")
            return False
        return True

    @commands.command()
    @commands.check(is_admin)
    async def setlotterychannel(self, ctx):
        """Admin command to set the current channel as the lottery channel"""
        channel_id = ctx.channel.id
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

        # Update .env file
        set_key(env_path, 'LOTTERY_CHANNEL_ID', str(channel_id))
        # Update current config
        Config.LOTTERY_CHANNEL_ID = channel_id

        await ctx.send(f"✅ This channel has been set as the Dank Memer lottery channel!")
        logger.info(f"Lottery channel set to {channel_id} by {ctx.author.id}")

    @commands.command()
    async def myentries(self, ctx):
        """Check your Dank Memer lottery entries"""
        if not await self.check_lottery_channel(ctx):
            return

        try:
            cooldown = self.check_cooldown(ctx.author.id, "myentries", 30)
            if cooldown:
                await ctx.send(f"⌛ Please wait {cooldown} seconds before checking your entries again.")
                return

            entries = self.db.get_user_entries(ctx.author.id)
            total_donated = self.db.get_user_total_donated(ctx.author.id)

            embed = discord.Embed(title="🎟️ Your Lottery Entries", color=discord.Color.blue())
            embed.add_field(name="Total Entries", value=str(entries), inline=False)
            embed.add_field(name="Total Donated", value=f"{total_donated:,} coins", inline=False)
            embed.set_footer(text=f"1 entry per {Config.ENTRY_THRESHOLD:,} coins donated")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in myentries command: {str(e)}")

    @commands.command()
    async def prize(self, ctx):
        """Show current Dank Memer lottery prize pool information"""
        if not await self.check_lottery_channel(ctx):
            return

        try:
            cooldown = self.check_cooldown(ctx.author.id, "prize", 60)
            if cooldown:
                await ctx.send(f"⌛ Please wait {cooldown} seconds before checking the prize again.")
                return

            total_donations = self.db.get_total_donations()
            taxed_prize = total_donations * (1 - Config.TAX_RATE)

            embed = discord.Embed(title="🎰 Dank Memer Lottery Prize Pool", color=discord.Color.gold())
            embed.add_field(name="Total Donations", value=f"{total_donations:,} coins", inline=False)
            embed.add_field(name="Prize after tax", value=f"{taxed_prize:,.0f} coins", inline=False)
            embed.add_field(name="Entry Cost", value=f"{Config.ENTRY_THRESHOLD:,} coins per entry", inline=False)
            embed.set_footer(text=f"Tax rate: {Config.TAX_RATE*100}%")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in prize command: {str(e)}")

    @commands.command()
    @commands.check(is_admin)
    async def pickwinner(self, ctx):
        """Admin command to pick a Dank Memer lottery winner"""
        if not await self.check_lottery_channel(ctx):
            return

        try:
            entries = self.db.get_all_entries()
            weighted_pool = [(user_id, count) for user_id, count in entries for _ in range(count)]

            if not weighted_pool:
                await ctx.send("❌ No valid entries found.")
                return

            winner_id, _ = random.choice(weighted_pool)
            winner_user = await self.bot.fetch_user(winner_id)
            total_prize = self.db.get_total_donations()
            taxed_prize = total_prize * (1 - Config.TAX_RATE)

            logger.info(f"Lottery winner picked: {winner_id}")

            embed = discord.Embed(title="🎉 Dank Memer Lottery Winner!", color=discord.Color.green())
            embed.add_field(name="Winner", value=winner_user.mention, inline=False)
            embed.add_field(name="Prize Pool", value=f"{total_prize:,} coins", inline=False)
            embed.add_field(name="Prize After Tax", value=f"{taxed_prize:,.0f} coins", inline=False)
            embed.set_footer(text="Please send the prize using Dank Memer's trade command")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in pickwinner command: {str(e)}")

    @tasks.loop(minutes=5.0)
    async def check_status(self):
        """Monitor bot status and send notifications if offline"""
        try:
            current_time = datetime.now()
            self.last_heartbeat = current_time
            logger.info("Bot status check - Online")
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            await self.notify_admins("⚠️ Bot status check failed - Please verify the bot is functioning correctly.")

    @tasks.loop(seconds=30)
    async def connection_monitor(self):
        """Monitor Discord connection status"""
        if not self.bot.is_closed():
            if self._disconnected_time:
                downtime = datetime.now() - self._disconnected_time
                logger.info(f"Bot reconnected after {downtime.total_seconds():.1f} seconds")
                await self.notify_admins(f"✅ Bot reconnected after {downtime.total_seconds():.1f} seconds of downtime")
                self._disconnected_time = None
        else:
            if not self._disconnected_time:
                self._disconnected_time = datetime.now()
                logger.warning("Bot disconnected from Discord")
                await self.notify_admins("⚠️ Bot disconnected from Discord - Attempting to reconnect...")

    async def notify_admins(self, message: str):
        """Send notification to all admin users"""
        try:
            for guild in self.bot.guilds:
                admin_roles = [role for role in guild.roles if role.name in Config.ADMIN_ROLES]
                for role in admin_roles:
                    for member in role.members:
                        try:
                            await member.send(message)
                        except:
                            continue
        except Exception as e:
            logger.error(f"Failed to notify admins: {str(e)}")

    @check_status.before_loop
    @connection_monitor.before_loop
    async def before_task_start(self):
        """Wait for bot to be ready before starting monitoring tasks"""
        await self.bot.wait_until_ready()

    def check_cooldown(self, user_id: int, command: str, cooldown: int) -> Optional[int]:
        current_time = datetime.now()
        cooldown_key = f"{user_id}:{command}"

        if cooldown_key in self._cooldowns:
            time_diff = (current_time - self._cooldowns[cooldown_key]).total_seconds()
            if time_diff < cooldown:
                return int(cooldown - time_diff)

        self._cooldowns[cooldown_key] = current_time
        return None

    @commands.command()
    async def status(self, ctx):
        """Check bot's current status and uptime"""
        try:
            uptime = datetime.now() - self.last_heartbeat
            connection_status = "Connected ✅" if not self.bot.is_closed() else "Disconnected ❌"

            embed = discord.Embed(title="🤖 Bot Status", color=discord.Color.green())
            embed.add_field(name="Connection Status", value=connection_status, inline=False)
            embed.add_field(name="Last Heartbeat", value=f"{self.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S')}", inline=False)
            embed.add_field(name="Uptime", value=f"{str(uptime).split('.')[0]}", inline=False)

            if self._disconnected_time:
                downtime = datetime.now() - self._disconnected_time
                embed.add_field(name="Current Downtime", value=f"{str(downtime).split('.')[0]}", inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error in status command: {str(e)}")


async def setup(bot):
    await bot.add_cog(Lottery(bot))
