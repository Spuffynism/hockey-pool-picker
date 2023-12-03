from source.backtest import BacktestingSource
from strategy import LaPresseValueStrategy, LaPresseMinusGamblingValueStrategy
from solver import CPSATSolver

SALARY_CAP = 83_500_000
EVALUATION_STRATEGY = LaPresseValueStrategy()
FIRST_PICKING_STRATEGY = LaPresseMinusGamblingValueStrategy()


def main():
    year = 2023
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


if __name__ == "__main__":
    main()
