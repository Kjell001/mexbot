#!/usr/bin/env python3

from .roll import *

DICE_KEEP = Roll(VALUES_KEEP)
DICE_GIVE = Roll(VALUES_GIVE)
DICE_MEX = Roll(VALUES_MEX)
LIMIT_MIN = 1
LIMIT_MAX = 3
LIMIT_DUEL = 1
STREAK = 3

# Roll status
PLAYER_ALREADY_ROLLED = -1
PLAYER_NOT_ALLOWED = -2

# All-player key
ALL_PLAYERS = '_all'


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
        self.streak = 1
        self.house = list()

    def add_roll(self, roll):
        self.rolls.append(roll)
        # Store house roll indices
        if len(self.rolls) > 1:
            if self.rolls[-1] == self.rolls[-2]:
                self.streak += 1
                if self.streak % STREAK == 0:
                    self.house.append(len(self.rolls) - 1)
            else:
                self.streak = 1

    def interrupt(self):
        self.holdit = True

    def roll_last(self):
        return self.rolls[-1]

    def get(self):
        labels = []
        label_current = 1
        charms = []
        for i, roll in enumerate(self.rolls):
            charm = []
            # Check mex charm
            if roll == DICE_MEX:
                charm.append(Charms.MEX)
            # Determine label and check give charm
            if roll == DICE_GIVE:
                labels.append('-')
                charm.append(Charms.GIVE)
            else:
                labels.append(str(label_current))
                label_current += 1
            # Check if last roll was held
            if i == len(self.rolls) - 1 and self.holdit:
                charm.append(Charms.HOLDIT)
            # Check house charm
            if i in self.house:
                charm.append(Charms.HOUSE)
            charms.append(charm)
        return self.rolls, labels, charms


class Game(object):
    INITIATED = 0
    ONGOING = 1
    UNDECIDED = 2
    OVER = 3
    CONCLUDED = 4

    def __init__(self, roll_limit=3, players_allowed=None, mex=0, tokens=None):
        self.limit = min(max(LIMIT_MIN, roll_limit), LIMIT_MAX)
        self.limit_init = self.limit
        self.players_allowed = players_allowed
        self.players = list()
        self.tokens = tokens if tokens else {ALL_PLAYERS: 0}
        self.roll_low = None
        self.players_low = []
        self.mex = mex
        self.state = Game.UNDECIDED if players_allowed else Game.INITIATED

    def add_tokens(self, player, amount):
        if player in self.tokens:
            self.tokens[player] += amount
        else:
            self.tokens[player] = amount

    def turn(self, player):
        # Check if player can throw
        if player in self.players:
            return PLAYER_ALREADY_ROLLED
        if self.players_allowed and player not in self.players_allowed:
            return PLAYER_NOT_ALLOWED
        self.players.append(player)
        self.state = Game.UNDECIDED if self.players_allowed else Game.ONGOING
        # Setup
        results = Results(self, player)
        roll = Roll()
        roll_num = 1
        # Throw dice
        while roll_num <= self.limit:
            results.add_roll(roll.snapshot())
            value1, fresh1 = roll.first()
            value2, fresh2 = roll.second()
            # Identify special situations
            if roll == DICE_GIVE:
                # Give, extra round
                roll.reroll()
                continue
            elif roll == DICE_MEX:
                # Mex
                if len(self.players) == 1:
                    self.limit = roll_num
                self.mex += 1
                break
            elif self.roll_low and roll == self.roll_low and roll_num < self.limit:
                # Check if this identical to lowest pair in game
                results.interrupt()
                break
            elif value1 in DICE_KEEP and fresh1:
                # Keep first dice
                roll.reroll(False, True)
            elif value2 in DICE_KEEP and fresh2:
                # Keep second dice
                roll.reroll(True, False)
            else:
                roll.reroll()
            # Increment roll count
            roll_num += 1
        # Update game state
        roll_last = results.roll_last()
        if self.roll_low and roll_last == self.roll_low:
            self.players_low.append(player)
        elif not self.roll_low or roll_last <= self.roll_low:
            self.players_low = [player]
            self.roll_low = roll_last.snapshot()
        self.add_tokens(ALL_PLAYERS, len(results.house))
        if self.players_allowed and len(self.players) == len(self.players_allowed):
            self.state = Game.OVER
        return results

    def conclude(self):
        tokens_all = self.tokens[ALL_PLAYERS]
        if tokens_all > 0:
            [self.add_tokens(player, tokens_all) for player in self.players]
        self.state = Game.CONCLUDED
        if len(self.players_low) == 1:
            self.add_tokens(self.players_low[0], self.mex + 1)
            self.tokens.pop(ALL_PLAYERS)
        else:
            # Return duel game when tied
            return Game(LIMIT_DUEL, self.players_low, self.mex, self.tokens)