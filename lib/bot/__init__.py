from asyncio.tasks import sleep
from discord import Intents
from discord.errors import Forbidden, HTTPException
from discord.ext.commands import Bot as BotBase
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import CommandNotFound, when_mentioned_or, command, has_permissions
from pathlib import Path
from discord.ext.commands.context import Context

from discord.ext.commands.errors import MissingRequiredArgument

from ..db import db

PREFIX = '!'
OWNER_IDS = [266745502563958784]
COGS = [p.stem for p in Path(".").glob("./lib/cogs/*.py")]

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
        if err == "on_command_error":
            await args[0].send("Something went wrong.")
            
        raise
    
    async def on_command_error(self, context, exception):
        if isinstance(exception, CommandNotFound):
            pass
        elif isinstance(exception, MissingRequiredArgument):
            pass
        elif hasattr(exception, "original"):
            if isinstance(exception.original, HTTPException):
                await context.send("Unable to send message.")
            elif isinstance(exception.original, Forbidden):
                await context.send("I do not have permissions to do that.")
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

        else:
            print("bot reconnnected")

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)

bot = Bot()