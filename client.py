#!/usr/bin/env python3

# Basic
import os
from random import shuffle, choice

# API request
import urllib.request
import requests
import json
from html import unescape

# Mex game
from mex import *

# Discord
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound


# CONNECT TO DISCORD -----------------------------

TOKEN_DISCORD_BOT = os.getenv("TOKEN_DISCORD_BOT")
bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print('Logged in as {}'.format(bot.user))
    await bot.change_presence(activity=discord.Game("Mex"))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error


# DEFINE COMMANDS --------------------------------

class Mex(commands.Cog):
    # Constants
    ROLL_LIMIT_DEFAULT = 3
    # Phrases
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
    # States
    games = dict()
    # Helpers
    get_member = commands.MemberConverter()

    def __init__(self, bot):
        self.bot = bot

    def dice_icon(self, value, dark=False):
        return self.emojis['dice{}{}'.format(str(value), 'd' if dark else '')]

    def roll_icons(self, roll, shade=True, sep=' '):
        value1, fresh1 = roll.first()
        value2, fresh2 = roll.second()
        if not shade:
            fresh1, fresh2 = True, True
        return self.dice_icon(value1, not fresh1) + sep + self.dice_icon(value2, not fresh2)

    def list_names(self, names):
        if len(names) == 1:
            return names[0]
        else:
            return ', '.join(names[:-1]) + ' en ' + names[-1]

    def make_message(self, results):
        game = results.game
        player = results.player
        # Announce
        line_user = choice(self.START).format(player)
        # Display rolls
        lines_roll = list()
        rolls, labels, charms = results.get()
        for i in range(len(rolls)):
            str_label = f'` {labels[i]} `'
            str_roll = self.roll_icons(rolls[i])
            str_charms = '  '.join(self.CHARM[c] for c in charms[i])
            lines_roll.append('{}  {}{}{}'.format(
                str_label,
                str_roll,
                '  ' if str_charms else '',
                str_charms
            ))
        # Display game status
        line_game = '{} {} laag met {}'.format(
            self.list_names(game.players_low),
            'zijn' if len(game.players_low) > 1 else 'is',
            self.roll_icons(game.roll_low, False)
        )
        if game.limit < game.limit_init:
            line_game = f'Mex in {game.limit}  ◇  ' + line_game
        if game.mex > 0:
            line_game += f'  ◇  {game.mex} mex'
        # Put message together
        return line_user + '\n\n' + '\n\n'.join(lines_roll) + '\n\n' + line_game

    @commands.Cog.listener()
    async def on_ready(self):
        print('Mex: loaded commands')
        self.emojis = dict((e.name, f'<:{e.name}:{str(e.id)}>') for e in self.bot.emojis)
        print('Mex: loaded emojis')

    @commands.group('mex', invoke_without_command=True)
    async def play(self, ctx, proxy_user=None):
        # Check for a game
        game = self.games.get(ctx.channel.id)
        if not game:
            await self.start(ctx)
            return
        # Check if a proxy user was specified by owner
        if proxy_user and (await self.bot.is_owner(ctx.message.author)):
            try:
                proxy_user = await self.get_member.convert(ctx, proxy_user)
            except commands.MemberNotFound:
                proxy_user = None
        # Play a turn
        player_mention = proxy_user.mention if proxy_user else ctx.message.author.mention
        results = game.turn(player_mention)
        # Construct and post message
        if results == PLAYER_ALREADY_ROLLED:
            message = choice(self.CHEAT).format(player_mention)
        else:
            message = self.make_message(results)
        await ctx.send(message)

    @play.group('start', aliases=['new'])
    async def start(self, ctx, roll_limit = ROLL_LIMIT_DEFAULT):
        game = Game(roll_limit)
        self.games[ctx.channel.id] = game
        author_mention = ctx.message.author.mention
        await ctx.send(f'**{author_mention} zet op**')
        await self.play(ctx)


class Quiz(commands.Cog):
    OPENTDB_ENDPOINT = 'https://opentdb.com/api.php'
    NO_QUESTION = -1

    def __init__(self, bot):
        self.bot = bot

    def fetch_question(self):
        # Make request
        params = {'amount': 1, 'type': 'multiple'}
        response = requests.get(self.OPENTDB_ENDPOINT, params)
        if not 200 <= response.status_code < 300:
            raise ConnectionError(f'{self.OPENTDB_ENDPOINT} could not be reached.')
        # Gather data
        data = json.loads(response.content)
        trivia = data['results'][0]
        question = unescape(trivia['question'])
        answer_correct = unescape(trivia['correct_answer'])
        answers = [unescape(a) for a in trivia['incorrect_answers']]
        # Append correct answer to wrong answers
        answers.append(answer_correct)
        return question, answers

    def make_message(self, question, answers):
        # Format question and answers
        line_quiz = f'*Secret quiz time: {question}*\n'
        lines_answers = []
        for i, answer in enumerate(answers):
            lines_answers.append('|| {} ||  {}'.format(
                '✅' if i == len(answers) - 1 else '❌',
                answer
            ))
        # Shuffle answers
        shuffle(lines_answers)
        # Return message
        return line_quiz + '\n'.join(lines_answers)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Quiz: loaded commands')

    @commands.command('ramswoertherevival', aliases=['rwr'])
    async def quiz(self, ctx):
        try:
            question, answers = self.fetch_question()
        except ConnectionError as inst:
            print(inst)
        else:
            await ctx.send(self.make_message(question, answers))


bot.add_cog(Mex(bot))
bot.add_cog(Quiz(bot))
bot.run(TOKEN_DISCORD_BOT)
