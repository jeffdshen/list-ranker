# Copyright (c) Jeffrey Shen

"""A simple implementation of the Elo rating system"""

from collections import defaultdict


class Elo:
    def __init__(self, base, scale, k):
        super().__init__()
        self.k = k
        self.base = base
        self.scale = scale

    def update(self, players, wins, k=None):
        if k is None:
            k = self.k
        base = self.base
        scale = self.scale
        scores = defaultdict(float)
        for winner, loser in wins:
            ew = 1.0 / (1.0 + base ** ((players[loser] - players[winner]) / scale))
            el = 1.0 - ew
            scores[winner] += 1.0 - ew
            scores[loser] += 0.0 - el

        for player, score in scores.items():
            players[player] += k * score
