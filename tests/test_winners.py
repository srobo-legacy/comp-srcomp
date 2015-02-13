from datetime import datetime
from dateutil.tz import tzutc

from sr.comp.winners import Award, compute_awards
from sr.comp.match_period import Match, MatchType
from sr.comp.teams import Team
from sr.comp.scores import TeamScore
from sr.comp.ranker import get_ranked_points

from nose.tools import eq_


KNOCKOUT_ROUNDS = [[Match(num=1, arena='A',
                          teams=['AAA', 'BBB', 'CCC', 'DDD'],
                          start_time=datetime(2014, 4, 26, 16, 30, tzinfo=tzutc()),
                          end_time=datetime(2014, 4, 26, 16, 35, tzinfo=tzutc()),
                          type=MatchType.knockout)]]

TEAMS = {'AAA': Team(tla='AAA', name='AAA Squad'),
         'BBB': Team(tla='BBB', name='BBBees'),
         'CCC': Team(tla='CCC', name='Team CCC'),
         'DDD': Team(tla='DDD', name='DDD Robotics')}

class MockScoreSet(object):
    def __init__(self, arena, game, scores, dsq=()):
        league_points = get_ranked_points(scores, dsq)
        team_key = {}
        gp_key = {}
        rp_key = {}
        for team, gp in scores.items():
            lp = league_points[team]
            team_key[team] = TeamScore(league=lp, game=gp)
            gp_key[team] = gp
            rp_key[team] = lp
        self.teams = team_key
        self.game_points = {(arena, game): gp_key}
        self.ranked_points = {(arena, game): rp_key}


class MockScores(object):
    def __init__(self, league={'AAA': 1, 'BBB': 1, 'CCC': 0, 'DDD': 0},
                       league_dsq=(),
                       knockout={'AAA': 0, 'BBB': 3, 'CCC': 0, 'DDD': 2},
                       knockout_dsq=('CCC',)):
        self.knockout = MockScoreSet('A', 1, knockout, knockout_dsq)
        self.league = MockScoreSet('A', 0, league, league_dsq)


def test_first():
    eq_(compute_awards(MockScores(), KNOCKOUT_ROUNDS, TEAMS).get(Award.first),
        'BBB')

def test_second():
    eq_(compute_awards(MockScores(), KNOCKOUT_ROUNDS, TEAMS).get(Award.second),
        'DDD')

def test_third():
    eq_(compute_awards(MockScores(), KNOCKOUT_ROUNDS, TEAMS).get(Award.third),
        'AAA')

