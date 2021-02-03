#!/usr/bin/env python3

# Basic
from random import choice
from .controllers import *
from .helpers import *

# Discord
from discord.ext import commands

# Mex game
from mex import *

# GAME_STOPPED = 1
# GAME_UNDECIDED = 2
# GAME_NOT_FOUND = 3

HOME_GUILD_ID = 800402178673213450
# DICE_STYLES = ('1929', 'casino')


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
    START_WAIT = 'Er kan nog geen nieuwe game opgezet worden',
    STOP_WAIT = 'Het duel is nog niet voorbij',
    NOT_DUELIST = 'Dit is niet jouw duel!',
    SEPARATOR = '-  -  -  -  -  -  -  -  -  -'
    CHARM = {
        Charms.MEX: '` Mex! `',
        Charms.GIVE: '` Uitdelen! `',
        Charms.HOLDIT: '` Vast! `',
        Charms.HOUSE: '` Huisborrel! `'
    }


# class GuildSettings(object):
#     def __init__(self):
#         self.game_count = 0
#         self.dice_style = DICE_STYLES[0]
#
#     def add_game_count(self):
#         self.game_count += 1
#         return self.game_count
#
#     def set_dice_style(self, dice_style):
#         if dice_style in DICE_STYLES:
#             self.dice_style = dice_style


