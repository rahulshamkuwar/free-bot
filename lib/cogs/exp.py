from lib.bot import Bot
from os import XATTR_CREATE
from random import randint
from datetime import datetime, timedelta
from typing import Optional
from discord.channel import TextChannel
from discord import Member
from discord.ext.commands import command, has_permissions, Cog, MissingPermissions
from discord.ext.commands.errors import BadArgument, MissingRequiredArgument


class Exp(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.cxn

    async def process_xp(self, message):
        async with self.db.acquire() as db:
            query = await db.fetchrow("SELECT XP, UserLevel, XPLock FROM exp WHERE UserID = ($1) AND GuildID = ($2);", message.author.id, message.guild.id)
            this_list = list(query.values())
            xp, lvl, xplock = this_list[0], this_list[1], this_list[2]
            if datetime.utcnow() > datetime.fromisoformat(xplock):
                await self.add_xp(message, xp, lvl)
    
    async def add_xp(self, message, xp, lvl):
        xp_to_add = randint(10, 20)
        newlvl = int(((xp+xp_to_add)//42) ** 0.55) 
        async with self.db.acquire() as db:
            await db.execute("UPDATE exp SET XP = XP + ($1), UserLevel = ($2), XPLock = ($3) WHERE UserID = ($4) AND GuildID = ($5);", xp_to_add, newlvl, ((datetime.utcnow() + timedelta(seconds = 60)).isoformat()), message.author.id, message.guild.id)
            if newlvl > lvl:
                query = await db.fetchrow("SELECT ExperienceID FROM guilds WHERE GuildID = ($1);", message.guild.id)
                xp_channel = query.get('experienceid')
                if xp_channel == 0:
                    await message.channel.send(f"Congrats {message.author.mention}! You just reached level {newlvl}!")
                else:
                    await message.guild.get_channel(xp_channel).send(f"Congrats {message.author.mention}! You just reached level {newlvl}!")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("exp")

    @command(name = "exp", help = "Select if to have experience levels or not. Send enabled or disabled after the command to specify which one.", aliases = ["experience", "xp"])
    @has_permissions(manage_guild = True)
    async def exp(self, ctx, passed: str):
        async with self.db.acquire() as db:
            if passed == "enabled":
                await db.execute("UPDATE guilds SET Experience = ($1) WHERE GuildID = ($2);", passed, ctx.guild.id)
                await ctx.send("Experience has been enabled.")
            elif passed == "disabled":
                await db.execute("UPDATE guilds SET Experience, ExperienceID = ($1, $2) WHERE GuildID = ($3);", passed, 0, ctx.guild.id)
                await ctx.send("Experience has been disabled.")
            else:
                await ctx.send("Please specify `enabled` or `disabled` after command to enable or disable experience levels.")
    
    @exp.error
    async def exp_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")
        elif isinstance(exception, MissingRequiredArgument):
            await ctx.send("Please specify `enabled` or `disabled` after command to enable or disable experience levels.")
    
    @command(name = "expchannel", help = "Select which channel to send experience level ups to. Defaults to channel with user's last sent message.", aliases = ["experiencechannel", "xpch"])
    @has_permissions(manage_guild = True)
    async def exp_channel(self, ctx, channel: TextChannel = None):
        async with self.db.acquire() as db:
            query = await db.fetchrow("SELECT Experience FROM guilds WHERE GuildID = ($1);", ctx.guild.id)
            exp = query.get('experience')
            if channel == None:
                await ctx.send("Please specify a channel to send messages to.")
            elif exp == "enabled":
                await db.execute("UPDATE guilds SET ExperienceID = ($1) WHERE GuildID = ($2);", channel.id, ctx.guild.id)
                await ctx.send("Experience channel set.")
            elif exp == "disabled":
                await ctx.send("Please enable experience with the `exp` command")
    
    @exp_channel.error
    async def exp_channel_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")
        elif isinstance(exception, MissingRequiredArgument):
            await ctx.send("Please specify a channel to send messages to.")

    @command(name = "remexpchannel", help = "Remove the current channel that sends experience level ups.", aliases = ["remexperiencechannel", "rxpch"])
    @has_permissions(manage_guild = True)
    async def remove_exp_channel(self, ctx):
        async with self.db.acquire() as db:
            query = await db.fetchrow("SELECT Experience, ExperienceID FROM guilds WHERE GuildID = ($1);", ctx.guild.id)
            exp = query.get('experience')
            if exp == "enabled":
                channel = query.get('experienceid')
                if channel == 0:
                    await ctx.send("There was no experience channel set so I couldn't remove it.")
                else:
                    await db.execute("UPDATE guilds SET ExperienceID = ($1) WHERE GuildID = ($2);", 0, ctx.guild.id)
                    await ctx.send("Experience channel removed.")
            elif exp == "disabled":
                await ctx.send("Please enable experience with the `exp` command.")
    
    @exp_channel.error
    async def remove_exp_channel_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")

    @command(name = "level", help = "Display the level of a specified user. If no user is specified the level of the user sending the command will be shown.", aliases = ["lvl"])
    async def level(self, ctx, member: Optional[Member]):
        member = member or ctx.author
        async with self.db.acquire() as db:
            query = await db.fetchrow("SELECT XP, UserLevel FROM exp WHERE UserID = ($1) AND GuildID = ($2);", member.id, ctx.guild.id) or (None, None)
            xp, lvl = query.get("xp"), query.get("userlevel")
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
        async with self.db.acquire() as db:
            query = await db.fetch(
                """
                SELECT 
                    UserID,
                    GuildID,
                    rank() OVER (PARTITION BY GuildID ORDER BY XP DESC) AS Rank
                FROM exp
                WHERE UserID = $1 AND GuildID = $2
                """, member.id, ctx.guild.id)
            rank = list(query[0].values())[0]
            len_query = await db.fetch(
                """
                SELECT COUNT(*)
                    FROM exp
                WHERE GuildID = $1
                    AND XP != 0
                """, ctx.guild.id
            )
            members = list(len_query[0].values())[0]
            await ctx.send(f"{member.display_name} is rank {rank} of {members}.")
    @rank.error
    async def rank_error(self, ctx, exception):
        if isinstance(exception, BadArgument):
            await ctx.send("Please specify which user to check the rank of. Or leave it blank and check your own rank.")
        elif isinstance(exception, BadArgument):
            await ctx.send("Please specify which user to check the rank of.")

    @Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and not message.content == "":
            async with self.db.acquire() as db:
                record = await db.fetchrow("SELECT Experience FROM guilds WHERE GuildID = ($1);", message.guild.id)
                exp = record.get('experience')
                if exp == "enabled":
                    await self.process_xp(message)

def setup(bot):
    bot.add_cog(Exp(bot))