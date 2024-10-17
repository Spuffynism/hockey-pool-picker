import json
from pathlib import Path

import pandas as pd
from pandas import json_normalize

from hockey_pool_picker.core.season import Season

player_type_map = {
    "forward": {"C", "R", "L"},
    "defender": {"D"},
    "goalie": {"G"},
}


class PuckpediaStatsAndCapHitSource:
    def __init__(self, season: Season):
        self.season = season

    def load(self, player_type):
        folder = "goalies" if player_type == "goalie" else "skaters"
        players = self.read_to_df(folder)

        players = players[players["pos"].isin(player_type_map[player_type])]
        assert (
            not players.empty
        ), f"No players of type {player_type} found for season {self.season}"
        players["name"] = players["p_fn"] + " " + players["p_ln"]
        players["cap_hit"] = (
            players["cap_hit"].str.replace(r"\D", "", regex=True).astype(int)
        )
        # keep ones that have played games
        players = players[players["st_gp"].astype(int) >= 1]
        # for goalies, on puckpedia, the goals and assists per season are not present
        players["goals"] = (
            players["st_g"].astype(int) if "st_g" in players.columns else 0
        )
        players["assists"] = (
            players["st_a"].astype(int) if "st_a" in players.columns else 0
        )
        if player_type == "goalie":
            players["wins"] = players["st_w"].astype(int)
            players["shutouts"] = players["st_so"].astype(int)
        # TODO(nico): add assertions that ensure all sources return expected columns
        return players

    def read_to_df(self, folder: str) -> pd.DataFrame:
        base_dir = Path(__file__).parent.parent.parent.parent
        dir_path = (
            base_dir
            / "data"
            / "puckpedia"
            / "manual"
            / f"{self.season.start}-{self.season.end}"
            / folder
        )
        if not dir_path.exists() or not dir_path.is_dir():
            raise FileNotFoundError(
                f"Directory {dir_path} not found or is not a directory"
            )

        all_files = dir_path.glob("*.json")
        df_list = []
        for file in all_files:
            with open(file) as data_file:
                data = json.load(data_file)
                # ['data']['p'] is sometimes a list of dicts, sometimes a dict of int -> dict
                # we convert it to a list of dicts
                if isinstance(data["data"]["p"], dict):
                    data["data"]["p"] = data["data"]["p"].values()
                df = json_normalize(data["data"]["p"])
                df_list.append(df)

        return pd.concat(df_list, ignore_index=True)

    def crawl(self):
        """
        I couldn't find a way to crawl PuckPedia, or use their API, since they have pretty good
        bot detection... so I manually downloaded the data for the 2020-21, 2021-22, 2022-23,
        and 2023-24 seasons.
        :return:
        """
        raise NotImplementedError
