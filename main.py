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

import logging
import logging.handlers
import json
import sys

from bot import Bot
from database.backend.sqlite import SQLiteBotDB

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def __setup_logging():
    # Setup logging format
    logfmt = (
        "[%(asctime)s] %(levelname)s - %(name)s (%(filename)s:%(lineno)d): %(message)s"
    )
    datefmt = "%d/%m/%Y %H:%M:%S"

    # Setup log levels by module
    # asyncio
    logging.getLogger("asyncio").setLevel(logging.WARN)

    # discord.py
    logging.getLogger("discord.client").setLevel(logging.WARN)
    logging.getLogger("discord.gateway").setLevel(logging.WARN)
    logging.getLogger("discord.http").setLevel(logging.WARN)
    logging.getLogger("discord.state").setLevel(logging.WARN)

    # aiosqlite
    logging.getLogger("aiosqlite").setLevel(logging.INFO)

    # Stdout output
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(logging.Formatter(fmt=logfmt, datefmt=datefmt))

    # File output
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename="bot.log", when="D", backupCount=7
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt=logfmt, datefmt=datefmt))

    logging.basicConfig(
        level=logging.DEBUG,
        encoding="utf-8",
        format=logfmt,
        datefmt=datefmt,
        handlers=[stdout_handler, file_handler],
    )


def main(config_file):
    # Initialize loggers
    __setup_logging()

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

    # Create bot with database instance and configuration
    bot = Bot(config["modules"], db, config)

    # Run
    bot.run(config["token"])


if __name__ == "__main__":
    # Read config file from arguments if specified, otherwise default to config.json
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Reading config.json")
        main("config.json")
