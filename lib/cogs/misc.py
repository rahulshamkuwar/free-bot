from re import S
from discord.ext.commands import command, has_permissions, Cog, CheckFailure
from lib.bot import Bot
# from ..db import db

class Misc(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.cxn
    
    @command(name = "prefix", help = "Select a prefix to trigger Freebot's functions.")
    @has_permissions(manage_guild = True)
    async def change_prefix(self, ctx, new_prefix: str):
        if len(new_prefix) > 5:
            await ctx.send("The prefix cannot be longer than 5 characters in length.")
        else:
            async with self.db.acquire() as db: 
                await db.execute("UPDATE guilds SET Prefix = ($1) WHERE GuildID = ($2);", (new_prefix, ctx.guild.id))
                await ctx.send(f"Prefix is now set to {new_prefix}.")

    @change_prefix.error
    async def change_prefix_error(self, ctx, exception):
        if isinstance(exception, CheckFailure):
            await ctx.send("You need the Manage Messages permissions to do that.")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("misc")

    @Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.update_db()
        await self.bot.update_profanity(guild = guild)

    @Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.leave_guild(guild = guild)


def setup(bot):
    bot.add_cog(Misc(bot))