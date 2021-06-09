from datetime import datetime

from discord.embeds import Embed
from discord.ext.commands import Cog, command, has_permissions, TextChannelConverter, MissingPermissions
from discord import Embed, mentions
from ..db import db

class Log(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("log")

    @command(name = "logs", help = "Select if to have logs or not. Send enabled or disabled after the command to specify which one.")
    @has_permissions(manage_guild = True)
    async def logs(self, ctx, passed: str, channel: TextChannelConverter = None):
        if passed == "enabled":
            if channel is None:
                await ctx.send("Please specify a channel to send logs to.")
            else:
                db.execute("UPDATE guilds SET Logs = ? WHERE GuildID = ?", passed, ctx.guild.id)
                db.execute("UPDATE guilds SET LogsChannelID = ? WHERE GuildID = ?", channel.id, ctx.guild.id)
                await ctx.send(f"Logs haven been enabled in {channel.mention}.")
        elif passed == "disabled":
            db.execute("UPDATE guilds SET Logs = ? WHERE GuildID = ?", passed, ctx.guild.id)
            db.execute("UPDATE guilds SET LogsChannelID = ? WHERE GuildID = ?", 0, ctx.guild.id)
            await ctx.send("Logs have been disabled.")
        else:
            await ctx.send("Please specify `enabled` or `disabled` after command to enable or disable logs.")
    
    @logs.error
    async def logs_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server..")
    
    @Cog.listener()
    async def on_member_update(self, before, after):
        send_message = db.field("SELECT Logs FROM guilds WHERE GuildID =?", after.guild.id)
        if send_message == "enabled":
            log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", after.guild.id)
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
        send_message = db.field("SELECT Logs FROM guilds WHERE GuildID =?", after.guild.id)
        if send_message == "enabled":
            log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", after.guild.id)
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
        send_message = db.field("SELECT Logs FROM guilds WHERE GuildID =?", message.guild.id)
        if send_message == "enabled":
            log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", message.guild.id) 
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