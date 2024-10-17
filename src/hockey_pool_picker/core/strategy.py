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

    def expect_columns(self, df, player_type, columns):
        for column in columns:
            if column not in df.columns:
                raise ValueError(
                    f"{column} is required for {player_type} for {self.__class__.__name__}"
                )


class MarqueurValueStrategy(ValueStrategy):
    def forward(self, player):
        self.expect_columns(player, "forward", ["goals", "assists"])
        return (player["goals"] * 2) + player["assists"]

    def defender(self, player):
        self.expect_columns(player, "defender", ["goals", "assists"])
        return (player["goals"] * 3) + (player["assists"] * 2)

    def goalie(self, player):
        self.expect_columns(player, "goalie", ["wins", "shutouts", "goals", "assists"])
        return (
            player["wins"] * 3
            + (player["shutouts"] * 5)
            + (player["goals"] * 5)
            + (player["assists"] * 2)
        )


class MarqueurWithDoubledDefendersStrategy(MarqueurValueStrategy):
    def defender(self, player):
        self.expect_columns(player, "defender", ["goals", "assists"])
        return ((player["goals"] * 3) + (player["assists"] * 2)) * 2


class MoneyballStrategy(MarqueurValueStrategy):
    def forward(self, player):
        self.expect_columns(player, "forward", ["assists"])
        return player["assists"]

    def defender(self, player):
        self.expect_columns(player, "defender", ["assists"])
        return player["assists"]

    def goalie(self, player):
        self.expect_columns(player, "goalie", ["saves_percent"])
        return (player["saves_percent"] * 1000).astype(
            "int32"
        )  # TODO(nico): why int32?


class MarqueurMinusGamblingValueStrategy(MarqueurValueStrategy):
    def goalie(self, player):
        self.expect_columns(player, "goalie", ["wins", "shutouts"])
        return (player["wins"] * 2) + (player["shutouts"] * 3)


class MarqueurWithPercentageStrategy(ValueStrategy):
    def __init__(self, minimum_games=52):
        super().__init__()
        self.minimum_games = minimum_games

    def forward(self, player):
        self.expect_columns(player, "forward", ["goals", "assists"])
        points = (player["goals"] * 2) + player["assists"]
        # This is definitely not the best way to normalize the forward/defender data with goalies
        return (points / 250) * 1000

    def defender(self, player):
        self.expect_columns(player, "defender", ["goals", "assists"])
        points = (player["goals"] * 3) + (player["assists"] * 2)
        return (points / 250) * 1000

    def goalie(self, player):
        self.expect_columns(player, "goalie", ["games_played", "saves_percent"])
        return np.where(
            player["games_played"] < self.minimum_games,
            0,
            (player["saves_percent"] * 1000).astype("int32"),
        )


STRATEGIES = {
    "marqueur": MarqueurValueStrategy,
    "marqueur_doubled_defenders": MarqueurWithDoubledDefendersStrategy,
    "marqueur_minus_gambling": MarqueurMinusGamblingValueStrategy,
    "marqueur_with_percentage": MarqueurWithPercentageStrategy,
    "moneyball": MoneyballStrategy,
}
