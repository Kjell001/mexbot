#!/usr/bin/env python3

#!/usr/bin/env python3

# Basic


# Discord
from discord.ext import commands

# Opregte Unlocker
import opregte

HOME_GUILD_ID = 800402178673213450

class Unlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def make_message(question, answers):
        pass

    @commands.Cog.listener()
    async def on_ready(self):
        print('Opregte Unlocker: loaded commands')

    @commands.command('unlock', aliases=['opregte'])
    async def unlock(self, ctx, url):
        try:
            article = opregte.Article(url)
        except AssertionError:
            ctx.message.add_reaction('🦟') # Mosquito
            return
        except ConnectionError:
            ctx.message.add_reaction('🦟') # Mosquito
            ctx.message.add_reaction('⚠') # Warning


