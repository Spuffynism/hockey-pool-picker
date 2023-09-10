import json
from datetime import datetime
from time import sleep
import pandas as pd

import requests
from bs4 import BeautifulSoup

from source.common import massage_players

HOCKEY_REFERENCE_ROBOTS_TXT_CRAWL_DELAY = 3

ID_COLUMN = "-9999"
player_positions = {
    "forward": ["C", "LW", "RW", "F", "W"],
    "defender": ["D"],
    "goalie": ["G"],
}


class HockeyReferencePlayersSource:
    def __init__(self, season):
        self.season = season

    def load(self, player_type):
        misc = self._load_to_df("skaters", "misc", columns={"Pos": "position"})
        misc = misc[misc["position"].isin(player_positions[player_type])]

        if player_type == "goalie":
            # wins, saves, shutouts, saves_percent * 1000
            goalies_all = self._load_to_df(
                "goalies",
                "all",
                columns={
                    "Player": "name",
                    "W": "wins",
                    "SV": "saves",
                    "SV%": "saves_percent",
                    "SO": "shutouts",
                    "G": "goals",
                    "A": "assists",
                    "GP": "games_played",
                },
            )
            df = pd.merge(
                goalies_all, misc, how="left", on=ID_COLUMN, suffixes=("", "_y")
            )
            # We drop the second "Matt Murray" even though it's a different goalie to
            # remove duplicates. Ideally, we'd have a better way of identifying players.
            df = df.drop_duplicates(subset="name", keep="first")
            return df.drop(df.filter(regex="_y$").columns, axis=1)

        basic = self._load_to_df(
            "skaters",
            "basic",
            columns={
                "Pos": "position",
                "G": "goals",
                "A": "assists",
                "GP": "games_played",
                "Player": "name",
            },
        )
        basic = basic[basic["position"].isin(player_positions[player_type])]

        advanced = self._load_to_df("skaters", "advanced", columns={"Pos": "position"})
        advanced = advanced[advanced["position"].isin(player_positions[player_type])]

        df = pd.merge(basic, advanced, how="left", on=ID_COLUMN, suffixes=("", "_y"))
        df = df.drop(df.filter(regex="_y$").columns, axis=1)
        df = df.merge(misc, how="left", on=ID_COLUMN, suffixes=("", "_y"))
        df = df.drop(df.filter(regex="_y$").columns, axis=1)

        return massage_players(df)

    def _load_to_df(self, player_type, stats_type, columns, dtype=None):
        return (
            pd.read_csv(
                f"data/hockey_reference/{self.season}_{player_type}_{stats_type}.csv",
                header=1,
                usecols=list(columns.keys()) + [ID_COLUMN],
            )
            .rename(columns=columns)
            .astype(dtype if dtype is not None else {})
            # Per-player totals are in the first row. Following rows for same player are
            # stats per-player, per-team.
            .drop_duplicates(subset=ID_COLUMN, keep="first")
        )


class HockeyReferenceGamesSource:
    def __init__(self, season):
        self.season = season

    def load(self):
        with open(f"data/hockey_reference/games_{self.season}.json") as f:
            games = json.load(f)
            games = pd.json_normalize(games)
            games["date"] = pd.to_datetime(games["date"])

            return games

    def write(self, games):
        with open(f"../data/hockey_reference/games_{self.season}.json", "w") as outfile:
            # default=str to handle dates
            outfile.write(
                json.dumps(
                    games, separators=(",", ":"), ensure_ascii=False, default=str
                )
            )

    def crawl(self):
        prefix = "https://www.hockey-reference.com"
        response = requests.request(
            "GET", f"{prefix}/leagues/NHL_{self.season}_games.html"
        )

        soup = BeautifulSoup(response.content, "html.parser")

        games = []
        game_rows = soup.find(id="games").find("tbody").find_all("tr")
        for i, game_row in enumerate(game_rows):
            link = game_row.find("th").find("a")
            full_link = f"{prefix}{link['href']}"

            percent_progress = round((i + 1) / len(game_rows) * 100, 2)
            print(f"({percent_progress}%) {i + 1}/{len(game_rows)}: {full_link}")

            date, scores, goalies = self._crawl_game(full_link)

            games.append({"date": date, "scores": scores, "goalies": goalies})

            sleep(HOCKEY_REFERENCE_ROBOTS_TXT_CRAWL_DELAY)

        return games

    def _crawl_game(self, link):
        response = requests.request("GET", link)

        soup = BeautifulSoup(response.content, "html.parser")

        date_str = soup.find(class_="scorebox_meta").find("div").text.strip()
        date = datetime.strptime(date_str, "%B %d, %Y, %I:%M %p")

        scoring_rows = soup.find(id="scoring").find_all("tr")

        scores = []
        for row in scoring_rows:
            cols = row.find_all("td")
            if len(cols) == 5:
                scorer = cols[3].find("a").text.strip()
                assists = [a.text.strip() for a in cols[4].find_all("a")]
                scores.append({"scorer": scorer, "assists": assists})

        goalies = []

        breadcrumb = (
            soup.find(id="footer_header")
            .find(class_="breadcrumbs")
            .find_all("a")[2]
            .text.split(",")[0]
        )
        codes = [place.strip() for place in breadcrumb.split("at")]

        for code in codes:
            goalie_rows = soup.find(id=f"{code}_goalies").find("tbody").find_all("tr")
            for row in goalie_rows:
                cols = row.find_all("td")
                maybe_name = cols[0].find("a")

                if maybe_name is None:
                    # Empty Net, no goalie
                    continue

                name = maybe_name.text.strip()
                decision = cols[1].text.strip()
                saves = cols[4].text.strip()
                shutout = cols[6].text.strip()
                saves_percent = cols[5].text.strip()

                if decision not in ["W", "L", "O"]:
                    raise Exception(f"Unknown decision: {decision}")

                goalies.append(
                    {
                        "decision": decision,
                        "name": name,
                        "shutout": int(shutout) == 1,
                        "saves": int(saves),
                        "saves_percent": float(saves_percent)
                        if saves_percent
                        else None,
                    }
                )

        return date, scores, goalies


def main():
    for season in [2022, 2023]:
        source = HockeyReferenceGamesSource(season)
        games = source.crawl()
        source.write(games)

    print("done!")


if __name__ == "__main__":
    main()
