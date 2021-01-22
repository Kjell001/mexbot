import os
import urllib.request
import json
from html import unescape
from random import randint, shuffle, choice
from copy import deepcopy
import discord


# CONSTANTS --------------------------------------

HUGE = float('inf')
PLAYER_ALREADY_ROLLED = 1
RETAIN = 1200 # 20 minutes
URL_TRIVIA = 'https://opentdb.com/api.php?amount=1&type=multiple'
TRIVIA_COMMAND = '!ramswoertherevival'
TOKEN_DISCORD_BOT = os.getenv("TOKEN_DISCORD_BOT")

# GAME CLASSES -----------------------------------

class Dice(object):
    def __init__(self, values=None):
        self.fresh = [True, True]
        if values:
            self.values = values.copy()
        else:
            self.values = [0, 0]
            self.roll()

    def first(self):
        return self.values[0], self.fresh[0]

    def second(self):
        return self.values[1], self.fresh[1]

    def roll(self, a=True, b=True):
        if a:
            self.values[0] = randint(1, Rules.SIDES_DICE)
            self.fresh[0] = True
        else:
            self.fresh[0] = False
        if b:
            self.values[1] = randint(1, Rules.SIDES_DICE)
            self.fresh[1] = True
        else:
            self.fresh[1] = False

    def score(self):
        if self == Rules.DICE_MEX:
            return HUGE
        elif self.values[0] == self.values[1]:
            return 100 * self.values[0]
        else:
            return 10 * max(self.values) + min(self.values)

    def snapshot(self):
        return deepcopy(self)

    def __contains__(self, value):
        return value in self.values

    def __eq__(self, other):
        return set(self.values) == set(other.values)

    def __lt__(self, other):
        return self.score() < other.score()

    def __le__(self, other):
        return self.score() <= other.score()

    def __gt__(self, other):
        return self.score() > other.score()

    def __ge__(self, other):
        return self.score() >= other.score()

    def __repr__(self):
        return 'Dice({}{}, {}{})'.format(
            self.values[0],
            '' if self.fresh[0] else '*',
            self.values[1],
            '' if self.fresh[1] else '*'
        )


class Rules(object):
    DICE_KEEP = Dice([1, 2])
    DICE_GIVE = Dice([1, 3])
    DICE_MEX = Dice([1, 2])
    DICE_IMPOSSIBLE = Dice([9, 9])
    SIDES_DICE = 6
    LIMIT_MIN = 1
    LIMIT_MAX = 3
    STREAK = 3


class Charms(object):
    MEX = 1
    GIVE = 2
    HOLDIT = 3
    HOUSE = 4


class Results(object):
    def __init__(self, game, player):
        self.rolls = []
        self.game = game
        self.player = player
        self.holdit = False

    def add_roll(self, dice):
        self.rolls.append(dice)

    def interrupt(self):
        self.holdit = True

    def dice_last(self):
        return self.rolls[-1]

    def get(self):
        labels = []
        label_current = 1
        charms = []
        streak = 1
        last_roll = None
        for i, roll in enumerate(self.rolls):
            charm = []
            # Check mex
            if roll == Rules.DICE_MEX:
                charm.append(Charms.MEX)
            # Check label and give charm
            if roll == Rules.DICE_GIVE:
                labels.append('-')
                charm.append(Charms.GIVE)
            else:
                labels.append(str(label_current))
                label_current += 1
            # Check if last roll was held
            if i == len(self.rolls) - 1 and self.holdit:
                charm.append(Charms.HOLDIT)
            # Check streak
            if i > 0:
                if roll == last_roll:
                    streak += 1
                else:
                    streak = 1
            if streak == Rules.STREAK:
                charm.append(Charms.HOUSE)
            charms.append(charm)
            last_roll = roll
        return self.rolls, labels, charms



