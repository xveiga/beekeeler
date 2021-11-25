import asyncio
import logging

from discord import Guild, Member, VoiceChannel
from discord.abc import GuildChannel
from discord.channel import TextChannel
from discord.ext import commands

from database.dao.guild import BotGuild
from database.dao.target import BotTarget
from database.dao.voicechannel import BotVoiceChannel
import cogs.utils as utils


def setup(bot):
    bot.add_cog(BitrateKiller(bot))


class BitrateKiller(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        # Channels with active bitrate reduction.
        # Key is channel id. Contains a tuple (task_handle, user_id_list)
        self.bk_channels = dict()

    def __del__(self):
        # Cancel all running tasks
        for c in self.bk_channels:
            c[0].cancel()

    async def _fetch_guild_changes(self):
        remote_guilds = await self.bot.fetch_guilds(limit=200).flatten()
        local_guilds = await self.bot.db.get_guilds()

        added, removed, persistent = await utils.local_remote_compare(
            local_guilds, remote_guilds, lambda l, r: l.gid == r.id
        )

        # Add new guilds
        for g in added:
            await self.bot.db.add_guild(BotGuild(g.id, g.name))
            self.logger.debug('Added guild "{}"'.format(g.name))

        # Remove old guilds
        for g in removed:
            await self.bot.db.remove_guild(g.gid)
            self.logger.debug('Removed guild "{}"'.format(g.name))

        # Update guild names
        for l, r in persistent:
            if l.name != r.name:
                await self.bot.db.set_guild_name(l.gid, r.name)

        for g in await self.bot.db.get_guilds():
            # Check control channel still exists
            if self.bot.get_channel(g.control_channel) is None:
                await self.bot.db.set_guild_cc(g.gid, None)

    async def _fetch_channel_changes(self):
        remote_channels = list(
            filter(lambda c: isinstance(c, VoiceChannel), self.bot.get_all_channels())
        )
        local_channels = await self.bot.db.get_voicechannels()
        added, removed, _ = await utils.local_remote_compare(
            local_channels, remote_channels, lambda l, r: l.cid == r.id
        )

        # Channel addition/removal
        for c in added:
            await self.bot.db.add_voicechannel(
                BotVoiceChannel(c.guild.id, c.id, c.bitrate)
            )
            self.logger.debug('Added voice channel "{}"'.format(c.name))

        for c in removed:
            await self.bot.db.remove_voicechannel(c.gid, c.cid)
            self.logger.debug('Removed voice channel "{}"'.format(c.cid))

        # Channel bitrate changes
        channels = await self.bot.db.get_voicechannels()
        for c in channels:
            channel = self.bot.get_channel(c.cid)
            await self.bot.db.set_voicechannel_bitrate(c.gid, c.cid, channel.bitrate)

    @commands.Cog.listener()
    async def on_ready(self):
        await self._fetch_guild_changes()
        await self._fetch_channel_changes()
        # TODO: Restore bkill tasks if enabled (and targets still present)
        self.logger.info("Ready")

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.logger.info("Disconnected")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        self.logger.debug("guild join: " + str(guild))
        await self.bot.db.add_guild(BotGuild(guild.id, guild.name))

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        self.logger.debug("guild remove: " + str(guild))
        await self.bot.db.remove_guild(guild.id)

    @commands.Cog.listener()
    async def on_guild_update(self, before: Guild, after: Guild):
        if before.name != after.name:
            self.logger.debug("guild name update: " + str(after) + " " + str(before))
            await self.bot.db.set_guild_name(after.id, after.name)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: GuildChannel):
        if isinstance(channel, VoiceChannel):
            # If voice channel add bitrate values to database
            await self.bot.db.add_voicechannel(
                BotVoiceChannel(channel.id, channel.guild.id, channel.bitrate)
            )
            self.logger.debug("on channel create: " + str(channel))

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: GuildChannel):
        if isinstance(channel, VoiceChannel):
            # If channel is voice channel, remove from database
            await self.bot.db.remove_voicechannel(channel.guild.id, channel.id)
            self.logger.debug("on channel delete: " + str(channel))
        elif isinstance(channel, TextChannel):
            # If channel is control channel, reset control for guild
            if channel.id == await self.bot.db.get_guild_cc(channel.guild.id):
                await self.bot.db.set_guild_cc(channel.guild.id, None)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: GuildChannel, after: GuildChannel):
        # If channel is voice channel and bitrate is modified
        # and bot is not active on this channel,
        # update default bitrate on database.
        if not await self.bot.db.get_voicechannel_bkill(after.guild.id, after.id):
            if isinstance(after, VoiceChannel):
                if before.bitrate != after.bitrate:
                    await self.bot.db.set_voicechannel_bitrate(
                        after.guild.id, after.id, after.bitrate
                    )
                    self.logger.debug("bitrate update: " + str(after))

        self.logger.debug("on channel update: " + str(after))

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceChannel, after: VoiceChannel
    ):
        self.logger.debug("on_voice_state_update")

        # If bkill disabled ignore
        if not await self.bot.db.get_guild_enable(member.guild.id):
            return

        # If control channel is not set ignore
        guild = await self.bot.db.get_guild(member.guild.id)
        if guild.control_channel is None:
            return
        cmd_channel = self.bot.get_channel(guild.control_channel)

        if before.channel:
            channel_task = self.bk_channels.get(before.channel.id)
            # await utils.send_message(self.logger, cmd_channel, "{0}".format(str(self.bk_channels[before.channel.id])))
            # if member is target from self.bk_channels:
            if channel_task is not None and member.id in channel_task[1]:
                # Remove current user from list
                channel_task[1].remove(member.id)
                self.bk_channels[before.channel.id] = channel_task
                # if target list is empty
                # await utils.send_message(self.logger, cmd_channel, "{0}".format(str(channel_task)))
                if len(channel_task[1]) == 0:
                    # stop task
                    channel_task[0].cancel()
                    # set bkill on channel to false
                    await self.bot.db.set_voicechannel_bkill(
                        before.channel.guild.id, before.channel.id, False
                    )
                    # restore bitrate on channel
                    await before.channel.edit(
                        bitrate=await self.bot.db.get_voicechannel_bitrate(
                            before.channel.guild.id, before.channel.id
                        )
                    )
                    # remove channel from self.bk_channels
                    self.bk_channels.pop(before.channel.id)
                    await utils.send_message(
                        self.logger,
                        cmd_channel,
                        "{0} bkill disabled `{1:.0f}kbps`".format(
                            before.channel.mention, before.channel.bitrate * 1e-3
                        ),
                    )

        if after.channel:
            # if member is target from database:
            if await self.bot.db.is_target(member.guild.id, member.id):
                # get channel from self.bk_channels
                channel_task = self.bk_channels.get(after.channel.id)
                # if channel entry does not exist:
                if channel_task is None:
                    # set bkill on channel to true
                    # TODO: This is unnecessary if checked on boot, may be reused for channel whitelisting
                    await self.bot.db.set_voicechannel_bkill(
                        after.channel.guild.id, after.channel.id, True
                    )
                    # start task
                    self.bk_channels[after.channel.id] = (
                        self.bot.loop.create_task(
                            self.timer_task(
                                after.channel,
                                cmd_channel,
                                guild.bitrate_reduction_interval,
                                guild.bitrate_reduction_amount,
                                guild.min_bitrate,
                            )
                        ),
                        [member.id],
                    )
            else:
                # add target to self.bk_channels list
                data = self.bk_channels[after.channel.id]
                self.bk_channels[after.channel.id] = (
                    data[0],
                    data[1].append(member.id),
                )

    async def timer_task(self, channel, cmd_channel, interval, amount, min):
        # TODO: On database modification event listener
        bitrate = channel.bitrate
        message = await utils.send_message(
            self.logger,
            cmd_channel,
            "{0} `{1:.0f}kbps`".format(channel.mention, channel.bitrate * 1e-3),
        )
        while bitrate > min:
            await asyncio.sleep(interval * 1e-3)
            bitrate -= amount
            await channel.edit(bitrate=bitrate)
            await utils.edit_message(
                self.logger,
                message,
                "{0} `{1:.0f}kbps`".format(
                    channel.mention,
                    channel.bitrate * 1e-3,
                ),
            )
        await utils.edit_message(
            self.logger,
            message,
            "{0} `{1:.0f}kbps` *minimum*".format(channel.mention, channel.bitrate),
        )

    # @commands.Cog.listener()
    # async def on_member_remove(member):
    #     # OPTION: If member is a target, remove from database
    #     # Thus, if the user rejoins, it won't apply bitrate reduction until
    #     # explicitly enabled again
    #     # May be possible to incorporate everything into one sql query
    #     # using "(SELECT ... from Target) ... OR (DELETE FROM Target ...)""
    #     # this way the delete part should be evaluated only if the select suceeds
    #     self.logger.debug("member remove: " + str(member))
    #     # or maybe just do the delete and ignore the exception if it fails

    # @commands.command(name="bkill")
    # @commands.guild_only()
    # async def kill(self, ctx: commands.Context, vc: VoiceChannel = None):
    #     if not await utils.check_cc(self.bot, ctx):
    #         return
    #     # TODO: Commands to trigger and cancel manually
    #     # get channel from self.bk_channels
    #     channel_task = self.bk_channels.get(vc.id)
    #     # if channel entry does not exist:
    #     if channel_task is None:
    #         # set bkill on channel to true
    #         # TODO: This is unnecessary if checked on boot, may be reused for channel whitelisting
    #         await self.bot.db.set_voicechannel_bkill(
    #             vc.guild.id, vc.id, True
    #         )
    #         # start task
    #         guild = await self.bot.db.get_guild(ctx.guild.id)
    #         self.bk_channels[vc.id] = (
    #             self.bot.loop.create_task(
    #                 self.timer_task(
    #                     vc,
    #                     guild.control_channel,
    #                     guild.bitrate_reduction_interval,
    #                     guild.bitrate_reduction_amount,
    #                     guild.min_bitrate,
    #                 )
    #             ),
    #             [ctx.author.id],
    #         )
    #     await utils.send_message(
    #         self.logger, ctx, "Channel: **" + str(vc) + "**"
    #     )
    #     #await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    # @commands.command(name="bcancel")
    # @commands.guild_only()
    # async def cancel(self, ctx: commands.Context, vc: VoiceChannel = None):
    #     if not await utils.check_cc(self.bot, ctx):
    #         return
    #     # TODO: Commands to trigger and cancel manually
    #     await utils.send_message(
    #         self.logger, ctx, "Channel: **" + str(vc) + "**"
    #     )
    #     #await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command(name="save")
    @commands.guild_only()
    async def save(self, ctx: commands.Context):
        """Saves bitrate from all channels in guild"""
        if not await utils.check_cc(self.bot, ctx):
            return
        for localc in await self.bot.db.get_guild_voicechannels(ctx.guild.id):
            channel = self.bot.get_channel(localc.cid)
            await self.bot.db.set_voicechannel_bitrate(
                localc.gid, localc.cid, channel.bitrate
            )
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command(name="restore")
    @commands.guild_only()
    async def restore(self, ctx: commands.Context):
        """Restores bitrate on all channels in guild"""
        if not await utils.check_cc(self.bot, ctx):
            return
        for localc in await self.bot.db.get_guild_voicechannels(ctx.guild.id):
            channel = self.bot.get_channel(localc.cid)
            await channel.edit(bitrate=localc.bitrate)
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command(name="arm")
    @commands.guild_only()
    async def arm(self, ctx: commands.Context):
        if not await utils.check_cc(self.bot, ctx):
            return
        await self.bot.db.set_guild_enable(ctx.guild.id, True)
        # TODO: Start all bkill tasks for guild
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command(name="disarm")
    @commands.guild_only()
    async def disarm(self, ctx: commands.Context):
        if not await utils.check_cc(self.bot, ctx):
            return
        await self.bot.db.set_guild_enable(ctx.guild.id, False)
        # Stop all bkill tasks for guild
        vc = await self.bot.db.get_guild_voicechannels(ctx.guild.id)
        if len(vc) > 0:
            for c in vc:
                bk_channel = self.bk_channels.get(c.cid)
                if bk_channel is not None:
                    handle = self.bot.get_channel(c.cid)
                    # stop task
                    bk_channel[0].cancel()
                    # set bkill on channel to false
                    await self.bot.db.set_voicechannel_bkill(
                        handle.guild.id, c.cid, False
                    )
                    # restore bitrate on channel
                    await handle.edit(
                        bitrate=await self.bot.db.get_voicechannel_bitrate(c.gid, c.cid)
                    )
                    # remove channel from self.bk_channels
                    self.bk_channels.pop(c.cid)
                    await utils.send_message(
                        self.logger,
                        ctx,
                        "{0} bkill disabled `{1:.0f}kbps`".format(
                            handle.mention, handle.bitrate * 1e-3
                        ),
                    )
        await ctx.message.add_reaction("\N{THUMBS UP SIGN}")

    @commands.command(name="control")
    @commands.guild_only()
    async def set_control_channel(self, ctx: commands.Context, cc: TextChannel = None):
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

    @commands.command(name="killer")
    @commands.guild_only()
    async def get_target_issuer(self, ctx: commands.Context, target: Member = None):
        """Find out who added a target. If argument is None, checks current user."""
        if not await utils.check_cc(self.bot, ctx):
            return
        cmd_uid = ctx.author.id if target is None else target.id
        issuer_uid = await self.bot.db.get_target_issuer(ctx.guild.id, cmd_uid)
        await utils.send_message(self.logger, ctx, str(issuer_uid))

    @commands.command(name="min")
    @commands.guild_only()
    async def set_min_bitrate(self, ctx: commands.Context, min: int):
        if not await utils.check_cc(self.bot, ctx):
            return
        await utils.send_message(
            self.logger, ctx, "Set min bitrate to **" + str(min) + "**"
        )
        await self.bot.db.set_guild_min_bitrate(ctx.guild.id, min)

    @commands.command(name="amount")
    @commands.guild_only()
    async def set_interval(self, ctx: commands.Context, amount: int, seconds: float):
        if not await utils.check_cc(self.bot, ctx):
            return
        await utils.send_message(
            self.logger,
            ctx,
            "Set reduction amount to **{0:1.0f}** kbps every **{1:1.0f}** seconds".format(
                amount * 1e-3, seconds
            ),
        )
        await self.bot.db.set_guild_bitrates(ctx.guild.id, amount, int(seconds * 1e3))

    @commands.command(name="targets")
    @commands.guild_only()
    async def list_targets(self, ctx: commands.Context):
        if not await utils.check_cc(self.bot, ctx):
            return
        await ctx.send(
            "Targets: "
            + ", ".join(
                "{} <- {}".format(t.uid, t.issuer)
                for t in await self.bot.db.get_targets(ctx.guild.id)
            )
        )

    @commands.command(name="add")
    @commands.guild_only()
    async def add_target(self, ctx: commands.Context, member: Member):
        if not await utils.check_cc(self.bot, ctx):
            return
        await self.bot.db.add_target(BotTarget(ctx.guild.id, member.id, ctx.author.id))
        await utils.send_message(self.logger, ctx, "Added " + str(member))

    @commands.command(name="remove")
    @commands.guild_only()
    async def remove_target(self, ctx: commands.Context, member: Member):
        if not await utils.check_cc(self.bot, ctx):
            return
        await self.bot.db.remove_target(ctx.guild.id, member.id)
        await utils.send_message(self.logger, ctx, "Removed " + str(member))

    @commands.command(name="clear")
    @commands.guild_only()
    async def clear_targets(self, ctx: commands.Context):
        if not await utils.check_cc(self.bot, ctx):
            return
        await self.bot.db.clear_targets(ctx.guild.id)
        await utils.send_message(self.logger, ctx, "Removed all targets")

    @arm.error
    @disarm.error
    @get_target_issuer.error
    @set_min_bitrate.error
    @set_interval.error
    @list_targets.error
    @add_target.error
    @remove_target.error
    @clear_targets.error
    @kill.error
    @cancel.error
    async def default_error(self, ctx: commands.Context, error):
        await utils.send_message(
            self.logger, ctx, str(error), before="```fix\n", after="\n```"
        )
