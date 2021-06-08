from random import randint
from datetime import datetime, timedelta
from typing import Optional
from discord.channel import TextChannel
from discord import Member
from discord.ext.commands import command, has_permissions, Cog, CheckFailure, MissingPermissions
from discord.ext.commands.errors import BadArgument
from ..db import db

class Exp(Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_xp(self, message):
        xp, lvl, xplock = db.record("SELECT XP, UserLevel, XPLock FROM exp WHERE UserID = ? AND GuildID = ?", message.author.id, message.guild.id)
        if datetime.utcnow() > datetime.fromisoformat(xplock):
            await self.add_xp(message, xp, lvl)
    
    async def add_xp(self, message, xp, lvl):
        xp_to_add = randint(10, 20)
        newlvl = int(((xp+xp_to_add)//42) ** 0.55) 
        db.execute("UPDATE exp SET XP = XP + ?, UserLevel = ?, XPLock = ? WHERE UserID = ? AND GuildID = ?", xp_to_add, newlvl, (datetime.utcnow() + timedelta(seconds = 60)).isoformat(), message.author.id, message.guild.id)
        if newlvl > lvl:
            xp_channel = db.field("SELECT ExperienceID FROM guilds WHERE GuildID =?", message.guild.id)
            if xp_channel == 0:
                await message.channel.send(f"Congrats {message.author.mention}! You just reached level {newlvl}!")
            else:
                await message.guild.get_channel(xp_channel).send(f"Congrats {message.author.mention}! You just reached level {newlvl}!")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("exp")

    @command(name = "exp", help = "Select if to have experience levels or not. Send enaled or disabled after command to specify which one.", aliases = ["experience", "xp"])
    @has_permissions(manage_guild = True)
    async def exp(self, ctx, passed: str):
        if passed == "enabled":
            db.execute("UPDATE guilds SET Experience = ? WHERE GuildID = ?", passed, ctx.guild.id)
            await ctx.send("Experience has been enabled.")
        elif passed == "disabled":
            db.execute("UPDATE guilds SET Experience = ? WHERE GuildID = ?", passed, ctx.guild.id)
            db.execute("UPDATE guilds SET ExperienceID = ? WHERE GuildID = ?", 0, ctx.guild.id)
            await ctx.send("Experience has been disabled.")
        else:
            await ctx.send("Please specify `enabled` or `disabled` after command to enable or disable experience levels.")
    
    @exp.error
    async def exp_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")
    
    @command(name = "expchannel", help = "Select which channel to send experience level ups to. Defaults to channel with user's last sent message.", aliases = ["experiencechannel", "xpch"])
    @has_permissions(manage_guild = True)
    async def exp_channel(self, ctx, channel: TextChannel = None):
        exp = db.field("SELECT Experience FROM guilds WHERE GuildID =?", ctx.guild.id)
        if channel == None:
            await ctx.send("Please specify a channel to send messages to.")
        elif exp == "enabled":
            db.execute("UPDATE guilds SET ExperienceID = ? WHERE GuildID = ?", channel.id, ctx.guild.id)
            await ctx.send("Experience channel set.")
        elif exp == "disabled":
            await ctx.send("Please enable experience with the `exp` command")
    
    @exp_channel.error
    async def exp_channel_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")

    @command(name = "remexpchannel", help = "Select which channel to send experience level ups to. Defaults to channel with user's last sent message.", aliases = ["remexperiencechannel", "rxpch"])
    @has_permissions(manage_guild = True)
    async def remove_exp_channel(self, ctx):
        exp = db.field("SELECT Experience FROM guilds WHERE GuildID =?", ctx.guild.id)
        if exp == "enabled":
            channel = db.field("SELECT ExperienceID FROM guilds WHERE GuildID =?", ctx.guild.id)
            if channel == 0:
                await ctx.send("There was no experience channel set so I couldn't remove it.")
            else:
                db.execute("UPDATE guilds SET ExperienceID = ? WHERE GuildID = ?", 0, ctx.guild.id)
                await ctx.send("Experience channel removed.")
        elif exp == "disabled":
            await ctx.send("Please enable experience with the `exp` command")
    
    @exp_channel.error
    async def remove_exp_channel_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")

    @command(name = "level", help = "Display the level of a specified user. If no user is specified the level of the user sending the command will be shown.", aliases = ["lvl"])
    async def level(self, ctx, member: Optional[Member]):
        member = member or ctx.author
        xp, lvl, = db.record("SELECT XP, UserLevel FROM exp WHERE UserID = ? AND GuildID = ?", member.id, ctx.guild.id) or (None, None)

        try:
            await ctx.send(f"{member.display_name} is on level {lvl:,} with {xp:,} XP.")
        except ValueError:
            await ctx.send(f"{member.display_name} does not have a level.")
    @level.error
    async def level_error(self, ctx, exception):
        if isinstance(exception, BadArgument):
            await ctx.send("Please specify which user to check the level of. Or leave it blank and check your own level.")
    
    @command(name = "rank", help = "Display the rank of a specified user. If no user is specified the rank of the user sending the command will be shown.", aliases = ["rnk"])
    async def rank(self, ctx, member: Optional[Member]):
        member = member or ctx.author
        ids = db.column("SELECT UserID FROM exp  WHERE UserID NOT IN (SELECT UserID FROM exp WHERE XP = 0) ORDER BY XP DESC")
        if member.id in ids:
            await ctx.send(f"{member.display_name} is rank {ids.index(member.id)+1} of len{len(ids)}.")
        else:
            await ctx.send(f"{member.display_name} does not have a rank.")
    @rank.error
    async def rank_error(self, ctx, exception):
        if isinstance(exception, BadArgument):
            await ctx.send("Please specify which user to check the rank of. Or leave it blank and check your own rank.")

    @command()

    @Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and not message.content == "":
            exp = db.field("SELECT Experience FROM guilds WHERE GuildID =?", message.guild.id)
            if exp == "enabled":
                await self.process_xp(message)

def setup(bot):
    bot.add_cog(Exp(bot))