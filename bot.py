import asyncio
import json
import sys
import datetime
from typing import OrderedDict
import logging
import logging.handlers

from discord import Intents
from discord.ext import commands

from database.backend.sqlite import SQLiteBotDB

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

"""
Discord bitrate reduction prank bot

Requires privileged intents (Server Members Intent enabled on bot page in developer portal)
https://discordapi.com/permissions.html#8

Scopes:
    - Bot

Bot Permissions:
    - Administrator (0x8)

Requires at least Python 3.9 (for function return type annotations)
"""


class Bot(commands.Bot):
    def __init__(self, extensions, db, config=None):
        self.db = db
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.prefixes = OrderedDict()

        # Enable intents for user list fetching
        intents = Intents.default()
        intents.members = True
        # Create bot
        super().__init__(command_prefix=self._get_prefix, intents=intents)
        self.add_listener(self.on_ready)

        for ext in extensions:
            try:
                self.load_extension(ext)
            except Exception as e:
                self.logger.error(
                    "Failed to load extension {}\n{}: {}".format(
                        ext, type(e).__name__, e
                    )
                )

    async def _get_prefix(self, bot, message):
        # If DM, use no prefix
        if message.guild is None:
            return ""
        # Check if current server is cached in memory
        gid = message.guild.id
        prefix = self.prefixes.get(gid)
        if prefix is not None:
            return prefix

        # Else, search in database
        prefix = await self.db.get_guild_prefix(gid)
        # If not found set default and add entry to database
        if prefix is None:
            prefix = "$"
            await self.db.set_guild_prefix(gid, prefix)
        # LIFO Cache eviction
        if len(self.prefixes) >= 100:
            self.prefixes.popitem(False)
        # Add to cache
        self.prefixes[gid] = prefix
        return prefix

    async def invalidate_prefix(self, gid: int):
        self.prefixes.pop(gid, None)

    async def _open_db(self):
        if self.db.is_open():
            return
        try:
            await self.db.open()
            if await self.db.is_first_run():
                await self.db.create_tables()
        except Exception as exception:
            self.logger.error(
                'Unable to access database "'
                + self.db.get_uri()
                + '": '
                + str(exception)
            )
            raise SystemExit from exception

    async def on_ready(self):
        self.logger.info(
            "Logged in as {0}#{1} (app name: {2}, id: {3})".format(
                self.user.display_name,
                self.user.discriminator,
                self.user.name,
                self.user.id,
            )
        )

    def run(self, *args, **kwargs):
        self.logger.info("Database: " + str(self.db.get_uri()))
        self.loop.run_until_complete(self._open_db())
        self.upstamp = datetime.datetime.utcnow()
        super().run(*args, **kwargs)
        loop = asyncio.new_event_loop()
        self.logger.info("Gracefully closing database")
        loop.run_until_complete(self.db.close())


def main(config_file):
    # Setup logging
    logfmt = (
        "[%(asctime)s] %(levelname)s - %(name)s (%(filename)s:%(lineno)d): %(message)s"
    )
    datefmt = "%d/%m/%Y %H:%M:%S"
    logging.basicConfig(
        level=logging.DEBUG,
        # filename="bot.log",
        encoding="utf-8",
        format=logfmt,
        datefmt=datefmt,
    )
    root_log = logging.getLogger()
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(logging.Formatter(fmt=logfmt, datefmt=datefmt))
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename="bot.log", when="D", backupCount=7
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt=logfmt, datefmt=datefmt))
    root_log.addHandler(stdout_handler)
    root_log.addHandler(file_handler)

    # Load config file
    try:
        with open(config_file, "rt") as file:
            config = json.load(file)
    except Exception as ex:
        logging.log.critical(
            "Unable to read config file " + config_file + ": " + str(ex)
        )
        raise SystemExit from ex

    # Initialize database (sqlite implementation)
    db = SQLiteBotDB(config["db"])
    bot = Bot(config["modules"], db, config)

    # Run
    bot.run(config["token"])


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Reading config.json")
        main("config.json")
