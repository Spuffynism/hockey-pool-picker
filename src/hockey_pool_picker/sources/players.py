import pandas as pd

from hockey_pool_picker.common import normalize_name, RETIRED_PLAYERS
from hockey_pool_picker.season import Season
from hockey_pool_picker.sources.hockey_reference_players import HockeyReferencePlayersSource
from hockey_pool_picker.sources.marqueur_cap_hit import MarqueurCapHitSource


class PlayersSource:
    def __init__(self, season: Season):
        self.season = season
        self.players_source = HockeyReferencePlayersSource(season)
        self.players_with_cap_hit_source = MarqueurCapHitSource(season)

    def load(self, player_type, value=None, weight=None):
        players = self.players_source.load(player_type)
        players_with_cap_hit = self.players_with_cap_hit_source.load(player_type)

        players["normalized_name"] = players["name"].map(normalize_name)
        players_with_cap_hit["normalized_name"] = players_with_cap_hit["name"].map(
            normalize_name
        )

        self._pick_out_anomalies(players, players_with_cap_hit)

        sown = self._sew_to_cap_hit(players, players_with_cap_hit)
        if value is not None:
            sown["value"] = value(sown)

        if weight is not None:
            sown["weight"] = sown[weight]

        return sown

    def _pick_out_anomalies(self, players, players_with_cap_hit):
        df = pd.merge(
            players,
            players_with_cap_hit,
            how="outer",
            on=["normalized_name"],
            suffixes=("_from_players_stats_source", "_from_cap_hit_source"),
        )
        condition = (df["name_from_players_stats_source"].isna() | df["name_from_cap_hit_source"].isna()) & (
            ~df["name_from_players_stats_source"].isin(RETIRED_PLAYERS) & ~df["name_from_cap_hit_source"].isin(RETIRED_PLAYERS)
        )
        if not df[condition].empty:
            print(
                f"Some players do not have a match between sources in season {self.season}:"
            )
            print(df[condition][["name_from_cap_hit_source", "name_from_players_stats_source"]].to_string())

    def _sew_to_cap_hit(self, players, players_with_cap_hit):
        df = pd.merge(
            players,
            players_with_cap_hit,
            how="inner",
            on=["normalized_name"],
            suffixes=("", "_y"),
        )
        return df.drop(df.filter(regex="_y$").columns, axis=1)
