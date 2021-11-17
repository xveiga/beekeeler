import typing
import datetime
import logging

from discord.ext import commands

import cogs.utils as utils


def setup(bot):
    bot.add_cog(HotSwapper(bot))


class HotSwapper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context):
        if not utils.check_admin(self.bot, ctx):
            return
        await utils.send_message(
            self.logger,
            ctx,
            "Uptime: " + str(datetime.datetime.utcnow() - self.bot.upstamp),
            before="*",
            after="*",
        )

    @commands.command()
    async def load(self, ctx: commands.Context, extension: str):
        if not utils.check_admin(self.bot, ctx):
            return
        self.bot.load_extension(extension)
        self.logger.info("Load extension " + str(extension))
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command()
    async def reload(
        self, ctx: commands.Context, extension: typing.Optional[str] = None
    ):
        if not utils.check_admin(self.bot, ctx):
            return
        if extension is None:
            # Copy to prevent keys changed during iteration
            extensions = self.bot.extensions.copy()
            for ext in extensions:
                self.bot.reload_extension(ext)
            await utils.send_message(
                self.logger,
                ctx,
                "Reloaded `" + "`, `".join(str(x) for x in extensions) + "`",
            )
        else:
            self.bot.reload_extension(extension)
            await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command()
    async def unload(self, ctx: commands.Context, extension: str):
        if not utils.check_admin(self.bot, ctx):
            return
        self.bot.unload_extension(extension)
        self.logger.info("Unload extension " + str(extension))
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @load.error
    @reload.error
    @unload.error
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        await utils.send_message(self.logger, ctx, "```fix\n{}\n```".format(str(error)))
