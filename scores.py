
from decimal import Decimal as D
import glob
import os
import sys

import ranker
import yaml_loader

class InvalidTeam(Exception):
    def __init__(self, tla):
        message = "Team {0} does not exist.".format(tla)
        super(InvalidTeam, self).__init__(message)
        self.tla = tla

class DuplicateScoresheet(Exception):
    def __init__(self, match_id):
        message = "Scoresheet for {0} has already been added.".format(match_id)
        super(DuplicateScoresheet, self).__init__(message)
        self.match_id = match_id

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

'''
The scorer that these classes consume should be a class that:
* accepts a dictionary equivalent to value of the 'teams' key from a Proton
  compatible input as its only constructor argument.
* has a 'calculate_scores' method which returns a dictionary of TLAs (ie
  the same keys as the input) to the numeric scores for each team.

Proton refers to [Proton 1.0.0-rc2](https://github.com/samphippen/proton)
'''

class LeagueScores(object):
    def __init__(self, resultdir, teams, scorer):
        self._scorer = scorer

        # Game points in each match
        # keys are (arena_id, match_num) tuples
        self.game_points = {}

        # Ranked points in each match
        # keys are (arena_id, match_num) tuples
        self.ranked_points = {}

        # Points for each team (TeamScore objects)
        # keys are team tlas
        self.teams = {}

        # Start with 0 points for each team
        for tla in teams:
            self.teams[tla] = TeamScore()

        # Find the scores for each match
        for resfile in results_finder(resultdir):
            self._load_resfile(resfile)

        # Sum the league scores for each team
        for match in self.ranked_points.values():
            for tla, score in match.iteritems():
                if tla not in self.teams:
                    raise InvalidTeam(tla)
                self.teams[tla].league_points += D(score)

        # Sum the game for each team
        for match in self.game_points.values():
            for tla, score in match.iteritems():
                if tla not in self.teams:
                    raise InvalidTeam(tla)
                self.teams[tla].game_points += score

    def _load_resfile(self, fname):
        y = yaml_loader.load(fname)

        match_id = (y["arena_id"], y["match_number"])
        if match_id in self.game_points:
            raise DuplicateScoresheet(match_id)

        game_points = self._scorer(y["teams"]).calculate_scores()
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
        self.ranked_points[match_id] = league_points

    @property
    def last_scored_match(self):
        """The most match with the highest id for which we have score data"""
        if len(self.ranked_points) == 0:
            return None
        matches = self.ranked_points.keys()
        return max(num for arena, num in matches)

class KnockoutScores(object):
    def __init__(self, resultdir, scorer):
        self._scorer = scorer

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
            raise DuplicateScoresheet(match_id)

        game_points = self._scorer(y["teams"]).calculate_scores()
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
    def __init__(self, root, teams, scorer):
        self.root = root
        self.league = LeagueScores(os.path.join(root, "league"), teams, scorer)
        self.knockout = KnockoutScores(os.path.join(root, "knockout"), scorer)
