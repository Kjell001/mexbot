#!/usr/bin/env python3

from random import randint
from copy import deepcopy

SIDES_DICE = 6
VALUES_KEEP = [1, 2]
VALUES_GIVE = [1, 3]
VALUES_MEX = [1, 2]
HUGE = float('inf')


class Roll(object):
    def __init__(self, values=None):
        self.fresh = [True, True]
        if values:
            self.values = values.copy()
        else:
            self.values = [0, 0]
            self.reroll()

    def first(self):
        return self.values[0], self.fresh[0]

    def second(self):
        return self.values[1], self.fresh[1]

    def reroll(self, a=True, b=True):
        if a:
            self.values[0] = randint(1, SIDES_DICE)
            self.fresh[0] = True
        else:
            self.fresh[0] = False
        if b:
            self.values[1] = randint(1, SIDES_DICE)
            self.fresh[1] = True
        else:
            self.fresh[1] = False

    def score(self):
        if set(self.values) == set(VALUES_KEEP):
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
        return self.score() == other.score()

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
            ' ' if self.fresh[0] else '*',
            self.values[1],
            ' ' if self.fresh[1] else '*'
        )