class Mex(commands.Cog):
    # Constants
    # ROLL_LIMIT_DEFAULT = 3
    # States
    # games = dict()
    # games_count = dict()
    # guild_settings = dict()
    # Helpers
    get_member = commands.MemberConverter()

    def __init__(self, bot):
        self.bot = bot
        self.channel_controllers = dict()
        self.emojis = None

    def add_channel_controller(self, channel):
        self.channel_controllers[channel.id] = ChannelController()

    def get_channel_controller(self, ctx):
        if ctx.channel.id not in self.channel_controllers:
            self.channel_controllers[ctx.channel.id] = ChannelController()
            print(f'Created controller for #{ctx.channel} in {ctx.guild}')
        return self.channel_controllers[ctx.channel.id]

    # def dice_icon(self, value, dark, style):
    #     key = 'd{}{}_{}'.format(str(value), 'd' if dark else '', style)
    #     return self.emojis[key]
    #
    # def roll_icons(self, roll, shade, style):
    #     value1, fresh1 = roll.first()
    #     value2, fresh2 = roll.second()
    #     if not shade:
    #         fresh1, fresh2 = True, True
    #     return ' '.join([
    #         self.dice_icon(value1, not fresh1, style),
    #         self.dice_icon(value2, not fresh2, style)
    #     ])

    def make_message_turn(self, ctx, results):
        channel_controller = self.get_channel_controller(ctx)
        game = channel_controller.game
        game_count = channel_controller.game_count
        player = results.player
        # Announce
        line_user = choice(Phrases.START).format(player)
        if len(game.players) == 1:
            line_user = f'**Game #{game_count:03d}** ' + line_user
        # Display rolls
        lines_roll = list()
        rolls, labels, charms = results.get()
        for i in range(len(rolls)):
            str_label = f'` {labels[i]} `'
            str_roll = channel_controller.get_roll_string(self.emojis, rolls[i], True)
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
            channel_controller.get_roll_string(self.emojis, game.roll_low, False)
        )
        if game.limit < game.limit_init:
            line_game = f'Mex in {game.limit}  ◇  ' + line_game
        if game.mex > 0:
            line_game += f'  ◇  {game.mex} mex'
        # Put message together
        return line_user + '\n\n' + '\n\n'.join(lines_roll) + '\n\n' + line_game

    def make_message_conclusion(self, ctx):
        channel_controller = self.get_channel_controller(ctx)
        game = channel_controller.game
        game_count = channel_controller.game_count
        message = f'**Game #{game_count:03d} over!**'
        if len(game.players) == 1:
            message += ' ' + Phrases.ALONE
        for player, tokens in game.get_tokens():
            message += f'\n` 🍺 x{tokens} `  {player}'
        return message

    @commands.Cog.listener()
    async def on_ready(self):
        print('Mex: loaded commands')
        home_guild_emojis = self.bot.get_guild(HOME_GUILD_ID).emojis
        self.emojis = dict((e.name, str(e)) for e in home_guild_emojis)
        print('Mex: loaded emojis')

    @commands.group('mex', invoke_without_command=True)
    async def play(self, ctx, proxy_user=None):
        channel_controller = self.get_channel_controller(ctx)
        if proxy_user and (await self.bot.is_owner(ctx.message.author)):
            # Check if a proxy user was specified by owner
            try:
                proxy_user = await self.get_member.convert(ctx, proxy_user)
            except commands.MemberNotFound:
                proxy_user = None
        player = proxy_user.mention if proxy_user else ctx.message.author.mention
        flag, results = channel_controller.take_turn(player)
        if flag == TURN_ALREADY_ROLLED:
            await ctx.send(choice(Phrases.CHEAT).format(player))
        elif flag == TURN_NOT_ALLOWED:
            await ctx.send(choice(Phrases.NOT_DUELIST).format(player))
        elif flag == TURN_TAKEN_GAME_OVER:
            await ctx.send(Phrases.SEPARATOR)
            await self.stop(ctx)

        ###################################
        # # Check for a game
        # game = self.games.get(ctx.channel.id)
        # if not game:
        #     await self.reset(ctx)
        #     return
        # # Check if a proxy user was specified by owner
        # if proxy_user and (await self.bot.is_owner(ctx.message.author)):
        #     try:
        #         proxy_user = await self.get_member.convert(ctx, proxy_user)
        #     except commands.MemberNotFound:
        #         proxy_user = None
        # # Play a turn
        # player_mention = proxy_user.mention if proxy_user else ctx.message.author.mention
        # results = game.turn(player_mention)
        # # Construct and post message
        # if results == PLAYER_ALREADY_ROLLED:
        #     await ctx.send(choice(Phrases.CHEAT).format(player_mention))
        # elif results == PLAYER_NOT_ALLOWED:
        #     pass ## Give reaction
        # else:
        #     await ctx.send(self.make_message_turn(ctx, results))
        # # Check if game is over
        # if game.state == GAME_OVER:
        #     await ctx.send(Phrases.SEPARATOR)
        #     await self.stop(ctx)

    @play.group('reset')
    async def reset(self, ctx, roll_limit=None):
        channel_controller = self.get_channel_controller(ctx)
        channel_controller.new_game(roll_limit)
        await self.play(ctx)

    @play.group('start', aliases=['new'])
    async def start(self, ctx, roll_limit=None):
        flag = await self.stop(ctx)
        if flag == STOP_GAME_UNDECIDED:
            return
        elif flag == STOP_GAME_DUEL:
            await ctx.send(Phrases.START_WAIT)
            return
        elif flag == STOP_GAME_OVER:
            await ctx.send(Phrases.SEPARATOR)
        await self.reset(ctx, roll_limit)

        ###################################
        # # Finish running game
        # stop_result = await self.stop(ctx)
        # # Check if a duel game is pending
        # if stop_result == GAME_UNDECIDED:
        #     await ctx.send(Phrases.START_WAIT)
        # else:
        #     if stop_result == GAME_STOPPED:
        #         await ctx.send(Phrases.SEPARATOR)
        #     await self.reset(ctx, roll_limit)

    @play.group('stop', aliases=['finish'])
    async def stop(self, ctx):
        channel_controller = self.get_channel_controller(ctx)
        flag = channel_controller.stop_game()
        game = channel_controller.game
        if flag == STOP_GAME_UNDECIDED:
            await ctx.send(Phrases.STOP_WAIT)
        elif flag == STOP_GAME_DUEL:
            await ctx.send(choice(Phrases.DUEL).format(list_names(game.players_allowed)))
        elif flag == STOP_GAME_OVER:
            await ctx.send(self.make_message_conclusion(ctx))
        return flag

        ###################################
        # game = channel_controller.game
        # # Get current game
        # game = self.games.get(ctx.channel.id)
        # if not game:
        #     return GAME_NOT_FOUND
        # elif game.state == GAME_UNDECIDED:
        #     return GAME_UNDECIDED
        # # Stop current game or start a duel
        # duel = game.conclude()
        # if duel:
        #     self.games[ctx.channel.id] = duel
        #     await ctx.send(choice(Phrases.DUEL).format(list_names(duel.players_allowed)))
        #     return GAME_UNDECIDED
        # else:
        #     await ctx.send(self.make_message_conclusion(ctx, game))
        #     self.games.pop(ctx.channel.id)
        #     return GAME_STOPPED

    @play.command('style')
    async def set_dice_style(self, ctx, dice_style=None):
        channel_controller = self.get_channel_controller(ctx)
        channel_controller.set_dice_style(dice_style)
