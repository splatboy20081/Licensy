from tortoise.models import Model
from tortoise.exceptions import FieldError, IntegrityError
from tortoise.fields import (
    OneToOneField, ForeignKeyRelation, ForeignKeyField, SmallIntField, IntField,
    BigIntField, CharField, BooleanField, DatetimeField, CASCADE, SET_NULL, RESTRICT
)

from bot.utils import i18n_handler
from bot.utils.licence_helper import LicenseFormatter


# TODO add either database level or code level checks for fields.
# TODO periodic check for cleaning data, example if LicensedMember has no more LicensedRoles then remove
# TODO DURATION?


class Guild(Model):
    """Represents Discord guild(server)."""
    id = BigIntField(pk=True, generated=False, description="Guild ID.")
    custom_prefix = CharField(
        max_length=10,
        default="",
        description=(
            "Represents guild prefix used for calling commands."
            "If it's not set (empty string) then default bot prefix from config will be used."
        )
    )
    custom_license_format = CharField(
        max_length=100,
        default="",
        description="Format to use when generating license. If it's a empty string then default format is used."
    )
    license_branding = CharField(
        max_length=50,
        default="",
        description=(
            "Custom branding string to be displayed in generated license."
            "It's position can be changed by changing license format. Can be empty string."
        )
    )
    timezone = SmallIntField(
        default=0,
        description=(
            "Timezone offset from UTC+0 (which is default bot timezone)."
            "For internal calculations the default bot timezone is always used,"
            "this is only used for **displaying** expiration date for guild."
        )
    )
    enable_dm_redeem = BooleanField(default=True, description="Can the redeem command also be used in bot DMs?")
    preserve_previous_duration = BooleanField(
        default=True,
        description=(
            "Behaviour to happen if the member redeems a role that he already has licenses for or if new role has "
            "the same tier power&level as existing licensed role (if tier_level is >0 aka activated)."
            "true-new duration will be sum of new duration + time remaining from the previous duration."
            "false-duration is reset and set to new duration only."
        )
    )
    language = CharField(max_length=2, default="en", description="Two letter language code per ISO 639-1")
    reminders_enabled = BooleanField(
        default=True,
        description=(
            "Whether reminders are enabled or not. Reminders notify members before the license expires."
        )
    )
    reminder_activations = OneToOneField("ReminderActivations", on_delete=RESTRICT)
    reminders_channel_id = BigIntField(
        default=0,
        description=(
            "Guild channel ID where reminder message will be sent."
            "Value of 0 (or any invalid ID) will disable sending messages."
        )
    )
    reminders_ping_in_reminders_channel = BooleanField(
        default=True,
        description="Whether to ping the reminding member when sending to reminders channel."
    )
    reminders_send_to_dm = BooleanField(
        default=True,
        description=(
            "Whether to **also** send reminder to member DM."
            "Note: This does not affect message sending to reminder channel."
        )
    )
    license_log_channel_enabled = BooleanField(default=False, description="Whether license logging is enabled or not.")
    license_log_channel_id = BigIntField(
        default=0,
        description=(
            "Guild channel where license logging messages will be sent."
            "Example: redeem/add_licenses commands uses, when license activates/expires/regenerates."
            "Value of 0 (or any invalid ID) will disable sending messages."
            )
        )
    bot_diagnostics_channel_enabled = BooleanField(default=False, description="Whether bot logging is enabled or not.")
    bot_diagnostics_channel_id = BigIntField(
        default=0,
        description=(
            "Guild channel where bot diagnostic messages will be sent."
            "Examples: bot updates and their state (start/end),"
            "errors that came from usage of the bot in that guild, changing any guild settings."
            "Updates about on_guild_role_delete&on_member_role_remove."
            "Usage of revoke/revoke_all/generate/delete/delete all."
            "Value of 0 (or any invalid ID) will disable sending messages."
        )
    )

    class Meta:
        table = "guilds"

    async def _post_delete(self, *args, **kwargs) -> None:
        """Deals with deleting ReminderActivations table after this table is deleted."""
        await super()._post_delete(*args, **kwargs)
        await self.reminder_activations.delete()

    async def _pre_save(self, *args, **kwargs) -> None:
        if len(self.custom_prefix) > self.custom_prefix.max_length:
            raise FieldError(f"Custom prefix has to be under {self.custom_prefix.max_length} characters.")
        elif not LicenseFormatter.is_secure(self.custom_license_format):
            raise FieldError("Your custom license format is not secure enough! Not enough possible permutations!")
        elif len(self.license_branding) > self.license_branding.max_length:
            raise FieldError(f"License branding has to be under {self.license_branding.max_length} characters.")
        elif self.timezone not in range(-12, 15):
            raise FieldError("Invalid timezone.")
        elif self.language not in i18n_handler.LANGUAGES:
            raise FieldError("Unsupported guild language.")

        await super()._pre_save(*args, **kwargs)


