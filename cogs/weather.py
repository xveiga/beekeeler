"""weather.py: This just prints the current weather at location $1 to the Discord channel."""

__author__      = "forcegk"
__copyright__   = "Copyright 2021, Galiza. Free as-in-freedom use :)"

import logging

from discord.ext import commands
from discord import Embed
from cogs import utils
from os import popen

def setup(bot):
    bot.add_cog(Weather(bot))


class Weather(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name="weather")
    async def weather(
        self,
        ctx: commands.Context,
        *args
    ):

        if len(args) == 0:
            args = ["a", "coruña"]

        if len(args) == 1 and args[0].lower() == "moon":
            await utils.send_message(
                    self.logger,
                    ctx,
                    "```\n{0}\n```".format(popen("/usr/bin/curl -s \"wttr.in/moon?T&lang=es\" | sed -e '$ d' | /usr/bin/sed -e 's/`/\u200b`/g'").read().rstrip())
                )
        else:
            await utils.send_message(
                self.logger,
                ctx,
                "```\n{0}\n```".format(popen("/usr/bin/curl -s \"wttr.in/{0}?T&lang=es\" | (head -n7 && echo \"\" && tail -n3) | head -n9  | tail -n8 | /usr/bin/sed -e 's/`/\u200b`/g'".format('+'.join(args))).read().rstrip())
            )
