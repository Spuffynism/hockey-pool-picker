from abc import abstractmethod, ABC

import numpy as np


class ValueStrategy(ABC):
    def apply(self, player, player_type):
        return {
            "forward": self.forward,
            "defender": self.defender,
            "goalie": self.goalie,
        }[player_type](player)

    @abstractmethod
    def forward(self, player):
        pass

    @abstractmethod
    def defender(self, player):
        pass

    @abstractmethod
    def goalie(self, player):
        pass


class LaPresseValueStrategy(ValueStrategy):
    def forward(self, player):
        return (player["goals"] * 2) + player["assists"]

    def defender(self, player):
        return (player["goals"] * 3) + (player["assists"] * 2)

    def goalie(self, player):
        return (
            player["wins"] * 3
            + (player["shutouts"] * 5)
            + (player["goals"] * 5)
            + (player["assists"] * 2)
        )


class LaPresseWithDoubledDefendersStrategy(LaPresseValueStrategy):
    def defender(self, player):
        return ((player["goals"] * 3) + (player["assists"] * 2)) * 2


class MoneyballStrategy(LaPresseValueStrategy):
    def forward(self, player):
        return player["assists"]

    def defender(self, player):
        return player["assists"]

    def goalie(self, player):
        return (player["saves_percent"] * 1000).astype("int32")


class LaPresseMinusGamblingValueStrategy(LaPresseValueStrategy):
    def goalie(self, player):
        return (player["wins"] * 2) + (player["shutouts"] * 3)


class LaPresseWithPercentageStrategy(ValueStrategy):
    def __init__(self, minimum_games=52):
        super().__init__()
        self.minimum_games = minimum_games

    def forward(self, player):
        points = (player["goals"] * 2) + player["assists"]
        # I'm not sure if this is the best way to normalize the forward/defender data
        # with goalies
        return (points / 250) * 1000

    def defender(self, player):
        points = (player["goals"] * 3) + (player["assists"] * 2)
        return (points / 250) * 1000

    def goalie(self, player):
        return np.where(
            player["games_played"] < self.minimum_games,
            0,
            (player["saves_percent"] * 1000).astype("int32"),
        )