class Role(Model):
    """A single role from guild."""
    id = BigIntField(pk=True, generated=False, description="Role ID.")
    guild: ForeignKeyRelation[Guild] = ForeignKeyField("models.Guild", on_delete=CASCADE)
    tier_level = SmallIntField(
        default=None,
        null=True,
        description=(
            "This represents tier for this role."
            "0 means that tiers are disabled for this role."
            "Members cannot have 2 roles from the same tier,if they do manage to redeem 2 of same tier then what will"
            "happen is that they will only get the one that has the higher tier power, other one will get deactivated."
        )
    )
    tier_power = SmallIntField(
        default=None,
        null=True,
        description=(
            "Used to determine role hierarchy if member is trying to claim 2 roles from the same tier level."
            "The one with higher tier power will remain while the other one will get deactivated."
            # TODO What happens with expiration date (if license is timed)
        )
    )  # TODO test if these None work with real scenario

    class Meta:
        table = "roles"
        unique_together = (("guild", "tier_level", "tier_power"),)


class RolePacket(Model):
    MAXIMUM_ROLES = 20

    guild: ForeignKeyRelation[Guild] = ForeignKeyField("models.Guild", on_delete=CASCADE)
    name = CharField(max_length=50)
    default_role_duration = IntField(
        description=(
            "Default role duration in minutes to use on new roles that don't specifically specify their own duration."
        )
    )

    class Meta:
        table = "role_packets"
        unique_together = (("name", "guild"),)

    async def _pre_save(self, *args, **kwargs) -> None:
        if len(self.name) > self.name.max_length:
            raise FieldError(f"Packet name has to be under {self.name.max_length} characters.")

        await super()._pre_save(*args, **kwargs)


class PacketRole(Model):
    """Single role from role packet."""
    role_packet: ForeignKeyRelation[RolePacket] = ForeignKeyField("models.RolePacket", on_delete=CASCADE)
    role: ForeignKeyRelation[Role] = ForeignKeyField("models.Role", on_delete=CASCADE)
    duration = IntField(description="Duration of this role in minutes to last when redeemed.")

    class Meta:
        table = "packet_roles"
        unique_together = (("role_packet", "role"),)

    async def _pre_save(self, *args, **kwargs) -> None:
        if self.duration < 0:
            raise FieldError("Invalid duration for role.")
        elif await self.role_packet.packet_roles.count() > RolePacket.MAXIMUM_ROLES:
            raise IntegrityError(
                f"Cannot add packet role to `{self.role_packet.name}` as number of "  # TODO maybe need to await?
                f"roles in packet would exceed limit of {RolePacket.MAXIMUM_ROLES} roles."
            )

        await super()._pre_save(*args, **kwargs)


