import logging

from discord import TextChannel
from discord.ext import commands

from cogs import utils


def setup(bot):
    bot.add_cog(AdminManagement(bot))


class AdminManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(aliases=["panik", "scram"], hidden=True)
    async def quit(self, ctx: commands.Context):
        await utils.send_message(self.logger, ctx, "*Emergency stop, terminating...*")
        await self.bot.close()

    @commands.command(name="leave", hidden=True)
    @commands.guild_only()
    async def leave(self, ctx: commands.Context):
        if not await utils.check_cc(self.bot, ctx):
            return
        await utils.send_message(self.logger, ctx, "Bye!")
        await ctx.guild.leave()
        await self.bot.db.remove_guild(ctx.guild.id)

    @commands.command(name="prefix", hidden=True)
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

    @commands.command(name="control", hidden=True)
    @commands.guild_only()
    async def set_control_channel(self, ctx: commands.Context, cc: TextChannel = None):
        """Set control channel for privileged commands"""
        old_cc = await self.bot.db.get_guild_cc(ctx.guild.id)
        # If command channel is set, accept changes only from command channel.
        # Otherwise, accept from any channel (for first time setup)
        if old_cc is not None and old_cc != ctx.channel.id:
            return

        self.logger.debug("Set control channel for guild " + str(cc))
        await self.bot.db.set_guild_cc(
            ctx.guild.id, (ctx.channel.id if cc is None else cc.id)
        )
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command(name="invite")
    async def invite(self, ctx: commands.Context):
        """Get invite link for a server"""
        await utils.send_message(
            self.logger,
            ctx,
            "*https://discord.com/api/oauth2/authorize?client_id={}&permissions=8&scope=bot*".format(
                self.bot.user.id
            ),
        )
