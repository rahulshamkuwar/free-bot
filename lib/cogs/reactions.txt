# from discord.ext.commands import Cog

# class Reactions(Cog):
#     def __init__(self, bot):
#         self.bot = bot
    
#     @Cog.listener()
#     async def on_ready(self):
#         if not self.bot.ready:
#             self.bot.cogs_ready.ready_up("reactions")
    
#     # @Cog.listener()
#     # async def on_reaction_add(self, reaction, user):
#     #     pass
    
#     # @Cog.listener()
#     # async def on_reaction_remove(self, reaction, user):
#     #     pass

#     @Cog.listener()
#     async def on_raw_reaction_add(self, payload):
#         pass
#     @Cog.listener()
#     async def on_raw_reaction_remove(self, payload):
#         pass

# def setup(bot):
#     bot.add_cog(Reactions(bot))