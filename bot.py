import sys
from json import load
from discord import Intents
from discord.channel import VoiceChannel
from discord.ext import commands, tasks

"""
Discord bitrate reduction prank bot

Invite link (OAuth2 Tab on developer portal):
https://discord.com/oauth2/authorize?client_id=887070716883787806&permissions=2064&scope=bot

Scopes:
    - Bot

Bot Permissions:
    General:
    - Manage Channels
    Text:
    - Send Messages
"""

class BotCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, config):
        self.bot = bot
        self.config = config
        self.reset()
        self.command_channel = None

    def reset(self):
        self.armed = False
        self.target = None
        self.channel = None
        self.original_bitrate = 0

    def check_command_channel(self, ctx):
        self.command_channel = ctx.channel
        return ctx.channel.name == self.config["control_channel_name"]

    async def get_user(self, ctx, username):
        async for member in ctx.guild.fetch_members(limit=100):
            if (
                username == member.name
                or username == member.name + "#" + member.discriminator
            ):
                return member
        return None

    def get_user_voice_channel(self, ctx, userid):
        for channel in ctx.guild.channels:
            if isinstance(channel, VoiceChannel):
                for member in channel.voice_states:
                    if member == userid:
                        return channel
        return None

    async def send_message(self, ctx, message):
        print(message)
        await ctx.send(message)

    # Magic
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # If not armed do nothing
        if not self.armed:
            return

        # If username is blacklisted
        print(member.name + "#" + member.discriminator)
        if member.id == self.target.id:
            if not before.channel and after.channel:
                # If user just joined a channel, activate for current channel
                self.channel = after.channel
                self.original_bitrate = self.channel.bitrate
                self.timer_task.start()
                await self.send_message(
                    self.command_channel,
                    member.name + " joined on " + str(after.channel),
                )
            elif before.channel and after.channel:
                # If user changes channel, restore original_bitrate on previous
                await before.channel.edit(
                    bitrate=self.original_bitrate
                    if self.original_bitrate != 0
                    else before.channel.bitrate
                )
                self.original_bitrate = after.channel.bitrate
                self.channel = after.channel
                if not self.timer_task.is_running():
                    self.timer_task.start()
                await self.send_message(
                    self.command_channel,
                    "{0} moved to {1}. Restored {2:.0f}kbps on {3}".format(
                        member.name,
                        after.channel.name,
                        before.channel.bitrate * 1e-3,
                        str(before.channel.name),
                    ),
                )
            else:
                # If user leaves, restore default settings.
                self.timer_task.stop()
                await before.channel.edit(
                    bitrate=self.original_bitrate
                    if self.original_bitrate != 0
                    else before.channel.bitrate
                )
                self.channel = None
                await self.send_message(
                    self.command_channel,
                    "{0} left {1}. Restored {2:.0f}kbps".format(
                        member.name, before.channel.name, before.channel.bitrate * 1e-3
                    ),
                )

    @commands.command(name="arm")
    async def enable(self, ctx: commands.Context, *, username: str):
        if not self.check_command_channel(ctx):
            return
        if self.timer_task.is_running():
            self.timer_task.cancel()
        # Find user id
        self.target = await self.get_user(ctx, username)
        self.armed = True
        # Check if user is already on any server channel
        channel = self.get_user_voice_channel(ctx, self.target.id)
        user = self.target.name + "#" + self.target.discriminator
        if channel:
            self.channel = channel
            self.original_bitrate = channel.bitrate
            self.timer_task.start()
            await self.send_message(
                self.command_channel,
                "Active on channel {0} for user {1}. Original bitrate {2:.0f}kbps".format(
                    channel.name,
                    str(user),
                    channel.bitrate * 1e-3,
                ),
            )
        else:
            await self.send_message(self.command_channel, "Armed for " + user)

    @commands.command(name="disarm")
    async def disable(self, ctx: commands.Context):
        if not self.check_command_channel(ctx):
            return

        if self.timer_task.is_running():
            self.timer_task.cancel()
            await self.channel.edit(bitrate=self.original_bitrate)
            await self.send_message(
                self.command_channel,
                "Disarmed. Restored {0:.0f}kbps on {1}".format(
                    self.channel.bitrate * 1e-3, str(self.channel.name)
                ),
            )
        else:
            await self.send_message(self.command_channel, "Disarmed")
        self.reset()

    @commands.command(name="status")
    async def status(self, ctx: commands.Context):
        if not self.check_command_channel(ctx):
            return
        await self.send_message(
            self.command_channel,
            "-- Status --\n"
            "Armed: {0}\n"
            "Target user: {1} ({2})\n"
            "Target channel: {3} ({4})\n"
            "Original Bitrate: {5}bps\n"
            "-- Configuration --\n"
            "Command channel: {6} ({7})\n"
            "Bitrate reduction amount: {8}bps/2sec\n"
            "Minimum bitrate: {9}".format(
                self.armed,
                self.target,
                "-" if self.target is None else self.target.id,
                self.channel,
                "-" if self.channel is None else self.channel.id,
                self.original_bitrate * 1e-3,
                self.command_channel,
                "-" if self.command_channel is None else self.command_channel.id,
                self.config["bitrate_reduction_amount"],
                self.config["min_bitrate"],
            ),
        )

    @commands.command(name="panik")
    async def stop(self, ctx: commands.Context):
        if not self.check_command_channel(ctx):
            return
        await self.send_message(self.command_channel, "Emergency stop, terminating...")
        await self.bot.close()

    @commands.command(name="scram")
    async def stop2(self, ctx: commands.Context):
        await self.stop(ctx)

    @commands.command(name="latency")
    async def latency(self, ctx: commands.Context):
        if not self.check_command_channel(ctx):
            return
        latency = f"{round(self.bot.latency * 1000)}ms"
        await self.send_message(self.command_channel, latency)

    @commands.command(name="reconfig")
    async def read_config(self, ctx: commands.Context):
        if not self.check_command_channel(ctx):
            return
        self.config = load_config("config.json")
        # self.timer_task.seconds?? = self.config["bitrate_reduction_interval"]
        await self.send_message(self.command_channel, "Reloaded configuration")

    @tasks.loop(seconds=2)
    async def timer_task(self):
        if not self.armed:
            self.timer_task.cancel()
            return
        bitrate = self.channel.bitrate - self.config["bitrate_reduction_amount"]
        min_bitrate = self.config["min_bitrate"]
        if bitrate <= min_bitrate:
            bitrate = min_bitrate
            await self.channel.edit(bitrate=bitrate)
            await self.send_message(
                self.command_channel,
                "Reached minimum bitrate: " + str(self.channel.bitrate),
            )
            self.timer_task.cancel()
        else:
            await self.channel.edit(bitrate=bitrate)
            await self.send_message(
                self.command_channel,
                "Set bitrate to {0:.0f}kbps on {1}".format(
                    self.channel.bitrate * 1e-3, str(self.channel.name)
                ),
            )


