"""neoflex.py: This just prints the neofetch to the Discord channel."""

__author__ = "forcegk"
__copyright__ = "Copyright 2021, Galiza. Free as-in-freedom use :)"

import logging

from discord.ext import commands
from os import popen
from os.path import exists


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
        message = (
            "```\n{0}\n```".format(
                popen(
                    "/usr/bin/neofetch | /usr/bin/sed -e 's/\x1B\[[0-9;\?]*[a-zA-Z]//g' | /usr/bin/sed -e 's/`/\u200b`/g'"
                )
                .read()
                .rstrip()
            )
            if exists("/usr/bin/neofetch")
            else "```diff\n- Neofetch is not available -\n```"
        )
        await ctx.send_message(self.logger, ctx, message)
