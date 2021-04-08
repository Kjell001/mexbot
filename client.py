#!/usr/bin/env python3

# Basic
import os
import sys
import signal

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


def cleanup(signalnum, _):
    print(f'Received signal \'{signal.strsignal(signalnum)}\'')
    # Invoke saving ChannelController states
    bot.get_cog('Mex').cleanup()
    print('*In Luigi voice*: "Bye bye"')
    sys.exit()


# signal.signal(signal.SIGINT, cleanup)
# signal.signal(signal.SIGTERM, cleanup)
bot.add_cog(Mex(bot))
bot.add_cog(Quiz(bot))
bot.run(TOKEN_DISCORD_BOT)
