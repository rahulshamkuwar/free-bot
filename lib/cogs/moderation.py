import discord
from discord.ext import commands
from discord.ext.commands import Cog, Converter, command
import asyncio

class DurationConverter(Converter):
    async def convert(self, ctx, argument):
        amount = argument[:-1]
        unit = argument[-1]

        if amount.isdigit() and unit in ["s", "m", "h", "d", "w", "mth", "y"]:
            return (int(amount), unit)
        raise commands.BadArgument(message="Not a valid duration!")

class Moderation(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    #Events
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("moderation")
    
    #Commands
    @command(name="ban", help="Ban a specified user.")
    async def ban(self, ctx, member: commands.MemberConverter, *, reason: str):
        await member.ban(reason = reason)
        await ctx.send(f"{member} has been banned.")
    
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.args.__contains__(discord.Member):
                await ctx.send("Please specify a user to ban.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to ban.")

    @command(name="tempban", help="Temp ban a specified user.")
    async def tempban(self, ctx, member: commands.MemberConverter, duration: DurationConverter, *, reason: str):
        multiplier = {"s" : 1, "m" : 60, "h" : 3600, "d" : 86400, "w" : 604800, "mth" : 2.628e+6, "y" : 3.154e+7}
        amount, unit = duration
        await member.ban(reason = reason)
        await ctx.send(f"{member} has been banned for {amount}{unit}.")
        await asyncio.sleep(amount * multiplier[unit])
        await ctx.guild.unban(member)
    
    @tempban.error
    async def tempban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.args.__contains__(discord.Member):
                await ctx.send("Please specify a user to temp ban.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to temp ban.")
            elif error.args.__contains__(DurationConverter):
                await ctx.send("Please specify a duration to temp ban.")

    @command(name="kick", help="Kick a specified user.")
    async def kick(self, ctx, member: commands.MemberConverter, *, reason: str):
        await member.kick(reason = reason)
        await ctx.send(f"{member} has been kicked.")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.args.__contains__(discord.Member):
                await ctx.send("Please specify a user to kick.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to kick.")

    @command(name="unban", help="Unban a specified user.")
    async def unban(self, ctx, member: commands.MemberConverter, *, reason: str):
        banned_users = await ctx.guild.ban()

        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member.name, member.discriminator):
                await ctx.guild.unban(user, reason = reason)
            return
        await ctx.send(f"{member} has been unbanned.")
    
    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.args.__contains__(discord.Member):
                await ctx.send("Please specify a user to unban.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to unban.")

    
    
    # @commands.command(name="mute", help="Mute a specified user")
    # async def mute(ctx, member: commands.MemberConverter, *, reason: str):
    #   multiplier = {"s" : 1, "m" : 60, "h" : 3600, "d" : 86400, "w" : 604800, "mth" : 2.628e+6, "y" : 3.154e+7}
        

    

def setup(bot):
    bot.add_cog(Moderation(bot))