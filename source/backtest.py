from source.common import inner_merge_dropping_duplicates, PLAYER_TYPES
from source.complete import PlayersSource


class BacktestingSource:
    def __init__(self, past_season):
        self.past = PlayersSource(past_season)
        self.present = PlayersSource(past_season + 1)

    def load(self, picking_strategy, evaluation_strategy):
        past_pool = []
        present_pool = []
        for player_type in PLAYER_TYPES:
            (past_players, present_players) = self._keep_intersection(
                self.past.load(player_type), self.present.load(player_type)
            )

            for a, b in zip(
                past_players["normalized_name"].to_list(),
                present_players["normalized_name"].to_list(),
            ):
                if a != b:
                    raise Exception(f"Names do not match {a} != {b}")

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

    def _keep_intersection(self, past, present):
        # TODO(nico): List who we're dropping
        intersection = inner_merge_dropping_duplicates(past, present, "normalized_name")

        return self.intersect(past, intersection).reset_index(
            drop=True
        ), self.intersect(present, intersection).reset_index(drop=True)

    def intersect(self, players, intersection):
        return players[
            players["normalized_name"].isin(intersection["normalized_name"])
        ].sort_values("normalized_name")
