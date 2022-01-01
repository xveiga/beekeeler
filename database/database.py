from database.dao.guild import BotGuild


class BotDB:
    async def open(self):
        raise NotImplementedError

    async def close(self):
        raise NotImplementedError

    async def is_first_run(self):
        raise NotImplementedError

    async def create_tables(self):
        raise NotImplementedError

    async def add_guild(self, guild: BotGuild):
        raise NotImplementedError

    async def get_guild(self, gid: int):
        raise NotImplementedError

    async def get_guilds(self):
        raise NotImplementedError

    async def get_guild_name(self):
        raise NotImplementedError

    async def get_guild_prefix(self, gid: int):
        raise NotImplementedError

    async def get_guild_cc(self, gid: int):
        raise NotImplementedError

    async def remove_guild(self, gid: int):
        raise NotImplementedError

    async def set_guild_cc(self, gid: int, cmd_channel: int):
        raise NotImplementedError

    async def set_guild_prefix(self, gid: int, cmd_prefix: str):
        raise NotImplementedError