class License(Model):
    key = CharField(pk=True, generated=False, max_length=50)
    reminder_activations = OneToOneField("ReminderActivations", on_delete=RESTRICT)
    guild: ForeignKeyRelation[Guild] = ForeignKeyField("models.Guild", on_delete=CASCADE)
    role_packet: ForeignKeyRelation[RolePacket] = ForeignKeyField("models.RolePacket", on_delete=SET_NULL, null=True)
    regenerating = BooleanField(default=False)
    uses_left = SmallIntField(
        default=1,
        description=(
            "Number of times this same license can be used (useful example for giveaways)."
            "Value of 0 marks this license as deactivated and it cannot be redeemed again."
        )
    )

    class Meta:
        table = "licenses"

    async def _post_delete(self, *args, **kwargs) -> None:
        """Deals with deleting ReminderActivations table after this table is deleted."""
        await super()._post_delete(*args, **kwargs)
        await self.reminder_activations.delete()

    async def _pre_save(self, *args, **kwargs) -> None:
        if self.uses_left < 0:
            raise FieldError("License number of uses cannot be negative.")
        elif self.regenerating and self.uses_left > 1:
            raise FieldError("License cannot be regenerating and have multiple-uses at the same time!")

        if self.regenerating and self.uses_left == 0:
            """Deals with regenerating licenses by creating a new licenses that has the same data as this one.

            Creates new license column with new key and marks it ready for activation (uses_left=1)
            Also copies reminder_activations data from previous license and creates new  reminder_activations table
            with that data since it is OneToOneField.
            """
            guild = await self.guild
            reminder_activations = await self.reminder_activations

            new_key = LicenseFormatter.generate_single(guild.custom_license_format, guild.license_branding)
            new_reminder_activations = await reminder_activations.clone()

            new_license = await self.clone(pk=new_key)
            new_license.reminder_activations = new_reminder_activations
            await new_license.save()

        await super()._pre_save(*args, **kwargs)


class LicensedMember(Model):
    member_id = BigIntField()
    license: ForeignKeyRelation[License] = ForeignKeyField("models.License", on_delete=CASCADE)

    class Meta:
        table = "licensed_members"
        unique_together = (("member_id", "license"),)


class LicensedRole(Model):
    role: ForeignKeyRelation[Role] = ForeignKeyField("models.Role", on_delete=CASCADE)
    licensed_member: ForeignKeyRelation[LicensedMember] = ForeignKeyField("models.LicensedMember", on_delete=CASCADE)
    expiration = DatetimeField(null=True)

    class Meta:
        table = "licensed_roles"
        unique_together = (("role", "licensed_member"),)


class Reminder(Model):
    activation = BigIntField(
        description=(
            "This represents amount of minutes to send the reminder before license expiration."
            "For example if the license duration is 10_080 minutes (aka 7 days) and reminder is set to 80 then "
            "reminder will be sent exactly after 10_000 minutes pass."
        )
    )
    send = BooleanField(
        default=False,
        description=(
            "Was this reminder sent to user or not."
            "We don't want to spam the user with reminders once activation activates."
        )
    )
    licensed_member: ForeignKeyRelation[LicensedMember] = ForeignKeyField(
        "models.LicensedMember",
        on_delete=CASCADE,
        description="Member who is going to be reminded about his license expiring."
    )

    class Meta:
        table = "reminders"
        unique_together = (("activation", "licensed_member"),)


class ReminderActivations(Model):
    first_activation = BigIntField()
    second_activation = BigIntField(default=0)
    third_activation = BigIntField(default=0)
    fourth_activation = BigIntField(default=0)
    fifth_activation = BigIntField(default=0)

    def __getitem__(self, activation: int):
        if activation == 1:
            return self.first_activation
        elif activation == 2:
            return self.second_activation
        elif activation == 3:
            return self.third_activation
        elif activation == 4:
            return self.fourth_activation
        elif activation == 5:
            return self.fifth_activation
        else:
            raise IndexError("No such activation.")

    @classmethod
    async def default(cls) -> "ReminderActivations":
        return await cls.create(first_activation=720)

    async def _pre_save(self, *args, **kwargs) -> None:
        self._check_valid_activations()
        await self._pre_save(*args, **kwargs)

    def _check_valid_activations(self):
        if not (
            self.first_activation
            > self.second_activation
            > self.third_activation
            > self.fourth_activation
            > self.fifth_activation
        ):
            raise FieldError("Reminder activation fields have to be ordered from highest to lowest.")

    class Meta:
        table = "reminders_settings"
        unique_together = (
            ("first_activation", "second_activation", "third_activation", "fourth_activation", "fifth_activation"),
        )
