import json
from datetime import datetime, timedelta
from time import sleep
import pandas as pd

from bs4 import BeautifulSoup
from pandas import read_json

from hockey_pool_picker import ndjson
from hockey_pool_picker.crawl_cache import session
from hockey_pool_picker.season import Season

CRAWL_DELAY = timedelta(seconds=3)

player_positions = {
    "forward": ["C", "LW", "RW", "F", "W"],
    "defender": ["D"],
    "goalie": ["G"],
}


class HockeyReferenceGamesSource:
    def __init__(self, season: Season):
        self.season = season

    def load(self):
        games = ndjson.read_to_df(self.file_name())
        games["date"] = pd.to_datetime(games["date"])

        return games

    def file_name(self):
        return f"hockey_reference/games_{self.season}.ndjson"

    def crawl(self):
        prefix = "https://www.hockey-reference.com"
        response = session.get(f"{prefix}/leagues/NHL_{self.season.end}_games.html")

        soup = BeautifulSoup(response.content, "html.parser")

        games = []
        game_rows = soup.find(id="games").find("tbody").find_all("tr")
        for i, game_row in enumerate(game_rows):
            link = game_row.find("th").find("a")
            full_link = f"{prefix}{link['href']}"

            percent_progress = round((i + 1) / len(game_rows) * 100, 2)
            print(
                f"\r({percent_progress:.2f}%) {i + 1}/{len(game_rows)}: {full_link}",
                end="",
            )

            date, scores, goalies, from_cache = self._crawl_game(full_link)

            games.append({"date": date, "scores": scores, "goalies": goalies})

            if not from_cache:
                sleep(CRAWL_DELAY.seconds)

        ndjson.write(self.file_name(), games)

    def _crawl_game(self, link):
        response = session.get(link)

        if response.status_code != 200:
            raise Exception(f"Failed to crawl game {link}", response)

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
                    continue

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

        return date, scores, goalies, response.from_cache
