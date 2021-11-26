import os
import inspect
import logging

from discord.ext import commands

from cogs import utils


def setup(bot):
    bot.add_cog(CodeEvaluator(bot))


class CodeEvaluator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    # NOTE: The commands below incur security vulnerabilities,
    # by allowing a remote attacker to run arbitrary commands and
    # gain control of the system. They were written rather quickly
    # and lack important safety checks.
    # ENABLE AT YOUR OWN RISK. You have been warned.

    @commands.command(name="latency")
    async def latency(self, ctx: commands.Context):
        if not await utils.check_cc(self.bot, ctx):
            return
        latency = f"{round(self.bot.latency * 1000)}ms"
        await utils.send_message(self.logger, ctx, latency)

    async def _pycmd_exec(self, ctx, cmd, *args, **kwargs):
        if not utils.check_admin(self.bot, ctx):
            return
        if not await utils.check_cc(self.bot, ctx):
            return
        msg = str(cmd(*args, **kwargs))
        await utils.send_message(self.logger, ctx, msg, before="```py\n", after="\n```")

    @commands.command(name="stat")
    async def _stat(self, ctx: commands.Context, path: str):
        await self._pycmd_exec(ctx, os.stat, path)

    @commands.command(name="listdir")
    async def _listdir(self, ctx: commands.Context, path: str):
        await self._pycmd_exec(ctx, os.listdir, path)

    # From https://github.com/Rapptz/RoboDanny/blob/master/cogs/admin.py#L55
    @commands.command(name="eval", pass_context=True, hidden=True)
    async def _eval(self, ctx: commands.Context, *, code: str):
        if not utils.check_admin(self.bot, ctx):
            return
        code = code.strip("` ")
        result = None

        env = {
            "bot": self.bot,
            "ctx": ctx,
        }

        env.update(globals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await utils.send_message(
                self.logger,
                ctx,
                "```fix\n{}\n```".format(type(e).__name__ + ": " + str(e)),
            )
            return

        await utils.send_message(self.logger, ctx, "```py\n{}\n```".format(result))

    @_eval.error
    @_stat.error
    @_listdir.error
    async def default_error(self, ctx: commands.Context, error):
        await utils.send_message(
            self.logger, ctx, str(error), before="```fix\n", after="\n```"
        )
        raise error

    # TODO: Execute remote sql for debugging
