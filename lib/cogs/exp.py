from random import randint
from datetime import datetime, timedelta
from discord.channel import TextChannel
from discord.ext.commands import command, has_permissions, Cog, CheckFailure, MissingPermissions
from ..db import db

class Exp(Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_xp(self, message):
        xp, lvl, xplock = db.record("SELECT XP, Level, XPLock, FROM exp WHERE UserID =?", message.author.id)
        if datetime.utcnow() > datetime.fromisoformat(xplock):
            await self.add_xp(message, xp, lvl)
    
    async def add_xp(self, message, xp, lvl):
        xp_to_add = randint(5, 15)
        newlvl = int((xp + xp_to_add)//42 ** 0.55)    
        db.execute("UDPATE exp SET XP = XP + ?, XPLock = ? WHERE UserID = ?", xp_to_add, newlvl, (datetime.utcnow() + timedelta(seconds = 60)).isoformat(), message.author.id)
        if newlvl > lvl:
            xp_channel = db.field("SELECT ExperienceID FROM guilds WHERE GuildID =?", self.ctx.guild.id)
            if xp_channel == 0:
                await message.channel.send(f"Congrats {message.author.mention}! You just reached level {newlvl}!")
            else:
                await xp_channel.send(f"Congrats {message.author.mention}! You just reached level {newlvl}!")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("exp")

    @command(name = "exp", help = "Select if to have experience levels or not. Send enaled or disabled after command to specify which one.", aliases = ["experience", "xp"])
    @has_permissions(manage_guild = True)
    async def exp(self, ctx, passed: str):
        if passed == "enabled":
            db.execute("UPDATE guilds SET Experience = ? WHERE GuildID = ?", passed, ctx.guild.id)
            ctx.send("Experience has been enabled.")
        elif passed == "disabled":
            db.execute("UPDATE guilds SET Experience = ? WHERE GuildID = ?", passed, ctx.guild.id)
            db.execute("UPDATE guilds SET ExperienceID = ? WHERE GuildID = ?", 0, ctx.guild.id)
            ctx.send("Experience has been disabled.")
        else:
            ctx.send("Please specify `enabled` or `disabled` after command to enable or disable experience levels.")
    
    @exp.error
    async def exp_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")
    
    @command(name = "expchannel", help = "Select which channel to send experience level ups to. Defaults to channel with user's last sent message.", aliases = ["experiencechannel", "xpch"])
    @has_permissions(manage_guild = True)
    async def exp_channel(self, ctx, channel: TextChannel = None):
        exp = db.field("SELECT Experience FROM guilds WHERE GuildID =?", self.ctx.guild.id)
        if channel == None:
            ctx.send("Please specify a channel to send messages to.")
        elif exp == "enabled":
            db.execute("UPDATE guilds SET ExperienceID = ? WHERE GuildID = ?", channel.id, ctx.guild.id)
            ctx.send("Experience channel set.")
        elif exp == "disabled":
            ctx.send("Please enable experience with the `exp` command")
    
    @exp_channel.error
    async def exp_channel_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")

    @command(name = "remexpchannel", help = "Select which channel to send experience level ups to. Defaults to channel with user's last sent message.", aliases = ["remexperiencechannel", "rxpch"])
    @has_permissions(manage_guild = True)
    async def exp_channel(self, ctx, channel: TextChannel = None):
        exp = db.field("SELECT Experience FROM guilds WHERE GuildID =?", self.ctx.guild.id)
        if channel == None:
            ctx.send("Please specify a channel to send messages to.")
        elif exp == "enabled":
            db.execute("UPDATE guilds SET ExperienceID = ? WHERE GuildID = ?", channel.id, ctx.guild.id)
            ctx.send("Experience channel set.")
        elif exp == "disabled":
            ctx.send("Please enable experience with the `exp` command")
    
    @exp_channel.error
    async def exp_channel_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")

    @Cog.listener
    async def on_message(self, message):
        if not message.author.bot:
            exp = db.field("SELECT Experience FROM guilds WHERE GuildID =?", self.ctx.guild.id)
            if exp == "enabled":
                await self.process_xp(message)

def setup(bot):
    bot.add_cog(Exp(bot))