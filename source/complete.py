import pandas as pd

from source.common import normalize_name, RETIRED_PLAYERS
from source.hockey_reference import HockeyReferencePlayersSource
from source.cap_friendly import CapFriendlyPlayersSource


class PlayersSource:
    def __init__(self, season):
        self.season = season
        self.players_source = HockeyReferencePlayersSource(season)
        self.players_with_cap_hit_source = CapFriendlyPlayersSource(season)

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
            suffixes=("", "_y"),
        )
        condition = (df["name"].isna() | df["name_y"].isna()) & (
            ~df["name"].isin(RETIRED_PLAYERS) & ~df["name_y"].isin(RETIRED_PLAYERS)
        )
        if not df[condition].empty:
            print(
                "Some players do not have a match between hockey-reference and cap "
                "friendly:"
            )
            print(df[condition].to_string())

    def _sew_to_cap_hit(self, players, players_with_cap_hit):
        df = pd.merge(
            players,
            players_with_cap_hit,
            how="inner",
            on=["normalized_name"],
            suffixes=("", "_y"),
        )
        return df.drop(df.filter(regex="_y$").columns, axis=1)
