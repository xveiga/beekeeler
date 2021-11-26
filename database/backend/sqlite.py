import re
import aiosqlite

from database.database import BotDB
from database.dao.guild import BotGuild
from database.dao.target import BotTarget
from database.dao.voicechannel import BotVoiceChannel


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
                name         TEXT,
                cmd_prefix   TEXT,
                cmd_channel  INTEGER,
                bkill_amt    INTEGER,
                bkill_int    INTEGER,
                bkill_min    INTEGER,
                bkill_enable BOOLEAN  NOT NULL,
                PRIMARY KEY(gid)
            );"""
            )
        )

        # Targeted users
        await self._conn.execute(
            self._filter_spaces(
                """CREATE TABLE Target (
                uid  INT    NOT NULL,
                gid  INT    NOT NULL,
                issuer  INT,
                PRIMARY KEY(uid, gid),
                FOREIGN KEY(gid) REFERENCES Guild(gid)
            );"""
            )
        )

        # Stores original bitrate of voice channel
        await self._conn.execute(
            self._filter_spaces(
                """CREATE TABLE VoiceChannel (
                cid     INT      NOT NULL,
                gid     INT      NOT NULL,
                br      INT      NOT NULL,
                bkill   BOOLEAN  NOT NULL,
                PRIMARY KEY(cid),
                FOREIGN KEY(gid) REFERENCES Guild(gid)
            );"""
            )
        )

        await self._conn.commit()

    async def add_guild(self, guild: BotGuild):
        await self._conn.execute(
            "INSERT INTO Guild (gid, name, cmd_channel, bkill_amt, bkill_int, bkill_min, bkill_enable) VALUES(?, ?, ?, ?, ?, ?, ?);",
            [
                guild.gid,
                guild.name,
                guild.control_channel,
                guild.bitrate_reduction_amount,
                guild.bitrate_reduction_interval,
                guild.min_bitrate,
                guild.enable,
            ],
        )
        await self._conn.commit()

    async def get_guild(self, gid: int) -> BotGuild:
        async with self._conn.execute(
            "SELECT gid, name, cmd_channel, bkill_amt, bkill_int, bkill_min, bkill_enable FROM Guild where gid=?;",
            [gid],
        ) as cursor:
            # return await self._get_guild_data(await cursor.fetchone())
            return BotGuild(*(await cursor.fetchone()))

    async def get_guilds(self) -> list[BotGuild]:
        async with self._conn.execute(
            "SELECT gid, name, cmd_channel, bkill_amt, bkill_int, bkill_min, bkill_enable FROM Guild ORDER BY gid ASC;"
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

    async def set_guild_name(self, gid: int, name: str):
        await self._conn.execute("UPDATE Guild SET name=? WHERE gid=?;", [name, gid])
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

    async def set_guild_bitrates(self, gid: int, amount: int, interval: int):
        await self._conn.execute(
            "UPDATE Guild SET bkill_amt=?, bkill_int=? WHERE gid=?;",
            [amount, interval, gid],
        )
        await self._conn.commit()

    async def set_guild_min_bitrate(self, gid: int, min: int):
        await self._conn.execute(
            "UPDATE Guild SET bkill_min=? WHERE gid=?;", [min, gid]
        )
        await self._conn.commit()

    async def set_guild_enable(self, gid: int, enable: bool):
        await self._conn.execute(
            "UPDATE Guild SET bkill_enable=? WHERE gid=?;", [enable, gid]
        )
        await self._conn.commit()

    async def add_target(self, target: BotTarget):
        await self._conn.execute(
            "INSERT INTO Target (gid, uid, issuer) VALUES(?, ?, ?);",
            [target.gid, target.uid, target.issuer],
        )
        await self._conn.commit()

    async def remove_target(self, gid: int, uid: int):
        await self._conn.execute(
            "DELETE FROM Target WHERE gid=? and uid=?;", [gid, uid]
        )
        await self._conn.commit()

    async def get_targets(self, gid: int):
        targets = []
        async with self._conn.execute(
            "SELECT uid, gid, issuer from Target where gid=?;",
            [gid],
        ) as tcursor:
            async for target in tcursor:
                targets.append(BotTarget(*target))
        return targets

    # async def set_target_name(self, gid: int, uid: int, name: str, discriminator:str):
    #     await self._conn.execute(
    #         "UPDATE Target SET name=?, discriminator=? WHERE gid=? and uid=?;", [name, discriminator, gid, uid]
    #     )
    #     await self._conn.commit()

    async def is_target(self, gid: int, uid: int):
        async with self._conn.execute(
            "SELECT EXISTS(SELECT 1 FROM Target where gid=? and uid=?);",
            [gid, uid],
        ) as cursor:
            return (await cursor.fetchone())[0] != 0

    async def get_target_issuer(self, gid: int, uid: int):
        async with self._conn.execute(
            "SELECT issuer FROM Target where gid=? and uid=?;", [gid, uid]
        ) as cursor:
            res = await cursor.fetchone()
            return None if res is None else (res)[0]

    async def clear_targets(self, gid: int):
        await self._conn.execute("DELETE FROM Target WHERE gid=?;", [gid])
        await self._conn.commit()

    async def add_voicechannel(self, voicechannel: BotVoiceChannel) -> None:
        await self._conn.execute(
            "INSERT INTO VoiceChannel (cid, gid, br, bkill) VALUES(?, ?, ?, ?);",
            [
                voicechannel.cid,
                voicechannel.gid,
                voicechannel.bitrate,
                voicechannel.bkill,
            ],
        )
        await self._conn.commit()

    async def get_voicechannels(self) -> list[BotVoiceChannel]:
        channels = []
        async with self._conn.execute(
            "SELECT gid, cid, br, bkill from VoiceChannel;"
        ) as ccursor:
            async for channel in ccursor:
                channels.append(BotVoiceChannel(*channel))
        return channels

    async def get_guild_voicechannels(self, gid: int) -> list[BotVoiceChannel]:
        channels = []
        async with self._conn.execute(
            "SELECT gid, cid, br, bkill from VoiceChannel WHERE gid=?;", [gid]
        ) as ccursor:
            async for channel in ccursor:
                channels.append(BotVoiceChannel(*channel))
        return channels

    async def get_voicechannel_bitrate(self, gid: int, cid: int) -> int:
        async with self._conn.execute(
            "SELECT br FROM VoiceChannel where gid=? and cid=?;", [gid, cid]
        ) as cursor:
            return (await cursor.fetchone())[0]

    async def set_voicechannel_bitrate(self, gid: int, cid: int, bitrate: int) -> None:
        await self._conn.execute(
            "UPDATE VoiceChannel SET br=? WHERE gid=? and cid=?;", [bitrate, gid, cid]
        )
        await self._conn.commit()

    async def get_voicechannel_bkill(self, gid: int, cid: int) -> bool:
        async with self._conn.execute(
            "SELECT bkill FROM VoiceChannel where gid=? and cid=?;", [gid, cid]
        ) as cursor:
            return (await cursor.fetchone())[0] != 0

    async def set_voicechannel_bkill(self, gid: int, cid: int, bkill: bool) -> None:
        await self._conn.execute(
            "UPDATE VoiceChannel SET bkill=? WHERE gid=? and cid=?;", [bkill, gid, cid]
        )
        await self._conn.commit()

    async def remove_voicechannel(self, gid: int, cid: int) -> None:
        await self._conn.execute(
            "DELETE FROM VoiceChannel WHERE gid=? and cid=?;", [gid, cid]
        )
        await self._conn.commit()
