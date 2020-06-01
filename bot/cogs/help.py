import logging

import discord
from discord.ext import commands

from bot import Licensy
from bot.utils.embed_handler import info
from bot.utils.misc import get_top_role_color


logger = logging.getLogger(__name__)


class PrettyHelpCommand(commands.MinimalHelpCommand):
    def get_ending_note(self):
        command_name = self.invoked_with
        return (
            "Type `{0}{1} <command>` for more info on a command.\n"
            "You can also type `{0}{1} <category>` for more info on a category."
        ).format(self.clean_prefix, command_name)

    def get_opening_note(self):
        if self.context.guild is None or self.context.author.guild_permissions.administrator:
            return
        else:
            return "Commands that you have no permission for are hidden."

    def add_bot_commands_formatting(self, _commands, heading):
        if _commands:
            outputs = [f"{command.name}\n\t{command.short_doc}" for command in _commands]
            joined = "```\n" + "\n".join(outputs) + "\n```"
            self.paginator.add_line(f"**__{heading}__**")
            self.paginator.add_line(joined)

    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(description=page, color=get_top_role_color(self.context.me))
            await destination.send(embed=embed)


class Help(commands.Cog):
    def __init__(self, bot: Licensy):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = PrettyHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        """Revert to default help command in case cog is unloaded"""
        self.bot.help_command = self._original_help_command

    @commands.command()
    async def faq(self, ctx):
        """
        Shows link to common Q/A about bot and it's usage.

        Output
        -------
        Link to FAQ residing on Github wiki.
        """
        bot_faq = f"You can read it on [Github wiki]({self.bot.config.FAQ_LINK})"
        await ctx.send(embed=info(bot_faq, ctx.me, title="FAQ"))

    @commands.command(aliases=["start"])
    async def quickstart(self, ctx):
        """
        Shows link that explains first time bot setup/usage.

        Output
        -------
        Link to quick-start explanation that is residing in Github source repository readme.
        """
        quickstart = f"See [Github link]({self.bot.config.QUICKSTART_LINK}) where quickstart is explained in detail."
        await ctx.send(embed=info(quickstart, ctx.me, title="Quickstart :)"))


def setup(bot):
    bot.add_cog(Help(bot))
