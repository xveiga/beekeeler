import asyncio
import datetime
from typing import OrderedDict
import logging
import logging.handlers

from discord import Intents
from discord.ext import commands

from utils.context import ExtendedContext
from utils.compare import local_remote_compare
from database.dao.guild import BotGuild

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


class Beekeeler(commands.Bot):
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

        for ext in extensions:
            try:
                self.load_extension("cogs.{0}".format(ext))
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

    async def _fetch_guild_changes(self):
        remote_guilds = await self.fetch_guilds(limit=200).flatten()
        local_guilds = await self.db.get_guilds()

        added, removed, persistent = await local_remote_compare(
            local_guilds, remote_guilds, lambda l, r: l.gid == r.id
        )

        # Add new guilds
        for g in added:
            await self.db.add_guild(BotGuild(g.id, g.name))
            self.logger.debug('Added guild "{}"'.format(g.name))

        # Remove old guilds
        for g in removed:
            await self.db.remove_guild(g.gid)
            self.logger.debug('Removed guild "{}"'.format(g.name))

        for g in await self.db.get_guilds():
            # Check control channel still exists
            if self.get_channel(g.control_channel) is None:
                await self.db.set_guild_cc(g.gid, None)

    async def _open_db(self):
        if self.db.is_open():
            return
        try:
            await self.db.open()
            if await self.db.is_first_run():
                self.logger.info("First run detected, creating database structures...")
                await self.db.create_tables()
            self.logger.info("Database initialization successful")
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
        await self._fetch_guild_changes()
        self.logger.info("Ready")

    async def process_commands(self, message):
        return await self.invoke(await self.get_context(message, cls=ExtendedContext))
        # return await super().process_commands(message)

    def run(self, *args, **kwargs):
        self.logger.info("Opening database: " + str(self.db.get_uri()))
        self.loop.run_until_complete(self._open_db())
        self.upstamp = datetime.datetime.utcnow()
        super().run(*args, **kwargs)
        loop = asyncio.new_event_loop()
        self.logger.info("Gracefully closing database")
        loop.run_until_complete(self.db.close())
