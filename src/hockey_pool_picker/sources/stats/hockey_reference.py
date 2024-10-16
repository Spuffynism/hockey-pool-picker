import json

from bs4 import BeautifulSoup

from hockey_pool_picker.sources import ndjson
from hockey_pool_picker.util import massage_players, merge_on_indices
from hockey_pool_picker.sources.crawl_cache import session
from hockey_pool_picker.core.season import Season

whole_number_columns = {
    "age",
    "games",
    "goals",
    "assists",
    "points",
    "plus_minus",
    "pen_min",
    "goals_ev",
    "goals_pp",
    "goals_sh",
    "goals_gw",
    "assists_es",
    "assists_pp",
    "assists_sh",
    "shots",
    "shots_attempted",
    "faceoff_wins",
    "faceoff_losses",
    "blocks",
    "hits",
    "takeaways",
    "giveaways",
    "games_played",
    "corsi_for",
    "corsi_against",
    "fenwick_for",
    "fenwick_against",
    "total_shots_attempted_all",
    "shots_thru_percentage",
    "goals_adjusted",
    "assists_adjusted",
    "points_adjusted",
    "total_goals_for",
    "power_play_goals_for",
    "total_goals_against",
    "power_play_goals_against",
    "games_goalie",
    "starts_goalie",
    "wins_goalie",
    "losses_goalie",
    "ties_goalie",
    "goals_against",
    "shots_against",
    "saves",
    "shutouts",
    "min_goalie",
    "quality_starts_goalie",
    "really_bad_starts_goalie",
    "ga_pct_minus",
}
decimal_columns = {
    "shot_pct",
    "faceoff_percentage",
    "corsi_rel_pct",
    "fenwick_pct",
    "fenwick_rel_pct",
    "on_ice_shot_pct",
    "on_ice_sv_pct",
    "pdo",
    "zs_offense_pct",
    "zs_defense_pct",
    "expected_plsmns",
    "corsi_pct",
    "goals_created_adjusted",
    "ops",
    "dps",
    "ps",
    "ev_exp_on_goals_for",
    "ev_exp_on_goals_against",
    "save_pct",
    "goals_against_avg",
    "gps",
    "quality_start_goalie_pct",
    "gs_above_avg",
}


player_positions = {
    "forward": ["C", "LW", "RW", "F", "W"],
    "defender": ["D"],
    "goalie": ["G"],
}


class HockeyReferencePlayersSource:
    def __init__(self, season: Season):
        self.season = season

    def crawl(self):
        # with this structure, it should be relatively trivial to now crawl other tables
        data = self._crawl_basic_stats()
        self._persist(data, "skaters", "basic")

        data = self.crawl_advanced_stats()
        self._persist(data, "skaters", "advanced")

        data = self.crawl_misc_stats()
        self._persist(data, "skaters", "misc")

        data = self.crawl_basic_goalies_stats()
        self._persist(data, "goalies", "all")

    def _crawl_basic_stats(self):
        rows = self._crawl_rows(
            url=f"https://www.hockey-reference.com/leagues/NHL_{self.season.end}_skaters.html",
            table_id="player_stats",
        )
        return self.structure_rows_to_dicts(rows)

    def crawl_advanced_stats(self):
        rows = self._crawl_rows(
            url=f"https://www.hockey-reference.com/leagues/NHL_{self.season.end}_skaters-advanced.html",
            table_id="stats_adv_rs",
        )
        return self.structure_rows_to_dicts(rows)

    def crawl_misc_stats(self):
        rows = self._crawl_rows(
            url=f"https://www.hockey-reference.com/leagues/NHL_{self.season.end}_skaters-misc.html",
            table_id="stats_misc_plus",
        )
        return self.structure_rows_to_dicts(rows)

    def crawl_basic_goalies_stats(self):
        rows = self._crawl_rows(
            url=f"https://www.hockey-reference.com/leagues/NHL_{self.season.end}_goalies.html",
            table_id="stats",
        )
        return self.structure_rows_to_dicts(rows)

    def _persist(self, data, player_type, stats_type):
        with open(self.file_name(player_type, stats_type), "w") as file:
            for row in data:
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def structure_rows_to_dicts(self, rows):
        data = []
        for row in rows:
            cells = row.find_all("td")

            if cells:
                row_data = {}

                for i, cell in enumerate(cells):
                    column_name = cell["data-stat"]
                    value = cell.text
                    if value == "League Average":
                        # skip the special "League Average" column
                        continue

                    if i == 0:
                        # hockey-reference creates unique player codes for each player. This helps with disambiguating
                        # players with the same name.
                        row_data["player_code"] = cell["data-append-csv"]

                    if column_name in whole_number_columns:
                        row_data[column_name] = int(value) if value != "" else 0
                    elif column_name in decimal_columns:
                        row_data[column_name] = float(value) if value != "" else 0
                    else:
                        row_data[column_name] = value

                data.append(row_data)
        return data

    def _crawl_rows(self, url, table_id):
        response = session.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        table = soup.find(id=table_id)

        return table.find_all("tr")

    def load(self, player_type):
        if player_type == "goalie":
            columns = {
                # TODO(nico): Add assertions to solver that makes sure columns are as expected
                "player": "name",
                "wins_goalie": "wins",
                "save_pct": "saves_percent",
                "games_goalie": "games_played",
            }
            # wins, saves, shutouts, saves_percent * 1000
            goalies_all = self._load_to_df(
                "goalies",
                "all",
                columns=columns,
            )

            expected_columns = set(columns.values())
            actual_columns = set(goalies_all.columns)
            assert expected_columns.issubset(
                actual_columns
            ), f"Missing goalie columns: {expected_columns.difference(actual_columns)}"

            # We drop the second "Matt Murray" even though it's a different goalie to
            # remove duplicates. Ideally, we'd have a better way of identifying players.
            goalies_all = goalies_all.drop_duplicates(subset="name", keep="first")
            return goalies_all

        misc = self._load_to_df("skaters", "misc", columns={"pos": "position"})
        misc = misc[misc["position"].isin(player_positions[player_type])]
        columns = {
            "games": "games_played",
            "name_display": "name",
            "pos": "position",
        }
        basic = self._load_to_df(
            "skaters",
            "basic",
            columns=columns,
        )
        expected_columns = set(columns.values())
        actual_columns = set(basic.columns)
        assert expected_columns.issubset(
            actual_columns
        ), f"Missing basic columns: {expected_columns.difference(actual_columns)}"
        basic = basic[basic["position"].isin(player_positions[player_type])]

        advanced = self._load_to_df("skaters", "advanced", columns={"pos": "position"})
        advanced = advanced[advanced["position"].isin(player_positions[player_type])]

        merged = merge_on_indices([basic, advanced, misc])

        return massage_players(merged)

    def _load_to_df(self, player_type, stats_type, columns=None, dtype=None):
        if columns is None:
            columns = {}
        df = (
            ndjson.read_to_df(self.file_name(player_type, stats_type))
            .rename(columns=columns)
            .astype(dtype if dtype is not None else {})
            # Per-player totals are in the first row. Following rows for same player are
            # stats per-player, per-team.
            .drop_duplicates(subset="player_code", keep="first")
        )
        df.set_index("player_code", inplace=True, verify_integrity=True)
        return df

    def file_name(self, player_type, stats_type):
        return f"hockey_reference/{self.season}_{player_type}_{stats_type}.ndjson"
