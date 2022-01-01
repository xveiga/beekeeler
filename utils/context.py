from discord.ext import commands


class ExtendedContext(commands.Context):
    """
    Discord.py commands.Context extension to allow custom helper functions
    """

    async def send_message(
        self, logger, channel, string, before="", after="", *args, **kwargs
    ):
        logger.debug(string)
        return await channel.send(before + string + after, *args, **kwargs)

    async def edit_message(
        self, logger, message, string, before="", after="", *args, **kwargs
    ):
        logger.debug(string)
        return await message.edit(content=before + string + after, *args, **kwargs)
