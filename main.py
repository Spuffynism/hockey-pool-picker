from season_simulator import SeasonSimulator
from source.backtest import BacktestingSource
from strategy import LaPresseValueStrategy
from solver import CPSATSolver

SALARY_CAP = 82_500_000
EVALUATION_STRATEGY = LaPresseValueStrategy()
FIRST_PICKING_STRATEGY = LaPresseValueStrategy()
PERIOD_PICKING_STRATEGY = LaPresseValueStrategy()


def main():
    year = 2022
    source = BacktestingSource(year)

    past_pool, present_pool = source.load(FIRST_PICKING_STRATEGY, EVALUATION_STRATEGY)

    solver = CPSATSolver()
    solution = solver.pick_pool(
        [group.to_dict("records") for group in past_pool], SALARY_CAP
    )

    print(f"{year} pick:")
    solution.print()

    print(f"\nTranslated to {year + 1}")
    solver.translate_to_data(present_pool).print()

    print("\nTrading...")
    season_simulator = SeasonSimulator(
        solver,
        year,
        present_pool,
        SALARY_CAP,
        EVALUATION_STRATEGY,
        PERIOD_PICKING_STRATEGY,
    )
    solution = season_simulator.progress(solution)
    solution.print()


if __name__ == "__main__":
    main()
