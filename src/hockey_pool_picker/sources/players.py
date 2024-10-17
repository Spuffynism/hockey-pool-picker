import pandas as pd

from hockey_pool_picker.util import normalize_name, RETIRED_PLAYERS
from hockey_pool_picker.core.season import Season
from hockey_pool_picker.sources.stats.hockey_reference import (
    HockeyReferencePlayersSource,
)
from hockey_pool_picker.sources.puckpedia import PuckpediaStatsAndCapHitSource


class PlayersSource:
    def __init__(self, season: Season):
        self.season = season
        self.players_source = HockeyReferencePlayersSource(season)
        self.players_with_cap_hit_source = PuckpediaStatsAndCapHitSource(season)

    # load players from both sources
    # add the normalized_name column to both dataframes
    def load(self, player_type):
        stats = self.players_source.load(player_type)
        # keep ones that have played games
        stats = stats[stats["games_played"] > 1]
        cap_hits = self.players_with_cap_hit_source.load(player_type)
        cap_hits = cap_hits[cap_hits["st_gp"].astype(int) > 1]

        stats["normalized_name"] = stats["name"].map(normalize_name)
        cap_hits["normalized_name"] = cap_hits["name"].map(normalize_name)

        self._pick_out_anomalies(stats, cap_hits)

        return self.join_to_cap_hit(stats, cap_hits)

    def _pick_out_anomalies(self, players, players_with_cap_hit):
        df = pd.merge(
            players,
            players_with_cap_hit,
            how="outer",
            on=["normalized_name"],
            suffixes=("_from_players_stats_source", "_from_cap_hit_source"),
        )
        is_na_or_retired = (
            df["name_from_players_stats_source"].isna()
            | df["name_from_cap_hit_source"].isna()
        ) & (
            ~df["name_from_players_stats_source"].isin(RETIRED_PLAYERS)
            & ~df["name_from_cap_hit_source"].isin(RETIRED_PLAYERS)
        )
        if not df[is_na_or_retired].empty:
            print(
                f"Some players do not have a match between sources in season {self.season}:"
            )
            print(
                df[is_na_or_retired][
                    ["name_from_cap_hit_source", "name_from_players_stats_source"]
                ].to_string()
            )

    def join_to_cap_hit(self, players, players_with_cap_hit):
        df = pd.merge(
            players,
            players_with_cap_hit,
            how="inner",
            on=["normalized_name"],
            suffixes=("", "_y"),
        )
        return df.drop(df.filter(regex="_y$").columns, axis=1)
