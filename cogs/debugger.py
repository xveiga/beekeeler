import os

# import sys
import inspect
import logging

# import subprocess

from discord.ext import commands

from utils.checks import admin_only, control_channel_only


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

    # @commands.command(name="restart", hidden=True)
    # @admin_only()
    # async def restart(self, ctx):
    #     await self.bot.close()
    #     await os.execv(sys.executable, sys.argv)

    @commands.command(name="latency")
    @control_channel_only()
    async def latency(self, ctx: commands.Context):
        latency = f"{round(self.bot.latency * 1000)}ms"
        await ctx.send_message(self.logger, ctx, latency)

    async def _pycmd_exec(self, ctx, cmd, *args, **kwargs):
        msg = str(cmd(*args, **kwargs))
        await ctx.send_message(self.logger, ctx, msg, before="```py\n", after="\n```")

    @commands.command(name="stat")
    @admin_only()
    @control_channel_only()
    async def _stat(self, ctx: commands.Context, path: str):
        await self._pycmd_exec(ctx, os.stat, path)

    @commands.command(name="listdir")
    @admin_only()
    @control_channel_only()
    async def _listdir(self, ctx: commands.Context, path: str):
        await self._pycmd_exec(ctx, os.listdir, path)

    # From https://github.com/Rapptz/RoboDanny/blob/master/cogs/admin.py#L55
    @commands.command(name="eval", pass_context=True, hidden=True)
    @admin_only()
    async def _eval(self, ctx: commands.Context, *, code: str):
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
            await ctx.send_message(
                self.logger,
                ctx,
                "```fix\n{}\n```".format(type(e).__name__ + ": " + str(e)),
            )
            return

        await ctx.send_message(self.logger, ctx, "```py\n{}\n```".format(result))

    @_eval.error
    @_stat.error
    @_listdir.error
    async def default_error(self, ctx: commands.Context, error):
        await ctx.send_message(
            self.logger, ctx, str(error), before="```fix\n", after="\n```"
        )
        raise error
