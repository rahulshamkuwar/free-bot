from datetime import datetime
from discord.embeds import Embed
from discord.ext.commands import command, has_permissions, Cog, TextChannelConverter, MissingPermissions
from ..db import db

class Welcome(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("welcome")
    
    @command(name = "welcome-message", help = "Select if to have a welcome message or not. Send enabled or disabled after the command to specify which one.")
    @has_permissions(manage_guild = True)
    async def welcome_message(self, ctx, passed: str, channel: TextChannelConverter = None):
        if passed == "enabled":
            if channel is None:
                await ctx.send("Please specify a channel to send welcome messages to.")
            else:
                db.execute("UPDATE guilds SET WelcomeMessage = ? WHERE GuildID = ?", passed, ctx.guild.id)
                db.execute("UPDATE guilds SET WelcomeChannelID = ? WHERE GuildID = ?", channel.id, ctx.guild.id)
                await ctx.send(f"Welcome message enabled and welcome channel set to {channel.mention}.")
        elif passed == "disabled":
            db.execute("UPDATE guilds SET WelcomeMessage = ? WHERE GuildID = ?", passed, ctx.guild.id)
            db.execute("UPDATE guilds SET WelcomeChannelID = ? WHERE GuildID = ?", 0, ctx.guild.id)
            await ctx.send("Welcome message disabled and welcome channel removed.")
        else:
            await ctx.send("Please specify `enabled` or `disabled` after command to enable or disable welcome messages.")
    
    @welcome_message.error
    async def welcome_message_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")

    @Cog.listener()
    async def on_member_join(self, member):
        send_message = db.field("SELECT WelcomeMessage FROM guilds WHERE GuildID =?", member.guild.id)
        if send_message == "enabled":
            channel = db.field("SELECT WelcomeChannelID FROM guilds WHERE GuildID =?", member.guild.id)
            await self.bot.get_channel(channel).send(f"Welcome {member.mention}! Please remember to adhere to the rules and have fun!")
        exp = db.field("SELECT Experience FROM guilds WHERE GuildID =?", member.guild.id)
        if exp == "enabled":
            db.execute("INSERT INTO exp (UserID, GuildID) VALUES (?, ?)", member.id, member.guild.id)
        send_log = db.field("SELECT Logs FROM guilds WHERE GuildID =?", member.guild.id)
        if send_log == "enabled":
            log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", member.guild.id)
            embed = Embed(title = "Member Joined Server", color = 0xDD2222, timestamp = datetime.utcnow())
            embed.set_thumbnail(url = member.default_avatar_url)
            fields = [("Member", member.mention, False),
                    ("Account Created On", member.created_at.strftime("%m/%d/%Y %H:%M:%S"), False),]
            for name, value, inline in fields:
                embed.add_field(name = name, value = value, inline = inline)
            await self.bot.get_channel(log_channel).send(embed = embed)

    @Cog.listener()
    async def on_member_remove(self, member):
        exp = db.field("SELECT Experience FROM guilds WHERE GuildID =?", member.guild.id)
        if exp == "enabled":
            db.execute("DELETE FROM exp WHERE UserID = ? AND GuildID = ?", member.id, member.guild.id)
        send_log = db.field("SELECT Logs FROM guilds WHERE GuildID =?", member.guild.id)
        if send_log == "enabled":
            log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", member.guild.id)
            embed = Embed(title = "Member Left Server", color = 0xDD2222, timestamp = datetime.utcnow())
            embed.set_thumbnail(url = member.default_avatar_url)
            fields = [("Member", member.mention, False),
                    ("Account Created On", member.created_at.strftime("%m/%d/%Y %H:%M:%S"), False),]
            for name, value, inline in fields:
                embed.add_field(name = name, value = value, inline = inline)
            await self.bot.get_channel(log_channel).send(embed = embed)
        
    
def setup(bot):
    bot.add_cog(Welcome(bot))