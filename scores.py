
from decimal import Decimal as D
import glob
import os
import sys

import ranker
from scorer import Scorer
import yaml_loader

class InvalidTeam(Exception):
    pass

class DuplicateScoresheet(Exception):
    pass

class TeamScore(object):
    def __init__(self, league = 0, game = 0):
        self.league_points = D(league)
        self.game_points = game

    def __eq__(self, other):
        return isinstance(other, TeamScore) and \
                other.league_points == self.league_points and \
                other.game_points == self.game_points

    def __repr__(self):
        return "TeamScore({0}, {1})".format(self.league_points, self.game_points)

def results_finder(root):
    for dname in glob.glob(os.path.join(root, "*")):
        if not os.path.isdir(dname):
            continue

        for resfile in glob.glob(os.path.join(dname, "*.yaml")):
            yield resfile

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
        for tla in teams:
            self.teams[tla] = TeamScore()

        # Find the scores for each match
        for resfile in results_finder(resultdir):
            self._load_resfile(resfile)

        # Sum the league scores for each team
        for match in self.match_league_points.values():
            for tla, score in match.iteritems():
                if tla not in self.teams:
                    raise InvalidTeam()
                self.teams[tla].league_points += D(score)

        # Sum the game for each team
        for match in self.game_points.values():
            for tla, score in match.iteritems():
                if tla not in self.teams:
                    raise InvalidTeam()
                self.teams[tla].game_points += score

    def _load_resfile(self, fname):
        y = yaml_loader.load(fname)

        match_id = (y["arena_id"], y["match_number"])
        if match_id in self.game_points:
            raise DuplicateScoresheet()

        game_points = Scorer(y["teams"]).calculate_scores()
        self.game_points[match_id] = game_points

        # Build the disqualification dict
        dsq = []
        for tla, scoreinfo in y["teams"].iteritems():
            # disqualifications and non-presence are effectively the same
            # in terms of league points awarding.
            if scoreinfo.get("disqualified", False) or \
                not scoreinfo.get("present", True):
                dsq.append(tla)

        league_points = ranker.get_ranked_points(game_points, dsq)
        self.match_league_points[match_id] = league_points

    @property
    def last_scored_match(self):
        """The most match with the highest id for which we have score data"""
        if len(self.match_league_points) == 0:
            return None
        matches = self.match_league_points.keys()
        return max(num for arena, num in matches)

class KnockoutScores(object):
    def __init__(self, resultdir):
        # Game points in each match
        # keys are (arena_id, match_num) tuples
        self.game_points = {}

        # Ranked points in each match
        # keys are (arena_id, match_num) tuples
        self.ranked_points = {}

        # Find the scores for each match
        for resfile in results_finder(resultdir):
            self._load_resfile(resfile)

    def _load_resfile(self, fname):
        y = yaml_loader.load(fname)

        match_id = (y["arena_id"], y["match_number"])
        if match_id in self.game_points:
            raise DuplicateScoresheet()

        game_points = Scorer(y["teams"]).calculate_scores()
        self.game_points[match_id] = game_points

        # Build the disqualification dict
        dsq = []
        for tla, scoreinfo in y["teams"].iteritems():
            # disqualifications and non-presence are effectively the same
            # in terms of league points awarding.
            if scoreinfo.get("disqualified", False) or \
                not scoreinfo.get("present", True):
                dsq.append(tla)

        self.ranked_points[match_id] = ranker.get_ranked_points(game_points, dsq)

class Scores(object):
    def __init__(self, root, teams):
        self.root = root
        self.league = LeagueScores(os.path.join(root, "league"), teams)
        self.knockout = KnockoutScores(os.path.join(root, "knockout"))
