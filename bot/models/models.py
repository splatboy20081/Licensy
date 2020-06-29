from tortoise.models import Model
from tortoise.fields import (
    ForeignKeyRelation, ForeignKeyField, SmallIntField, IntField, BigIntField,
    CharField, BooleanField, DatetimeField, CASCADE, SET_NULL
)


class Guild(Model):
    id = BigIntField(pk=True, generated=False)
    custom_prefix = CharField(max_length=10, default="")
    custom_license_format = CharField(max_length=100, default="")
    license_branding = CharField(max_length=50, default="")
    timezone = SmallIntField(default=0)
    enable_dm_redeem = BooleanField(default=True)
    preserve_previous_duration = BooleanField(default=True)
    language = CharField(max_length=5, default="en")

    reminders_enabled = BooleanField(default=True)
    reminder_activation_one = SmallIntField(default=1)
    reminder_activation_two = SmallIntField(default=0)
    reminder_activation_three = SmallIntField(default=0)
    reminders_channel_id = BigIntField(default=0)
    reminders_ping_in_reminders_channel = BooleanField(default=True)
    reminders_send_to_dm = BooleanField(default=True)

    license_log_channel_enabled = BooleanField(default=False)
    license_log_channel_id = BigIntField(default=0)

    bot_diagnostics_channel_enabled = BooleanField(default=False)
    bot_diagnostics_channel_id = BigIntField(default=0)

    class Meta:
        table = "guilds"


class Role(Model):
    guild: ForeignKeyRelation[Guild] = ForeignKeyField("models.Guild", on_delete=CASCADE)
    id = BigIntField(pk=True, generated=False)
    tier_level = SmallIntField(default=None, null=True)
    tier_power = SmallIntField(default=None, null=True)

    class Meta:
        table = "roles"
        unique_together = (("guild", "tier_level", "tier_power"),)


class RolePacket(Model):
    guild: ForeignKeyRelation[Guild] = ForeignKeyField("models.Guild", on_delete=CASCADE)
    name = CharField(max_length=50)
    default_role_duration_minutes = IntField()

    class Meta:
        table = "role_packets"
        unique_together = (("name", "guild"),)


class PacketRole(Model):
    role_packet: ForeignKeyRelation[RolePacket] = ForeignKeyField("models.RolePacket", on_delete=CASCADE)
    duration_minutes = IntField()
    role: ForeignKeyRelation[Role] = ForeignKeyField("models.Role", on_delete=CASCADE)

    class Meta:
        table = "packet_roles"
        unique_together = (("role_packet", "role"),)


class License(Model):
    guild: ForeignKeyRelation[Guild] = ForeignKeyField("models.Guild", on_delete=CASCADE)
    role_packet: ForeignKeyRelation[RolePacket] = ForeignKeyField("models.RolePacket", on_delete=SET_NULL, null=True)
    key = CharField(pk=True, generated=False, max_length=50)
    regenerating = BooleanField(default=False)
    uses_left = SmallIntField()

    class Meta:
        table = "licenses"


class LicensedMember(Model):
    member_id = BigIntField()
    reminder_one_sent = BooleanField(default=False)
    reminder_two_sent = BooleanField(default=False)
    reminder_three_sent = BooleanField(default=False)
    license: ForeignKeyRelation[License] = ForeignKeyField("models.License", on_delete=CASCADE)

    class Meta:
        table = "licensed_members"
        unique_together = (("member_id", "license"),)


class LicensedRole(Model):
    role: ForeignKeyRelation[Role] = ForeignKeyField("models.Role", on_delete=CASCADE)
    expiration = DatetimeField(null=True)
    licensed_member: ForeignKeyRelation[LicensedMember] = ForeignKeyField("models.LicensedMember", on_delete=CASCADE)

    class Meta:
        table = "licensed_roles"
        unique_together = (("role", "licensed_member"),)
