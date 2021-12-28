#!/usr/bin/env python3

# Imports


class GuildController(object):
    def __init__(self):
        self.players = dict()
    
    def add_scores(self, scores):
        for mention, points in scores.items():
            if mention not in self.players:
                self.players[mention] = Player()
            player = self.players[mention]
            player.add_result(points)
    
    def get_scores_content(self):
        lines = [f'`{"Rank":>6s}{"Score":>8s}{"Played":>8s}`']
        ranked = sorted(self.players.items(), key=lambda x: -x[1].score)
        for rank, data in enumerate(ranked):
            mention, player = data
            line = f'`{rank + 1:6d}{player.score:8,d}{player.played:8,d}` {mention}'
            lines.append(line)
        return '\n'.join(lines)


class Player(object):
    SCORE_DEFAULT = 100
    
    def __init__(self):
        self.score = self.SCORE_DEFAULT
        self.played = 0
        self.correct = 0
        self.incorrect = 0
    
    def add_result(self, points):
        self.score += points
        self.played += 1
        self.correct += 1 if points > 0 else 0
        self.incorrect += 1 if points <= 0 else 0
