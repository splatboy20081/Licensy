import discord

from typing import Final


BOT_DESCRIPTION: Final = "Licensy bot - easily manage expiration of roles with subscriptions!"
SUPPORT_CHANNEL_INVITE: Final = "https://discord.gg/trCYUkz"
PATREON_LINK: Final = "https://www.patreon.com/Licensy"
PAYPAL_LINK: Final = "https://www.paypal.me/wizardofcro"
TOP_GG_VOTE_LINK: Final = "https://top.gg/bot/604057722878689324"
SOURCE_CODE_LINK: Final = "https://github.com/albertopoljak/Licensy/"
FAQ_LINK: Final = "https://github.com/albertopoljak/Licensy/wiki/FAQ"
QUICKSTART_LINK: Final = "https://github.com/albertopoljak/Licensy#quickstart-bot-usage"
DEFAULT_PREFIX: Final = "."  # TODO temporal for development phase

DEVELOPER_LOG_CHANNEL_ID: Final = 613847243266719755
SUGGESTIONS_CHANNEL_ID: Final = 621366699316215828
GUILD_LOG_CHANNEL_ID: Final = 716792061302407260
UPDATE_CHANNEL_ID: Final = 625404542535598090
MAXIMUM_UNUSED_GUILD_LICENSES: Final = 100  # Change this then also change FAQ
MAXIMUM_LICENSE_DURATION_HOURS: Final = 8784  # Represents maximum possible hours (leap year) in 12 months

BOT_OWNERS: Final = {  # Warning! These users bypass all checks such as permissions and cool-downs
    "BrainDead": 197918569894379520
}

BOT_PERMISSIONS: Final = discord.Permissions()
BOT_PERMISSIONS.update(manage_roles=True, read_messages=True, send_messages=True, manage_messages=True)

DATABASE_DSN: Final = "sqlite://db.sqlite3"
