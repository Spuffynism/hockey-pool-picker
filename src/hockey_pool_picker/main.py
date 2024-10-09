from hockey_pool_picker.crawl_cache import session
from hockey_pool_picker.season import Season
from hockey_pool_picker.season_simulator import SeasonSimulator
from hockey_pool_picker.backtest import BacktestingSource
from hockey_pool_picker.strategy import LaPresseValueStrategy
from hockey_pool_picker.solver import CPSATSolver

SALARY_CAP = 82_500_000
EVALUATION_STRATEGY = LaPresseValueStrategy()
FIRST_PICKING_STRATEGY = LaPresseValueStrategy()
PERIOD_PICKING_STRATEGY = LaPresseValueStrategy()


def main():
    # TODO(nico): crawl if we don't have the required data
    season = Season(start=2022)
    source = BacktestingSource(season)

    past_pool, present_pool = source.load(FIRST_PICKING_STRATEGY, EVALUATION_STRATEGY)

    solver = CPSATSolver()
    solution = solver.pick_pool(
        [group.to_dict("records") for group in past_pool], SALARY_CAP
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
        SALARY_CAP,
        EVALUATION_STRATEGY,
        PERIOD_PICKING_STRATEGY,
    )
    solution = season_simulator.progress(solution)
    solution.print()


if __name__ == "__main__":
    main()
