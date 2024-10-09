import re

from bs4 import BeautifulSoup

from hockey_pool_picker import ndjson
from hockey_pool_picker.crawl_cache import session
from hockey_pool_picker.season import Season

player_type_map = {
    "C": "forward",
    "AG": "forward",
    "AD": "forward",
    "D": "defender",
    "G": "goalie",
}


class MarqueurCapHitSource:
    def __init__(self, season: Season):
        self.season = season

    def load(self, player_type):
        players = ndjson.read_to_df(f"marqueur/{self.season}.ndjson")

        df = players[players["type"] == player_type]
        assert not df.empty, f"No players of type {player_type} found for season {self.season}"
        return df

    def crawl(self):
        # 165 is the 2023-2024 season
        adjustment = 2023 - 165
        url = f"https://www.marqueur.com/hockey/stats/nhl/salaries.php?a={self.season.start - adjustment}&e=0&p=0&o=0"
        response = session.request("GET", url)

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.select_one('body > div.w3-main > div.pl15.pr15.pb20 > div > div.p20 > table')
        players = []
        for i, row in enumerate(table.find_all('tr')):
            if i <= 1:
                # skip the first 2 header rows
                continue
            cells = row.find_all('td')
            row_data = {}
            for j, cell in enumerate(cells):
                if j == 0:
                    row_data['name'] = cell.find('a').text
                    position = re.findall(r'\((.*?)\)', cell.text)[0]
                    row_data['type'] = player_type_map[position]
                # the row has a varying number of td items for some reason... instead of plucking the
                # cap hit by position, we just pick the last td, which always contains the cap hit.
                elif j == len(cells) - 1:
                    row_data['cap_hit'] = int(cell.text.replace(' ', '').strip())

            players.append(row_data)

        ndjson.write(f"marqueur/{self.season}.ndjson", players)
