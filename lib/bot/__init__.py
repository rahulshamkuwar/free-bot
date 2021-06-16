from datetime import datetime
import os
from dotenv import load_dotenv
from asyncio.tasks import sleep
from discord import Intents
from discord.errors import Forbidden, HTTPException, InvalidArgument
from discord.ext.commands import Bot as BotBase
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import CommandNotFound, when_mentioned_or
from pathlib import Path
from discord.ext.commands.context import Context
from discord.ext.commands.errors import BadArgument, MissingPermissions, MissingRequiredArgument
import asyncpg
from os.path import isfile
# from ..db import db

load_dotenv(".env")
PREFIX = '!'
OWNER_IDS = [os.getenv("OWNER_IDS")]
COGS = [p.stem for p in Path(".").glob("./lib/cogs/*.py")]
IGNORE_EXCEPTIONS = (BadArgument, MissingRequiredArgument, MissingPermissions)
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "./data/db/database.db"
BUILD_PATH = "./data/db/build.sql"
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

async def get_prefix(bot, message):
    query = await bot.cxn.fetchrow("SELECT Prefix FROM guilds WHERE GuildID = ($1);", message.guild.id)
    prefix = query.get("prefix")
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
        self.guild_ready = False
        # self.scheduler = AsyncIOScheduler()
        
        # db.auto_save(self.scheduler)
        super().__init__(command_prefix = get_prefix, owner_ids = OWNER_IDS, intents = Intents.all())
    
    def setup(self):
        for cog in COGS:
            self.load_extension(f"lib.cogs.{cog}")
            print(f"{cog} cog loaded")
        print("setup complete")
    
    async def start_db(self):
        # async with asyncpg.create_pool(database = "Freebot", host = "localhost", user = "postgres", password = POSTGRES_PASSWORD) as pool:
        #     async with pool.acquire() as cxn:
        #         self.cxn = cxn
        #         if isfile(BUILD_PATH):
        #             with open(BUILD_PATH, "r", encoding = "utf-8") as script:
        #                 await self.cxn.execute(script.read())
        self.cxn = await asyncpg.create_pool(database = "Freebot", host = "localhost", user = "postgres", password = POSTGRES_PASSWORD)
        if isfile(BUILD_PATH):
            with open(BUILD_PATH, "r", encoding = "utf-8") as script:
                await self.cxn.execute(script.read())


    async def update_db(self):
        async with self.cxn.acquire() as db:
            for guild in self.guilds:
                await db.execute("INSERT INTO guilds (GuildID) VALUES ($1) ON CONFLICT (GuildID) DO NOTHING;", guild.id)
                for member in guild.members:
                    if not member.bot:
                        await db.execute("INSERT INTO exp (UserID, GuildID, XPLock) VALUES ($1, $2, $3) ON CONFLICT (GuildID, UserID) DO NOTHING;", member.id, member.guild.id, datetime.utcnow().isoformat())
            q_stored_members = await db.fetch("SELECT UserID, GuildID FROM exp;")
            to_remove = []

            for stored in q_stored_members:
                guild = self.get_guild(stored.get('guildid'))
                user_id = stored.get('userid')
                if not guild.get_member(user_id):
                    to_remove.append((user_id, guild.id))

            if to_remove:
                for _id, guild in to_remove:
                    await db.execute("DELETE FROM exp WHERE UserID = ($1) AND GuildID = ($2);", _id, guild)
        self.guild_ready = True
    
    async def leave_guild(self, guild):
        async with self.cxn.acquire() as db:
            await db.execute("DELETE FROM guilds WHERE GuildID = $1", guild.id)
            await db.execute("DELETE FROM exp WHERE GuildID = $1", guild.id)
    
    async def update_profanity(self, guild):
        prof_list = ["anal","anus","ballsack","blowjob","blow job","boner","clitoris","cock","cunt","dick","dildo","dyke","fag","fuck","jizz","labia","muff","nigger","nigga","penis","piss","pussy","scrotum","sex","shit","slut","smegma","spunk","twat","vagina","wank","whore"]
        async with self.cxn.acquire() as db: 
            await db.execute("UPDATE guilds SET ProfanityList = $1 WHERE GuildId = $2", prof_list, guild.id)

    def run(self, version):
        self.VERSION = version
        print("runnnig setup...")
        self.setup()
        
        self.TOKEN = BOT_TOKEN
        
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
            # self.scheduler.start()

            while not self.cogs_ready.all_ready():
                await sleep(0.5)
            
            self.ready = True
            print("bot ready")

            await self.update_db()

        else:
            print("bot reconnnected")

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)
bot = Bot()
bot.loop.run_until_complete(bot.start_db())