from hockey_pool_picker.sources.hockey_reference_games import HockeyReferenceGamesSource
from hockey_pool_picker.sources.hockey_reference_players import HockeyReferencePlayersSource
from hockey_pool_picker.sources.marqueur_cap_hit import MarqueurCapHitSource
from hockey_pool_picker.sources.players import PlayersSource
from hockey_pool_picker.season import Season


seasons = [Season(start=year) for year in range(2020, 2024)]

def test_load_player_source():
    for season in seasons:
        source = PlayersSource(season)
        for player_type in ["goalie", "forward", "defender"]:
            first, second = source.load(player_type)
            assert len(first) > 0
            assert len(second) > 0


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


def test_load_marqueur():
    for season in seasons:
        source = MarqueurCapHitSource(season)
        for player_type in ["goalie", "forward", "defender"]:
            dataframe = source.load(player_type)
            assert len(dataframe) > 0
