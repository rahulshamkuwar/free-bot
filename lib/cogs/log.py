from datetime import datetime
from lib.bot import Bot

from discord.embeds import Embed
from discord.ext.commands import Cog, command, has_permissions, TextChannelConverter, MissingPermissions
from discord import Embed
# from ..db import db

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
                    await db.execute("UPDATE guilds SET Logs = ($1) WHERE GuildID = ($2);", passed, ctx.guild.id)
                    await db.execute("UPDATE guilds SET LogsChannelID = ($1) WHERE GuildID = ($2);", channel.id, ctx.guild.id)
                    await ctx.send(f"Logs haven been enabled in {channel.mention}.")
            elif passed == "disabled":
                await db.execute("UPDATE guilds SET Logs = ($1) WHERE GuildID = ($2);", passed, ctx.guild.id)
                await db.execute("UPDATE guilds SET LogsChannelID = ? WHERE GuildID = ($2);", 0, ctx.guild.id)
                await ctx.send("Logs have been disabled.")
            else:
                await ctx.send("Please specify `enabled` or `disabled` after command to enable or disable logs.")
    
    @logs.error
    async def logs_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server..")
    
    @Cog.listener()
    async def on_member_update(self, before, after):
        async with self.db.acquire() as db:
            query = await db.fetchrow("SELECT Logs, LogsChannelID FROM guilds WHERE GuildID = ($1);", after.guild.id)
            send_message = query.get("logs")
            if send_message == "enabled":
                # query = await db.fetchrow("SELECT LogsChannelID FROM guilds WHERE GuildID = ($1);", after.guild.id)
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
    
    @Cog.listener()
    async def on_message_edit(self, before, after):
        async with self.db.acquire() as db:
            query = await db.fetchrow("SELECT Logs, LogsChannelID FROM guilds WHERE GuildID = ($1);", after.guild.id)
            send_message = query.get("logs")
            if send_message == "enabled":
                # query = await db.fetchrow("SELECT LogsChannelID FROM guilds WHERE GuildID = ($1);", after.guild.id)
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
        async with self.db.acquire() as db:
            query = await db.fetchrow("SELECT Logs, LogsChannelID FROM guilds WHERE GuildID = ($1);", message.guild.id)
            send_message = query.get("logs")
            if send_message == "enabled":
                # query = await db.fetchrow("SELECT LogsChannelID FROM guilds WHERE GuildID = ($1);", message.guild.id)
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