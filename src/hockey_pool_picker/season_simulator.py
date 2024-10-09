import calendar
from collections import defaultdict
from datetime import datetime
from statistics import mean

from dateutil.relativedelta import relativedelta
from prompt_toolkit.win32_types import SMALL_RECT

from hockey_pool_picker.season import Season
from hockey_pool_picker.solver import Solution
from hockey_pool_picker.common import PLAYER_TYPES
from hockey_pool_picker.sources.hockey_reference_games import HockeyReferenceGamesSource


def evaluate_period(players_over_period, solution, evaluation_strategy):
    picks = []
    for i, player_type in enumerate(PLAYER_TYPES):
        group = players_over_period[i]
        group["value"] = evaluation_strategy.apply(group, player_type)
        names = [player["name"] for player in solution.picks()[i]]
        picked_players = group[group["name"].isin(names)]

        picks.append(picked_players)

    # We should list % increase/decrease of choices
    # Maybe when passing our players to the trading algo, we should only pass players
    # for the last month, instead of for the whole season
    summary = Solution([group.to_dict("records") for group in picks]).summary()
    return summary.iloc[-1]["value"]


def get_month_period(season: Season, month, days=0):
    start = datetime(season.start, month, 1) + relativedelta(days=days)

    last_day_of_month = calendar.monthrange(season.start, month)[1]
    end = datetime(season.start, month, last_day_of_month, 23, 59, 59, 999999)

    return start, end


class SeasonSimulator:
    def __init__(
        self,
        solver,
        season: Season,
        present_pool,
        salary_cap,
        evaluation_strategy,
        picking_strategy,
    ):
        self.solver = solver
        self.season = season
        self.present_pool = present_pool
        self.salary_cap = salary_cap
        self.evaluation_strategy = evaluation_strategy
        self.picking_strategy = picking_strategy

    def progress(self, solution):
        # TODO(nico): Revisit this amazingly beautiful logic 😇
        # regular season is from October 7, 2022, and ended April 14, 2023.
        games = HockeyReferenceGamesSource(self.season).load()
        periods = [
            (self.season, 10),
            (self.season, 11),
            (self.season, 12),
            (self.season.next(), 1),
            (self.season.next(), 2),
            (self.season.next(), 3),
            (self.season.next(), 4),
        ]
        total_value = 0
        for period_season, period_month in periods:
            start_look, end_look = get_month_period(period_season, period_month, days=-7)
            start_pts, end_pts = get_month_period(period_season, period_month)

            # - we could pick only players that have increased in the past 2-3 periods,
            # instead of checking only last period
            # - we could remove players that get hurt as they get hurt
            look_games_for_period = games[
                (start_look <= games["date"]) & (games["date"] <= end_look)
            ]
            pts_games_for_period = games[
                (start_pts <= games["date"]) & (games["date"] <= end_pts)
            ]

            pts_players_over_period = []
            look_players_over_period = []
            for i, player_type in enumerate(PLAYER_TYPES):
                pts_players_over_period.append(
                    self.player_stats_for_games(
                        self.present_pool[i].copy(),
                        pts_games_for_period.copy(),
                        player_type,
                        self.picking_strategy,
                    )
                )
                look_players_over_period.append(
                    self.player_stats_for_games(
                        self.present_pool[i].copy(),
                        look_games_for_period.copy(),
                        player_type,
                        self.picking_strategy,
                    )
                )

            value = evaluate_period(
                pts_players_over_period, solution, self.evaluation_strategy
            )
            total_value += value

            if (period_season, period_month) == periods[-1]:
                print(
                    f'Looking from {start_look.strftime("%b %d, %Y")} to '
                    f'{end_look.strftime("%b %d, %Y")}'
                )
                print(f'{start_pts.strftime("%B %Y")}: {value}')
                print("\n")
                # last period, we don't pick trades
                break

            new_solution = self.solver.pick_trades(
                solution,
                [group.to_dict("records") for group in look_players_over_period],
                self.salary_cap,
                5,
            )

            print(
                f'Looking from {start_look.strftime("%B %Y %d")} to '
                f'{end_look.strftime("%B %Y %d")}'
            )
            print(f'{start_pts.strftime("%B %Y")}: {value}')
            solution.print_differences(new_solution)
            print()

            solution = new_solution

        print(f"Total value: {total_value} ({2626 - total_value} to go)")
        return solution

    def player_stats_for_games(self, players, games, player_type, strategy):
        goals = defaultdict(int)
        assists = defaultdict(int)
        saves = defaultdict(int)
        saves_percent = defaultdict(list)
        wins = defaultdict(int)
        shutouts = defaultdict(int)
        games_played = defaultdict(int)

        for _, game in games.iterrows():
            for score in game.scores:
                for assist in score["assists"]:
                    assists[assist] += 1

                goals[score["scorer"]] += 1

            for goalie in game.goalies:
                games_played[goalie["name"]] += 1
                saves[goalie["name"]] += goalie["saves"]

                if goalie["saves_percent"] is not None:
                    saves_percent[goalie["name"]].append(goalie["saves_percent"])

                if "decision" in goalie and goalie["decision"] == "W":
                    # TODO(nico): It isn't clear if we should double-count shutouts and
                    #  wins. Right now, we do.
                    wins[goalie["name"]] += 1
                    if goalie["shutout"]:
                        shutouts[goalie["name"]] += 1

        for i, player in players.iterrows():
            players.at[i, "goals"] = goals[player["name"]]
            players.at[i, "assists"] = assists[player["name"]]

            if player_type == "goalie":
                players.at[i, "assists"] = assists[player["name"]]
                players.at[i, "wins"] = wins[player["name"]]
                players.at[i, "shutouts"] = shutouts[player["name"]]
                players.at[i, "games_played"] = games_played[player["name"]]
                players.at[i, "saves_percent"] = (
                    mean(saves_percent[player["name"]])
                    if player["name"] in saves_percent
                    else 0
                )

        players["value"] = strategy.apply(players, player_type)

        return players
