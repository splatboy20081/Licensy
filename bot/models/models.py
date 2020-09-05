from typing import Tuple

from tortoise.models import Model
from tortoise.queryset import QuerySet
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


class ReminderActivations(Model):
    first_activation = BigIntField(default=720)
    second_activation = BigIntField(default=0)
    third_activation = BigIntField(default=0)
    fourth_activation = BigIntField(default=0)
    fifth_activation = BigIntField(default=0)

    @classmethod
    async def create_easy(
        cls,
        first_activation: int,
        second_activation: int = 0,
        third_activation: int = 0,
        fourth_activation: int = 0,
        fifth_activation: int = 0
    ) -> "ReminderActivations":
        return await cls.create(
            first_activation=first_activation,
            second_activation=second_activation,
            third_activation=third_activation,
            fourth_activation=fourth_activation,
            fifth_activation=fifth_activation
        )

    def get_all_activations(self) -> Tuple[int, ...]:
        """Helper method for easier accessing all fields.

        If one of model activation fields change this also needs to change.
        """
        return (
            self.first_activation, self.second_activation, self.third_activation,
            self.fourth_activation, self.fifth_activation
        )

    def __getitem__(self, activation: int):
        return self.get_all_activations()[activation]

    async def _post_save(self, *args, **kwargs) -> None:
        self._check_valid_first_activation()
        self._check_activation_ranges()
        self._check_valid_order_activations()  # TODO does it get saved if this raises?

        await super()._post_save(*args, **kwargs)

    def _check_valid_first_activation(self):
        """This table, if it exists, should have at least one proper activation."""
        return self.get_all_activations()[0] > 0

    def _check_activation_ranges(self):
        for activation in self.get_all_activations():
            if activation < 0:
                raise FieldError(f"Reminder activation value {activation} cannot be negative.")

    def _check_valid_order_activations(self):
        """Checks if activations are in good order.

        First activation has to be the highest number as it is first activation therefore it has to activate first
        so to achieve that it has to be the highest number as the number represent how long before license expiration
        will reminder activate.

        Every next activation has to be smaller than the previous (smaller == later reminder).
        """
        # Ignore activations that are set to 0 as those are considered disabled,
        # also because our check would fail (0 == 0 and 0 < 0)
        positive_activations = tuple(activation for activation in self.get_all_activations() if activation > 0)
        for activation_pair in zip(positive_activations, positive_activations[1:]):
            if activation_pair[0] == activation_pair[1]:
                raise FieldError("Reminder activation fields can't have duplicate values.")
            elif activation_pair[0] < activation_pair[1]:
                raise FieldError("Reminder activation fields have to be ordered from highest to lowest.")

    class Meta:
        table = "reminders_settings"


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
            "Timezone integer offset from UTC+0 (which is default bot timezone)."
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
    reminder_activations = OneToOneField(
        "models.ReminderActivations",
        on_delete=RESTRICT,
        description="Will be created upon guild creation automatically.",
        related_name="guild"
    )
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
    license_log_channel_id = BigIntField(
        default=0,
        description=(
            "Guild channel where license logging messages will be sent."
            "Example: redeem/add_licenses commands uses, when license activates/expires/regenerates."
            "Value of 0 (or any invalid ID) will disable sending messages."
            )
        )
    diagnostic_channel_id = BigIntField(
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
        await self.reminder_activations.delete()  # TODO test this

    async def _pre_save(self, *args, **kwargs) -> None:
        if (max_prefix_length := self._meta.fields_map['custom_prefix'].max_length) < len(self.custom_prefix):
            raise FieldError(f"Custom prefix has to be under {max_prefix_length} characters.")
        elif self.custom_license_format and not LicenseFormatter.is_secure(self.custom_license_format):
            generated_permutations = LicenseFormatter.get_format_permutations(self.custom_license_format)
            raise FieldError(
                f"Your custom license format '{self.custom_license_format}' is not secure enough!"
                f"Not enough possible permutations!"
                f"Required: {LicenseFormatter.min_permutation_count}, got: {generated_permutations}"
            )
        elif (max_brand_length := self._meta.fields_map['license_branding'].max_length) < len(self.license_branding):
            raise FieldError(f"License branding has to be under {max_brand_length} characters.")
        elif self.timezone not in range(-12, 15):
            raise FieldError("Invalid timezone.")
        elif self.language not in i18n_handler.LANGUAGES:
            raise FieldError("Unsupported guild language.")

        await super()._pre_save(*args, **kwargs)

    @classmethod
    async def create(cls, **kwargs) -> Model:
        # TODO test if not passing and passing one works
        reminder_activations = kwargs.pop("reminder_activations", None)
        if not reminder_activations:
            reminder_activations = await ReminderActivations.create()

        return await super().create(reminder_activations=reminder_activations, **kwargs)


class AuthorizedRole(Model):
    role_id = BigIntField()
    guild: ForeignKeyRelation[Guild] = ForeignKeyField("models.Guild", on_delete=CASCADE)
    authorization_level = SmallIntField(
        default=1,
        description="Depending on authorization level this role can use certain privileged commands from the guild."
    )

    class Meta:
        table = "authorized_users"
        unique_together = (("role_id", "guild"),)

    async def _pre_save(self, *args, **kwargs) -> None:
        if not (1 <= self.authorization_level <= 5):
            raise FieldError("Authorization level has to be in 1-5 range.")
        await super()._pre_save(*args, **kwargs)


class Role(Model):
    """A single role from guild."""
    id = BigIntField(pk=True, generated=False, description="Role ID.")
    guild: ForeignKeyRelation[Guild] = ForeignKeyField("models.Guild", on_delete=CASCADE, related_name="roles")
    tier_level = SmallIntField(
        default=0,
        description=(
            "This represents tier for this role."
            "0 means that tiers are disabled for this role."
            "Members cannot have 2 roles from the same tier,if they do manage to redeem 2 of same tier then what will"
            "happen is that they will only get the one that has the higher tier power, other one will get deactivated."
        )
    )
    tier_power = SmallIntField(
        default=1,
        description=(
            "Used to determine role hierarchy if member is trying to claim 2 roles from the same tier level."
            "The one with higher tier power will remain while the other one will get deactivated."
            # TODO What happens with expiration date (if license is timed)
        )
    )

    class Meta:
        table = "roles"
        unique_together = (("guild", "id"),)

    async def _pre_save(self, *args, **kwargs) -> None:
        if not (0 <= self.tier_level <= 100):
            raise FieldError("Role tier power has to be in 0-100 range.")
        elif not (0 <= self.tier_power <= 9):
            raise FieldError("Role tier power has to be in 0-9 range.")
        elif self.tier_level != 0:  # If it's not disabled
            # TODO test if QuerySet error since guild might not be loaded
            if await Role.get(guild=self.guild, tier_level=self.tier_level, tier_power=self.tier_power).exists():
                raise IntegrityError("Can't have 2 roles with same tier level/power!")

        await super()._pre_save(*args, **kwargs)


class RolePacket(Model):
    MAXIMUM_ROLES = 20

    guild: ForeignKeyRelation[Guild] = ForeignKeyField("models.Guild", on_delete=CASCADE, related_name="packets")
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
        if (max_name_length := self._meta.fields_map['name'].max_length) < len(self.name):
            raise FieldError(f"Packet name has to be under {max_name_length} characters.")
        elif self.default_role_duration < 0:
            raise FieldError("Role packet default role duration cannot be negative.")

        await super()._pre_save(*args, **kwargs)


class PacketRole(Model):
    """Single role from role packet."""
    role: ForeignKeyRelation[Role] = ForeignKeyField("models.Role", on_delete=CASCADE)
    role_packet: ForeignKeyRelation[RolePacket] = ForeignKeyField(
        "models.RolePacket",
        on_delete=CASCADE,
        related_name="packet_roles"
    )
    duration = IntField(
        description=(
            "Duration of this role in minutes to last when redeemed."
            "Defaults to role_packet.default_role_duration if not set during creation."
        )
    )

    class Meta:
        table = "packet_roles"
        unique_together = (("role", "role_packet"),)

    @classmethod
    async def create(cls, **kwargs) -> Model:
        # If not specified during the creation then use the default one from role_packet.default_role_duration
        role_packet = kwargs.get("role_packet")
        duration = kwargs.pop("duration", None)
        if not duration:
            duration = role_packet.default_role_duration
        return await super().create(duration=duration, **kwargs)

    async def _pre_save(self, *args, **kwargs) -> None:
        if self.duration < 0:
            raise FieldError("Invalid duration for role.")
        # +1 since this is pre_save so it won't count this current one
        elif await self.role_packet.packet_roles.all().count() + 1 > RolePacket.MAXIMUM_ROLES:
            raise IntegrityError(
                f"Cannot add packet role to `{self.role_packet.name}` as number of "  # TODO maybe need to await?
                f"roles in packet would exceed limit of {RolePacket.MAXIMUM_ROLES} roles."
            )

        # Since we're accessing foreign attributes that might not yet be loaded (QuerySet)
        # we should load them just in case.
        role_guild = self.role.guild
        role_packet_guild = self.role_packet.guild

        if isinstance(role_guild, QuerySet):
            role_guild = await self.role.guild.first()
        if isinstance(role_packet_guild, QuerySet):
            role_packet_guild = await self.role_packet.guild.first()

        if role_guild.id != role_packet_guild.id:
            raise IntegrityError("Packet role fields have to point to the same guild!")

        await super()._pre_save(*args, **kwargs)


class License(Model):
    KEY_MIN_LENGTH = 14
    MAXIMUM_USES_LEFT = 1_000_000

    key = CharField(pk=True, generated=False, max_length=50)
    guild: ForeignKeyRelation[Guild] = ForeignKeyField("models.Guild", on_delete=CASCADE)
    reminder_activations = OneToOneField("models.ReminderActivations", on_delete=RESTRICT)
    regenerating = BooleanField(default=False)
    # only used if it's regenerating? I can make licensed members right at creation
    role_packet: ForeignKeyRelation[RolePacket] = ForeignKeyField(
        "models.RolePacket",
        on_delete=SET_NULL,
        null=True,
        description=(
            "[optional] Only used if the license is regenerating. so we know"
            "When all roles from license expire and the license is set as regenerating we will"
            "know which roles to re-add. Note that if the role_packet changes in the meantime it"
            "is possible the new roles will be different from previous ones."
        )

    )
    uses_left = SmallIntField(
        default=1,
        description=(
            "Number of times this same license can be used (useful example for giveaways)."
            "Value of 0 marks this license as deactivated and it cannot be redeemed again."
        )
    )

    class Meta:
        table = "licenses"

    @classmethod
    async def create(cls, **kwargs) -> Model:
        # If not specified during the creation then use the reminder_activations from guild.reminder_activations
        reminder_activations = kwargs.pop("reminder_activations", None)
        if not reminder_activations:
            reminder_activations = await ReminderActivations.create()
        return await super().create(reminder_activations=reminder_activations, **kwargs)

    async def _post_delete(self, *args, **kwargs) -> None:
        """Deals with deleting ReminderActivations table after this table is deleted."""
        await super()._post_delete(*args, **kwargs)
        await self.reminder_activations.delete()

    async def _pre_save(self, *args, **kwargs) -> None:
        if len(self.key) < self.KEY_MIN_LENGTH:
            raise FieldError(f"License key has to be longer than {self.KEY_MIN_LENGTH} characters.")
        elif self.uses_left < 0:
            raise FieldError("License number of uses cannot be negative.")
        elif self.uses_left > self.MAXIMUM_USES_LEFT:
            raise FieldError("License number of uses is too big.")
        elif self.regenerating and self.uses_left > 1:
            raise FieldError("License cannot be regenerating and have multiple-uses at the same time!")

        if self.regenerating and self.uses_left == 0:
            """Deals with regenerating licenses by creating a new licenses that has the same data as this one.

            Creates new license column with new key and marks it ready for activation (uses_left=1)
            Also copies reminder_activations data from previous license and creates new  reminder_activations table
            with that data since it is OneToOneField.
            """
            guild = await self.guild

            new_key = LicenseFormatter.generate_single(guild.custom_license_format, guild.license_branding)
            new_reminder_activations = await self.reminder_activations.clone()

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
    sent = BooleanField(
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
