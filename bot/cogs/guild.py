import logging
from typing import Union

import discord
from discord.ext import commands

from bot import Licensy, models
from bot.utils.i18n_handler import LANGUAGES
from bot.utils.licence_helper import LicenseFormatter
from bot.utils.embed_handler import success, failure, info
from bot.utils.converters import NonNegativeInteger


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

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def prefix(self, ctx, *, prefix: str):
        """
        Changes guild prefix.

        Parameters
        ----------
        prefix: str
            New prefix to be used in guild. Maximum size is 10 characters.
        """
        if ctx.prefix == prefix:
            await ctx.send(embed=failure(f"Already using prefix **{prefix}**"))
        elif len(prefix) > 10:
            await ctx.send(embed=failure("Prefix is too long! Maximum of 10 characters please."))
        else:
            await models.Guild.get(id=ctx.guild.id).update(custom_prefix=prefix)
            self.bot.update_prefix_cache(ctx.guild.id, prefix)
            await ctx.send(embed=success(f"Successfully changed prefix to **{prefix}**", ctx.me))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def license_format(self, ctx, license_format: str):
        if LicenseFormatter.is_secured(license_format):
            await models.Guild.get(id=ctx.guild.id).update(custom_license_format=license_format)
            await ctx.send(embed=success("Successfully changed license format.", ctx.me))
        else:
            await ctx.send(
                embed=failure(
                    "Format is not secure enough.\n\n"
                    f"Current permutation count: {LicenseFormatter.get_format_permutations(license_format)}\n"
                    f"Required permutation count: {LicenseFormatter.min_permutation_count}"
                )
            )

    @commands.command(disabled=True, aliases=["branding"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def license_branding(self, ctx, license_branding: str):
        if len(license_branding) > 50:
            await ctx.send(embed=failure("Branding is too long! Maximum of 50 characters please."))
        else:
            await models.Guild.get(id=ctx.guild.id).update(license_branding=license_branding)
            await ctx.send(embed=success("Successfully updated guild branding.", ctx.me))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def timezone(self, ctx, timezone: int):
        """
        Changes guild timezone.

        Parameters
        ----------
        timezone: int
            Timezone in UTC (from -12 to 14).

            Note that this does not change bot behaviour in any way, you cannot change the bot timezone itself.
            This is just used to displaying bot time in your guild timezone.
        """
        if timezone not in range(-12, 15):
            await ctx.send(embed=failure("Invalid UTC timezone."))
        else:
            await models.Guild.get(id=ctx.guild.id).update(timezone=timezone)
            await ctx.send(embed=success("Successfully updated guild timezone.", ctx.me))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setup_guild_misc(self, ctx, enable_dm_redeem: bool, preserve_previous_duration: bool, language: str):
        await models.Guild.get(id=ctx.guild.id).update(enable_dm_redeem=enable_dm_redeem)
        await models.Guild.get(id=ctx.guild.id).update(preserve_previous_duration=preserve_previous_duration)
        updated_count = 2

        if language not in LANGUAGES:
            await ctx.send(embed=failure(f"**{language}** is not found in available languages."))
        else:
            await models.Guild.get(id=ctx.guild.id).update(preserve_previous_duration=language)
            updated_count += 1

        await ctx.send(embed=success(f"Successfully updated {updated_count} fields."))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setup_reminders(
            self,
            ctx,
            reminders_enabled: bool,
            reminder_activation_one: NonNegativeInteger,
            reminder_activation_two: NonNegativeInteger,
            reminder_activation_three: NonNegativeInteger,
            reminders_channel: discord.TextChannel,
            reminders_ping_in_reminders_channel: bool,
            reminders_send_to_dm: bool
    ):
        await models.Guild.get(id=ctx.guild.id).update(
            reminders_enabled=reminders_enabled,
            reminder_activation_one=reminder_activation_one,
            reminder_activation_two=reminder_activation_two,
            reminder_activation_three=reminder_activation_three,
            reminders_channel_id=reminders_channel.id,
            reminders_ping_in_reminders_channel=reminders_ping_in_reminders_channel,
            reminders_send_to_dm=reminders_send_to_dm
        )
        await ctx.send(embed=success("Reminders successfully set."))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setup_logs(
            self,
            ctx,
            license_log_channel_enabled: bool,
            license_log_channel: discord.TextChannel
    ):
        await models.Guild.get(id=ctx.guild.id).update(
            license_log_channel_enabled=license_log_channel_enabled,
            license_log_channel_id=license_log_channel.id
        )
        await ctx.send(embed=success("Log channel successfully updated."))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setup_diagnostics(
            self,
            ctx,
            bot_diagnostics_channel_enabled: bool,
            bot_diagnostics_channel: discord.TextChannel
    ):
        await models.Guild.get(id=ctx.guild.id).update(
            bot_diagnostics_channel_enabled=bot_diagnostics_channel_enabled,
            bot_diagnostics_channel_id=bot_diagnostics_channel.id
        )
        await ctx.send(embed=success("Bot diagnostic channel successfully updated."))

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
