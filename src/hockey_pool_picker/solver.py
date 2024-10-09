import pandas as pd
from ortools.sat.python import cp_model


class Solution:
    def __init__(self, picks, pick_indices=[]):
        self.forwards_group = Solution._build_group(picks[0], "forwards")
        self.defenders_group = Solution._build_group(picks[1], "defenders")
        self.goalies_group = Solution._build_group(picks[2], "goalies")

        self.pick_indices = pick_indices

    def picks(self):
        return [
            group["players"]
            for group in [self.forwards_group, self.defenders_group, self.goalies_group]
        ]

    @staticmethod
    def _build_group(players, name):
        return {
            "name": name,
            "players": players,
            "weight": sum(player["weight"] for player in players),
            "value": sum(player["value"] for player in players),
        }

    def print(self):
        df = pd.DataFrame(
            self.forwards_group["players"]
            + self.defenders_group["players"]
            + self.goalies_group["players"]
        )
        #print(df[df.columns[~df.columns.isin([ID_COLUMN])]].to_string())

        print(self._build_summary().to_string(index=False))

    def summary(self):
        summary_df = self._build_summary()
        return summary_df.loc[summary_df["name"] == "total"][["weight", "value"]]

    def print_summary(self):
        print(self.summary().to_string(index=False))

    def _build_summary(self):
        groups = [self.forwards_group, self.defenders_group, self.goalies_group]

        summary_df = pd.DataFrame(
            [[group["name"], group["weight"], group["value"]] for group in groups],
            columns=["name", "weight", "value"],
        )
        summary_df.loc[len(summary_df)] = [
            "total",
            summary_df["weight"].sum(),
            summary_df["value"].sum(),
        ]

        return summary_df

    def print_differences(self, after):
        removed = []
        added = []
        for before_group, after_group in zip(self.picks(), after.picks()):
            after_names = set([player["name"] for player in after_group])
            before_names = set([player["name"] for player in before_group])

            removed += [
                player for player in before_group if player["name"] not in after_names
            ]
            added += [
                player for player in after_group if player["name"] not in before_names
            ]

        for player in removed:
            print(
                f"\033[31m- {player['name']} {player['weight']} {player['value']}"
                f"\033[39m"
            )

        for player in added:
            print(
                f"\033[32m+ {player['name']} {player['weight']} {player['value']}"
                f"\033[39m"
            )


FORWARDS_COUNT = 12
DEFENDERS_COUNT = 6
GOALIES_COUNT = 2
PICKS_COUNT = [FORWARDS_COUNT, DEFENDERS_COUNT, GOALIES_COUNT]


class CPSATSolver:
    def __init__(self):
        self._reset()

    def _reset(self):
        self.model = cp_model.CpModel()
        self.solution = None

    def pick_pool(self, pool, salary_cap):
        self._reset()

        x = self._constrain_team_structure(pool, salary_cap)
        self._maximize(x, pool)
        self._solve(x, pool)

        return self.solution

    def _constrain_team_structure(self, pool, salary_cap):
        players_count = [len(group) for group in pool]

        x = {}
        for j, players in enumerate(players_count):
            for i in range(players):
                # x[i, j] = 1 if player is picked
                x[i, j] = self.model.NewBoolVar(f"x_{i}_{j}")

        for j, (players, count) in enumerate(zip(players_count, PICKS_COUNT)):
            # we must have the exact player count
            self.model.Add(
                cp_model.LinearExpr.Sum([x[i, j] for i in range(players)]) == count
            )

        self.model.Add(
            cp_model.LinearExpr.Sum(
                [
                    x[i, j] * pool[j][i]["weight"]
                    for j in range(len(players_count))
                    for i in range(players_count[j])
                ]
            )
            <= salary_cap
        )

        return x

    def pick_trades(self, solution, pool, salary_cap, trades_count):
        self._reset()

        x = self._constrain_team_structure(pool, salary_cap)

        # we want to keep at least count(picks) - trades_count
        picks = []
        for i, group in enumerate(solution.pick_indices):
            picks += [x[j, i] for j in group]

        self.model.Add(
            cp_model.LinearExpr.Sum(picks)
            >= cp_model.LinearExpr.Sum(PICKS_COUNT) - trades_count
        )

        self._maximize(x, pool)
        self._solve(x, pool)

        return self.solution

    def _maximize(self, x, pool):
        expressions = []
        coefficients = []
        for j, players in enumerate(pool):
            for i in range(len(players)):
                expressions.append(x[i, j])
                coefficients.append(players[i]["value"])

        self.model.Maximize(cp_model.LinearExpr.WeightedSum(expressions, coefficients))

    def _solve(self, x, pool):
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status != cp_model.OPTIMAL:
            raise "No optimal solution."

        picks = [[], [], []]
        pick_indices = [[], [], []]
        for j, players in enumerate(pool):
            for i in range(len(players)):
                if solver.BooleanValue(x[i, j]):
                    picks[j].append(players[i])
                    pick_indices[j].append(i)

        self.solution = Solution(picks, pick_indices)

    def translate_to_data(self, players):
        picks = [[], [], []]
        pick_indices = [[], [], []]
        for i, (picked_players, players) in enumerate(
            zip(self.solution.picks(), players)
        ):
            for picked_player in picked_players:
                for j, player in players.iterrows():
                    if picked_player["name"] == player["name"]:
                        picks[i].append(player)
                        pick_indices[i].append(j)
                        break

        return Solution(picks, pick_indices)
