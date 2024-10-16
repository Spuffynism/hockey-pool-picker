import argparse

from hockey_pool_picker.core.season import Season, SEASONS_CAP_HIT
from hockey_pool_picker.core.season_simulator import SeasonSimulator
from hockey_pool_picker.sources.backtest import BacktestingSource
from hockey_pool_picker.core.strategy import (
    STRATEGIES,
)
from hockey_pool_picker.core.solver import CPSATSolver
from hockey_pool_picker.sources.players import PlayersSource


def main():
    args = parse_args()
    salary_cap = SEASONS_CAP_HIT[args.season]

    season = Season(start=args.season)
    source = BacktestingSource(season, PlayersSource)

    past_pool, present_pool = source.load(
        STRATEGIES[args.picking_strategy](), STRATEGIES[args.evaluation_strategy]()
    )

    solver = CPSATSolver()
    solution = solver.pick_pool(
        [group.to_dict("records") for group in past_pool], salary_cap
    )

    print(f"{season} pick:")
    solution.print()

    print(f"\nTranslated to {season.next()}")
    solver.translate_to_data(present_pool).print()

    print("\nTrading...")
    season_simulator = SeasonSimulator(
        solver,
        season,
        present_pool,
        salary_cap,
        STRATEGIES[args.evaluation_strategy](),
        STRATEGIES[args.period_strategy](),
    )
    solution = season_simulator.progress(solution)
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
    parser.add_argument(
        "--period_strategy",
        type=str,
        default="marqueur",
        choices=STRATEGIES.keys(),
        help="Period strategy. This is the strategy used to pick players for each monthly period.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()