from typing import Union

from discord import Embed, Color, Member, User
from discord.ext.commands import Context


def simple_embed(message: str, title: str, color: Color) -> Embed:
    """
    Constructs basic embed.

    Parameters
    ----------
    message: str
        Description to be used for embed.
    title: str
        Title to be used for embed.
    color: discord.Color
        Color to be used for embed

    Returns
    -------
    embed: discord.Embed
        Newly constructed embed.
    """
    return Embed(title=title, description=message, color=color)


def info(message: str, member: Union[Member, User, None] = None, title: str = "Info") -> Embed:
    """
    Constructs embed with title that has default value "Info".
    Embed color depends on passed member top role color.

    Parameters
    ----------
    message: str
        Description to be used for embed.
    member: Union[Member, User, None]
        Member object to get the color of it's top role from. Default value None.
        If type is User or None then the color will be green.
    title: str
        Title to be used for embed. Defaults to "Info"

    Returns
    -------
    embed: discord.Embed
        Newly constructed embed.

    """
    return Embed(title=title, description=message, color=get_top_role_color(member, fallback_color=Color.green()))


def success(message: str, member: Union[Member, User, None] = None) -> Embed:
    """
    Constructs embed with fixed title "Success".
    Embed color depends on passed member top role color.

    Parameters
    ----------
    message: str
         Description to be used for embed.
    member: Union[Member, User, None]
        Member object to get the color of it's top role from. Default value None.
        If type is User or None then the color will be green.

    Returns
    -------
    embed: discord.Embed
            Newly constructed embed with title "Success".
    """
    return simple_embed(message, "Success", get_top_role_color(member, fallback_color=Color.green()))


def warning(message: str) -> Embed:
    """
    Constructs embed with fixed title "Warning" and fixed color gold.

    Parameters
    ----------
    message: str
        Description to be used for embed.

    Returns
    -------
    embed: discord.Embed
            Newly constructed embed with title "Warning" and gold color.
    """
    return simple_embed(message, "Warning", Color.dark_gold())


def failure(message: str) -> Embed:
    """
    Constructs embed with fixed title "Failure" and fixed color red.

    Parameters
    ----------
    message: str
        Description to be used for embed.

    Returns
    -------
    embed: discord.Embed
            Newly constructed embed with title "Failure" and red color.
    """
    return simple_embed(message, "Failure", Color.red())


def log(message: str, *, ctx: Union[Context, None], title: str = "Log") -> Embed:
    """
    Constructs log embed that can have additional info from context such as
    guild, author and channel ID set in its footer.
    Color is fixed to red.

    Parameters
    ----------
    message: str
        Description to be used for embed.
    ctx: Union[discord.ext.commands.Context, None]
        Context to get footer data from.
        Data is guild (if it's not None), author and channel ID.
        If ctx is None returns embed without footer.
    title: str
        Title to be used for embed. Defaults to "Log"

    Returns
    -------
    embed: discord.Embed
        Newly constructed log embed.
    """
    log_embed = simple_embed(message, title, Color.red())

    if ctx is not None:
        guild = "DM" if ctx.guild is None else ctx.guild.id
        author = f"Author: {ctx.author} ; {ctx.author.id}"
        footer = f"Guild: {guild}    Author: {author}    Channel {ctx.channel.id}"
        log_embed.set_footer(text=footer)

    return log_embed


def get_top_role_color(member: Union[Member, User, None], *, fallback_color: Color) -> Color:
    """
    Tries to get member top role color and if it fails then returns fallback_color (this makes it work in DMs).
    Will also return fallback_color if the retrieved top role is the default (gray) Discord role color.

    Parameters
    ----------
    member: Union[Member, User, None]
        Member object to get the color of it's top role from.
        If member top role is default (gray) Discord role color then fallback_color will be used as return.
        Also if type is User or None then the fallback_color will be returned.
    fallback_color: discord.Color
        Color to return in case param member is not of type discord.Member
        or if top role from param member is the default (gray) Discord role.

    Returns
    -------
    color: discord.Color
        Color representing top role color.
    """
    try:
        color = member.top_role.color
    except AttributeError:
        # Fix for DMs
        return fallback_color

    if color == Color.default():
        return fallback_color
    else:
        return color
