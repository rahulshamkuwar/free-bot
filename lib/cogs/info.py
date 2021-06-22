from collections import namedtuple
from datetime import datetime
from lib.cogs.help import HelpMenu

from discord.ext.menus import MenuPages
from lib.bot import Bot
from typing import Optional
from discord import Embed, embeds
from typing import Optional
from discord.ext.commands import command, Cog
from discord.member import Member

class Info(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @command(name = "userinfo", aliases = ["ui", "memberinfo", "mi"], help = "Get information about a specified user.")
    async def user_info(self, ctx, target: Optional[Member], passed: Optional[str]):
        if passed == "help":
            menu = MenuPages(source=HelpMenu(ctx, list(self.get_commands())),
							 delete_message_after=True,
                             clear_reactions_after = True,
							 timeout=60.0)
            await menu.start(ctx)
            return
        member = target or ctx.author
        embed = Embed(title = "User Information", color = member.color, timestamp = datetime.utcnow())
        embed.set_thumbnail(url = member.avatar_url)
        fields = [("ID", member.id, False), 
                  ("Name", str(member), True),
                  ("Bot?", member.bot, True),
                  ("Top Role", member.top_role.mention, True),
                  ("Status", str(member.status).title(), True),
                  ("Account Created On", member.created_at.strftime("%m/%d/%Y %H:%M:%S"), True),
                  ("Joined Server On", member.joined_at.strftime("%m/%d/%Y %H:%M:%S"), True)]
        for name, value, inline in fields:
            embed.add_field(name = name, value = value, inline = inline)
        await ctx.send(embed = embed)

    @command(name = "serverinfo", aliases = ["si", "guildinfo", "gi"], help = "Get information about a specified server.")
    async def server_info(self, ctx, passed: Optional[str]):
        if passed == "help":
            menu = MenuPages(source=HelpMenu(ctx, list(self.get_commands())),
							 delete_message_after=True,
                             clear_reactions_after = True,
							 timeout=60.0)
            await menu.start(ctx)
            return
        embed = Embed(title="Server information",
					  color=ctx.guild.owner.color,
					  timestamp=datetime.utcnow())
        embed.set_thumbnail(url=ctx.guild.icon_url)
        
        statuses = [len(list(filter(lambda m: str(m.status) == "online", ctx.guild.members))),
					len(list(filter(lambda m: str(m.status) == "idle", ctx.guild.members))),
					len(list(filter(lambda m: str(m.status) == "dnd", ctx.guild.members))),
					len(list(filter(lambda m: str(m.status) == "offline", ctx.guild.members)))]
        fields = [("ID", ctx.guild.id, True),
				  ("Owner", ctx.guild.owner, True),
				  ("Region", ctx.guild.region, True),
				  ("Created at", ctx.guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
				  ("Members", len(ctx.guild.members), True),
				  ("Humans", len(list(filter(lambda m: not m.bot, ctx.guild.members))), True),
				  ("Bots", len(list(filter(lambda m: m.bot, ctx.guild.members))), True),
				  ("Banned members", len(await ctx.guild.bans()), True),
				  ("Statuses", f"🟢 {statuses[0]} 🟠 {statuses[1]} 🔴 {statuses[2]} ⚪ {statuses[3]}", True),
				  ("Text channels", len(ctx.guild.text_channels), True),
				  ("Voice channels", len(ctx.guild.voice_channels), True),
				  ("Categories", len(ctx.guild.categories), True),
				  ("Roles", len(ctx.guild.roles), True),
				  ("Invites", len(await ctx.guild.invites()), True),
				  ("\u200b", "\u200b", True)]
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        
        await ctx.send(embed=embed)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("info")

def setup(bot):
    bot.add_cog(Info(bot))