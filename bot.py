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

import json
import sys
import logging

from beekeeler import Beekeeler
from utils.logging import setup_logging
from database.backend.sqlite import SQLiteBotDB


def main(config_file):
    # Initialize loggers
    setup_logging()

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
    bot = Beekeeler(config["modules"], db, config)

    # Run
    bot.run(config["token"])


if __name__ == "__main__":
    # Read config file from arguments if specified, otherwise default to config.json
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Reading config.json")
        main("config.json")
