import discord
from discord.ext import commands
import asyncio

class DurationConverter(commands.Converter):
    async def convert(self, ctx, argument):
        amount = argument[:-1]
        unit = argument[-1]

        if amount.isdigit() and unit in ["s", "m", "h", "d", "w", "mth", "y"]:
            return (int(amount), unit)
        raise commands.BadArgument(message="Not a valid duration!")

class Example(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    #Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online.")
    
    @commands.Cog.listener()
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.args.__contains__(discord.Member):
                await ctx.send("Please specify a user to ban.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to ban.")
    #Commands
    @commands.command(name="ban", help="Ban a specified user")
    async def ban(self, ctx, member: commands.MemberConverter, *, reason: str):
        await member.ban(reason = reason)
        await ctx.send(f"{member} has been banned")
    
    @commands.command(name="tempban", help="Ban a specified user")
    async def tempban(self, ctx, member: commands.MemberConverter, reason: str, duration: DurationConverter):
        multiplier = {"s" : 1, "m" : 60, "h" : 3600, "d" : 86400, "w" : 604800, "mth" : 2.628e+6, "y" : 3.154e+7}
        amount, unit = duration
        await member.ban(reason = reason)
        await ctx.send(f"{member} has been banned for {amount}{unit}")
        await asyncio.sleep(amount * multiplier[unit])
        await ctx.guild.unban(member)

    @commands.command(name="kick", help="Kick a specified user")
    async def kick(self, ctx, member: commands.MemberConverter, *, reason: str):
        await member.kick(reason = reason)
        await ctx.send(f"{member} has been kicked")

    @commands.command(name="unban", help="Unban a specified user")
    async def unban(self, ctx, *, member: commands.MemberConverter):
        banned_users = await ctx.guild.bans()

        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member.name, member.discriminator):
                await ctx.guild.unban(user)
            return
        await ctx.send(f"{member} has been unbanned")
    # @commands.command(name="mute", help="Mute a specified user")
    # async def mute(ctx, member: commands.MemberConverter, *, reason: str):
    #   multiplier = {"s" : 1, "m" : 60, "h" : 3600, "d" : 86400, "w" : 604800, "mth" : 2.628e+6, "y" : 3.154e+7}
        

    

def setup(client):
    client.add_cog(Example(client))