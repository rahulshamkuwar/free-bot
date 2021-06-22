from datetime import datetime
from lib.cogs.help import HelpMenu

from discord.ext.menus import MenuPages
from lib.bot import Bot
from discord.embeds import Embed
from discord.ext.commands import command, has_permissions, Cog, TextChannelConverter, MissingPermissions


class Welcome(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.cxn

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("welcome")
    
    @command(name = "welcomemessage", help = "Select if to have a welcome message or not. Send `enabled` or `disabled` after the command to specify which one. To view a list of commands, send `help` after the command.")
    @has_permissions(manage_guild = True)
    async def welcome_message(self, ctx, passed: str, channel: TextChannelConverter = None):
        async with self.db.acquire() as db:
            if passed == "enabled":
                if channel is None:
                    await ctx.send("Please specify a channel to send welcome messages to.")
                else:
                    await db.execute("UPDATE guilds SET (WelcomeMessage, WelcomeChannelID) = ($1, $2) WHERE GuildID = ($3);", passed, channel.id, ctx.guild.id)
                    await ctx.send(f"Welcome message enabled and welcome channel set to {channel.mention}.")
            elif passed == "disabled":
                await db.execute("UPDATE guilds SET (WelcomeMessage, WelcomeChannelID) = ($1, $2) WHERE GuildID = ($3);", passed, 0, ctx.guild.id)
                await ctx.send("Welcome message disabled and welcome channel removed.")
            elif passed == "help":
                menu = MenuPages(source=HelpMenu(ctx, list(self.get_commands())),
							 delete_message_after=True,
                             clear_reactions_after = True,
							 timeout=60.0)
                await menu.start(ctx)
            else:
                await ctx.send("Please specify `enabled` or `disabled` after the command to enable or disable welcome messages.")
    
    @welcome_message.error
    async def welcome_message_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")

    @Cog.listener()
    async def on_member_join(self, member):
        async with self.db.acquire() as db:
            query = await db.fetchrow("SELECT WelcomeMessage, WelcomeChannelID, Experience, Logs, LogsChannelID FROM guilds WHERE GuildID = ($1);", member.guild.id)
            send_message = query.get("welcomemessage")
            if send_message == "enabled":
                channel = query.get("welcomechannelid")
                await self.bot.get_channel(channel).send(f"Welcome {member.mention}! Please remember to adhere to the rules and have fun!")
            exp = query.get('experience')
            if exp == "enabled":
                await db.execute("INSERT INTO exp (UserID, GuildID) VALUES (($1), ($2))", member.id, member.guild.id)
            send_log = query.get("logs")
            if send_log == "enabled":
                log_channel = query.get("logschannelid")
                embed = Embed(title = "Member Joined Server", color = 0xDD2222, timestamp = datetime.utcnow())
                embed.set_thumbnail(url = member.default_avatar_url)
                fields = [("Member", member.mention, False),
                        ("Account Created On", member.created_at.strftime("%m/%d/%Y %H:%M:%S"), False),]
                for name, value, inline in fields:
                    embed.add_field(name = name, value = value, inline = inline)
                await self.bot.get_channel(log_channel).send(embed = embed)

    @Cog.listener()
    async def on_member_remove(self, member):
        async with self.db.acquire() as db:
            query = await db.fetchrow("SELECT Experience, Logs, LogsChannelID FROM guilds WHERE GuildID = ($1);", member.guild.id)
            exp = query.get('experience')
            if exp == "enabled":
                await db.execute("DELETE FROM exp WHERE UserID = ($1) AND GuildID = ($2)", member.id, member.guild.id)
            send_log = query.get("logs")
            if send_log == "enabled":
                log_channel = query.get("logschannelid")
                embed = Embed(title = "Member Left Server", color = 0xDD2222, timestamp = datetime.utcnow())
                embed.set_thumbnail(url = member.default_avatar_url)
                fields = [("Member", member.mention, False),
                        ("Account Created On", member.created_at.strftime("%m/%d/%Y %H:%M%S"), False),]
                for name, value, inline in fields:
                    embed.add_field(name = name, value = value, inline = inline)
                await self.bot.get_channel(log_channel).send(embed = embed)
        
    
def setup(bot):
    bot.add_cog(Welcome(bot))