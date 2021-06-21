from datetime import datetime
from typing import Optional
from discord.channel import DMChannel
from discord.embeds import Embed
from discord.ext.commands import command, has_permissions, Cog
from discord.ext.commands.converter import CategoryChannelConverter, GuildConverter, TextChannelConverter
from discord.ext.commands.core import bot_has_permissions
from discord.ext.commands.errors import BotMissingPermissions, MissingPermissions, MissingRequiredArgument
from discord.ext.menus import MenuPages, ListPageSource
from discord.member import Member
from discord.message import Message
from lib.bot import Bot

class ModMailMenu(ListPageSource):
	def __init__(self, ctx, data):
		self.ctx = ctx

		super().__init__(data, per_page=3)

	async def write_page(self, menu, fields=[]):
		offset = (menu.current_page*self.per_page) + 1
		len_data = len(self.entries)

		embed = Embed(title="Modmail Servers", description = "Copy the server ID for the server you want to send a message to.", color = self.ctx.message.author.color, timestamp = datetime.utcnow())
		embed.set_thumbnail(url=self.ctx.message.author.avatar_url)
		embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} servers.")

		for name, value in fields:
			embed.add_field(name=name, value=value, inline=False)

		return embed

	async def format_page(self, menu, entries):
		fields = []

		for entry in entries:
			fields.append((entry.name, entry.id))

		return await self.write_page(menu, fields)


