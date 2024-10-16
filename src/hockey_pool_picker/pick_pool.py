import argparse

from hockey_pool_picker.core.season import Season, SEASONS_CAP_HIT
from hockey_pool_picker.sources.backtest import BacktestingSource
from hockey_pool_picker.sources.players import PlayersSource
from hockey_pool_picker.core.strategy import STRATEGIES
from hockey_pool_picker.core.solver import CPSATSolver


def main():
    args = parse_args()

    season = Season(start=args.season)
    source = BacktestingSource(season, PlayersSource)

    past_pool, _ = source.load(
        STRATEGIES[args.picking_strategy](), STRATEGIES[args.evaluation_strategy]()
    )

    solver = CPSATSolver()
    solution = solver.pick_pool(
        [group.to_dict("records") for group in past_pool], SEASONS_CAP_HIT[args.season]
    )

    print("pick:")
    solution.print()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backtest pool picking strategies against from past to present seasons."
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2022,
        choices=[2020, 2021, 2022],
        help="Start year of the season for which to backtest against",
    )
    parser.add_argument(
        "--evaluation_strategy",
        type=str,
        default="marqueur",
        choices=STRATEGIES.keys(),
        help="Evaluation strategy. This is the strategy used to evaluate the pool of players.",
    )
    parser.add_argument(
        "--picking_strategy",
        type=str,
        default="marqueur",
        choices=STRATEGIES.keys(),
        help="Picking strategy. This is the strategy used to pick the initial pool of players.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
