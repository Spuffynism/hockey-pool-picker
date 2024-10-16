from hockey_pool_picker.core.season import Season
from hockey_pool_picker.sources.puckpedia import PuckpediaStatsAndCapHitSource


# Since the PuckPediaCapHitSource was populated by hand, we define a few tests that
# ensure the data is properly loaded and populated.


def test_2022():
    source = PuckpediaStatsAndCapHitSource(Season(start=2022))
    players = source.load("forward")

    player = players[players["p_url"] == "connor-mcdavid"].iloc[0]
    assert player["name"] == "Connor McDavid"
    assert player["pos"] == "C"
    assert player["cap_hit"] == 12_500_000

    player = players[players["p_url"] == "alex-chiasson"].iloc[0]
    assert player["name"] == "Alex Chiasson"
    assert player["pos"] == "R"
    assert player["cap_hit"] == 750_000