class Game(object):
    def __init__(self, roll_limit=3):
        self.limit = min(max(Rules.LIMIT_MIN, roll_limit), Rules.LIMIT_MAX)
        self.limit_init = self.limit
        self.players = list()
        self.roll_low = None
        self.players_low = []
        self.mex = 0

    def turn(self, player):
        # Check if player can throw
        if player in self.players:
            return PLAYER_ALREADY_ROLLED
        self.players.append(player)
        # Setup
        results = Results(self, player)
        dice = Dice()
        roll_num = 1
        # Throw dice
        while roll_num <= self.limit:
            results.add_roll(dice.snapshot())
            value1, fresh1 = dice.first()
            value2, fresh2 = dice.second()
            # Identify special situations
            if self.roll_low and dice == self.roll_low and roll_num < self.limit:
                # Check if this identical to lowest pair in game
                results.interrupt()
                break
            elif dice == Rules.DICE_GIVE:
                # Give, extra round
                dice.roll()
                continue
            elif dice == Rules.DICE_MEX:
                # Mex
                if len(self.players) == 1:
                    self.limit = roll_num
                self.mex += 1
                break
            elif value1 in Rules.DICE_KEEP and fresh1:
                # Keep first dice
                dice.roll(False, True)
            elif value2 in Rules.DICE_KEEP and fresh2:
                # Keep second dice
                dice.roll(True, False)
            else:
                dice.roll()
            # Increment roll count
            roll_num += 1
        # Update game state
        dice_last = results.dice_last()
        if self.roll_low and dice_last == self.roll_low:
            self.players_low.append(player)
        elif not self.roll_low or dice_last <= self.roll_low:
            self.players_low = [player]
            self.roll_low = dice_last.snapshot()
        return results


# TRIVIA -----------------------------------------

def get_trivia_response():
    # Fetch trivia
    with urllib.request.urlopen(URL_TRIVIA) as url:
        data = json.loads(url.read().decode())
    trivia = data['results'][0]
    question = unescape(trivia['question'])
    answer_correct = unescape(trivia['correct_answer'])
    answers = [unescape(a) for a in trivia['incorrect_answers']]
    answers.append(answer_correct)
    # Format
    line_quiz = '*Secret quiz time: {}*\n'.format(question)
    lines_answers = []
    for i, answer in enumerate(answers):
        lines_answers.append('|| {} ||  {}'.format(
            '✅' if i == len(answers) - 1 else '❌',
            answer
        ))
    shuffle(lines_answers)
    return line_quiz + '\n'.join(lines_answers)


# PHRASES ----------------------------------------

class Phrases:
    START = (
        '{} werpt de teerling',
        'De beurt is aan {}',
        '{} grijpt naar de dobbels',
        '{} hoopt op mex',
        '{} ruikt even aan de dobbelstenen',
        '{} heeft nog geen dorst'
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


# CONNECT TO DISCORD -----------------------------

client = discord.Client()
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

@client.event
async def on_ready():
    global emojis
    print('Logged in as {0.user}'.format(client))
    # Fetch emojis
    emojis = dict([(e.name, '<:' + e.name + ':' + str(e.id) + '>') for e in client.emojis])

@client.event
async def on_message(message):
    # OWN MESSAGE
    if message.author == client.user:
        return
    # TRIVIA
    elif message.content.replace(' ', '').lower() == TRIVIA_COMMAND:
        response = get_trivia_response()
        await message.channel.send(response)
    # MEX
    elif message.content.startswith('!mex'):
        global emojis, Phrases
        # Parse arguments
        args = message.content.lower().split()
        new_game = len(args) > 1 and args[1] == 'start'
        try:
            roll_limit = int(args[2]) if len(args) > 2 else 3
        except ValueError:
            roll_limit = 3
        # Get info
        channel_id = message.channel.id
        user_id = message.author.id
        user_mention = '<@{}>'.format(user_id)
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
                str_label = '` {} `'.format(labels[i])
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
        #await message.channel.send(response, delete_after=RETAIN)
        await message.channel.send(response)

client.run(TOKEN_DISCORD_BOT)
