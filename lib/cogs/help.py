from lib.bot import Bot
from typing import Optional
from discord import Embed
from discord.utils import get
from discord.ext.menus import MenuPages, ListPageSource
from discord.ext.commands import Cog
from discord.ext.commands import command


def syntax(command):
	cmd_and_aliases = "|".join([str(command), *command.aliases])
	params = []

	for key, value in command.params.items():
		if key not in ("self", "ctx"):
			params.append(f"[{key}]" if "NoneType" in str(value) else f"<{key}>")

	params = " ".join(params)

	return f"`{cmd_and_aliases} {params}`"


class HelpMenu(ListPageSource):
	def __init__(self, ctx, data):
		self.ctx = ctx

		super().__init__(data, per_page=3)

	async def write_page(self, menu, fields=[]):
		offset = (menu.current_page*self.per_page) + 1
		len_data = len(self.entries)

		embed = Embed(title="Help",
					  description="Welcome to the Freebot help dialog!",
					  color=self.ctx.author.color)
		embed.set_thumbnail(url=self.ctx.guild.me.avatar_url)
		embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} commands.")

		for name, value in fields:
			embed.add_field(name=name, value=value, inline=False)

		return embed

	async def format_page(self, menu, entries):
		fields = []

		for entry in entries:
			fields.append((entry.name or "No description", syntax(entry)))
			fields.append(("Command description", entry.help))

		return await self.write_page(menu, fields)


class Help(Cog):
	def __init__(self, bot: Bot):
		self.bot = bot
		self.bot.remove_command("help")

	async def cmd_help(self, ctx, command):
		embed = Embed(title=f"Help with `{command}`",
					  description=syntax(command),
					  color=ctx.author.color)
		embed.add_field(name="Command description", value=command.help)
		await ctx.send(embed=embed)

	@command(name="help", help = "Shows the help dialog. If no specific command is give, it will show a pagination of all commands.")
	async def show_help(self, ctx, cmd: Optional[str]):
		if cmd is None:
			u_commands = list(self.bot.commands)
			s_commands = sorted(u_commands, key = lambda x: x.cog_name.lower())
			menu = MenuPages(source=HelpMenu(ctx, s_commands),
							 delete_message_after=True,
                             clear_reactions_after = True,
							 timeout=60.0)
			await menu.start(ctx)

		else:
			if (command := get(self.bot.commands, name=cmd)):
				await self.cmd_help(ctx, command)

			else:
				await ctx.send("That command does not exist.")

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.bot.cogs_ready.ready_up("help")


def setup(bot):
	bot.add_cog(Help(bot))