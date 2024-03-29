#!/usr/bin/env python3

# Basic
import os
import sys
import signal
import asyncio

# Discord
import discord
from discord.ext.commands import CommandNotFound

# Commands
import mexbot
import quiz_interactive
import lute

TOKEN_DISCORD_BOT = os.getenv("TOKEN_DISCORD_BOT")
TOKEN_DISCORD_LUTE = os.getenv("TOKEN_DISCORD_LUTE")
FTP_HOST = os.getenv('FTP_HOST')
FTP_USERNAME = os.getenv('FTP_USERNAME')
FTP_PASSWORD = os.getenv('FTP_PASSWORD')

# Set up MexBot
bot = discord.ext.commands.Bot(command_prefix='!', help_command=None)


@bot.event
async def on_ready():
    print('Logged in as {}'.format(bot.user))
    await bot.change_presence(activity=discord.Game("Mex"))


@bot.event
async def on_command_error(_, error):
    if isinstance(error, CommandNotFound):
        return
    raise error


bot.add_cog(mexbot.Mex(bot, FTP_HOST, FTP_USERNAME, FTP_PASSWORD))
bot.add_cog(quiz_interactive.Quiz(bot, FTP_HOST, FTP_USERNAME, FTP_PASSWORD))


# Set up Lute
LuteBot = discord.ext.commands.Bot(command_prefix='!', help_command=None)


@LuteBot.event
async def on_ready():
    print('Logged in as {}'.format(LuteBot.user))
    await LuteBot.change_presence(activity=discord.Game('Steenwijker Courant'))


@LuteBot.event
async def on_command_error(_, error):
    if isinstance(error, CommandNotFound):
        return
    raise error


LuteBot.add_cog(lute.Unlock(LuteBot))


def cleanup(signalnum, _):
    print(f'- - -\nReceived signal \'{signal.strsignal(signalnum)}\'')
    bot.get_cog('Mex').cleanup()
    bot.get_cog('Quiz').cleanup()
    print('*In Luigi voice*: "Bye bye"')
    sys.exit()


async def cleanup2(signalnum):
    print(f'- - -\nReceived signal \'{signal.strsignal(signalnum)}\'')
    bot.get_cog('Mex').cleanup()
    await bot.get_cog('Quiz').cleanup2()
    print('*In Luigi voice*: "Bye bye"')
    sys.exit()


# Run both bots concurrently
loop = asyncio.get_event_loop()
loop.create_task(bot.start(TOKEN_DISCORD_BOT))
loop.create_task(LuteBot.start(TOKEN_DISCORD_LUTE))
# Add signal handlers for proper cleanup
# signal.signal(signal.SIGINT, cleanup)
# signal.signal(signal.SIGTERM, cleanup)
loop.add_signal_handler(
    signal.SIGINT,
    lambda: asyncio.ensure_future(cleanup2(signal.SIGINT))
)
loop.add_signal_handler(
    signal.SIGTERM,
    lambda: asyncio.ensure_future(cleanup2(signal.SIGTERM))
)
loop.run_forever()
