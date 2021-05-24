# Copyright (c) Jeffrey Shen

import argparse
import csv
import pathlib

from elo import Elo
import selectors


def add_args(parser):
    parser.add_argument(
        "--in_file",
        type=str,
        required=True,
        help="File to read the list of items from (as a txt)."
        "Can also read from the out_file as a CSV, which must be in Excel format.",
    )
    parser.add_argument(
        "--out_file",
        type=str,
        default=None,
        help="File to output the list of items as a CSV. Defaults to in_file.csv",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=10,
        help="The number of passes to loop over the list of items. "
        "For each pass, the selected half of each group beats other half.",
    )
    parser.add_argument(
        "--seeding_passes",
        type=int,
        default=0,
        help="Number of seeding passes to use, before proceeding to user-inputted passes. "
        "In this mode, group matches are held with higher seeds automatically winning. "
        "The seed is determined by the placement of the item in the input file. "
        "Only works if the in_file is a txt (not csv).",
    )
    add_elo_args(parser)
    selectors.add_args(parser)


def add_elo_args(parser):
    parser.add_argument(
        "--elo_base",
        type=float,
        default=10.0,
        help="The base of the exponent for calculating the expected score.",
    )
    parser.add_argument(
        "--elo_scale",
        type=float,
        default=400.0,
        help="The scaling factor in the exponent for calculating expected score.",
    )
    parser.add_argument(
        "--elo_k",
        type=float,
        default=24.0,
        help="The k-factor for Elo updates.",
    )
    parser.add_argument(
        "--elo_default",
        type=float,
        default=1500.0,
        help="Default Elo to assign items at the beginning.",
    )


def read_input(in_file, elo_default):
    players = {}
    if pathlib.PurePath(in_file).suffix == ".csv":
        with open(in_file, newline="") as file:
            reader = csv.reader(file)
            cols = None
            for row in reader:
                if cols is not None and len(row) != cols:
                    raise RuntimeError(
                        f"CSV was ill-formatted, found {len(row)} cols instead of {cols}"
                    )
                cols = len(row)
                elo = elo_default
                if len(row) > 1:
                    elo = float(row[1])
                players[row[0]] = elo
        is_csv = True
    else:
        with open(in_file) as file:
            player_list = [line.strip() for line in file]
            player_list = [player for player in player_list if player]
            for player in player_list:
                players[player] = elo_default
        is_csv = False

    return players, is_csv


def save_output(out_file, players):
    output = sorted(list(players.items()),key=lambda item: item[1], reverse=True)
    with open(out_file, "w", newline="") as file:
        writer = csv.writer(file)
        for player, score in output:
            writer.writerow([player, int(score)])


def main():
    parser = argparse.ArgumentParser("Rank a list of items using elo.")
    add_args(parser)

    args = parser.parse_args()
    if args.out_file is None:
        args.out_file = pathlib.PurePath(args.in_file).with_suffix(".csv")

    elo = Elo(args.elo_base, args.elo_scale, args.elo_k)
    selector = selectors.get_selector(args.selector_name, args)
    players, is_csv = read_input(args.in_file, args.elo_default)
    print(f"Loaded {len(players)} items from input file {args.in_file}")

    if not is_csv and args.seeding_passes > 0:
        player_seeds = {k: v for v, k in enumerate(players.keys())}
        print(f"Executing {args.seeding_passes} seeding passes...")
        for n in range(args.seeding_passes):
            batches = selector.select(players)
            results = []
            for batch in batches:
                winners = sorted(batch, key=lambda p: player_seeds[p])[:len(batch) // 2]
                losers = [p for p in batch if p not in winners]
                for w in winners:
                    for l in losers:
                        results.append((w, l))
            elo.update(players, results)
            
        print(f"Updating Elo ratings and saving to output file {args.out_file}")
        save_output(args.out_file, players)

    for n in range(args.passes):
        print(f"Executing pass number {n + 1} out of {args.passes}")
        batches = selector.select(players)
        results = []
        for batch in batches:
            print(
                "Select your top half or so, in no particular order, comma-separated, using their indices, out of:"
            )
            for p, player in enumerate(batch):
                print(f"{p}. {player} ({int(players[player])})")

            try:
                winners = input()
                winners = winners.split(",")
                winners = [winner.strip() for winner in winners]
                winners = [int(winner) for winner in winners if winner]
                winners = [
                    winner for winner in winners if winner >= 0 and winner < len(batch)
                ]
            except Exception as e:
                print("Skipping batch due to exception:", e)
                continue

            losers = [i for i in range(len(batch)) if i not in winners]
            for w in winners:
                for l in losers:
                    results.append((batch[w], batch[l]))
        print(f"Updating Elo ratings and saving to output file {args.out_file}")
        elo.update(players, results)
        save_output(args.out_file, players)

    print("Finished all passes!")


if __name__ == "__main__":
    main()
