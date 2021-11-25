from database.dao.guild import BotGuild
from database.dao.target import BotTarget
from database.dao.voicechannel import BotVoiceChannel


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

    async def get_guild_enable(self, gid: int):
        raise NotImplementedError

    async def remove_guild(self, gid: int):
        raise NotImplementedError

    async def set_guild_name(self, gid: int, name: str):
        raise NotImplementedError

    async def set_guild_cc(self, gid: int, cmd_channel: int):
        raise NotImplementedError

    async def set_guild_prefix(self, gid: int, cmd_prefix: str):
        raise NotImplementedError

    async def set_guild_bitrates(self, gid: int, amount: int, interval: int):
        raise NotImplementedError

    async def set_guild_min_bitrate(self, gid: int, min: int):
        raise NotImplementedError

    async def set_guild_enable(self, gid: int, enable: bool):
        raise NotImplementedError

    async def add_target(self, target: BotTarget):
        raise NotImplementedError

    async def remove_target(self, gid: int, uid: int):
        raise NotImplementedError

    async def get_targets(self, gid: int):
        raise NotImplementedError

    async def is_target(self, gid: int, uid: int):
        raise NotImplementedError

    async def get_target_issuer(self, gid: int, uid: int):
        raise NotImplementedError

    async def clear_targets(self, gid: int) -> None:
        raise NotImplementedError

    async def add_voicechannel(self, voicechannel: BotVoiceChannel) -> None:
        raise NotImplementedError

    async def get_voicechannels(self) -> list[BotVoiceChannel]:
        return NotImplementedError

    async def get_guild_voicechannels(self, gid: int) -> list[BotVoiceChannel]:
        return NotImplementedError

    async def get_voicechannel_bitrate(self, gid: int, cid: int) -> int:
        raise NotImplementedError

    async def set_voicechannel_bitrate(self, gid: int, cid: int, bitrate: int) -> None:
        raise NotImplementedError

    async def get_voicechannel_bkill(self, gid: int, cid: int) -> bool:
        raise NotImplementedError

    async def set_voicechannel_bkill(self, gid: int, cid: int, bkill: bool) -> None:
        raise NotImplementedError

    async def remove_voicechannel(self, gid: int, cid: int) -> None:
        raise NotImplementedError
