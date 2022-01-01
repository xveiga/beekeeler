import logging

from discord.ext import commands
from discord import VoiceChannel


def setup(bot):
    bot.add_cog(UserMover(bot))


class UserMover(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command(name="move")
    @commands.guild_only()
    async def move_channel_users(
        self,
        ctx: commands.Context,
        arg1: VoiceChannel = None,
        arg2: VoiceChannel = None,
    ):
        """Move all users from a voice channel to another"""

        # Arg parsing
        if arg1 and arg2:
            src = arg1
            dest = arg2
        elif arg1:
            # Source is issuer's current channel if it exists
            vc = ctx.author.voice
            if vc is None:
                await ctx.send_message(
                    self.logger,
                    ctx,
                    "You are not in a *voice channel*, you must specify **both** *source* and *destination*: `move <source> <destination>`",
                )
                return
            src = vc.channel
            dest = arg1
        else:
            await ctx.send_message(
                self.logger,
                ctx,
                "Wrong arguments. Usage: `move <source> <destination>`",
            )
            return

        # Check if source and destinations are the same
        if src.id == dest.id:
            await ctx.send_message(
                self.logger,
                ctx,
                "Already in {0}".format(src.mention),
            )
            return

        # Move all users from src channel to dest channel
        usercount = len(src.members)
        for user in src.members:
            await user.move_to(dest)

        await ctx.send_message(
            self.logger,
            ctx,
            "Moved **{0}** users from {1} to {2}".format(
                usercount, src.mention, dest.mention
            ),
        )

    @move_channel_users.error
    async def move_channel_users_error(self, ctx: commands.Context, exception):
        await ctx.send_message(self.logger, ctx, str(exception))
        raise exception