class Modmail(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = bot.cxn
    
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("modmail")
    
    @command(name = "modmail", help = "Select if to have modmail or not. Send enabled or disabled after the command to specify which one.")
    @has_permissions(manage_guild = True, manage_channels = True)
    @bot_has_permissions(manage_channels = True)
    async def modmail(self, ctx, passed: str, category: Optional[CategoryChannelConverter] = None, channel: Optional[TextChannelConverter] = None):
        async with self.db.acquire() as db:
            if passed == "enabled":
                if category is None:
                    await ctx.send("Please specify a category to send modmail messages to.")
                elif channel is None:
                    await ctx.send("Please specify a notifications channel for modmail notifications.")
                else:
                    await db.execute("UPDATE guilds SET (Modmail, ModmailCategoryID, ModmailNotificationID) = ($1, $2, $3) WHERE GuildID = ($4);", passed, category.id, channel.id,ctx.guild.id)
                    await ctx.send(f"Modmail messages will be sent in new channels in {category.mention}. Please note that the permissions of each channel will sync with the category's permissions. Additionally, please do not edit the name or topic of any channels that are created, doing so will cause issues to the modmail system with that user.")
            elif passed == "disabled":
                await db.execute("UPDATE guilds SET (Modmail, ModmailCategoryID, ModmailNotificationID) = ($1, $2, $3) WHERE GuildID = ($4);", passed, 0, 0, ctx.guild.id)
                await ctx.send("Modmail has been disabled.")
            else:
                await ctx.send("Please specify `enabled` or `disabled` after the command to enable or disable modmail.")
    
    @modmail.error
    async def modmail_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")
        elif isinstance(exception, BotMissingPermissions):
            await ctx.send("I do not have permission to manage channels.")
        elif isinstance(exception, MissingRequiredArgument):
            await ctx.send("Please send `enabled` followed by the category ID and then the notification channel ID. Or send `disabled` to disable modmail.")
    

    @command(name = "modmailservers", help = "Get the server ID to send your modmail ticket to by DM-ing the bot.")
    async def modmail_servers(self, ctx):
        if not ctx.message.author.bot:
            if not isinstance(ctx.message.channel, DMChannel):
                await ctx.send("This commmand can only be used in DMs with me.")
                return
            menu = MenuPages(source=ModMailMenu(ctx, list(ctx.message.author.mutual_guilds)), delete_message_after=True, clear_reactions_after = True, timeout=60.0)
            await menu.start(ctx)

    @command(name = "newticket", help = "Start a new modmail ticket by DM-ing the bot and sending the server ID you want to send a message to.")
    async def modmail_new_ticket(self, ctx, guild: GuildConverter):
        if not ctx.message.author.bot:
            if not isinstance(ctx.message.channel, DMChannel):
                await ctx.send("This commmand can only be used in DMs with me.")
                return
            async with self.db.acquire() as db:
                query = await db.fetchrow("SELECT Modmail, ModmailCategoryID, ModmailNotificationID FROM guilds WHERE GuildID = ($1);", guild.id)
                modmail = query.get('modmail')
                if modmail == 'enabled':
                    blacklist_query = await db.fetchrow("SELECT UserID from blacklist WHERE GuildID = $1", guild.id)
                    if blacklist_query:
                        await ctx.send("You have been blacklisted from sending messages to this server. For more details please contact the mods from this server.")
                        return
                    category = guild.get_channel(query.get('modmailcategoryid'))
                    ticket_exists = False
                    if len(category.text_channels) >= 50:
                        notif_channel = await TextChannelConverter.convert(ctx = ctx, argument = query.get('modmailnotificationid'))
                        mod_embed = Embed(title = "Max Number of Tickets Reached", description = f"You have reached 50 tickets, which is the maximum number of tickets allowed. Please consider closing some tickets so that other users may create a new ticket.", color = 0xFF0000, timestamp = datetime.utcnow())
                        await notif_channel.send(embed = mod_embed)

                        user_embed = Embed(title = "Max Number of Tickets Reached", description = f"This server has reached 50 tickets, which is the maximum number of tickets allowed. Please contact the mods in this server.", color = 0xFF0000, timestamp = datetime.utcnow())
                        await ctx.message.channel.send(embed = user_embed)
                        return
                    else:
                        for this_channel in category.text_channels:
                            if int(this_channel.topic or "1") == ctx.message.author.id and this_channel.name == ctx.message.author.name:
                                ticket_exists = True
                        if not ticket_exists:
                            channel = await category.create_text_channel(name = ctx.author.name)
                            await db.execute("UPDATE modmail SET CurrentTicketID = $1 WHERE UserID = $2;", category.id, ctx.message.author.id)
                            await channel.edit(topic = ctx.message.author.id, sync_permissions = True)
                            mod_embed = Embed(title = "New Ticket Created!", description = f"A new ticket has been created by {ctx.message.author.mention}! Please use the `send` or `asend` commands to send any messages for this ticket. To close this ticket use `close` or `aclose`.", color = ctx.message.author.color, timestamp = datetime.utcnow())
                            mod_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                            await channel.send(embed = mod_embed)

                            user_embed = Embed(title = "New Ticket Created!", description = f"A new ticket has been created with {guild.name}! Please use the `send` command to send any messages for this ticket. To pause this ticket use `pauseticket`.", color = 0x00FF00, timestamp = datetime.utcnow())
                            user_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                            await ctx.message.channel.send(embed = user_embed)
                            if len(category.text_channels) == 50:
                                notif_channel = await TextChannelConverter.convert(ctx = ctx, argument = query.get('modmailnotificationid'))
                                mod_embed = Embed(title = "Max Number of Tickets Reached", description = f"You have reached 50 tickets, which is the maximum number of tickets allowed. Please consider closing some tickets so that other users may create a new ticket.", color = 0xFF0000, timestamp = datetime.utcnow())
                                await notif_channel.send(embed = mod_embed)
                        else:
                            await ctx.send("You already have an existing ticket with this server! Please use `resumeticket` in order to resume a previous ticket with the server.")
                else:
                    await ctx.send("This server has not enabled modmail yet. Please contact the mods in this server.")
    
    @modmail_new_ticket.error
    async def modmail_new_ticket_error(self, ctx, exception):
        if isinstance(exception, MissingRequiredArgument):
                await ctx.send("Please specify the server ID you want to send a message to. If you do not know the server ID, use `modmailservers` to find a list of servers and their IDs.")
    
    @command(name = "resumeticket", help = "Resume an old modmail ticket by DM-ing the bot and sending the server ID you want to send a message to.")
    async def modmail_resume_ticket(self, ctx, guild: GuildConverter):
        if not ctx.message.author.bot:
            if not isinstance(ctx.message.channel, DMChannel):
                await ctx.send("This commmand can only be used in DMs with me.")
                return
            async with self.db.acquire() as db:
                query = await db.fetchrow("SELECT Modmail, ModmailCategoryID, ModmailNotificationID FROM guilds WHERE GuildID = ($1);", guild.id)
                modmail = query.get('modmail')
                if modmail == 'enabled':
                    blacklist_query = await db.fetchrow("SELECT UserID from blacklist WHERE GuildID = $1", guild.id)
                    if blacklist_query:
                        await ctx.send("You have been blacklisted from sending messages to this server. For more details please contact the mods from this server.")
                        return
                    category = self.bot.get_channel(query.get('modmailcategoryid'))
                    ticket_exists = False
                    for this_channel in category.text_channels:
                        if int(this_channel.topic or "1") == ctx.message.author.id and this_channel.name == ctx.message.author.name:
                            ticket_exists = True
                    if ticket_exists:
                        await db.execute("UPDATE modmail SET CurrentTicketID = $1 WHERE UserID = $2;", category.id, ctx.message.author.id)
                        user_embed = Embed(title = "Ticket Resumed!", description = f"Ticket has been resumed with {guild.name}! Please use the `send` command to send any messages for this ticket. To pause this ticket use `pauseticket`.", color = 0x00FF00, timestamp = datetime.utcnow())
                        user_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                        await ctx.message.channel.send(embed = user_embed)
                    else:
                        await ctx.send("You do not have an existing ticket with this server! Please use `newticket` in order to create a new ticket with the server.")
                else:
                    await ctx.send("This server has not enabled modmail yet. Please contact the mods in this server.")

    
    @modmail_resume_ticket.error
    async def modmail_resume_ticket_error(self, ctx, exception):
        if isinstance(exception, MissingRequiredArgument):
                await ctx.send("Please specify the server ID you want to send a message to. If you do not know the server ID, use `modmailservers` to find a list of servers and their IDs.")
    
    @command(name = "pauseticket", help = "Pause the current modmail ticket.")
    async def pause_ticket(self, ctx):
        if not ctx.message.author.bot:
            if not isinstance(ctx.message.channel, DMChannel):
                await ctx.send("This commmand can only be used in DMs with me.")
                return
            async with self.db.acquire() as db:
                await db.execute("UPDATE modmail SET CurrentTicketID = $1 WHERE UserID = $2", 0, ctx.message.author.id)
                user_embed = Embed(title = "Ticket paused", description = f"This ticket has been paused. To start a new ticket, please use `newticket`, or to resume a previous ticket, use `resumeticket`.", color = 0xFFFF00, timestamp = datetime.utcnow())
                user_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                await ctx.send(embed = user_embed)
    
    @command(name = "send", help = "Use this command to send messages for modmail tickets.")
    async def send(self, ctx, *, mail: str = None):
        if not ctx.message.author.bot:
            if mail == None or mail.strip() == "":
                await ctx.send("Please write a message after the command to send.")
                return
            async with self.db.acquire() as db:
                is_dm_channel = isinstance(ctx.message.channel, DMChannel)
                if is_dm_channel:
                    query = await db.fetchrow("Select CurrentTicketID from modmail WHERE UserID = $1", ctx.message.author.id)
                    category_id = query.get('currentticketid')
                    if category_id == 0:
                        await ctx.send("Please specify which server to send this message to! Either use `newticket` or `resumeticket`.")
                        return
                    category = self.bot.get_channel(category_id)
                    blacklist_query = await db.fetchrow("SELECT UserID from blacklist WHERE GuildID = $1", category.guild.id)
                    if blacklist_query:
                        await ctx.send("You have been blacklisted from sending messages to this server. For more details please contact the mods from this server.")
                        return
                    channel = None
                    for this_channel in category.text_channels:
                        if int(this_channel.topic or "1") == ctx.message.author.id and this_channel.name == ctx.message.author.name:
                            channel = this_channel
                    mod_embed = Embed(title = "New Message", description = f"A new message received from {ctx.message.author.mention}.", color = channel.guild.get_member(ctx.message.author.id).color, timestamp = datetime.utcnow())
                    mod_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                    mod_embed.add_field(name = "Message:", value = mail, inline = False)
                    await channel.send(embed = mod_embed)

                    user_embed = Embed(title = "Message sent", description = f"New message sent to {category.guild.name}.", color = 0x00FF00, timestamp = datetime.utcnow())
                    user_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                    user_embed.add_field(name = "Message:", value = mail, inline = False)
                    await ctx.message.channel.send(embed = user_embed)
                else:
                    query = await db.fetchrow("Select ModmailCategoryID from guilds WHERE GuildID = $1", ctx.message.guild.id)
                    category = ctx.message.guild.get_channel(query.get('modmailcategoryid'))
                    if not (ctx.message.channel in list(category.text_channels)):
                        await ctx.send("This commmand can only be used in DMs with me or in a ticket channel in a server.")
                        return
                    blacklist_query = await db.fetchrow("SELECT UserID from blacklist WHERE GuildID = $1", category.guild.id)
                    if blacklist_query:
                        await ctx.send("This user has been blacklisted from sending messages to this server.")
                        return
                    user = self.bot.get_user(int(ctx.message.channel.topic))
                    mod_embed = Embed(title = "Message sent", description = f"New message sent to {user.mention}.", color = ctx.message.author.color, timestamp = datetime.utcnow())
                    mod_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                    mod_embed.add_field(name = "Message:", value = mail, inline = False)
                    await ctx.message.channel.send(embed = mod_embed)

                    user_embed = Embed(title = "New Message", description = f"A new message received from {category.guild.name}.", color = ctx.message.author.color, timestamp = datetime.utcnow())
                    user_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                    user_embed.add_field(name = "Message:", value = mail, inline = False)
                    await user.send(embed = user_embed)

    @send.error
    async def send_error(self, ctx, exception):
        if isinstance(exception, MissingRequiredArgument):
            await ctx.send("Please write a message after the command to send.")

    @command(name = "asend", help = "Use this command to send messages anonymously for modmail tickets.")
    async def asend(self, ctx, *, mail: str = None):
        if not ctx.message.author.bot:
            if isinstance(ctx.message.channel, DMChannel):
                await ctx.send("This commmand can only be used in a ticket channel in a server.")
                return
            async with self.db.acquire() as db:
                query = await db.fetchrow("Select ModmailCategoryID from guilds WHERE GuildID = $1", ctx.message.guild.id)
                category = ctx.message.guild.get_channel(query.get('modmailcategoryid'))
                blacklist_query = await db.fetchrow("SELECT UserID from blacklist WHERE GuildID = $1", category.guild.id)
                if blacklist_query:
                    await ctx.send("This user has been blacklisted from sending messages to this server.")
                    return
                if not (ctx.message.channel in list(category.text_channels)):
                    await ctx.send("This commmand can only be used in a ticket channel in a server.")
                    return
                if mail == None or mail.strip() == "":
                    await ctx.send("Please write a message after the command to send.")
                    return
                user = self.bot.get_user(int(ctx.message.channel.topic))
                mod_embed = Embed(title = "Message sent", description = f"New message sent to {user.mention}.", color = 0x00FF00, timestamp = datetime.utcnow())
                mod_embed.set_thumbnail(url = category.guild.icon_url)
                mod_embed.add_field(name = "Message:", value = mail, inline = False)
                await ctx.message.channel.send(embed = mod_embed)

                user_embed = Embed(title = "New Message", description = f"A new message received from {category.guild.name}.", color = 0x00FF00, timestamp = datetime.utcnow())
                user_embed.set_thumbnail(url = category.guild.icon_url)
                user_embed.add_field(name = "Message:", value = mail, inline = False)
                await user.send(embed = user_embed)

    @asend.error
    async def asend_error(self, ctx, exception):
        if isinstance(exception, MissingRequiredArgument):
            await ctx.send("Please write a message after the command to send.")

    @command(name = "close", help = "Close a modmail ticket in the specific channel.")
    async def close(self, ctx):
        if not ctx.message.author.bot:
            if isinstance(ctx.message.channel, DMChannel):
                await ctx.send("This commmand can only be used in a ticket channel in a server.")
                return
            async with self.db.acquire() as db:
                query = await db.fetchrow("SELECT Modmail, ModmailCategoryID, ModmailNotificationID FROM guilds WHERE GuildID = ($1);", ctx.message.guild.id)
                modmail = query.get('modmail')
                if modmail == 'enabled':
                    category = ctx.message.guild.get_channel(query.get('modmailcategoryid'))
                    if not (ctx.message.channel in list(category.text_channels)):
                        await ctx.send("This commmand can only be used in a ticket channel in a server.")
                        return
                    user = self.bot.get_user(int(ctx.message.channel.topic))
                    await db.execute("UPDATE modmail SET CurrentTicketID = $1 WHERE UserID = $2", 0, user.id)
                    user_embed = Embed(title = "Ticket closed", description = f"This ticket has been closed by {ctx.message.author.mention} for {ctx.message.guild.name}.", color = ctx.message.author.color, timestamp = datetime.utcnow())
                    user_embed.set_thumbnail(url = ctx.message.author.avatar_url)
                    await user.send(embed = user_embed)
                    await ctx.message.channel.delete()
                else:
                    await ctx.send("Please enable modmail in this server to use this command.")
    
    @command(name = "aclose", help = "Anonymously close a modmail ticket in the specific channel.")
    async def aclose(self, ctx):
        if not ctx.message.author.bot:
            if isinstance(ctx.message.channel, DMChannel):
                await ctx.send("This commmand can only be used in a ticket channel in a server.")
                return
            async with self.db.acquire() as db:
                query = await db.fetchrow("SELECT Modmail, ModmailCategoryID, ModmailNotificationID FROM guilds WHERE GuildID = ($1);", ctx.message.guild.id)
                modmail = query.get('modmail')
                if modmail == 'enabled':
                    category = ctx.message.guild.get_channel(query.get('modmailcategoryid'))
                    if not (ctx.message.channel in list(category.text_channels)):
                        await ctx.send("This commmand can only be used in a ticket channel in a server.")
                        return
                    user = self.bot.get_user(int(ctx.message.channel.topic))
                    await db.execute("UPDATE modmail SET CurrentTicketID = $1 WHERE UserID = $2", 0, user.id)
                    user_embed = Embed(title = "Ticket closed", description = f"The ticket for {ctx.message.guild.name} has been closed.", color = 0xFF0000, timestamp = datetime.utcnow())
                    user_embed.set_thumbnail(url = ctx.message.guild.icon_url)
                    await user.send(embed = user_embed)
                    await ctx.message.channel.delete()
                else:
                    await ctx.send("Please enable modmail in this server to use this command.")
    
    @command(name = "blacklist", help = "Add a user to a blacklist to block them from using modmail tickets.")
    @has_permissions(manage_guild = True)
    async def blacklist(self, ctx, member: Member):
        if not ctx.message.author.bot:
            async with self.db.acquire() as db:
                await db.execute("INSERT INTO blacklist (UserID, GuildID) VALUES ($1, $2) ON CONFLICT DO NOTHING", member.id, ctx.guild.id)
                await ctx.send("User has been added to the blacklist.")

    @blacklist.error
    async def blacklist_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")
        elif isinstance(exception, MissingRequiredArgument):
            await ctx.send("Please send the member to blacklist from this server's modmail system.")
    
    @command(name = "whitelist", help = "Remove a user from the blacklist.")
    @has_permissions(manage_guild = True)
    async def whitelist(self, ctx, member: Member):
        if not ctx.message.author.bot:
            async with self.db.acquire() as db:
                await db.execute("DELETE FROM blacklist WHERE (UserID, GuildID) = ($1, $2)", member.id, ctx.guild.id)
                await ctx.send("User has been removed from the blacklist.")
                
    @whitelist.error
    async def whitelist_error(self, ctx, exception):
        if isinstance(exception, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")
        elif isinstance(exception, MissingRequiredArgument):
            await ctx.send("Please send the member to remove from blacklist.")

def setup(bot):
    bot.add_cog(Modmail(bot))