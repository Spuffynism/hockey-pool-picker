from hockey_pool_picker.util import (
    inner_merge_dropping_duplicates,
    PLAYER_TYPES,
)
from hockey_pool_picker.core.season import Season
from hockey_pool_picker.sources.puckpedia import PuckpediaStatsAndCapHitSource


class BacktestingSource:
    def __init__(self, past_season: Season, source):
        self.past_season = past_season
        self.source = source

    def load(self, picking_strategy, evaluation_strategy):
        past_pool = []
        present_pool = []
        for player_type in PLAYER_TYPES:
            past_season_df = self.source(self.past_season).load(player_type)
            present_season_df = self.source(self.past_season.next()).load(player_type)

            # as the puckpedia source provides both stats and cap hits, we don't need to join separate sources
            if self.source == PuckpediaStatsAndCapHitSource:
                (past_players, present_players) = self._keep_intersection(
                    past_season_df, present_season_df, "p_id"
                )
            else:
                (past_players, present_players) = self._keep_intersection(
                    past_season_df, present_season_df
                )
                for a, b in zip(
                    past_players["normalized_name"].to_list(),
                    present_players["normalized_name"].to_list(),
                ):
                    assert (
                        a == b
                    ), f"Names of type {player_type} do not match {a} != {b}"

                if not past_players["normalized_name"].equals(
                    present_players["normalized_name"]
                ):
                    raise Exception(f"{player_type} do not match!")

            past_players["value"] = picking_strategy.apply(past_players, player_type)
            # to ensure we have a pool valid for next year, we use players' next year
            # cap hit as weight.
            past_players["weight"] = present_players["cap_hit"]

            present_players["value"] = evaluation_strategy.apply(
                present_players, player_type
            )
            present_players["weight"] = present_players["cap_hit"]

            past_pool.append(past_players)
            present_pool.append(present_players)

        return past_pool, present_pool

    def _keep_intersection(self, past, present, column="normalized_name"):
        # TODO(nico): List who we're dropping
        intersection = inner_merge_dropping_duplicates(past, present, column)

        return self.intersect(past, intersection, column).reset_index(
            drop=True
        ), self.intersect(present, intersection, column).reset_index(drop=True)

    def intersect(self, players, intersection, column):
        return players[players[column].isin(intersection[column])].sort_values(column)
