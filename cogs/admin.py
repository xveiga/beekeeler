import logging
from datetime import datetime

from discord import TextChannel
from discord.ext import commands

from utils.checks import admin_only, control_channel_only


def setup(bot):
    bot.add_cog(AdminManagement(bot))


class AdminManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(aliases=["panik", "scram"], hidden=True)
    async def quit(self, ctx: commands.Context):
        await ctx.send_message(self.logger, ctx, "*Emergency stop, terminating...*")
        await self.bot.close()

    @commands.command(name="leave", hidden=True)
    @commands.guild_only()
    @control_channel_only()
    @admin_only()
    async def leave(self, ctx: commands.Context):
        await ctx.send_message(self.logger, ctx, "Bye!")
        await ctx.guild.leave()
        await self.bot.db.remove_guild(ctx.guild.id)

    @commands.command(name="prefix", hidden=True)
    @commands.guild_only()
    @admin_only()
    @control_channel_only()
    async def set_prefix(self, ctx: commands.Context, prefix: str):
        # TODO: Possible BUG if the user sets an invalid prefix, the only way to
        # reset it is to kick the bot out of the server and re-add it again
        await ctx.send_message(
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
        await ctx.send_message(
            self.logger,
            ctx,
            "*https://discord.com/api/oauth2/authorize?client_id={}&permissions=8&scope=bot*".format(
                self.bot.user.id
            ),
        )

    @commands.command(name="uptime")
    @admin_only()
    async def uptime(self, ctx: commands.Context):
        await ctx.send_message(
            self.logger,
            ctx,
            "Uptime: " + str(datetime.utcnow() - self.bot.upstamp),
            before="*",
            after="*",
        )

    ### Module hot-swapping commands ####
    @commands.command(hidden=True)
    @admin_only()
    async def load(self, ctx: commands.Context, extension: str):
        self.bot.load_extension("cogs.{0}".format(extension))
        self.logger.info("Load extension " + str(extension))
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command(hidden=True)
    @admin_only()
    async def reload(self, ctx: commands.Context, extension: str = None):
        if extension is None:
            # Copy to prevent keys changed during iteration
            extensions = self.bot.extensions.copy()
            for ext in extensions:
                self.bot.reload_extension(ext)
            await ctx.send_message(
                self.logger,
                ctx,
                "Reloaded `" + "`, `".join(str(x[5:]) for x in extensions) + "`",
            )
        else:
            self.bot.reload_extension("cogs.{0}".format(extension))
            await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command(hidden=True)
    @admin_only()
    async def unload(self, ctx: commands.Context, extension: str):
        self.bot.unload_extension("cogs.{0}".format(extension))
        self.logger.info("Unload extension " + str(extension))
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @load.error
    @reload.error
    @unload.error
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        await ctx.send_message(self.logger, ctx, "```fix\n{}\n```".format(str(error)))
