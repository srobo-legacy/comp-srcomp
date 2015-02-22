
from collections import OrderedDict
from functools import total_ordering
import glob
import os

from sr.comp import ranker
from . import yaml_loader


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


@total_ordering
class TeamScore(object):
    def __init__(self, league=0, game=0):
        self.league_points = league
        self.game_points = game

    @property
    def _ordering_key(self):
        # Sort lexicographically by league points, then game points
        return self.league_points, self.game_points

    def __eq__(self, other):
        return (isinstance(other, type(self)) and
                self._ordering_key == other._ordering_key)

    # total_ordering doesn't provide this!
    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            # TeamScores are greater than other things (that have no score)
            return False
        return self._ordering_key < other._ordering_key

    def __repr__(self):
        return "TeamScore({0}, {1})".format(self.league_points,
                                            self.game_points)


def results_finder(root):
    for dname in glob.glob(os.path.join(root, "*")):
        if not os.path.isdir(dname):
            continue

        for resfile in glob.glob(os.path.join(dname, "*.yaml")):
            yield resfile


# The scorer that these classes consume should be a class that:
# * accepts a dictionary equivalent to value of the 'teams' key from a Proton
#   compatible input as its only constructor argument.
# * has a 'calculate_scores' method which returns a dictionary of TLAs (ie
#   the same keys as the input) to the numeric scores for each team.
#
# Proton refers to [Proton 1.0.0-rc2](https://github.com/samphippen/proton)
class BaseScores(object):
    def __init__(self, resultdir, teams, scorer):
        self._scorer = scorer

        # Game points in each match
        # keys are (arena_id, match_num) tuples
        self.game_points = {}

        # Positions in each match
        # keys are (arena_id, match_num) tuples
        self.game_positions = {}

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

        # Sum the game for each team
        for match in self.game_points.values():
            for tla, score in match.items():
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
        for tla, scoreinfo in y["teams"].items():
            # disqualifications and non-presence are effectively the same
            # in terms of league points awarding.
            if (scoreinfo.get("disqualified", False) or
               not scoreinfo.get("present", True)):
                dsq.append(tla)

        positions = ranker.calc_positions(game_points, dsq)
        self.game_positions[match_id] = positions
        self.ranked_points[match_id] = ranker.calc_ranked_points(positions, dsq)

    @property
    def last_scored_match(self):
        """The most match with the highest id for which we have score data"""
        if len(self.ranked_points) == 0:
            return None
        matches = self.ranked_points.keys()
        return max(num for arena, num in matches)


class LeagueScores(BaseScores):
    @staticmethod
    def rank_league(team_scores):
        """Given a mapping of TLA to TeamScore, returns a mapping of TLA
           to league position which both allows for ties and enables their
           resolution deterministically."""

        # Reverse sort the (tla, score) pairs so the biggest scores are at the
        # top. We break perfect ties by TLA, which is not fair but is
        # deterministic.
        # Note that the unfair result is only present within the key ordering
        # of the resulting OrderedDict -- the values it contains will admit
        # to tied values.
        # Both of these are used within the system -- the knockouts need
        # a list of teams to seed with, various awards (and humans) want
        # a result which allows for ties.
        ranking = sorted(team_scores.items(),
                         key=lambda x: (x[1], x[0]),
                         reverse=True)
        positions = OrderedDict()
        pos = 1
        last_score = None
        for i, (tla, score) in enumerate(ranking, start=1):
            if score != last_score:
                pos = i
            positions[tla] = pos
            last_score = score
        return positions

    def __init__(self, resultdir, teams, scorer):
        super(LeagueScores, self).__init__(resultdir, teams, scorer)

        # Sum the league scores for each team
        for match in self.ranked_points.values():
            for tla, score in match.items():
                if tla not in self.teams:
                    raise InvalidTeam(tla)
                self.teams[tla].league_points += score

        self.positions = self.rank_league(self.teams)


class KnockoutScores(BaseScores):
    pass


class Scores(object):
    def __init__(self, root, teams, scorer):
        self.root = root
        self.league = LeagueScores(os.path.join(root, "league"),
                                   teams, scorer)
        self.knockout = KnockoutScores(os.path.join(root, "knockout"),
                                       teams, scorer)

        lsm = self.knockout.last_scored_match
        if lsm is None:
            lsm = self.league.last_scored_match

        self.last_scored_match = lsm
