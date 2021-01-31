#!/usr/bin/env python3

# Basic
from random import choice
from .helpers import *

# Discord
from discord.ext import commands

# Mex game
from mex import *


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
            list_names(game.players_low),
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
