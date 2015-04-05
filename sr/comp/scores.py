"""Utilities for working with scores."""

from collections import OrderedDict
from functools import total_ordering
import glob
import os

from sr.comp import ranker, yaml_loader


class InvalidTeam(Exception):
    """An exception that occurs when a score contains an invalid team."""

    def __init__(self, tla):
        message = "Team {0} does not exist.".format(tla)
        super(InvalidTeam, self).__init__(message)
        self.tla = tla


class DuplicateScoresheet(Exception):
    """
    An exception that occurs if two scoresheets for the same match have been
    entered.
    """

    def __init__(self, match_id):
        message = "Scoresheet for {0} has already been added.".format(match_id)
        super(DuplicateScoresheet, self).__init__(message)
        self.match_id = match_id


@total_ordering
class TeamScore(object):
    """
    A team score.

    :param int league: The league points.
    :param int game: The game points.
    """

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
    """An iterator that finds score sheet files."""

    for dname in glob.glob(os.path.join(root, "*")):
        if not os.path.isdir(dname):
            continue

        for resfile in glob.glob(os.path.join(dname, "*.yaml")):
            yield resfile


def get_validated_scores(scorer_cls, input_data):
    """
    Helper function which mimics the behaviour from libproton.

    Given a libproton (Proton 2.0.0-rc1) compatible class this will calculate
    the scores and validate the input.
    """

    teams_data = input_data['teams']
    extra_data = input_data.get('other')  # May be absent

    scorer = scorer_cls(teams_data)
    scores = scorer.calculate_scores()

    # Also check the validation, if supported. Explicit pre-check so
    # that we don't accidentally hide any AttributeErrors (or similar)
    # which come from inside the method.
    if hasattr(scorer, 'validate'):
        scorer.validate(extra_data)

    return scores


# The scorer that these classes consume should be a class that is compatible
# with libproton in its Proton 2.0.0-rc1 form.
# See https://github.com/PeterJCLaw/proton and
# http://srobo.org/cgit/comp/libproton.git.
class BaseScores(object):
    """
    A generic class that holds scores.

    :param str resultdir: Where to find score sheet files.
    :param dict teams: The teams in the competition.
    :param dict scorer: The scorer logic.
    """

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

        game_points = get_validated_scores(self._scorer, y)
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
        self.ranked_points[match_id] = ranker.calc_ranked_points(positions,
                                                                 dsq)

    @property
    def last_scored_match(self):
        """The most match with the highest id for which we have score data."""
        if len(self.ranked_points) == 0:
            return None
        matches = self.ranked_points.keys()
        return max(num for arena, num in matches)


class LeagueScores(BaseScores):
    """A class which holds league scores."""

    @staticmethod
    def rank_league(team_scores):
        """
        Given a mapping of TLA to TeamScore, returns a mapping of TLA to league
        position which both allows for ties and enables their resolution
        deterministically.
        """

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

class TiebreakerScores(BaseScores):
    pass


class Scores(object):
    """
    A simple class which stores references to the league and knockout scores.
    """

    def __init__(self, root, teams, scorer):
        self.root = root
        self.league = LeagueScores(os.path.join(root, "league"),
                                   teams, scorer)
        self.knockout = KnockoutScores(os.path.join(root, "knockout"),
                                       teams, scorer)
        self.tiebreaker = TiebreakerScores(os.path.join(root, "tiebreaker"),
                                           teams, scorer)

        lsm = None
        for scores in (self.tiebreaker, self.knockout, self.league):
            lsm = scores.last_scored_match
            if lsm is not None:
                break

        self.last_scored_match = lsm
