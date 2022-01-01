import sys
import logging


def setup_logging():
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
