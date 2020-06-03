import sys
import logging
import traceback
import importlib
from typing import Union, Generator
from asyncio.exceptions import TimeoutError as AsyncioTimeoutError

import discord
from discord.ext import commands

from bot import config
from bot.database_client import DatabaseClient
from bot.utils.embed_handler import failure, log
from bot.utils.licence_helper import get_current_time
from bot.utils.errors import DatabaseMissingData


logger = logging.getLogger(__name__)
console_logger = logging.getLogger("console")


class Licensy(commands.Bot):
    def __init__(self):
        self.config = config
        self.db_client = DatabaseClient()
        self.update_in_progress: bool = False
        self.up_time_start_time = get_current_time()
        self._prefix_cache = {}
        self._language_cache = {}
        self._owner = None
        self._was_ready_once = False

        super().__init__(
            max_messages=None,
            command_prefix=Licensy.prefix_callable,
            case_insensitive=True,
            description=self.config.BOT_DESCRIPTION,
            owner_ids=set(self.config.BOT_OWNERS.values())
        )

    @property
    def owner_mention(self) -> str:
        """Owner is loaded on first on_ready, however if bot is just booted up this will return just 'loading'"""
        return self._owner.mention if self._owner is not None else "loading"

    @staticmethod
    async def prefix_callable(bot: "Licensy", message: discord.Message) -> str:
        return await bot.get_guild_prefix(message.guild)

    async def get_guild_prefix(self, guild: Union[discord.Guild, None]) -> str:
        default_prefix = self.config.DEFAULT_PREFIX

        # In case of DMs just return default prefix
        if guild is None:
            return default_prefix

        if cached_prefix := self._prefix_cache.get(guild.id):
            return cached_prefix

        try:
            fetched_prefix = await self.db_client.get_guild_prefix(guild.id)
        except Exception as err:
            # If fetching prefix from database errors just use the default prefix.
            logger.error(
                f"Can't get guild {guild} prefix. Error:{err}. "
                f"Using '{default_prefix}' as prefix."
            )
            return default_prefix
        else:
            self._prefix_cache[guild.id] = fetched_prefix
            return fetched_prefix

    def reload_config(self):
        importlib.reload(config)
        self.description = config.BOT_DESCRIPTION
        logger.info("Config successfully reloaded.")

    async def _populate_prefix_cache(self) -> None:
        self._prefix_cache = await self.db_client.get_all_guild_prefixes()
        logger.info("Guild prefix cache successfully reloaded.")

    async def _populate_language_cache(self) -> None:
        self._language_cache = await self.db_client.get_all_guild_languages()
        logger.info("Guild language cache successfully reloaded.")

    async def _load_owner(self) -> discord.User:
        app_info = await self.application_info()
        return app_info.owner

    async def on_ready(self):
        if not self._was_ready_once:
            await self._first_on_ready()
            self._was_ready_once = True

        # On each reconnect repopulate the cache
        await self._populate_prefix_cache()
        await self._populate_language_cache()

    async def _first_on_ready(self):
        console_logger.info(
            f"Successfully logged in as {self.user.name} ID:{self.user.id} \t"
            f"d.py {discord.__version__} \t"
            "Further logging output will go to log file.."
        )

        self._owner = await self._load_owner()

    async def on_command_error(self, context: commands.Context, exception: Exception):
        ctx = context

        # If command has local error handler, return
        if hasattr(ctx.command, "on_error"):
            return

        # Get the original exception if there is any (for example CommandInvokeError,  ConversionError..)
        error = getattr(exception, "original", exception)

        if isinstance(error, commands.MissingPermissions):
            # Note that this check is specifically for error raised by @commands.has_permissions

            # Bot owners can bypass guild permissions
            if not await self.owner_bypass(ctx):
                await ctx.send(embed=failure(f"{error}"))

        elif isinstance(error, commands.CommandOnCooldown):
            # Cool-downs are ignored for bot owners
            if not await self.owner_bypass(ctx):
                await ctx.send(embed=failure(f"{error}"), delete_after=5)

        elif isinstance(error, discord.errors.Forbidden):
            # Reference https://discord.com/developers/docs/topics/opcodes-and-status-codes
            if error.code == 50013:  # Missing Permissions
                msg = f"{error}.\nCheck role hierarchy - I can only manage roles below me."
            elif error.code == 50007:  # Cannot send messages to this user.
                msg = f"{error}.\nHint: Disabled DMs?"
            else:
                msg = f"{error}."

            try:
                await ctx.send(embed=failure(msg))
            except discord.errors.Forbidden:
                # If we get Forbidden again just ignore.
                return

        elif isinstance(error, DatabaseMissingData):
            await ctx.send(embed=failure(f"Database error: {error}"))
            await self.log_error(f"{error}", ctx=ctx)

        elif isinstance(error, AsyncioTimeoutError):
            await ctx.send(embed=failure("You took too long to reply."))

        elif isinstance(error, commands.CommandError):
            # Capture any other command error and notify context. This is so we don't
            # log traceback from custom or any other command errors and spam the log channel.
            # (custom means any errors derived from CommandError but not available in dpy library)
            await ctx.send(embed=failure(f"{error}"), delete_after=5)

        else:
            # If we got here it means we got an unexpected error / possible bug.
            await self._deal_with_unexpected_command_error(ctx, error)

    async def _deal_with_unexpected_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """
        Deals with unexpected command error by getting the traceback and basic info on context and sending it to log.
        It will also notify the context channel about the error but in short note (will cut the message if it's too
        long as to not spam the chat).

        Parameters
        ----------
        ctx: discord.ext.commands.Context
            Context where the error occurred.
        error: Exception
            Error that was raised.
        """
        error_type = type(error)

        # Don't spam the chat with long errors.
        feedback_error = str(error) if len(str(error)) < 200 else "Error too long to display."
        feedback_message = f"Uncaught {error_type} exception in command '{ctx.command}'"

        traceback_message = traceback.format_exception(etype=error_type, value=error, tb=error.__traceback__)
        log_message = f"{feedback_message} {traceback_message}"

        logger.critical(log_message)
        await self.log_error(log_message, ctx=ctx)
        await ctx.send(embed=failure(f"{feedback_message}: {feedback_error}"))

    async def on_error(self, event: str, *args, **kwargs):
        ctx = self._try_to_get_context(*args, **kwargs)
        exception_type, exception_value, exception_traceback = sys.exc_info()

        if isinstance(exception_type, discord.Forbidden):
            return  # Ignore annoying messages (eg. if user disables DMs and event tries to DM)

        traceback_message = traceback.format_exception(
            etype=exception_type,
            value=exception_value,
            tb=exception_traceback
        )

        log_message = f"{event} event error exception!\n{traceback_message}"
        logger.critical(log_message)
        await self.log_error(log_message, ctx=ctx)

    @classmethod
    def _try_to_get_context(cls, *args, **kwargs) -> Union[commands.Context, None]:
        """
        Tries to extract context from *args and **kwargs, if not found returns None.

        Returns
        -------
        context: Union[commands.Context, None]
            Context if found else None
        """
        if ctx := kwargs.pop("ctx", None) is not None:
            return ctx

        for arg in args:
            if isinstance(arg, commands.Context):
                return arg

        # Sometimes it isn't context but message and context can be recreated with it.
        for arg in args:
            if isinstance(arg, discord.Message):
                return commands.Context(message=arg, prefix="dummy")

    async def owner_bypass(self, ctx: commands.Context) -> bool:
        """
        Bot owners can bypass guild permissions and command cool-downs.
        Bot owners are set from config upon bot initialization.

        Parameters
        ----------
        ctx: discord.ext.commands.Context
            Context where the command was called.
            If the command message author is one of bot owners then re-invoke the command.
        Returns
        -------
        is_developer: bool
            Is context message author is one of bot owners or not.

        """
        if ctx.message.author.id not in self.owner_ids:
            return False

        # reinvoke() bypasses error handlers so we surround it with try/catch and just log the errors.
        try:
            await ctx.reinvoke()
        except Exception as e:
            logger.warning(f"Re-invoking command for owner bypass failed: {ctx.message} {e}")
            await ctx.send(embed=failure(f"{e}"))
        else:
            return True

    async def log_error(self, message: str, *, ctx: Union[commands.Context, None] = None):
        if not self.is_ready() or self.is_closed():
            return

        error_log_channel = self.get_channel(self.config.DEVELOPER_LOG_CHANNEL_ID)
        if error_log_channel is None:
            logger.critical("Can't send to error log channel as error log channel can't be found!")
            return

        split_messages = list(Licensy.split_string_into_chunks(message, 1800))

        for count, message in enumerate(split_messages):
            if count > 5:
                await error_log_channel.send("```Stopping spam, too many pages. See log for more info.```")
                break

            title = f"Log {count + 1}/{len(split_messages)}"

            if count == 0:
                # Log with full info only on the first log message.
                log_embed = log(message, ctx=ctx, title=title)
            else:
                log_embed = log(message, title=title)

            await error_log_channel.send(embed=log_embed)

    @staticmethod
    def split_string_into_chunks(string: str, chunk_size: int) -> Generator[str, None, None]:
        for i in range(0, len(string), chunk_size):
            yield string[i:i + chunk_size]
