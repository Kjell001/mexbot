#!/usr/bin/env python3

# Basic
from random import choice
from .helpers import *

# Discord
from discord.ext import commands

# Mex game
from mex import *

GAME_STOPPED = 1
GAME_UNDECIDED = 2
GAME_NOT_FOUND = 3


class Phrases(object):
    START = (
        '{} werpt de teerling',
        'De beurt is aan {}',
        '{} grijpt naar de dobbels',
        '{} hoopt op mex',
        '{} ruikt even aan de dobbelstenen',
        '{} heeft nog geen dorst',
        '{} likt aan de dobbelstenen',
        '{} gooit de dobbels bijna van tafel',
        '{} probeert een trick shot',
        'Geloof in het hart van de dobbelstenen {}!',
    )
    CHEAT = (
        '{} CHEATOR COMPLETOR!',
        '{} eist een hertelling, maar de uitslag is hetzelfde',
        '{}, je bent al aan de beurt geweest valsspelert!',
        'Volgende potje mag je weer {}',
    )
    DUEL = (
        '{} duelleren tot de dood!',
        '{} vechten het onderling uit',
        '{} moeten nog even door',
        '{}, er kan er maar één de laagste zijn!',
    )
    ALONE = 'Wie alleen speelt, verliest altijd...'
    WAIT = 'Er kan nog geen nieuwe game opgezet worden'
    SEPARATOR = '-  -  -  -  -  -  -  -  -  -'
    CHARM = {
        Charms.MEX: '` Mex! `',
        Charms.GIVE: '` Uitdelen! `',
        Charms.HOLDIT: '` Vast! `',
        Charms.HOUSE: '` Huisborrel! `'
    }


class Mex(commands.Cog):
    # Constants
    ROLL_LIMIT_DEFAULT = 3
    # States
    games = dict()
    games_count = dict()
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

    def add_game_count(self, guild_id):
        if guild_id in self.games_count:
            self.games_count[guild_id] += 1
        else:
            self.games_count[guild_id] = 1

    def make_message_turn(self, ctx, results):
        game = results.game
        player = results.player
        # Announce
        line_user = choice(Phrases.START).format(player)
        if len(game.players) == 1:
            game_num = self.games_count[ctx.guild.id]
            line_user = f'**Game #{game_num:03d}** ' + line_user
        # Display rolls
        lines_roll = list()
        rolls, labels, charms = results.get()
        for i in range(len(rolls)):
            str_label = f'` {labels[i]} `'
            str_roll = self.roll_icons(rolls[i])
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
            self.roll_icons(game.roll_low, False)
        )
        if game.limit < game.limit_init:
            line_game = f'Mex in {game.limit}  ◇  ' + line_game
        if game.mex > 0:
            line_game += f'  ◇  {game.mex} mex'
        # Put message together
        return line_user + '\n\n' + '\n\n'.join(lines_roll) + '\n\n' + line_game

    def make_message_conclusion(self, ctx, game):
        game_num = self.games_count[ctx.guild.id]
        message = f'**Game #{game_num:03d} over!**'
        if len(game.players) == 1:
            message += ' ' + Phrases.ALONE
        tokens_sorted = sorted(game.tokens.items(), key=lambda x: x[1], reverse=True)
        for player, tokens in tokens_sorted:
            message += (f'\n` 🍺 x{tokens} `  {player}')
        return message

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
            await self.reset(ctx)
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
            message = choice(Phrases.CHEAT).format(player_mention)
        else:
            message = self.make_message_turn(ctx, results)
        await ctx.send(message)
        # Check if game is over
        if game.state == Game.OVER:
            await ctx.send(Phrases.SEPARATOR)
            await self.stop(ctx)

    @play.group('start', aliases=['new'])
    async def start(self, ctx, roll_limit = ROLL_LIMIT_DEFAULT):
        # Finish running game
        stop_result = await self.stop(ctx)
        # Check if a duel game is pending
        if stop_result == GAME_UNDECIDED:
            await ctx.send(Phrases.WAIT)
        else:
            if stop_result == GAME_STOPPED:
                await ctx.send(Phrases.SEPARATOR)
            await self.reset(ctx, roll_limit)

    @play.group('stop', aliases=['finish'])
    async def stop(self, ctx):
        # Get current game
        game = self.games.get(ctx.channel.id)
        if not game:
            return GAME_NOT_FOUND
        elif game.state == Game.UNDECIDED:
            return GAME_UNDECIDED
        # Stop current game or start a duel
        duel = game.conclude()
        if duel:
            self.games[ctx.channel.id] = duel
            await ctx.send(choice(Phrases.DUEL).format(list_names(duel.players_allowed)))
            return GAME_UNDECIDED
        else:
            await ctx.send(self.make_message_conclusion(ctx, game))
            self.games.pop(ctx.channel.id)
            return GAME_STOPPED

    @play.group('reset')
    async def reset(self, ctx, roll_limit = ROLL_LIMIT_DEFAULT):
        self.games[ctx.channel.id] = Game(roll_limit)
        self.add_game_count(ctx.guild.id)
        await self.play(ctx)
