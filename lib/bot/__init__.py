from asyncio.tasks import sleep
from discord import Intents
from discord.errors import Forbidden, HTTPException, InvalidArgument
from discord.ext.commands import Bot as BotBase
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import CommandNotFound, when_mentioned_or
from pathlib import Path
from discord.ext.commands.context import Context

from discord.ext.commands.errors import BadArgument, MissingPermissions, MissingRequiredArgument

from ..db import db

PREFIX = '!'
OWNER_IDS = [266745502563958784]
COGS = [p.stem for p in Path(".").glob("./lib/cogs/*.py")]
IGNORE_EXCEPTIONS = (BadArgument, MissingRequiredArgument, MissingPermissions)

def get_prefix(bot, message):
    prefix = db.field("SELECT Prefix FROM guilds WHERE GuildID =?", message.guild.id)
    return when_mentioned_or(prefix)(bot, message)

class Ready(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)
    
    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f"{cog} cog ready")

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])

class Bot(BotBase):
    def __init__(self):
        self.ready = False
        self.cogs_ready = Ready()
        self.guild = None
        self.scheduler = AsyncIOScheduler()
        
        db.auto_save(self.scheduler)
        super().__init__(command_prefix = get_prefix, owner_ids = OWNER_IDS, intents = Intents.all(),)
    
    def setup(self):
        for cog in COGS:
            self.load_extension(f"lib.cogs.{cog}")
            print(f"{cog} cog loaded")
        print("setup complete")

    def update_db(self):
        db.multiexec("INSERT OR IGNORE INTO guilds (GuildID) VALUES (?)", ((guild.id,) for guild in self.guilds))
        db.multiexec("INSERT OR IGNORE INTO exp (UserID, GuildID) VALUES (?, ?)", ((member.id, member.guild.id) for guild in self.guilds for member in guild.members if not member.bot))
        stored_members = db.records("SELECT UserID, GuildID FROM exp")
        to_remove = []
        for _id, guild_id in stored_members:
            guild = self.get_guild(guild_id)
            if not guild.get_member(_id):
                to_remove.append((_id, guild.id))

        if to_remove:
            db.multiexec("DELETE FROM exp WHERE UserID = ? AND GuildID = ?",((_id, guild) for _id, guild in to_remove))
        
        db.commit()
    
    def run(self, version):
        self.VERSION = version
        print("runnnig setup...")
        self.setup()

        with open("BOT_TOKEN.txt", "r") as token_file:
            self.TOKEN = token_file.read()
        
        super().run(self.TOKEN, reconnect=True)
    async def process_commands(self, message):
        ctx = await self.get_context(message = message, cls = Context)

        if ctx.command is not None and ctx.guild is not None:
            if self.ready:
                await self.invoke(ctx = ctx)
            else:
                await ctx.send("I'm not ready to receive commands yet. Please wait a moment...")

    async def on_connect(self):
        print("bot connected")
    
    async def on_disconnect(self):
        print("bot disconnected")
    
    async def on_error(self, err, *args, **kwargs):
        if err not in IGNORE_EXCEPTIONS and err == "on_command_error":
            await args[0].send("Something went wrong.")
        raise
    
    async def on_command_error(self, ctx, exception):
        if any([isinstance(exception, error) for error in IGNORE_EXCEPTIONS]):
            pass
        elif isinstance(exception, InvalidArgument):
            await ctx.send("Please provide the correct argument type.")
        elif hasattr(exception, "original"):
            if isinstance(exception.original, HTTPException):
                await ctx.send("Unable to send message.")
            elif isinstance(exception.original, Forbidden):
                await ctx.send("I do not have permissions to do that.")
            else :
                raise exception.original
        else:
            raise exception
    
    async def on_ready(self):
        if not self.ready:
            self.scheduler.start()

            while not self.cogs_ready.all_ready():
                await sleep(0.5)
            
            self.ready = True
            print("bot ready")

            self.update_db()

        else:
            print("bot reconnnected")

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)

bot = Bot()