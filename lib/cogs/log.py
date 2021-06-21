from datetime import datetime

from discord.activity import Spotify, Streaming
from discord.channel import DMChannel
from discord.enums import ActivityType
from discord.member import Member
from lib.bot import Bot

from discord.embeds import Embed
from discord.ext.commands import Cog, command, has_permissions, TextChannelConverter, MissingPermissions
from discord import Embed


class Log(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.cxn
    
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("log")

    @command(name = "logs", help = "Select if to have logs or not. Send enabled or disabled after the command to specify which one.")
    @has_permissions(manage_guild = True)
    async def logs(self, ctx, passed: str, channel: TextChannelConverter = None):
        async with self.db.acquire() as db:
            if passed == "enabled":
                if channel is None:
                    await ctx.send("Please specify a channel to send logs to.")
                else:
                    await db.execute("UPDATE guilds SET (Logs, LogsChannelID) = ($1, $2) WHERE GuildID = ($3);", passed, channel.id, ctx.guild.id)
                    await ctx.send(f"Logs haven been enabled in {channel.mention}.")
            elif passed == "disabled":
                await db.execute("UPDATE guilds SET (Logs, LogsChannelID) = ($1, $2) WHERE GuildID = ($3);", passed, 0, ctx.guild.id)
                await ctx.send("Logs have been disabled.")
            else:
                await ctx.send("Please specify `enabled` or `disabled` after the command to enable or disable logs.")
    
    @logs.error
    async def logs_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")
    
    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        async with self.db.acquire() as db:
            query = await db.fetchrow("SELECT Logs, LogsChannelID, Stream, StreamChannelID, StreamListenRoleID, StreamPingRoleID FROM guilds WHERE GuildID = ($1);", after.guild.id)
            send_message = query.get("logs")
            if send_message == "enabled":
                log_channel = query.get("logschannelid")
                if before.display_name != after.display_name:
                    embed = Embed(title = "Member Update", description = "Nickname Change", color = after.color, timestamp = datetime.utcnow())
                    embed.set_thumbnail(url = after.avatar_url)
                    fields = [("Before", before.display_name, False), ("After", after.display_name, False)]
                    for name, value, inline in fields:
                        embed.add_field(name = name, value = value, inline = inline)
                    await self.bot.get_channel(log_channel).send(embed = embed)
                elif before.roles != after.roles:
                    embed = Embed(title = "Member Update", description = "Roles Update", color = after.color, timestamp = datetime.utcnow())
                    embed.set_thumbnail(url = after.avatar_url)
                    fields = [("Before", ",".join([r.mention for r in before.roles]), False), ("After", ",".join([r.mention for r in after.roles]), False)]
                    for name, value, inline in fields:
                        embed.add_field(name = name, value = value, inline = inline)
                    await self.bot.get_channel(log_channel).send(embed = embed)
            if not after.bot:
                send_notif = query.get("stream")
                if send_notif == "enabled":
                    activity_list = list(after.activities)
                    is_streaming = False
                    stream = None
                    for activity in activity_list:
                        if isinstance(activity, Streaming):
                            is_streaming = True
                            stream = activity
                    if is_streaming:
                        listen_role_id = query.get("streamlistenroleid")
                        if after.roles.__contains__(after.guild.get_role(listen_role_id)):
                            channel_id = query.get("streamchannelid")
                            ping_role = after.guild.get_role(query.get("streampingroleid"))
                            embed = Embed(title = f"{after.display_name} is streaming!", color = after.color, timestamp = datetime.utcnow())
                            # embed.set_image(url = stream.assets['large_image']) there is no way to get the image url rn for streaming :()
                            fields = [("Stream name", stream.name, False), ("Game", stream.game, False)]
                            for name, value, inline in fields:
                                embed.add_field(name = name, value = value, inline = inline)
                            await self.bot.get_channel(channel_id).send(f"Hey {ping_role.mention}, {after.mention} is streaming on {stream.platform}! Go watch them now at {stream.url} !")
                            await self.bot.get_channel(channel_id).send(embed = embed)
    
    @Cog.listener()
    async def on_message_edit(self, before, after):
        if not isinstance(after.channel, DMChannel):
            async with self.db.acquire() as db:
                query = await db.fetchrow("SELECT Logs, LogsChannelID FROM guilds WHERE GuildID = ($1);", after.guild.id)
                send_message = query.get("logs")
                if send_message == "enabled":
                    log_channel = query.get("logschannelid")
                    if not after.author.bot:
                        if before.content != after.content:
                            embed = Embed(title = "Message Update", description = "Message Edited", color = after.author.color, timestamp = datetime.utcnow())
                            embed.set_thumbnail(url = after.author.avatar_url)
                            embed.add_field(name = "User", value = after.author.mention, inline = False)
                            embed.add_field(name = "Channel", value = after.channel, inline = False)
                            fields = [("Before", before.content, False), ("After", after.content, False)]
                            for name, value, inline in fields:
                                embed.add_field(name = name, value = value, inline = inline)
                            await self.bot.get_channel(log_channel).send(embed = embed)
    
    @Cog.listener()
    async def on_message_delete(self, message):
        if not isinstance(message.channel, DMChannel):
            async with self.db.acquire() as db:
                query = await db.fetchrow("SELECT Logs, LogsChannelID FROM guilds WHERE GuildID = ($1);", message.guild.id)
                send_message = query.get("logs")
                if send_message == "enabled":
                    log_channel = query.get("logschannelid")
                    if not message.author.bot:
                        embed = Embed(title = "Message Update", description = "Message Deleted", color = message.author.color, timestamp = datetime.utcnow())
                        embed.set_thumbnail(url = message.author.avatar_url)
                        embed.add_field(name = "User", value = message.author.mention, inline = False)
                        embed.add_field(name = "Channel", value = message.channel, inline = False)
                        fields = [("Content", message.content, False),]
                        for name, value, inline in fields:
                            embed.add_field(name = name, value = value, inline = inline)
                        await self.bot.get_channel(log_channel).send(embed = embed)

def setup(bot):
    bot.add_cog(Log(bot))