import inspect
import logging

from discord.ext import commands

import cogs.utils as utils


def setup(bot):
    bot.add_cog(CodeEvaluator(bot))


class CodeEvaluator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name="latency")
    async def latency(self, ctx: commands.Context):
        if not await utils.check_cc(self.bot, ctx):
            return
        latency = f"{round(self.bot.latency * 1000)}ms"
        await utils.send_message(self.logger, ctx, latency)

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
    async def _eval_error(self, ctx: commands.Context, error):
        await utils.send_message(self.logger, ctx, str(error))
        raise error

    # TODO: Execute remote sql for debugging
