import os
import logging
import traceback
from sys import stdout
from pathlib import Path

from dotenv import load_dotenv

from bot import Licensy


root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")

console_logger = logging.getLogger("console")
console = logging.StreamHandler(stdout)
console.setFormatter(formatter)
console_logger.addHandler(console)

root_logger.addHandler(console)  # TODO temporal for development stage

load_dotenv()
bot = Licensy()


for extension_path in Path("bot/cogs").glob("*.py"):
    extension_name = extension_path.stem
    dotted_path = f"bot.cogs.{extension_name}"

    try:
        bot.load_extension(dotted_path)
    except Exception as e:
        traceback_msg = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        console_logger.info(f"Failed to load cog {dotted_path} - traceback:{traceback_msg}")
    else:
        console_logger.info(f"loaded {dotted_path}")


"""
uvloop is a ultra fast asyncio event loop that makes asyncio 2-4x faster.
It's a optional dependency as it is not supported on Windows.
"""
try:
    # noinspection PyUnresolvedReferences
    import uvloop
    uvloop.install()
except ImportError:
    console_logger.info("uvloop not supported on this system.")
else:
    console_logger.info("uvloop successfully installed.")


bot.run(os.getenv("BOT_TOKEN"))
