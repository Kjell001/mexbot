#!/usr/bin/env python3

# Basic
from random import choice
from .controllers import *
from .helpers import *
from warnings import warn

# Discord
from discord.ext import commands

# Mex game
from mex import *
import ftp_instance

HOME_GUILD_ID = 800402178673213450
FILE_DUMP = 'dumps/channel_con_{}.dump'


class Phrases(object):
    START = (
        '{} werpt de teerling',
        '{} is aan de beurt',
        '{} grijpt naar de dobbels',
        '{} hoopt op mex',
        '{} ruikt even aan de dobbelstenen',
        '{} heeft nog geen dorst',
        '{} likt aan de dobbelstenen',
        '{} gooit de dobbels bijna van tafel',
        '{} probeert een trick shot',
        '{} gelooft in het hart van de dobbelstenen',
        '{} gooit zonder te kijken',
        '{} schudt de dobbelsten net iets te lang',
        '{} werpt de dobbels in Mt. Doom'
        '{} mengt zich in de strijd',
        '{} vindt het stiekem wel spannend',
        '{} denkt aan zijn lievelingsgetal',
        '{} weet zeker dat het mex wordt'
    )
    CHEAT = (
        '{} CHEATOR COMPLETOR!',
        '{} eist een hertelling, maar de uitslag is hetzelfde',
        '{}, je bent al aan de beurt geweest vuile maltdrinker!',
        'Volgende potje mag je weer {}',
    )
    DUEL = (
        '{} duelleren tot de dood!',
        '{} vechten het onderling uit',
        '{} moeten nog even door',
        '{}, er kan er maar één de laagste zijn!',
        '{} trekken hun revolvers',
        '{} wisselen een veelbetekenende blik',
        '{} gaan een extra rondje niet uit de weg'
    )
    ALONE = 'Wie alleen speelt, verliest altijd...'
    START_WAIT = 'Er kan nog geen nieuwe game opgezet worden'
    STOP_WAIT = 'Het duel is nog niet voorbij'
    NOT_DUELIST = 'Dit is niet jouw duel!'
    SEPARATOR = '-  -  -  -  -  -  -  -  -  -'
    CHARM = {
        Charms.MEX: '` Mex! `',
        Charms.GIVE: '` Uitdelen! `',
        Charms.HOLDIT: '` Vast! `',
        Charms.HOUSE: '` Huisborrel! `'
    }


class Mex(commands.Cog):
    get_member = commands.MemberConverter()

    def __init__(self, bot, ftp_host, ftp_usr, ftp_pwd):
        self.bot = bot
        self.channel_controllers = dict()
        self.ftp = ftp_instance.Connector(ftp_host, ftp_usr, ftp_pwd)
        self.emojis = None

    def store_channel_controller(self, channel_id):
        channel_con = self.channel_controllers.get(channel_id)
        assert channel_con, "No channel controller for this context."
        fname = f'mexbot_{channel_id}.pickle'
        try:
            self.ftp.store_instance(channel_con, fname)
            print(f'Stored controller to {fname} on {self.ftp.host}')
        except ConnectionError:
            warn(f'Could not store {fname} to {self.ftp.host} due to a '
                 f'connection error')
    
    def restore_channel_controller(self, channel_id):
        fname = f'mexbot_{channel_id}.pickle'
        try:
            if self.ftp.file_exists(fname):
                channel_con = self.ftp.load_instance(fname)
                print(f'Restored controller from {fname} on {self.ftp.host}')
                return channel_con
        except ConnectionError:
            warn(f'Could not attempt to restore {fname} from {self.ftp.host} '
                 f'due to a connection error')
        return None

    def add_channel_controller(self, ctx):
        channel_con = self.restore_channel_controller(ctx.channel.id)
        if not channel_con:
            channel_con = ChannelController()
        self.channel_controllers[ctx.channel.id] = channel_con

    def get_channel_controller(self, ctx):
        if ctx.channel.id not in self.channel_controllers:
            self.add_channel_controller(ctx)
        return self.channel_controllers[ctx.channel.id]

    def cleanup(self):
        for channel_id in self.channel_controllers:
            self.store_channel_controller(channel_id)

    def make_message_turn(self, ctx, results):
        channel_con = self.get_channel_controller(ctx)
        game = channel_con.game
        game_count = channel_con.game_count
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
            str_roll = channel_con.get_roll_string(self.emojis, rolls[i], True)
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
            channel_con.get_roll_string(self.emojis, game.roll_low, False)
        )
        if game.limit < game.limit_init:
            line_game = f'Mex in {game.limit}  ◇  ' + line_game
        if game.mex > 0:
            line_game += f'  ◇  {game.mex} mex'
        # Put message together
        return line_user + '\n\n' + '\n\n'.join(lines_roll) + '\n\n' + line_game

    def make_message_conclusion(self, ctx, game):
        channel_controller = self.get_channel_controller(ctx)
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
        player = ctx.message.author.mention
        if proxy_user and (await self.bot.is_owner(ctx.message.author)):
            try:
                proxy_user = await self.get_member.convert(ctx, proxy_user)
                player = proxy_user.mention
            except commands.MemberNotFound:
                pass
        channel_controller = self.get_channel_controller(ctx)
        flag, results = channel_controller.take_turn(player)
        if flag == TURN_ALREADY_ROLLED:
            await ctx.send(choice(Phrases.CHEAT).format(player))
        elif flag == TURN_NOT_ALLOWED:
            await ctx.send(Phrases.NOT_DUELIST)
        else:
            await ctx.send(self.make_message_turn(ctx, results))
            if flag == TURN_SUCCES_GAME_OVER:
                await ctx.send(Phrases.SEPARATOR)
                await self.stop(ctx)

    @play.group('give', aliases=['uitdelen'])
    async def give(self, ctx, *args):
        player = ctx.message.author.mention
        channel_controller = self.get_channel_controller(ctx)
        for mention in args:
            try:
                member = await self.get_member.convert(ctx, mention)
            except commands.MemberNotFound:
                await ctx.message.add_reaction(self.emojis['chip_red'])
                continue
            target = member.mention
            flag = channel_controller.give_token(player, target)
            if flag == GIVE_NO_GAME:
                await ctx.message.add_reaction(self.emojis['chip_red'])
            elif flag == GIVE_NOT_ALLOWED:
                await ctx.message.add_reaction(self.emojis['chip_yellow'])
            else:
                await ctx.message.add_reaction(self.emojis['chip_green'])

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

    @play.group('stop', aliases=['finish'])
    async def stop(self, ctx):
        channel_controller = self.get_channel_controller(ctx)
        game = channel_controller.game
        flag = channel_controller.stop_game()
        if flag == STOP_GAME_UNDECIDED:
            msg = Phrases.STOP_WAIT
            await ctx.send(msg)
        elif flag == STOP_GAME_DUEL:
            msg = choice(Phrases.DUEL).format(list_names(game.players_allowed))
            await ctx.send(msg)
        elif flag == STOP_GAME_OVER:
            msg = self.make_message_conclusion(ctx, game)
            await ctx.send(msg)
            self.store_channel_controller(ctx.channel.id)
        return flag

    @play.command('style')
    async def set_dice_style(self, ctx, dice_style=None):
        channel_controller = self.get_channel_controller(ctx)
        channel_controller.set_dice_style(dice_style)
