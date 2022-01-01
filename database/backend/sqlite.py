import re
import aiosqlite

from database.database import BotDB
from database.dao.guild import BotGuild


class SQLiteBotDB(BotDB):
    def __init__(self, dbfile):
        super().__init__()
        self._is_open = False
        self._dbfile = dbfile
        self._conn = None

    async def open(self):
        self._is_open = True
        self._conn = await aiosqlite.connect(self._dbfile)

    async def close(self):
        await self._conn.close()
        self._is_open = False

    async def is_first_run(self):
        cursor = await self._conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table';"
        )
        first_time = (await cursor.fetchone())[0] <= 0
        return first_time

    def get_uri(self):
        return self._dbfile

    def is_open(self):
        return self._is_open

    def _filter_spaces(self, command):
        # re.sub removes indentation spaces to save db space (as sqlite just
        # copies declaration directly on the database file)
        return re.sub(" +", " ", command.replace("\n", ""))

    async def create_tables(self):
        # Bot configuration parameters for a guild
        await self._conn.execute(
            self._filter_spaces(
                """CREATE TABLE Guild (
                gid          INTEGER  NOT NULL,
                cmd_prefix   TEXT,
                cmd_channel  INTEGER,
                PRIMARY KEY(gid)
            );"""
            )
        )
        await self._conn.commit()

    async def add_guild(self, guild: BotGuild):
        await self._conn.execute(
            "INSERT INTO Guild (gid, cmd_channel) VALUES(?, ?);",
            [
                guild.gid,
                guild.control_channel,
            ],
        )
        await self._conn.commit()

    async def get_guild(self, gid: int) -> BotGuild:
        async with self._conn.execute(
            "SELECT gid, cmd_channel,  FROM Guild where gid=?;",
            [gid],
        ) as cursor:
            # return await self._get_guild_data(await cursor.fetchone())
            return BotGuild(*(await cursor.fetchone()))

    async def get_guilds(self) -> list[BotGuild]:
        async with self._conn.execute(
            "SELECT gid FROM Guild ORDER BY gid ASC;"
        ) as cursor:
            guilds = []
            async for guild in cursor:
                # NOTE: The order on the database SELECT query MUST MATCH the one
                # of the __init__ attributes on BotGuild, BotTarget and BotVoiceChannel
                guilds.append(BotGuild(*guild))
            return guilds

    async def get_guild_name(self, gid: int):
        async with self._conn.execute(
            "SELECT name FROM Guild where gid=?;", [gid]
        ) as cursor:
            return (await cursor.fetchone())[0]

    async def get_guild_prefix(self, gid: int):
        async with self._conn.execute(
            "SELECT cmd_prefix FROM Guild where gid=?;", [gid]
        ) as cursor:
            return (await cursor.fetchone())[0]

    async def get_guild_cc(self, gid: int):
        async with self._conn.execute(
            "SELECT cmd_channel FROM Guild where gid=?;", [gid]
        ) as cursor:
            return (await cursor.fetchone())[0]

    async def get_guild_enable(self, gid: int):
        async with self._conn.execute(
            "SELECT bkill_enable FROM Guild where gid=?;", [gid]
        ) as cursor:
            return (await cursor.fetchone())[0]

    async def remove_guild(self, gid: int):
        # NOTE: Adding "ON DELETE CASCADE" on Guild table creation statement also deletes foreign key dependencies.
        # This way the database engine takes the responsibility of deleting related VoiceChannel and Target rows.
        # Needs the pragma "foreign_keys = ON" to work though, which requires further investigation.
        await self._conn.execute("DELETE FROM VoiceChannel WHERE gid=?;", [gid])
        await self._conn.execute("DELETE FROM Target WHERE gid=?;", [gid])
        await self._conn.execute("DELETE FROM Guild WHERE gid=?;", [gid])
        await self._conn.commit()

    async def set_guild_cc(self, gid: int, cmd_channel: int):
        await self._conn.execute(
            "UPDATE Guild SET cmd_channel=? WHERE gid=?;", [cmd_channel, gid]
        )
        await self._conn.commit()

    async def set_guild_prefix(self, gid: int, cmd_prefix: str):
        await self._conn.execute(
            "UPDATE Guild SET cmd_prefix=? WHERE gid=?;", [cmd_prefix, gid]
        )
        await self._conn.commit()
