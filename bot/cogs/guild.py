import logging

import discord
from discord.ext import commands
from tortoise.exceptions import IntegrityError

from bot import Licensy
from bot import models
from bot.utils.embed_handler import success, failure


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
            await ctx.send(embed=success(f"Successfully changed prefix to **{prefix}**", ctx.me))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def license_format(self, ctx, license_format: str):
        # TODO check if format is secure enough/valid
        if True:
            await models.Guild.get(id=ctx.guild.id).update(custom_license_format=license_format)
            await ctx.send(embed=success("Successfully changed license format.", ctx.me))

    @commands.command(disabled=True, aliases=["branding"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def license_branding(self, ctx, license_branding: str):
        # TODO clean content of any special characters including spaces
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
            Note that this does not change bot behaviour in any way, you cannot change the bot
            timezone itself. This is just used to displaying bot time in your guild timezone.
        """
        if timezone not in range(-12, 15):
            await ctx.send(embed=failure("Invalid UTC timezone."))
        else:
            await models.Guild.get(id=ctx.guild.id).update(timezone=timezone)
            await ctx.send(embed=success("Successfully updated guild timezone.", ctx.me))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def toggle_dm_redeem(self, ctx):
        previous_data = await Guild.get(id=ctx.guild.id).values_list("enable_dm_redeem", flat=True)
        next_state = not previous_data[0]
        await models.Guild.get(id=ctx.guild.id).update(enable_dm_redeem=next_state)
        await ctx.send(embed=success(f"DM redeem is set to **{next_state}**"))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def toggle_duration_preservation(self, ctx):
        previous_data = await Guild.get(id=ctx.guild.id).values_list("preserve_previous_duration", flat=True)
        next_state = not previous_data[0]
        await models.Guild.get(id=ctx.guild.id).update(preserve_previous_duration=next_state)
        await ctx.send(embed=success(f"Preserve previous duration is set to **{next_state}**"))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def setup_reminders(
            self,
            ctx,
            reminders_enabled: bool,
            reminder_activation_one: int,
            reminder_activation_two: int,
            reminder_activation_three: int,
            reminders_channel: discord.TextChannel,
            reminders_ping_in_reminders_channel: bool,
            reminders_send_to_dm: bool
    ):
        # TODO positive integer converter for reminder activation
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

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def edit_role(
            self,
            ctx,
            role: discord.Role,
            tier_level: int,
            tier_power: int
    ):
        # TODO positive integer for tiers (0 is disabled)
        if tier_level == 0:
            tier_level = None

        if tier_power == 0:
            tier_power = None

        if (role := await models.Role.get(id=role.id)).exists():
            await role.update(tier_level=tier_level, tier_power=tier_power)
        else:
            guild = await models.Guild.get(id=ctx.guild.id)
            await models.Role.create(guild=guild, id=role.id, tier_level=tier_level, tier_power=tier_power)

        await ctx.send(embed=success("Role updated."))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def create_role_packet(
            self,
            ctx,
            name: str,
            default_role_duration_minutes: int
    ):
        # TODO positive integer for duration
        # TODO filter name

        guild = await models.Guild.get(id=ctx.guild.id)

        try:
            await models.RolePacket.create(
                guild=guild,
                name=name,
                default_role_duration_minutes=default_role_duration_minutes
            )
        except IntegrityError:
            # TODO will this even work? Tortoise does not seem to propagate errors properly
            await ctx.send(embed=failure("Role packet with that name already exists."))
        else:
            await ctx.send(embed=success("Role updated."))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def add_packet_role(
            self,
            ctx,
            role_packet_name: str,
            role: discord.Role
    ):
        pass

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove_packet_role(
            self,
            ctx,
            role_packet_name: str,
            role: discord.Role
    ):
        pass

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def edit_packet_role(
            self,
            ctx,
            role_packet_name: str,
            role: discord.Role,
            duration_minutes: int
    ):
        pass

    @commands.command(disabled=True)
    @commands.guild_only()
    async def guild_info(self, ctx):
        """
        Shows database data for the guild.
        """
        guild = await models.Guild.get(id=ctx.guild.id)
        if not (prefix := guild.prefix):
            prefix = self.bot.get_guild_prefix(ctx.guild)

        stored_license_count = 0
        active_license_count = 0

        msg = (
            "Database guild info:\n"
            f"Prefix: **{prefix}**\n"
            f"Stored licenses: **{stored_license_count}**\n"
            f"Active role subscriptions: **{active_license_count}**"
        )

        await ctx.send(embed=success(msg, ctx.me))


def setup(bot):
    bot.add_cog(Guild(bot))
