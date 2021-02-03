#!/usr/bin/env python3

# Imports
from mex import *

# Constants
DICE_STYLES = ('1929', 'casino')

NO_GAME_FOUND = 0

TURN_TAKEN = 1
TURN_TAKEN_GAME_OVER = 2
TURN_ALREADY_ROLLED = 3
TURN_NOT_ALLOWED = 4

STOP_GAME_OVER = 5
STOP_GAME_DUEL = 6
STOP_GAME_UNDECIDED = 7
STOP_GAME_UNPLAYED = 8


class ChannelController(object):
    def __init__(self):
        self.game = None
        self.game_count = 0
        self.dice_style = DICE_STYLES[0]

    def new_game(self, roll_limit=None):
        roll_limit = roll_limit or LIMIT_DEFAULT
        self.game = Game(roll_limit)
        self.game_count += 1

    def take_turn(self, player):
        if not self.game:
            self.new_game()
        results = self.game.turn(player)
        if results == PLAYER_ALREADY_ROLLED:
            return TURN_ALREADY_ROLLED, None
        elif results == PLAYER_NOT_ALLOWED:
            return TURN_NOT_ALLOWED, None
        else:
            if self.game.state == GAME_OVER:
                return TURN_TAKEN_GAME_OVER, results
            else:
                return TURN_TAKEN, results

    def stop_game(self):
        if not self.game:
            return NO_GAME_FOUND
        elif self.game.state == GAME_UNDECIDED:
            return STOP_GAME_UNDECIDED
        else:  # GAME_ONGOING or GAME_OVER
            if not self.game.players_low:
                # No turns taken yet
                return STOP_GAME_UNPLAYED
            else:
                self.game.distribute_shared_tokens()
                if len(self.game.players_low) == 1:
                    # Wrap up game
                    self.game.distribute_loser_tokens()
                    return STOP_GAME_OVER
                else:
                    # Set up duel
                    duelists = self.game.players_low
                    self.game.set_limit(LIMIT_DUEL)
                    self.game.set_allowed_players(duelists)
                    self.game.refresh()
                    return STOP_GAME_DUEL

    def set_dice_style(self, dice_style):
        if dice_style not in DICE_STYLES:
            return False
        else:
            self.dice_style = dice_style
            return True

    def get_roll_string(self, emojis, roll, shade):
        value1, fresh1 = roll.first()
        value2, fresh2 = roll.second()
        if not shade:
            fresh1, fresh2 = True, True
        key1 = 'd{}{}_{}'.format(str(value1), '' if fresh1 else 'd', self.dice_style)
        key2 = 'd{}{}_{}'.format(str(value2), '' if fresh2 else 'd', self.dice_style)
        return ' '.join([emojis[key1], emojis[key2]])
