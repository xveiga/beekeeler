"""neoflex.py: This just prints the neofetch to the Discord channel."""

__author__      = "forcegk"
__copyright__   = "Copyright 2021, Galiza. Free as-in-freedom use :)"

import logging

from discord.ext import commands
from discord import Embed
from cogs import utils
from os import popen

def setup(bot):
    bot.add_cog(Neoflex(bot))


class Neoflex(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name="neofetch")
    async def neofetch(
        self,
        ctx: commands.Context,
    ):

        await utils.send_message(
            self.logger,
            ctx,
            "```\n{0}\n```".format(popen("/usr/bin/neofetch | /usr/bin/sed -e 's/\x1B\[[0-9;\?]*[a-zA-Z]//g' | /usr/bin/sed -e 's/`/\u200b`/g'").read().rstrip())
        )
