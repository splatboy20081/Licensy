import logging

import discord
from discord.ext import commands

from bot import Licensy, models
from bot.utils.i18n_handler import LANGUAGES
from bot.utils.converters import NonNegativeInteger
from bot.utils.embed_handler import success, failure
from bot.utils.licence_helper import LicenseFormatter


logger = logging.getLogger(__name__)


class Configuration(commands.Cog):
    def __init__(self, bot: Licensy):
        self.bot = bot

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
        if LicenseFormatter.is_secure(license_format):
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


def setup(bot):
    bot.add_cog(Configuration(bot))
