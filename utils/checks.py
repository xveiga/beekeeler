from discord.ext import commands


def admin_only():
    """Checks if the current user is a bot admin/owner"""
    return commands.check(lambda ctx: ctx.author.id in ctx.bot.config["admin_ids"])


def control_channel_only():
    """Checks if the curret message was sent over the bot control channel"""
    return commands.check(
        lambda ctx: ctx.bot.db.get_guild_cc(ctx.guild.id) == ctx.channel.id
    )
