from datetime import datetime
from discord.activity import Streaming
from discord.embeds import Embed
from discord.ext.commands.converter import RoleConverter, TextChannelConverter
from discord.member import Member
from lib.bot import Bot
from discord.ext.commands import Cog, command, has_permissions, MissingPermissions, bot_has_permissions, BotMissingPermissions

class Stream(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.cxn

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("streaming")
    
    @command(name = "stream", help = "Select if to receive stream notifications or not. Send enabled, followed by the channel to ping in, the role to listen to, then the role to ping. Or send disabled after the command.")
    @has_permissions(manage_guild = True, manage_roles = True)
    @bot_has_permissions(manage_roles = True)
    async def stream(self, ctx, passed: str, channel: TextChannelConverter = None, listen_role: RoleConverter = None, ping_role: RoleConverter = None):
        async with self.db.acquire() as db:
            if passed == "enabled":
                if channel is None:
                    await ctx.send("Please specify a channel to send notifications to for streams.")
                elif listen_role is None:
                    await ctx.send("Please specify a role to listen for streams.")
                elif ping_role is None:
                    await ctx.send("Please specify a role to ping for streams.")
                else:    
                    await db.execute("UPDATE guilds SET (Stream, StreamChannelID, StreamListenRoleID, StreamPingRoleID) = ($1, $2, $3, $4) WHERE GuildID = ($5);", passed, channel.id, listen_role.id, ping_role.id, ctx.guild.id)
                    await ctx.send(f"Stream notifications haven been enabled in {channel.mention} and will ping {ping_role.mention} and will listen to {listen_role.mention}.")
            elif passed == "disabled":
                await db.execute("UPDATE guilds SET (Stream, StreamChannelID, StreamListenRoleID, StreamPingRoleID) = ($1, $2, $3, $4) WHERE GuildID = ($5);", passed, 0, 0, 0, ctx.guild.id)
                await ctx.send("stream notifications have been disabled.")
            else:
                await ctx.send("Please specify `enabled` or `disabled` after the command to enable or disable stream notifications.")

    @stream.error
    async def stream_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server and roles.")
        elif isinstance(exception, BotMissingPermissions):
            await ctx.send("I do not have permissions to manage roles.")
    
    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        if not after.bot:
            async with self.db.acquire() as db:
                query = await db.fetchrow("SELECT Stream, StreamChannelID, StreamListenRoleID, StreamPingRoleID FROM guilds WHERE GuildID = ($1);", after.guild.id)
                send_notif = query.get("stream")
                if send_notif == "enabled":
                    if after.activity is Streaming:
                        listen_role_id = query.get("streamlistenroleid")
                        if after.roles.__contains__(after.guild.get_role(listen_role_id)):
                            channel_id = query.get("streamchannelid")
                            ping_role = after.guild.get_role(query.get("streampingroleid"))
                            stream = after.activity
                            embed = Embed(title = f"{after.mention} is streaming!", color = after.color, timestamp = datetime.utcnow())
                            embed.set_image(stream.large_image_url)
                            fields = [("Stream name", stream.name, False), ("Game", stream.game, False)]
                            for name, value, inline in fields:
                                embed.add_field(name = name, value = value, inline = inline)
                            await self.bot.get_channel(channel_id).send(f"Hey {ping_role.mention}, {after.mention} is streaming on {stream.platform}! Go watch them now at {stream.url}!")
                            await self.bot.get_channel(channel_id).send(embed = embed)

def setup(bot):
    bot.add_cog(Stream(bot))