# Copyright (c) Jeffrey Shen

"""Methods for selecting batches of games to play."""

import random

def get_selector(name, args):
    if name == "spaced":
        return SpacedSelector(args.selector_min_spacing, args.selector_max_batch)
    raise RuntimeError("Unsupported selector: {}".format(name))


def add_args(parser):
    parser.add_argument(
        "--selector_name",
        type=str,
        default="spaced",
        choices=("spaced",),
        help="The name of the selector method to use.",
    )
    parser.add_argument(
        "--selector_max_batch",
        type=int,
        default=10,
        help="The number of items to consider at once.",
    )
    parser.add_argument(
        "--selector_min_spacing",
        type=float,
        default=4.0,
        help="The minimum amount of spacing between items before considering splitting into a new batch.",
    )


class SpacedSelector:
    def __init__(self, min_spacing, max_batch):
        super().__init__()
        self.min_spacing = min_spacing
        self.max_batch = max_batch

    def is_batch_finished(self, players, batch, score):
        if len(batch) >= self.max_batch:
            return True
        spacing = abs(players[batch[0]] - players[batch[-1]]) / len(batch)
        if spacing < self.min_spacing:
            return False

        new_spacing = abs(players[batch[0]] - score) / (len(batch) + 1)
        return new_spacing > spacing

    def select(self, players):
        player_list = list(players.items())
        random.shuffle(player_list)
        player_list.sort(key=lambda item: item[1], reverse=True)
        batches = []
        for player, score in player_list:
            if not batches or self.is_batch_finished(players, batches[-1], score):
                batches.append([])
            batches[-1].append(player)

        # Handle the last batch
        if len(batches) >= 2 and len(batches[-1]) == 1:
            batch = batches.pop()
            batches[-1] += batch

        if len(batches[-1]) > self.max_batch:
            batch = batches[-1]
            batches[-1] = batch[: len(batch) // 2]
            batches.append(batch[len(batch) // 2 :])
        return batches
