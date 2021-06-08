from discord.ext.commands import command, has_permissions, Cog, CheckFailure
from ..db import db

class Misc(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @command(name = "prefix", help = "Select a prefix to trigger Freebot's functions.")
    @has_permissions(manage_guild = True)
    async def change_prefix(self, ctx, new_prefix: str):
        if len(new_prefix) > 5:
            await ctx.send("The prefix cannot be longer than 5 characters in length.")
        else:
            db.execute("UPDATE guilds SET Prefix = ? WHERE GuildID = ?", new_prefix, ctx.guild.id)
            await ctx.send(f"Prefix is now set to {new_prefix}.")

    @change_prefix.error
    async def change_prefix_error(self, ctx, exception):
        if isinstance(exception, CheckFailure):
            await ctx.send("You need the Manage Messages permissions to do that.")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("misc")


def setup(bot):
    bot.add_cog(Misc(bot))