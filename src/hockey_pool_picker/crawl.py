import argparse

from hockey_pool_picker.crawl_cache import session
from hockey_pool_picker.season import Season
from hockey_pool_picker.sources.hockey_reference_games import HockeyReferenceGamesSource
from hockey_pool_picker.sources.hockey_reference_players import HockeyReferencePlayersSource
from hockey_pool_picker.sources.marqueur_cap_hit import MarqueurCapHitSource


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seasons",
        nargs="+",
        type=int,
        default=[2021, 2022],
        help="List of seasons to crawl",
    )
    parser.add_argument(
        "--crawlers",
        nargs="+",
        default=["hockey_reference", "marqueur"],
        choices=["hockey_reference", "marqueur"],
        help="List of crawlers to use",
    )

    args = parser.parse_args()

    for season_year in args.seasons:
        season = Season(start=season_year)
        # TODO(nico): Handle players considered forwards by hockey-reference but
        #  defenders by cap friendly:
        #  ['Mason Geertsen', 'Hunter Drew', 'Luke Witkowski']
        for crawler in args.crawlers:
            if crawler == "marqueur":
                MarqueurCapHitSource(season).crawl()
            elif crawler == "hockey_reference":
                HockeyReferenceGamesSource(season).crawl()
                HockeyReferencePlayersSource(season).crawl()


if __name__ == "__main__":
    run()
