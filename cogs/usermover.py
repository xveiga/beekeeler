import logging

from discord.ext import commands
from discord import VoiceChannel

import cogs.utils as utils


def setup(bot):
    bot.add_cog(UserMover(bot))


class UserMover(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name="move")
    @commands.guild_only()
    async def move_channel_users(
        self, ctx: commands.Context, destination: VoiceChannel = None
    ):
        if not await utils.check_cc(self.bot, ctx):
            return
        # TODO: Move all users from issuer's channel to another channel
