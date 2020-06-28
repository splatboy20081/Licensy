import re

from discord.ext.commands import BadArgument, Context, Converter


class Duration(Converter):
    """
    Convert duration strings into integer representing minute duration.
    Original source: https://github.com/python-discord/bot/blob/master/bot/converters.py
    """

    duration_parser = re.compile(
        r"((?P<years>\d+?) ?(years|year|y) ?)?"
        r"((?P<months>\d+?) ?(months|month) ?)?"
        r"((?P<weeks>\d+?) ?(weeks|week|w) ?)?"
        r"((?P<days>\d+?) ?(days|day|d) ?)?"
        r"((?P<hours>\d+?) ?(hours|hour|h) ?)?"
        r"((?P<minutes>\d+?) ?(minutes|minute|min))?"
    )

    minute_converter = {
        "years": 365 * 24 * 60,
        "months": 30 * 24 * 60,
        "weeks": 7 * 24 * 60,
        "days": 24 * 60,
        "hours": 60,
        "minutes": 1
    }

    async def convert(self, ctx: Context, duration_string: str) -> int:
        """
        Convert duration strings into integer representing minute duration.
        Example "3m 7days" will be converted to 139680.

        Parameters
        ----------
        ctx: Context
            Command context.
        duration_string: str
            String that will be converted to duration. Some valid examples:
                5y 3months 7h
                3m 7weeks
                5hours 3years
                4w

            You can stack same keywords:
                3m 5m 7m
                1y 7d 1y

            Each entry has to be some number followed by one of the keywords defined in duration_parser.
            Converter is not case sensitive and support following keywords:
            - years: `years`, `year`, `y`
            - months: `months`, `month`
            - weeks: `weeks`, `week`, `w`
            - days: `days`, `day`, `d`
            - hours: `hours`, `hour`, `h`
            - minutes: 'minutes', `minute`, `min`

            Months do not have keyword 'm' because it can be confused for minutes.

        Returns
        -------
        minutes: int
            Total duration in minutes that was specified in duration_string.
        """
        minutes = 0

        for word in duration_string.split():
            match = self.duration_parser.fullmatch(word)
            if match is None or not match.group(0):
                raise BadArgument(f"Invalid duration provided `{word}`.")

            time_data = {k: int(v) for k, v in match.groupdict(default=0).items()}
            for key, value in time_data.items():
                minutes += self.minute_converter[key] * value

        return minutes


class PositiveInteger(Converter):
    async def convert(self, ctx: Context, message: str) -> int:
        """
        Converts param message to positive int (>0).

        Parameters
        ----------
        ctx: discord.ext.commands.Context
            Context for converter.
        message: str
            Message argument that we will try to convert to positive integer.

        Raises
        ------
        ValueError
            Param message can't be converted to int.

        discord.ext.commands.BadArgument
            If the integer is not positive aka less than 1.

        Returns
        -------
        positive_integer : int
            Integer that is positive (>0)
        """
        integer = int(message)
        if integer < 1:
            raise BadArgument("Passed integer has to be larger than zero.")
        else:
            return integer
