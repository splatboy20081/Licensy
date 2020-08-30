import discord

"""
Patches built in Discord classes attributes so that the bot uses slightly less memory.

For example patching Member by setting joined_at and premium_since to always None
could save about 3 times as much bytes, which can lead do dozen of MBs in saving since
bots can have hundreds of thousands of Member objects.

Completely safe to use as all changed attributes can still be accessed as usual.
"""


class OptimizedBaseUser(discord.user.BaseUser):
    """Forces avatar to always be None."""
    __slots__ = ('name', 'id', 'discriminator', 'avatar', 'bot', 'system', '_public_flags', '_state')

    def _update(self, data):
        data['avatar'] = None
        super()._update(data)

    @classmethod
    def _copy(cls, user):
        copy = super()._copy(user)
        copy.avatar = None
        return copy


class OptimizedMember(discord.Member):
    """
    Forces joined_at and premium_since attributes to always be None.
    Forces activities to always be empty.
    """
    __slots__ = ('_roles', 'joined_at', 'premium_since', '_client_status',
                 'activities', 'guild', 'nick', '_user', '_state')

    def __init__(self, *, data, guild, state):
        data['joined_at'] = None
        data['premium_since'] = None
        data['activities'] = []
        super().__init__(data=data, guild=guild, state=state)

    def _update(self, data):
        data['premium_since'] = None
        super()._update(data)

    def _presence_update(self, data, user):
        data['activities'] = []
        super()._presence_update(data, user)


discord.BaseUser = OptimizedBaseUser
discord.Member = OptimizedMember
