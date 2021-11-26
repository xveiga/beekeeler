import logging

from discord.ext import commands

from cogs import utils


def setup(bot):
    bot.add_cog(AdminManagement(bot))


class AdminManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(aliases=["panik", "scram"])
    async def quit(self, ctx: commands.Context):
        await utils.send_message(self.logger, ctx, "*Emergency stop, terminating...*")
        await self.bot.close()

    @commands.command(name="leave")
    @commands.guild_only()
    async def leave(self, ctx: commands.Context):
        if not await utils.check_cc(self.bot, ctx):
            return
        await utils.send_message(self.logger, ctx, "Bye!", tts=True)
        await ctx.guild.leave()
        await self.bot.db.remove_guild(ctx.guild.id)

    @commands.command(name="prefix")
    @commands.guild_only()
    async def set_prefix(self, ctx: commands.Context, prefix: str):
        if not await utils.check_cc(self.bot, ctx):
            return
        # TODO: Possible BUG if the user sets an invalid prefix, the only way to
        # reset it is to kick the bot out of the server and re-add it again
        await utils.send_message(
            self.logger, ctx, "*New control prefix is* `{}`".format(prefix)
        )
        await self.bot.db.set_guild_prefix(ctx.guild.id, prefix)
        await self.bot.invalidate_prefix(ctx.guild.id)

    @commands.command(name="invite")
    async def invite(self, ctx: commands.Context):
        await utils.send_message(
            self.logger,
            ctx,
            "*https://discord.com/api/oauth2/authorize?client_id={}&permissions=8&scope=bot*".format(
                self.bot.user.id
            ),
        )
