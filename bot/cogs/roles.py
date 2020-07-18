import logging

import discord
from discord.ext import commands
from tortoise.exceptions import IntegrityError, DoesNotExist

from bot import Licensy, models
from bot.utils.misc import embed_space
from bot.utils.converters import PositiveInteger
from bot.utils.embed_handler import success, failure, info


logger = logging.getLogger(__name__)


class Roles(commands.Cog):
    def __init__(self, bot: Licensy):
        self.bot = bot

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def show_role_hierarchy(self, ctx):
        roles = await models.Role.filter(tier_level__gte=0)
        if not roles:
            await ctx.send(embed=failure("Hierarchy not set. Not a single role has tier level > 0"))
        else:
            hierarchy = sorted(roles, key=lambda _role: (_role.tier_power, _role.tier_level))
            levels = {}
            for role in hierarchy:
                levels.setdefault(role.tier_power, [])
                levels[role.tier_power].append((role.id, role.tier_level))

            message = []
            for level, sub_tuple in levels.items():
                message.append(f"**Level {level}:**")
                for role_id, role_power in sub_tuple:
                    message.append(f"{self.tab}{role_power} {self.safe_role_as_mention(ctx.guild, role_id)}")
                message.append("\n")

            await ctx.send(embed=info("\n".join(message), ctx.me, "Role hierarchy"))

    @classmethod
    def safe_role_as_mention(cls, guild: discord.Guild, role_id: int) -> str:
        role = guild.get_role(role_id)
        if role is None:
            return f"{role_id}"
        else:
            return role.mention

    @property
    def tab(self):
        return embed_space*4

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def edit_role(
            self,
            ctx,
            role: discord.Role,
            tier_level: PositiveInteger = None,
            tier_power: PositiveInteger = None
    ):
        role = await self.get_or_create_role_if_it_no_exists(ctx.guild.id, role.id)
        role.tier_level = tier_level
        role.tier_power = tier_power
        try:
            await role.save()
        except IntegrityError:
            await ctx.send(embed=failure("Cannot have 2 roles with the same tier power and level."))
        else:
            await ctx.send(embed=success("Role updated."))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def create_role_packet(
            self,
            ctx,
            name: str,
            default_role_duration_minutes: PositiveInteger
    ):
        """
        Arguments
        ----------
        name: str
            Name for accessing this role packet.
            Warning! No spaces allowed! Use _ or similar instead.

        default_role_duration_minutes: PositiveInteger
            When roles are added to this packet this is their default duration unless otherwise specified
            (you can specify manually when adding new role).
        """
        guild = await models.Guild.get(id=ctx.guild.id)

        try:
            await models.RolePacket.create(
                guild=guild,
                name=name,
                default_role_duration_minutes=default_role_duration_minutes
            )
        except IntegrityError:
            # TODO This also propagates driver exception, should be fixed in tortoise update
            # TODO (it is properly caught but still shows up in log as traceback)
            await ctx.send(embed=failure("Role packet with that name already exists."))
        else:
            await ctx.send(embed=success("Role packet successfully created."))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def add_packet_role(
            self,
            ctx,
            role_packet_name: str,
            role: discord.Role,
            duration_minutes: PositiveInteger = None
    ):
        # TODO converter for role instead of create_role_if_not_exist
        guild = await models.Guild.get(id=ctx.guild.id)
        db_role = await self.get_or_create_role_if_it_no_exists(ctx.guild.id, role.id)
        role_packet = await models.RolePacket.get(name=role_packet_name, guild=guild)

        if duration_minutes is None:
            duration_minutes = role_packet.default_role_duration_minutes

        try:
            await models.PacketRole.create(role_packet=role_packet, duration_minutes=duration_minutes, role=db_role)
        except IntegrityError:
            await ctx.send(embed=failure("That role already exists in that role packet."))
        else:
            await ctx.send(embed=success("Packet role successfully added", ctx.me))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def remove_packet_role(
            self,
            ctx,
            role_packet_name: str,
            role: discord.Role
    ):
        # TODO converter for role instead of create_role_if_not_exist
        guild = await models.Guild.get(id=ctx.guild.id)
        db_role = await self.get_or_create_role_if_it_no_exists(ctx.guild.id, role.id)
        role_packet = await models.RolePacket.get(guild=guild, name=role_packet_name)

        await models.PacketRole.get(role_packet=role_packet, role=db_role).delete()
        await ctx.send(embed=success("Packet role successfully removed.", ctx.me))

    @commands.command(disabled=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def edit_packet_role(
            self,
            ctx,
            role_packet_name: str,
            role: discord.Role,
            duration_minutes: PositiveInteger
    ):
        """
        First two parameters are for getting correct packet role.
        Only duration_minutes can be edited.
        """
        # TODO converter for role instead of create_role_if_not_exist
        guild = await models.Guild.get(id=ctx.guild.id)
        db_role = await self.get_or_create_role_if_it_no_exists(ctx.guild.id, role.id)
        role_packet = await models.RolePacket.get(guild=guild, name=role_packet_name)
        await models.PacketRole.get(role_packet=role_packet, role=db_role).update(duration_minutes=duration_minutes)
        await ctx.send(embed=success("Packet role successfully updated.", ctx.me))

    @classmethod
    async def get_or_create_role_if_it_no_exists(cls, guild_id: int, role_id: int) -> models.Role:
        try:
            return await models.Role.get(id=role_id)
        except DoesNotExist:
            guild = await models.Guild.get(id=guild_id)
            return await models.Role.create(guild=guild, id=role_id)


def setup(bot):
    bot.add_cog(Roles(bot))
