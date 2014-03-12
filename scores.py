from decimal import Decimal as D
import glob
import os
from scorer import Scorer
import sys
import yaml

try:
    from yaml import CLoader as YAML_Loader
except ImportError:
    from yaml import Loader as YAML_Loader

class InvalidTeam(Exception):
    pass

class LeagueScores(object):
    def __init__(self, resultdir, teams):
        self.resultdir = resultdir

        # Game points in each match
        # keys are match numbers
        self.matches = {}

        # League points in each match
        # keys are match numbers
        self.match_league_points = {}

        # League points for each team
        # keys are team tlas
        self.teams = {}

        # Start with 0 points for each team
        for tla in teams.keys():
            self.teams[tla] = D(0)

        # Find the scores for each match
        for resfile in glob.glob( os.path.join( resultdir, "*.yaml" ) ):
            self._load_resfile( resfile )

        # Sum the scores for each team
        for match in self.match_league_points.values():
            for tla, score in match.iteritems():

                if tla not in self.teams:
                    raise InvalidTeam()

                self.teams[tla] += score
            self.teams

    def _load_resfile(self, fname):
        with open(fname, "r") as f:
            y = yaml.load(f, Loader = YAML_Loader)

        game_points = Scorer(y["teams"]).calculate_scores()
        match_num = y["match_number"]

        self.matches[match_num] = game_points
        self.match_league_points[match_num] = self._league_points(game_points)

    def _league_points(self, game_points):
        "Find the league points given these game_points"

        # TODO: Deal with disqualifications and absences
        p = {}
        for tla, game_score in game_points.iteritems():
            # TODO: Do this properly
            p[tla] = game_score

        return p


class Scores(object):
    def __init__(self, resultdir, teams):
        self.resultdir = resultdir
        self.league = LeagueScores(resultdir, teams)


