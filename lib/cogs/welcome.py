from discord.ext.commands import command, has_permissions, Cog, CheckFailure, TextChannelConverter, MissingPermissions
from ..db import db

class Welcome(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("welcome")
    
    @command(name = "welcome-message", help = "Select if to have a welcome message or not. Send enaled or disabled after command to specify which one.")
    @has_permissions(manage_guild = True)
    async def welcome_message(self, ctx, passed: str, channel: TextChannelConverter = None):
        if passed == "enabled":
            if channel is None:
                ctx.send("Please specify a channel to send welcome messages to.")
            else:
                db.execute("UPDATE guilds SET WelcomeMessage = ? WHERE GuildID = ?", passed, ctx.guild.id)
                db.execute("UPDATE guilds SET WelcomeChannelID = ? WHERE GuildID = ?", channel.id, ctx.guild.id)
        elif passed == "disabled":
            db.execute("UPDATE guilds SET WelcomeMessage = ? WHERE GuildID = ?", passed, ctx.guild.id)
            db.execute("UPDATE guilds SET WelcomeChannelID = ? WHERE GuildID = ?", 0, ctx.guild.id)
        else:
            ctx.send("Please specify `enabled` or `disabled` after command to enable or disable welcome messages.")
    
    @welcome_message.error
    async def welcome_message_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")

    @Cog.listener()
    async def on_memeber_join(self, member):
        send_message = db.field("SELECT WelcomeMessage FROM guilds WHERE GuildID =?", self.ctx.guild.id)
        if send_message == "enabled":
            channel = db.field("SELECT WelcomeChannelID FROM guilds WHERE GuildID =?", self.ctx.guild.id)
            await self.bot.get_channel(channel).send(f"Welcome {member.mention}! Please remember to adhere to the rules and have fun!")
        exp = db.field("SELECT Experience FROM guilds WHERE GuildID =?", self.ctx.guild.id)
        if exp == "enabled":
            db.execute("INSERT INTO exp (UserID) VALUES (?)", member.id)

    @Cog.listener()
    async def on_member_remove(self, member):
        exp = db.field("SELECT Experience FROM guilds WHERE GuildID =?", self.ctx.guild.id)
        if exp == "enabled":
            db.execute("DELETE FROM exp WHERE UserID = ?", member.id)
    
def setup(bot):
    bot.add_cog(Welcome(bot))