class BotErrors(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        """A global error handler cog."""

        if isinstance(error, commands.CommandNotFound):
            return  # Return because we don't want to show an error for every command not found
        elif isinstance(error, commands.CommandOnCooldown):
            message = f"This command is on cooldown. Please try again after {round(error.retry_after, 1)} seconds."
        elif isinstance(error, commands.MissingPermissions):
            message = "You are missing the required permissions to run this command!"
        elif isinstance(error, commands.UserInputError):
            message = "Something about your input was wrong, please check your input and try again!"
        else:
            message = "Oh no! Something went wrong while running the command!"

        await ctx.send(message, delete_after=5)
        await ctx.message.delete(delay=5)


def load_config(config_file):
    with open(config_file, "rt") as f:
        config = load(f)
    return config


def save_config(config_file, config_dict):
    with open(config_file, "wt") as f:
        f.write(json.dumps(config))


def main(config_file):
    # Load config file
    config = load_config(config_file)

    # Enable intents for user list fetching
    intents = Intents.default()
    intents.members = True
    # Create bot
    bot = commands.Bot(command_prefix=config["command_prefix"], intents=intents)
    bot.add_cog(BotCommands(bot, config))
    bot.add_cog(BotErrors(bot))

    # Run
    bot.run(config["token"])


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Using config.json")
        main("config.json")
