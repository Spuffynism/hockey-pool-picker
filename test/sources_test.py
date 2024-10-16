from hockey_pool_picker.sources.games.hockey_reference import HockeyReferenceGamesSource
from hockey_pool_picker.sources.stats.hockey_reference import (
    HockeyReferencePlayersSource,
)
from hockey_pool_picker.sources.cap_hit.marqueur import MarqueurCapHitSource
from hockey_pool_picker.sources.players import PlayersSource
from hockey_pool_picker.core.season import Season


seasons = [Season(start=year) for year in range(2020, 2024)]


def test_load_player_source():
    for season in seasons:
        source = PlayersSource(season)
        for player_type in ["goalie", "forward", "defender"]:
            dataframe = source.load(player_type)
            assert len(dataframe) > 0
            assert {"value", "weight"}.issubset(set(list(dataframe.columns)))


def test_load_hockey_reference_players():
    for season in seasons:
        source = HockeyReferencePlayersSource(season)
        for player_type in ["goalie", "forward", "defender"]:
            dataframe = source.load(player_type)
            assert len(dataframe) > 0


def test_load_hockey_reference_games():
    for season in seasons:
        source = HockeyReferenceGamesSource(season)
        dataframe = source.load()
        assert len(dataframe) > 0
        assert list(dataframe.columns) == ["date", "scores", "goalies"]


def test_load_marqueur():
    for season in seasons:
        source = MarqueurCapHitSource(season)
        for player_type in ["goalie", "forward", "defender"]:
            dataframe = source.load(player_type)
            assert len(dataframe) > 0
            assert list(dataframe.columns) == ["name", "type", "cap_hit"]
