import os
import asyncio
import logging
from sys import stdout

from dotenv import load_dotenv
from tortoise import Tortoise

from bot import Licensy
from bot.config import DATABASE_DSN


load_dotenv()

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
console_logger = logging.getLogger("console")
console = logging.StreamHandler(stdout)
console.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(message)s"))
console_logger.addHandler(console)
root_logger.addHandler(console)  # TODO temporal for development stage


"""
uvloop is a fast, drop-in replacement of the built-in asyncio event loop that makes asyncio 2-4x faster.
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


async def database_init():
    await Tortoise.init(
        db_url=DATABASE_DSN,
        modules={'models': ["bot.models.models"]}
    )
    await Tortoise.generate_schemas()


loop = asyncio.get_event_loop()
loop.run_until_complete(database_init())
Licensy(loop=loop).run(os.getenv("BOT_TOKEN"))
