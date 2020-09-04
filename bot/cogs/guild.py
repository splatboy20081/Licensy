import logging
from typing import Union

from discord.ext import commands

from bot import Licensy, models
from bot.utils.embed_handler import info


logger = logging.getLogger(__name__)


class Guild(commands.Cog):
    def __init__(self, bot: Licensy):
        self.bot = bot
        self.bot.loop.create_task(self.startup_guild_database_check())

    async def startup_guild_database_check(self):
        """
        Finds and adds any guilds that bot is in but are missing in the database.
        This is mainly for rare cases of Discord API issues where weird things can happen.

        Note: Never delete guilds just because database data and loaded guilds cache mismatch.
        It's possible that Discord down-times can cause bot to not see some guilds.
        """
        logger.info("Starting database guild checkup..")
        db_guilds_ids = await models.Guild.all().values_list("id", flat=True)
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            if guild.id not in db_guilds_ids:
                logger.info(f"Guild {guild.id} {guild} found but not registered. Adding entry to database.")
                await models.Guild.create(id=guild.id)

        logger.info("Database guild checkup done!")

    @commands.command(disabled=True, aliases=["guild_data", "guild"])
    @commands.guild_only()
    async def guild_info(self, ctx):
        """
        Shows database data for the guild.
        """
        guild = await models.Guild.get(id=ctx.guild.id)

        msgs = [
            f"Cached prefix {await self.bot.get_guild_prefix(ctx.guild)}",
            f"Custom prefix: {self._is_setup(guild.custom_prefix)}",

            f"\nCustom license format: {self._is_setup(guild.custom_license_format)}",
            f"License branding: {self._is_setup(guild.license_branding)}",
            f"Guild timezone: {self._is_setup(guild.timezone)}",
            f"DM redeem enabled: {guild.enable_dm_redeem}",
            f"Preserve previous duration enabled: {guild.preserve_previous_duration}",
            f"Guild language: {guild.language}",

            f"\nReminders enabled {guild.reminders_enabled}",
        ]

        if guild.reminders_enabled:
            msgs.extend([
                f"Reminder activation one: {self._is_setup(guild.reminder_activation_one)}",
                f"Reminder activation two: {self._is_setup(guild.reminder_activation_two)}",
                f"Reminder activation three: {self._is_setup(guild.reminder_activation_three)}",
                f"Reminder channel ID: {self._is_setup(guild.reminders_channel_id)}",
                f"Ping reminder in reminders channel: {guild.reminders_ping_in_reminders_channel}",
                f"Send reminders to dm: {guild.reminders_send_to_dm}"
            ])

        msgs.append(f"\nLicense log channel enabled {guild.license_log_channel_enabled}")
        if guild.license_log_channel_enabled:
            msgs.append(f"License log channel ID {self._is_setup(guild.license_log_channel_id)}")

        msgs.append(f"\nBot diagnostics channel enabled {guild.bot_diagnostics_channel_enabled}")
        if guild.bot_diagnostics_channel_enabled:
            msgs.append(f"Bot diagnostics channel ID {self._is_setup(guild.bot_diagnostics_channel_id)}")

        # TODO stored license count/active license count

        await ctx.send(embed=info("\n".join(msgs), ctx.me, title="Database guild info"))

    @staticmethod
    def _is_setup(value: Union[int, str]) -> Union[int, str]:
        """
        Default values in database (considered not set by user) are empty strings for string and 0 for integers.
        So this function just checks for those default values so instead of showing empty strings and zeroes
        we show "Not set".
        """
        if isinstance(value, int):
            if value == 0:
                return "Not set"
            else:
                return value
        elif isinstance(value, str):
            if value:
                return value
            else:
                return "Not set"


def setup(bot):
    bot.add_cog(Guild(bot))
