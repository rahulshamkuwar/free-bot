from enum import auto
from better_profanity import profanity
from re import search
from datetime import datetime
from typing import Optional
from discord import Role, Permissions, Embed, Member
from discord.channel import TextChannel
from discord.ext import commands
from discord.ext.commands import Cog, Converter, command, has_permissions, bot_has_permissions, MissingRequiredArgument, MemberConverter, BotMissingPermissions, MissingPermissions
import asyncio
from ..db import db

profanity.load_censor_words_from_file("./data/profanity.txt")
class DurationConverter(Converter):
    async def convert(self, ctx, argument):
        amount = argument[:-1]
        unit = argument[-1]

        if amount.isdigit() and unit in ["s", "m", "h", "d", "w", "mth", "y"]:
            return (int(amount), unit)
        raise commands.BadArgument(message="Not a valid duration!")

class Mod(Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    
    #Events
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("mod")
    
    @Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            if not message.author.guild_permissions.is_superset(Permissions(manage_guild = True)):
                check_profanity = db.field("SELECT Profanity FROM guilds WHERE GuildID =?", message.guild.id)
                # auto_links = db.field("SELECT AutoLinks FROM guilds WHERE GuildID =?", message.guild.id)
                if check_profanity == "enabled":
                    if profanity.contains_profanity(message.content):
                        await message.delete()
                        await message.channel.send("You can't use that word here.", delete_after = 10)
                # elif auto_links == "enabled":
                #     if search(self.url_regex, message.content):
                #         await message.delete()
                #         await message.channel.send("You can't send links in this channel.", delete_after = 10)

    
    #Commands

    # @command(name = "autolinks", help = "Select if to automatically delete external links or not. Send enaled or disabled after command to specify which one.")
    # @has_permissions(manage_guild = True)
    # async def auto_links(self, ctx, passed: str):
    #     if passed == "enabled":
    #         db.execute("UPDATE guilds SET AutoLinks = ? WHERE GuildID = ?", passed, ctx.guild.id)
    #     elif passed == "disabled":
    #         db.execute("UPDATE guilds SET AutoLinks = ? WHERE GuildID = ?", passed, ctx.guild.id)
    #     else:
    #         await ctx.send("Please specify `enabled` or `disabled` after command to enable or disable auto deletion of external links.")
    
    # @auto_links.error
    # async def auto_links_error(self, ctx, error):
    #     if isinstance(error, MissingRequiredArgument):
    #             await ctx.send("Please specify `enabled` or `disabled` after command to enable or disable auto deletion of external links.")
    #     elif isinstance(error, MissingPermissions):
    #         await ctx.send("User does not have permissions to manage server.")
    
    # @command(name = "linksaddchannel", help = "Select which channel to ignore deleting links.", aliases = ["lac"])
    # @has_permissions(manage_guild = True)
    # async def links_add_channel(self, ctx, passed: TextChannel):
    #     auto_links = db.field("SELECT AutoLinks FROM guilds WHERE GuildID =?", ctx.guild.id)
    #     if auto_links == "enabled":
    #         db.execute("UPDATE guilds SET AutoLinksID = ? WHERE GuildID = ?", passed.id, ctx.guild.id)
    #     elif auto_links == "disabled":
    #         ctx.send("Please enable `autolinks` first before using this command.")

    # @links_add_channel.error
    # async def links_add_channel_error(self, ctx, error):
    #     if isinstance(error, MissingRequiredArgument):
    #             await ctx.send("Please specify which channel to ignore for external links.")
    #     elif isinstance(error, MissingPermissions):
    #         await ctx.send("User does not have permissions to manage server.")

    # @command(name = "linksremovechannel", help = "Remove a channel from ignored channels for external links.", aliases = ["lrc"])
    # @has_permissions(manage_guild = True)
    # async def links_add_channel(self, ctx, passed: TextChannel):
    #     auto_links = db.field("SELECT AutoLinks FROM guilds WHERE GuildID =?", ctx.guild.id)
    #     if auto_links == "enabled":
    #         db.execute("UPDATE guilds SET AutoLinksID = ? WHERE GuildID = ?", passed.id, ctx.guild.id)
    #     elif auto_links == "disabled":
    #         await ctx.send("Please enable `autolinks` first before using this command.")

    @command(name = "autoprofanity", help = "Select if to have auto profanity or not. Send enaled or disabled after command to specify which one.")
    @has_permissions(manage_guild = True)
    async def auto_profanity(self, ctx, passed: str):
        if passed == "enabled":
                db.execute("UPDATE guilds SET Profanity = ? WHERE GuildID = ?", passed, ctx.guild.id)
                await ctx.send("Auto profanity checks are enabled.")
        elif passed == "disabled":
            db.execute("UPDATE guilds SET Profanity = ? WHERE GuildID = ?", passed, ctx.guild.id)
            await ctx.send("Auto profanity checks are disabled.")
        else:
            await ctx.send("Please specify `enabled` or `disabled` after command to enable or disable auto profanity.")
    
    @auto_profanity.error
    async def auto_profanity_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
                await ctx.send("Please specify `enabled` or `disabled` after command to enable or disable welcome messages.")
        elif isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")

    @command(name = "addprofanity", help = "Add a list of words seperated by spaces to the profanity list.", aliases = ["addswears", "addcurses"])
    @has_permissions(manage_guild = True)
    async def add_profanity(self, ctx, *words):
        with open("./data/profanity.txt", "a", encoding = "utf-8") as f:
            f.write("".join([f"{word}\n" for word in words]))
        profanity.load_censor_words_from_file("./data/profanity.txt")
        await ctx.send("Words have been added to profanity list.")
    
    @add_profanity.error
    async def add_profanity_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
                await ctx.send("Please specify a list of words seperated by spaces to add to the profanity list.")
        elif isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")
    
    @command(name = "delprofanity", help = "Remove a list of words seperated by spaces from the profanity list.", aliases = ["removeprofanity", "delswears", "delcurses", "removeswears", "removecurses"])
    @has_permissions(manage_guild = True)
    async def remove_profanity(self, ctx, *words):
        with open("./data/profanity.txt", "r", encoding = "utf-8") as f:
            stored = [word.strip() for word in f.readlines()]

        with open("./data/profanity.txt", "w", encoding = "utf-8") as f:
            f.write("".join([f"{word}\n" for word in stored if word not in words]))
        
        profanity.load_censor_words_from_file("./data/profanity.txt")
        await ctx.send("Words have been removed from profanity list.")
    
    @remove_profanity.error
    async def remove_profanity_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
                await ctx.send("Please specify a list of words seperated by spaces to remove from the profanity list.")
        elif isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to manage server.")

    @command(name="ban", help="Ban a specified user.")
    @bot_has_permissions(ban_members = True)
    @has_permissions(ban_members = True)
    async def ban(self, ctx, member: MemberConverter, *, reason: str):
        if (ctx.guild.me.top_role.position > member.top_role.position and not member.guild_permissions.administrator):
            await member.ban(reason = reason)
            await ctx.send(f"{member.mention} has been banned.")
            send_message = db.field("SELECT Logs FROM guilds WHERE GuildID =?", ctx.guild.id)
            if send_message == "enabled":
                log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", ctx.guild.id)
                embed = Embed(title = "Member Banned", color = 0xDD2222, timestamp = datetime.utcnow())
                fields = [("Member", member.mention, False),
                        ("Banned by", ctx.author.mention, False),
                        ("Reason", reason, False)]
                for name, value, inline in fields:
                    embed.add_field(name = name, value = value, inline = inline)
                embed.set_thumbnail(url = member.default_avatar_url)
                await self.bot.get_channel(log_channel).send(embed = embed)
        elif member.guild_permissions.administrator:
            await ctx.send(f"Cannot ban {member.mention} since they are an admin.")
        else:
            await ctx.send(f"Cannot ban {member.mention} since their role is higher than mine.")
    
    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            if error.args.__contains__(Member):
                await ctx.send("Please specify a user to ban.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to ban.")
        elif isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to ban.")
        elif isinstance(error, BotMissingPermissions):
            await ctx.send("I do not have permissions to ban.")

    @command(name="tempban", help="Temp ban a specified user.")
    @bot_has_permissions(ban_members = True)
    @has_permissions(ban_members = True)
    async def tempban(self, ctx, member: MemberConverter, duration: DurationConverter, *, reason: str):
        if (ctx.guild.me.top_role.position > member.top_role.position and not member.guild_permissions.administrator):
            multiplier = {"s" : 1, "m" : 60, "h" : 3600, "d" : 86400, "w" : 604800, "mth" : 2.628e+6, "y" : 3.154e+7}
            amount, unit = duration
            await member.ban(reason = reason)
            await ctx.send(f"{member.mention} has been banned for {amount}{unit}.")
            await asyncio.sleep(amount * multiplier[unit])
            await ctx.guild.unban(member)
            send_message = db.field("SELECT Logs FROM guilds WHERE GuildID =?", ctx.guild.id)
            if send_message == "enabled":
                log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", ctx.guild.id)
                embed = Embed(title = "Member Temp Banned", color = 0xDD2222, timestamp = datetime.utcnow())
                embed.set_thumbnail(url = member.default_avatar_url)
                fields = [("Member", member.mention, False),
                        ("Banned by", ctx.author.mention, False),
                        ("Reason", reason, False),
                        ("Duration", f"{amount}{unit}", False)]
                for name, value, inline in fields:
                    embed.add_field(name = name, value = value, inline = inline)
                await self.bot.get_channel(log_channel).send(embed = embed)
        elif member.guild_permissions.administrator:
            await ctx.send(f"Cannot temp ban {member.mention} since they are an admin.")
        else:
            await ctx.send(f"Cannot temp ban {member.mention} since their role is higher than mine.")

    
    @tempban.error
    async def tempban_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            if error.args.__contains__(Member):
                await ctx.send("Please specify a user to temp ban.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to temp ban.")
            elif error.args.__contains__(DurationConverter):
                await ctx.send("Please specify a duration to temp ban.")
        elif isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to ban.")
        elif isinstance(error, BotMissingPermissions):
            await ctx.send("I do not have permissions to ban.")

    @command(name="kick", help="Kick a specified user.")
    @bot_has_permissions(kick_members = True)
    @has_permissions(kick_members = True)
    async def kick(self, ctx, member: MemberConverter, *, reason: str):
        if (ctx.guild.me.top_role.position > member.top_role.position and not member.guild_permissions.administrator):
            await member.kick(reason = reason)
            await ctx.send(f"{member.mention} has been kicked.")
            send_message = db.field("SELECT Logs FROM guilds WHERE GuildID =?", ctx.guild.id)
            if send_message == "enabled":
                log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", ctx.guild.id)
                embed = Embed(title = "Member Kicked", color = 0xDD2222, timestamp = datetime.utcnow())
                embed.set_thumbnail(url = member.default_avatar_url)
                fields = [("Member", member.mention, False),
                        ("Kicked by", ctx.author.mention, False),
                        ("Reason", reason, False)]
                for name, value, inline in fields:
                    embed.add_field(name = name, value = value, inline = inline)
                await self.bot.get_channel(log_channel).send(embed = embed)
        elif member.guild_permissions.administrator:
            await ctx.send(f"Cannot kick {member.mention} since they are an admin.")
        else:
            await ctx.send(f"Cannot kick {member.mention} since their role is higher than mine.")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            if error.args.__contains__(Member):
                await ctx.send("Please specify a user to kick.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to kick.")
        elif isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to kick.")
        elif isinstance(error, BotMissingPermissions):
            await ctx.send("I do not have permissions to kick.")

    @command(name="unban", help="Unban a specified user.")
    @bot_has_permissions(ban_members = True)
    @has_permissions(ban_members = True)
    async def unban(self, ctx, member: MemberConverter, *, reason: str):
        banned_users = await ctx.guild.bans()

        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member.name, member.discriminator):
                await ctx.guild.unban(user, reason = reason)
            return
        await ctx.send(f"{member} has been unbanned.")
    
    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            if error.args.__contains__(Member):
                await ctx.send("Please specify a user to unban.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to unban.")
        elif isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to ban.")
        elif isinstance(error, BotMissingPermissions):
            await ctx.send("I do not have permissions to ban.")
    
    @command(name = "muted-role", help = "Define a muted role. If no role is provided, a new one will be created")
    @bot_has_permissions(manage_roles = True)
    @has_permissions(manage_messages = True, manage_roles = True)
    async def muted_role(self, ctx, role: Optional[Role] = None):
        if role == None:
            permissions = Permissions(add_reactions = False, connect = False, send_messages = False, send_tts_messages = False, use_slash_commands = False)
            new_muted_role = await ctx.guild.create_role(name = "Muted", permissions = permissions, color = 0x251616)
            db.execute("UPDATE guilds SET MutedRoleID = ? WHERE GuildID = ?", new_muted_role.id, ctx.guild.id)
            await ctx.send(f"{new_muted_role.mention} has been created.")
        else:
            db.execute("UPDATE guilds SET MutedRoleID = ? WHERE GuildID = ?", role.id, ctx.guild.id)
            await ctx.send(f"{role.mention} has been added to database.")
    
    @muted_role.error
    async def muted_role_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to manage messages and roles.")
        elif isinstance(error, BotMissingPermissions):
            await ctx.send("I do not have permissions to manage roles.")

    @command(name = "mute", help = "Mute a specified user.")
    @bot_has_permissions(manage_messages = True, manage_roles = True)
    @has_permissions(manage_messages = True)
    async def mute(self, ctx, member: MemberConverter, duration: DurationConverter, *, reason: str ):
        muted_role_id = db.field("SELECT MutedRoleID FROM guilds WHERE GuildID =?", ctx.guild.id)
        if muted_role_id == 0:
            await ctx.send("Please define a muted role. This can be done with the `muted-role` command.")
        else:
            role = ctx.guild.get_role(muted_role_id)
            if not role in member.roles:
                if (ctx.guild.me.top_role.position > member.top_role.position and not member.guild_permissions.administrator):
                    multiplier = {"s" : 1, "m" : 60, "h" : 3600, "d" : 86400, "w" : 604800, "mth" : 2.628e+6, "y" : 3.154e+7}
                    amount, unit = duration
                    await member.add_roles(muted_role_id, reason = reason)
                    await ctx.send(f"{member.mention} has been muted for {amount}{unit}.")
                    send_message = db.field("SELECT Logs FROM guilds WHERE GuildID =?", ctx.guild.id)
                    if send_message == "enabled":
                        log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", ctx.guild.id)
                        embed = Embed(title = "Member Muted", color = 0xDD2222, timestamp = datetime.utcnow())
                        embed.set_thumbnail(url = member.default_avatar_url)
                        fields = [("Member", member.mention, False),
                                ("Muted by", ctx.author.mention, False),
                                ("Reason", reason, False)]
                        for name, value, inline in fields:
                            embed.add_field(name = name, value = value, inline = inline)
                        await self.bot.get_channel(log_channel).send(embed = embed)
                    await asyncio.sleep(amount * multiplier[unit])
                    await member.remove_roles(muted_role_id, reason = "Automatic unmute.")
                    if send_message == "enabled":
                        log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", ctx.guild.id)
                        embed = Embed(title = "Member Unmuted", color = 0xDD2222, timestamp = datetime.utcnow())
                        embed.set_thumbnail(url = member.default_avatar_url)
                        fields = [("Member", member.mention, False),
                                ("Unmuted by", ctx.author.mention, False),
                                ("Reason", "Automatic unmute", False)]
                        for name, value, inline in fields:
                            embed.add_field(name = name, value = value, inline = inline)
                        await self.bot.get_channel(log_channel).send(embed = embed)

                elif member.guild_permissions.administrator:
                    await ctx.send(f"Cannot mute {member.mention} since they are an admin.")
                else:
                    await ctx.send(f"Cannot mute {member.mention} since their role is higher than mine.")
            else:
                await ctx.send(f"{member.mention} is already muted.")
    
    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            if error.args.__contains__(Member):
                await ctx.send("Please specify a user to mute.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to mute.")
            elif error.args.__contains__(DurationConverter):
                await ctx.send("Please specify a duration to mute.")
        elif isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to manage messages.")
        elif isinstance(error, BotMissingPermissions):
            await ctx.send("I do not have permissions to manage messages or manage roles.")

    @command(name = "unmute", help = "Unmute a specified user.")
    @bot_has_permissions(manage_messages = True, manage_roles = True)
    @has_permissions(manage_messages = True)
    async def unmute(self, ctx, member: MemberConverter, *, reason: str ):
        muted_role_id = db.field("SELECT MutedRoleID FROM guilds WHERE GuildID =?", ctx.guild.id)
        if muted_role_id == 0:
            await ctx.send("Please define a muted role. This can be done with the `muted-role` command.")
        else:
            if (ctx.guild.me.top_role.position > member.top_role.position and not member.guild_permissions.administrator):
                await member.remove_roles(muted_role_id, reason = reason)
                send_message = db.field("SELECT Logs FROM guilds WHERE GuildID =?", ctx.guild.id)
                if send_message == "enabled":
                    log_channel = db.field("SELECT LogsChannelID FROM guilds WHERE GuildID =?", ctx.guild.id)
                    embed = Embed(title = "Member Unmuted", color = 0xDD2222, timestamp = datetime.utcnow())
                    embed.set_thumbnail(url = member.default_avatar_url)
                    fields = [("Member", member.mention, False),
                            ("Unmuted by", ctx.author.mention, False),
                            ("Reason", reason, False)]
                    for name, value, inline in fields:
                        embed.add_field(name = name, value = value, inline = inline)
                    await self.bot.get_channel(log_channel).send(embed = embed)
            elif member.guild_permissions.administrator:
                await ctx.send(f"Cannot unmute {member.mention} since they are an admin.")
            else:
                await ctx.send(f"Cannot unmute {member.mention} since their role is higher than mine.")
    
    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            if error.args.__contains__(Member):
                await ctx.send("Please specify a user to mute.")
            elif error.args.__contains__(str):
                await ctx.send("Please specify a reason to mute.")
        elif isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to manage messages.")
        elif isinstance(error, BotMissingPermissions):
            await ctx.send("I do not have permissions to manage messages or manage roles.")

    @command(name = "clear", aliases = ["purge"], help = "Mass delete messages.")
    @bot_has_permissions(manage_messages = True)
    @has_permissions(manage_messages = True)
    async def clear_messages(self, ctx, limit: int):
        with ctx.channel.typing():
            await ctx.message.delete()
            deleted = await ctx.channel.purge(limit = limit)
            await ctx.send(f"Deleted {len(deleted):,} messages.", delete_after = 5)
    
    @clear_messages.error
    async def clear_messages_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("Please specify the number of messages to delete.")
        elif isinstance(error, MissingPermissions):
            await ctx.send("User does not have permissions to manage messages.")
        elif isinstance(error, BotMissingPermissions):
            await ctx.send("I do not have permissions to manage messages.")

def setup(bot):
    bot.add_cog(Mod(bot))
