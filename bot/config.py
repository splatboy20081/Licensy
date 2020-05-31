import discord

from typing import Final


BOT_DESCRIPTION: Final = "Licensy bot - easily manage expiration of roles with subscriptions!"
SUPPORT_CHANNEL_INVITE: Final = "https://discord.gg/trCYUkz"
PATREON_LINK: Final = "https://www.patreon.com/Licensy"
TOP_GG_VOTE_LINK: Final = "https://top.gg/bot/604057722878689324"
SOURCE_CODE_LINK: Final = "https://github.com/albertopoljak/Licensy/"
DEFAULT_PREFIX: Final = "lic!"

DEVELOPER_LOG_CHANNEL_ID: Final = 613847243266719755
GUILD_LOG_CHANNEL_ID: Final = 716792061302407260
UPDATE_CHANNEL_ID: Final = 625404542535598090
MAXIMUM_UNUSED_GUILD_LICENSES: Final = 100
MAXIMUM_LICENSE_DURATION_HOURS: Final = 8784  # Represents maximum possible hours (leap year) in 12 months

DEVELOPERS: Final = {
    "BrainDead": 197918569894379520
}

BOT_PERMISSIONS: Final = discord.Permissions()
BOT_PERMISSIONS.update(manage_roles=True, read_messages=True, send_messages=True, manage_messages=True)
