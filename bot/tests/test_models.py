from tortoise import exceptions
from tortoise.contrib import test
from tortoise.contrib.test import initializer, finalizer

from bot.models import models
from bot.utils.i18n_handler import LANGUAGES


initializer(['bot.models.models'], db_url="sqlite://test-{}.sqlite")
# TODO test cascade deletions


class TestModels(test.TestCase):
    async def test_guild_unique(self):
        await models.Guild.create(id=123)

        # Guild IDs are unique
        with self.assertRaises(exceptions.IntegrityError):
            await models.Guild.create(id=123)

    async def test_license_key_unique(self):
        guild_1 = await models.Guild.create(id=123)
        guild_2 = await models.Guild.create(id=456)

        await models.License.create(key="A"*20, guild=guild_1, reminder_activations=guild_1.reminder_activations)

        # Licenses keys are unique, no matter the guild
        with self.assertRaises(exceptions.IntegrityError):
            await models.License.create(key="A" * 20, guild=guild_2, reminder_activations=guild_2.reminder_activations)

    async def test_roles_unique(self):
        guild1 = await models.Guild.create(id=123)
        guild2 = await models.Guild.create(id=456)

        # Create some roles
        await models.Role.create(id=11, guild=guild1)
        await models.Role.create(id=12, guild=guild1)
        await models.Role.create(id=21, guild=guild2)
        await models.Role.create(id=22, guild=guild2)
        await models.Role.create(id=23, guild=guild2)

        # Role IDs should be unique, no matter the guild
        with self.assertRaises(exceptions.IntegrityError):
            await models.Role.create(id=11, guild=guild1)
        with self.assertRaises(exceptions.IntegrityError):
            await models.Role.create(id=11, guild=guild2)

        self.assertEqual(2, await guild1.roles.all().count())
        self.assertEqual(3, await guild2.roles.all().count())

    async def test_guild_prefix(self):
        # Guild prefix can be any string as long as it's within length limit.
        valid_prefix = ("", "test", "123", "?*+", "owo_prefix")
        invalid_prefix = ("long_prefix", "very_long_prefix")
        guild = await models.Guild.create(id=123)

        for valid in valid_prefix:
            guild.custom_prefix = valid
            await guild.save()

        for invalid in invalid_prefix:
            guild.custom_prefix = invalid
            with self.assertRaises(exceptions.FieldError):
                await guild.save()

    async def test_guild_license_format(self):
        valid_license_formats = (
            "",  # empty string means to use default format provided by LicenseFormatter class (which is secure).
            "DDDDD-DDDDD-DDDDD-DDDDD-DDDDD",
            "AAAA(LLL)-SAS+DAAD/SOS",
            "AAAAAAAAAAAAAA",
            "AA!A?A{A}A*A-A+A1A2A3A4AA"
        )
        invalid_license_formats = ("test", "AA", "AAAAAAAAAA", "1234567890")
        guild = await models.Guild.create(id=123)

        for valid in valid_license_formats:
            guild.custom_license_format = valid
            await guild.save()

        for invalid in invalid_license_formats:
            guild.custom_license_format = invalid
            with self.assertRaises(exceptions.FieldError):
                await guild.save()

    async def test_guild_branding(self):
        # Everything is valid as long as it's within length limit.
        valid_branding = ("", "1234567890", "?*/*-+!#$%$&/(", "blabla", "t"*50)
        invalid_branding = ("t"*51, )
        guild = await models.Guild.create(id=123)

        for valid in valid_branding:
            guild.license_branding = valid
            await guild.save()

        for invalid in invalid_branding:
            guild.license_branding = invalid
            with self.assertRaises(exceptions.FieldError):
                await guild.save()

    async def test_guild_timezone(self):
        valid_timezone = range(-12, 15)
        # Technically some of timezones can have decimal place but we don't allow those.
        invalid_timezone = (-100, -14, -13, -9.5, -9.3, 3.3, 15, 16, 100)
        guild = await models.Guild.create(id=123)

        for valid in valid_timezone:
            guild.timezone = valid
            await guild.save()

        for invalid in invalid_timezone:
            guild.timezone = invalid
            with self.assertRaises(exceptions.FieldError):
                await guild.save()

    async def test_guild_language(self):
        invalid_languages = (
            "",  # cannot be emtpy
            "eng",  # has to condone to standard (2 letter)
            "xx"  # non-existent language
        )
        guild = await models.Guild.create(id=123)

        # Depending on defined languages in i18n_handler
        for valid in LANGUAGES:
            guild.language = valid
            await guild.save()

        for invalid in invalid_languages:
            guild.language = invalid
            with self.assertRaises(exceptions.FieldError):
                await guild.save()

    async def test_guild_reminders_creation(self):
        # ReminderActivations table should be auto-created when creating new guild.
        self.assertEqual(0, await models.ReminderActivations.all().count())
        guild1 = await models.Guild.create(id=123)
        self.assertEqual(1, await models.ReminderActivations.all().count())
        guild2 = await models.Guild.create(id=456)
        self.assertEqual(2, await models.ReminderActivations.all().count())

        # Default values of auto-created ReminderActivations tables should be the same since we didn't specify specific
        # values, access to attributes should work.
        self.assertEqual(guild1.reminder_activations.first_activation, guild2.reminder_activations.first_activation)

        # If we manually specify ReminderActivations table it should not auto create
        reminder_activations_3 = await models.ReminderActivations.create(second_activation=60)
        guild3 = await models.Guild.create(id=789, reminder_activations=reminder_activations_3)
        self.assertEqual(3, await models.ReminderActivations.all().count())

        # Created ReminderActivations tables should be unique for each guild
        self.assertNotEqual(guild1.reminder_activations.id, guild2.reminder_activations.id)
        self.assertNotEqual(guild2.reminder_activations.id, guild3.reminder_activations.id)

    async def test_model_copy(self):
        # This test will fail because tortoise copy is either broken or I'm not using it as I'm supposed to?
        await models.Guild.create(id=123)
        guild_reminders = await models.ReminderActivations.get(id=1)
        clone = guild_reminders.clone()
        await clone.save()  # fails ... guessing I need to manually get next auto-generating ID

        self.assertEqual(2, await models.ReminderActivations.all().count())

    async def test_role_packet_unique_name(self):
        guild1 = await models.Guild.create(id=123)
        guild2 = await models.Guild.create(id=456)

        # Create some packets
        await models.RolePacket.create(guild=guild1, name="packet11", default_role_duration=720)
        await models.RolePacket.create(guild=guild1, name="packet12", default_role_duration=360)
        await models.RolePacket.create(guild=guild2, name="packet22", default_role_duration=0)

        # Packet names should be unique per guild
        await models.RolePacket.create(guild=guild2, name="packet11", default_role_duration=720)
        with self.assertRaises(exceptions.IntegrityError):
            await models.RolePacket.create(guild=guild1, name="packet11", default_role_duration=720)
        with self.assertRaises(exceptions.IntegrityError):
            await models.RolePacket.create(guild=guild2, name="packet11", default_role_duration=720)

    async def test_role_packet_default_role_duration(self):
        guild1 = await models.Guild.create(id=123)

        # Cannot have negative default role duration
        with self.assertRaises(exceptions.FieldError):
            await models.RolePacket.create(guild=guild1, name="negative", default_role_duration=-1)

    async def test_packet_role(self):
        guild1 = await models.Guild.create(id=123)
        guild2 = await models.Guild.create(id=456)

        # Create some roles
        role11 = await models.Role.create(id=11, guild=guild1)
        role21 = await models.Role.create(id=21, guild=guild2)
        role22 = await models.Role.create(id=22, guild=guild2)

        # Create some role packets
        role_packet_1 = await models.RolePacket.create(guild=guild1, name="packet1", default_role_duration=360)
        role_packet_2 = await models.RolePacket.create(guild=guild2, name="packet2", default_role_duration=720)

        # Add roles to role packet
        await models.PacketRole.create(role=role11, role_packet=role_packet_1)
        await models.PacketRole.create(role=role21, role_packet=role_packet_2)
        await models.PacketRole.create(role=role22, role_packet=role_packet_2)

        # Cannot have 2 of the same roles in the packet.
        with self.assertRaises(exceptions.IntegrityError):
            await models.PacketRole.create(role=role11, role_packet=role_packet_1)
        with self.assertRaises(exceptions.IntegrityError):
            await models.PacketRole.create(role=role21, role_packet=role_packet_2)

        # Cannot add role from X guild to role packet that is from Y guild (guilds have to be the same).
        with self.assertRaises(exceptions.IntegrityError):
            await models.PacketRole.create(role=role11, role_packet=role_packet_2)
        with self.assertRaises(exceptions.IntegrityError):
            await models.PacketRole.create(role=role21, role_packet=role_packet_1)

    async def test_packet_role_default_duration(self):
        guild1 = await models.Guild.create(id=123)
        guild2 = await models.Guild.create(id=456)

        # Create some roles
        role11 = await models.Role.create(id=11, guild=guild1)
        role21 = await models.Role.create(id=21, guild=guild2)
        role22 = await models.Role.create(id=22, guild=guild2)
        role23 = await models.Role.create(id=23, guild=guild2)

        # Create some role packets
        role_packet_1 = await models.RolePacket.create(guild=guild1, name="packet1", default_role_duration=360)
        role_packet_2 = await models.RolePacket.create(guild=guild2, name="packet2", default_role_duration=720)

        # Add roles to role packet without specifying duration
        packet_role_11 = await models.PacketRole.create(role=role11, role_packet=role_packet_1)
        packet_role_21 = await models.PacketRole.create(role=role21, role_packet=role_packet_2)
        packet_role_22 = await models.PacketRole.create(role=role22, role_packet=role_packet_2)

        # If duration is not specified during the creation of packet role it should use duration from it's role packet
        self.assertEqual(role_packet_1.default_role_duration, packet_role_11.duration)
        self.assertEqual(role_packet_2.default_role_duration, packet_role_21.duration)
        self.assertEqual(role_packet_2.default_role_duration, packet_role_22.duration)

        # If duration is specified during the creation of packet role it should use that duration
        packet_role_23 = await models.PacketRole.create(role=role23, role_packet=role_packet_2, duration=999)
        self.assertEqual(999, packet_role_23.duration)

    async def test_packet_role_duration(self):
        guild = await models.Guild.create(id=123)
        role = await models.Role.create(id=1, guild=guild)
        role_packet = await models.RolePacket.create(guild=guild, name="packet1", default_role_duration=360)

        # Packet role duration cannot be negative
        with self.assertRaises(exceptions.FieldError):
            await models.PacketRole.create(role=role, role_packet=role_packet, duration=-1)

    async def test_packet_role_maximum_roles(self):
        guild1 = await models.Guild.create(id=123)

        # Create some role packets
        role_packet = await models.RolePacket.create(guild=guild1, name="packet1", default_role_duration=360)

        for role_number in range(models.RolePacket.MAXIMUM_ROLES):
            role = await models.Role.create(id=role_number, guild=guild1)
            await models.PacketRole.create(role=role, role_packet=role_packet)

        self.assertEqual(await role_packet.packet_roles.all().count(), models.RolePacket.MAXIMUM_ROLES)

        # If we add one more over the limit it should error
        role = await models.Role.create(id=models.RolePacket.MAXIMUM_ROLES, guild=guild1)
        with self.assertRaises(exceptions.IntegrityError):
            await models.PacketRole.create(role=role, role_packet=role_packet)

    async def test_packet_role_queryset(self):
        """
        Packet role has a check that checks if role guild and role packet guild are the same.
        However due to nature of async tortoise ORM and lazy loading it can happen that those
        guilds are not loaded but are QuerySet instead.

        This test checks if guilds are properly checked if they are QuerySet.
        """
        guild1 = await models.Guild.create(id=123)
        role1 = await models.Role.create(id=11, guild=guild1)

        # If we were to capture this variable and pass it when creating packet role it would work.
        # We would be able to access attribute role_packet.guild.id since we're passing already loaded guild.
        await models.RolePacket.create(guild=guild1, name="packet1", default_role_duration=360)
        # However we're going to get it instead. This way guild attribute is not loaded and is of type QuerySet.
        # So if we try to access role_packet.guild.id it will fail.
        # Guild is not loaded even if passed as kwarg because it's just used to differentiate,
        # ORM backend won't load all foreign keys (since that could be a lot of loading).
        role_packet = await models.RolePacket.get(guild=guild1, name="packet1")
        # Now packet_role_1 will have a role_packet attribute and it's guild attribute will be QuerySet.
        # Model has to fetch it now it order to access it's ID.
        packet_role_1 = await models.PacketRole.create(role=role1, role_packet=role_packet, duration=999)

        # Let's do the same thing but with role
        await models.Role.create(id=22, guild=guild1)
        role2 = await models.Role.get(id=22)
        packet_role_2 = await models.PacketRole.create(role=role2, role_packet=role_packet, duration=888)

        # Extra check for peace of mind
        packet_roles = await role_packet.packet_roles.all()
        self.assertEqual(packet_roles[0], packet_role_1)
        self.assertEqual(packet_roles[1], packet_role_2)

    async def test_license_key(self):
        guild = await models.Guild.create(id=123)
        role_packet = await models.RolePacket.create(guild=guild, name="packet1", default_role_duration=360)

        valid_keys = ("quite_long_key", "very__long"*5)
        invalid_keys = ("", "very_short", "quite___short")

        for valid in valid_keys:
            await models.License.create(key=valid, guild=guild, role_packet=role_packet)

        for invalid in invalid_keys:
            with self.assertRaises(exceptions.FieldError):
                await models.License.create(key=invalid, guild=guild, role_packet=role_packet)

    async def test_license_uses(self):
        guild = await models.Guild.create(id=123)
        role_packet = await models.RolePacket.create(guild=guild, name="packet1", default_role_duration=360)

        # Invalid uses left
        with self.assertRaises(exceptions.FieldError):
            await models.License.create(key="12345"*4, guild=guild, role_packet=role_packet, uses_left=-1)

        # Too big uses left
        with self.assertRaises(exceptions.FieldError):
            await models.License.create(key="67890" * 4, guild=guild, role_packet=role_packet, uses_left=1_000_001)

    @classmethod
    def tearDownClass(cls):
        finalizer()
