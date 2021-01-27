#!/usr/bin/env python3

# Basic
import os
from random import shuffle, choice

# API request
import urllib.request
import json
from html import unescape

# Mex game
from mex import *

# Discord
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound


# CONSTANTS --------------------------------------

URL_TRIVIA = 'https://opentdb.com/api.php?amount=1&type=multiple'
TOKEN_DISCORD_BOT = os.getenv("TOKEN_DISCORD_BOT")
USER_ID_OWNER = int(os.getenv("DISCORD_USER_ID_OWNER"))


class Args:
    NEW_GAME = ('start', 'nieuw', 'new')
    ROLL_LIMIT_DEFAULT = 3


class Phrases:
    START = (
        '{} werpt de teerling',
        'De beurt is aan {}',
        '{} grijpt naar de dobbels',
        '{} hoopt op mex',
        '{} ruikt even aan de dobbelstenen',
        '{} heeft nog geen dorst',
        '{} likt aan de dobbelstenen',
        '{} gooit de dobbels bijna van tafel',
        '{} probeert een trick shot'
    )
    CHEAT = (
        '{} CHEATOR COMPLETOR!',
        '{} eist een hertelling, maar de uitslag is hetzelfde',
        '{}, je bent al aan de beurt geweest valsspelert!',
        'Volgende potje mag je weer {}'
    )
    CHARM = {
        Charms.MEX: '` Mex! `',
        Charms.GIVE: '` Uitdelen! `',
        Charms.HOLDIT: '` Vast! `',
        Charms.HOUSE: '` Huisborrel! `'
    }


# HELPERS ----------------------------------------

emojis = dict()
games = dict()

def dice_icon(value, dark=False):
    return emojis['dice{}{}'.format(str(value), 'd' if dark else '')]

def roll_icons(roll, shade=True, sep=' '):
    value1, fresh1 = roll.first()
    value2, fresh2 = roll.second()
    if not shade:
        fresh1, fresh2 = True, True
    return dice_icon(value1, not fresh1) + sep + dice_icon(value2, not fresh2)

def list_names(names):
    if len(names) == 1:
        return names[0]
    else:
        return ', '.join(names[:-1]) + ' en ' + names[-1]


# CONNECT TO DISCORD -----------------------------

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print('Logged in as {}'.format(bot.user))
    await bot.change_presence(activity=discord.Game("Mex"))
    # Fetch emojis
    global emojis
    emojis = dict((e.name, f'<:{e.name}:{str(e.id)}>') for e in bot.emojis)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error

@bot.command(name='mex')
async def _mex(ctx, arg1=None, arg2=None):
    # Parse arguments
    new_game = arg1 in Args.NEW_GAME if arg1 else False
    roll_limit = Args.ROLL_LIMIT_DEFAULT
    if new_game:
        try:
            roll_limit = int(arg2)
        except (ValueError, TypeError): pass
    # Get info
    channel_id = ctx.channel.id
    user_id = ctx.author.id
    if user_id == USER_ID_OWNER and ctx.message.mentions:
        # Allow owner to take turns for others for debugging
        user_id = ctx.message.mentions[0].id
    user_mention = f'<@{user_id}>'
    # Determine current game
    game = games.get(channel_id)
    if new_game or game is None:
        game = Game(roll_limit)
        games[channel_id] = game
    # Play a turn
    results = game.turn(user_mention)
    # Construct response
    if results == PLAYER_ALREADY_ROLLED:
        response = choice(Phrases.CHEAT).format(user_mention)
    else:
        # Announce
        line_user = choice(Phrases.START).format(user_mention)
        # Display rolls
        lines_roll = list()
        rolls, labels, charms = results.get()
        for i in range(len(rolls)):
            str_label = f'` {labels[i]} `'
            str_roll = roll_icons(rolls[i])
            str_charms = '  '.join(Phrases.CHARM[c] for c in charms[i])
            lines_roll.append('{}  {}{}{}'.format(
                str_label,
                str_roll,
                '  ' if str_charms else '',
                str_charms
            ))
        # Display game status
        line_game = '{} {} laag met {}'.format(
            list_names(game.players_low),
            'zijn' if len(game.players_low) > 1 else 'is',
            roll_icons(game.roll_low, False)
        )
        if game.limit < game.limit_init:
            line_game = 'Mex in {}  ◇  '.format(game.limit) + line_game
        if game.mex > 0:
            line_game += '  ◇  {} mex'.format(game.mex)
        # Put response together
        response = line_user + '\n\n' + '\n\n'.join(lines_roll) + '\n\n' + line_game
    # Post response
    await ctx.send(response)

@bot.command(name='ramswoertherevival')
async def _quiz(ctx, arg1=None, arg2=None):
    # Fetch trivia
    with urllib.request.urlopen(URL_TRIVIA) as url:
        data = json.loads(url.read().decode())
    trivia = data['results'][0]
    question = unescape(trivia['question'])
    answer_correct = unescape(trivia['correct_answer'])
    answers = [unescape(a) for a in trivia['incorrect_answers']]
    answers.append(answer_correct)
    # Construct quiz content
    line_quiz = f'*Secret quiz time: {question}*\n'
    lines_answers = []
    for i, answer in enumerate(answers):
        lines_answers.append('|| {} ||  {}'.format(
            '✅' if i == len(answers) - 1 else '❌',
            answer
        ))
    # Shuffle correct answer in other answers
    shuffle(lines_answers)
    # Post response
    response = line_quiz + '\n'.join(lines_answers)
    await ctx.send(response)

bot.run(TOKEN_DISCORD_BOT)
