import json
import re
from decimal import Decimal
from re import sub

import pandas as pd

from source.common import massage_players

import requests

from bs4 import BeautifulSoup


player_type_map = {
    "forwards": "forward",
    "defense": "defender",
    "goalies": "goalie",
}


class CapFriendlyPlayersSource:
    def __init__(self, season):
        self.season = season

    def load(self, player_type):
        with open(f"data/cap_friendly/{player_type}_{self.season}.json") as f:
            players = json.load(f)
            df = (
                pd.DataFrame(players, columns=["name", "games_played", "cap_hit"])
                # Players that sign contracts after the beginning of the season appear
                # twice in the cap friendly list. Let's just drop the duplicates.
                # An alternative (read: better but more complicated) strategy would be
                # to figure out which cap_hit is actually taken into account by hockey
                # pools and use that.
                .drop_duplicates(subset="name", keep="first")
            )

            return massage_players(df)

    def write(self, players, player_type):
        with open(
            f"../data/cap_friendly/{player_type}_{self.season}.json", "w"
        ) as outfile:
            outfile.write(
                json.dumps(players, separators=(",", ":"), ensure_ascii=False)
            )

    def crawl(self, player_type):
        players = []
        for page in range(1, 20):
            url = self.build_url(player_type, page)
            print(url)
            response = requests.request("GET", url)

            data = response.json()["data"]
            results = data["results"]
            pagination = data["pagination"]
            limit = int(re.search(r"Page\s\d+\sof\s(\d+)", pagination).group(1))

            soup = BeautifulSoup(results, "html.parser")

            rows = soup.find("tbody").find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                name = cols[0].find("a").text.strip()
                games_played = (
                    int(cols[1].text.strip()) if cols[1].text.strip() != "-" else 0
                )
                goals = int(cols[2].text.strip()) if cols[2].text.strip() != "-" else 0
                assists = (
                    int(cols[3].text.strip()) if cols[3].text.strip() != "-" else 0
                )
                wins = int(cols[10].text.strip()) if cols[10].text.strip() != "-" else 0
                losses = (
                    int(cols[11].text.strip()) if cols[11].text.strip() != "-" else 0
                )
                shutouts = (
                    int(cols[12].text.strip()) if cols[12].text.strip() != "-" else 0
                )
                save_percentage = (
                    int(float(cols[14].text.strip()) * 1000)
                    if cols[14].text.strip() != "-"
                    else 0
                )

                cap_hit = int(Decimal(sub(r"[^\d.]", "", cols[15].text.strip())))

                players.append(
                    {
                        "name": name,
                        "games_played": games_played,
                        "goals": goals,
                        "assists": assists,
                        "cap_hit": cap_hit,
                        "type": player_type_map[player_type],
                        "wins": wins,
                        "losses": losses,
                        "save_percentage": save_percentage,
                        "shutouts": shutouts,
                    }
                )

            print(f"crawled {page}/{limit}")

        return players

    def build_url(self, player_type, page):
        return (
            f"https://www.capfriendly.com/ajax/browse/active/{self.season}/caphit/all/{player_type}"
            f"?stats-season={self.season}"
            "&hide=team,clauses,age,position,handed,expiry-status,salary"
            f"&pg={page}"
        )


def main():
    for season in [2024]:
        source = CapFriendlyPlayersSource(season)
        for player_type in ["forwards", "defense", "goalies"]:
            players = source.crawl(player_type)

            # TODO(nico): Handle players considered forwards by hockey-reference but
            #  defenders by cap friendly:
            #  ['Mason Geertsen', 'Hunter Drew', 'Luke Witkowski']

            source.write(players, player_type_map[player_type])

    print("done!")


if __name__ == "__main__":
    main()
