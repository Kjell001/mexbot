#!/usr/bin/env python3

# Basic
import os

# Discord
import discord
from discord.ext.commands import CommandNotFound

# Commands
from mexbot import *
from quiz import *

TOKEN_DISCORD_BOT = os.getenv("TOKEN_DISCORD_BOT")

bot = commands.Bot(command_prefix='!', help_command=None)

@bot.event
async def on_ready():
    print('Logged in as {}'.format(bot.user))
    await bot.change_presence(activity=discord.Game("Mex"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error

bot.add_cog(Mex(bot))
bot.add_cog(Quiz(bot))

bot.run(TOKEN_DISCORD_BOT)
