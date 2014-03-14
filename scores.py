from decimal import Decimal as D
import glob
import os
import ranker
from scorer import Scorer
import sys
import yaml

try:
    from yaml import CLoader as YAML_Loader
except ImportError:
    from yaml import Loader as YAML_Loader

class InvalidTeam(Exception):
    pass

class DuplicateScoresheet(Exception):
    pass

class LeagueScores(object):
    def __init__(self, resultdir, teams):
        self.resultdir = resultdir

        # Game points in each match
        # keys are (arena_id, match_num) tuples
        self.game_points = {}

        # League points in each match
        # keys are (arena_id, match_num) tuples
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
                self.teams[tla] += D(score)

    def _load_resfile(self, fname):
        with open(fname, "r") as f:
            y = yaml.load(f, Loader = YAML_Loader)

        match_id = (y["arena_id"], y["match_number"])
        if match_id in self.game_points:
            raise DuplicateScoresheet()

        game_points = Scorer(y["teams"]).calculate_scores()
        self.game_points[match_id] = game_points

        # Build the disqualification dict
        dsq = []
        for tla, scoreinfo in y["teams"].iteritems():
            if "disqualified" in scoreinfo and scoreinfo["disqualified"]:
                dsq.append(tla)

        league_points = ranker.get_ranked_points(game_points, dsq)
        self.match_league_points[match_id] = league_points

class Scores(object):
    def __init__(self, resultdir, teams):
        self.resultdir = resultdir
        self.league = LeagueScores(resultdir, teams)


