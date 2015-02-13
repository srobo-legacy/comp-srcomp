from datetime import datetime
from dateutil.tz import tzutc

from sr.comp.winners import Award, compute_awards
from sr.comp.match_period import Match, MatchType
from sr.comp.teams import Team
from sr.comp.scores import TeamScore

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

class MockLeague(object):
    pass

class MockKnockout(object):
    def __init__(self):
        self.teams = {'AAA': TeamScore(league=4, game=0),
                      'BBB': TeamScore(league=8, game=3),
                      'CCC': TeamScore(league=0, game=0),
                      'DDD': TeamScore(league=6, game=2)}
        self.game_points = {('A', 1): {'AAA': 0,
                                       'BBB': 3,
                                       'CCC': 0,
                                       'DDD': 2}}
        self.ranked_points = {('A', 1): {'AAA': 4,
                                         'BBB': 8,
                                         'CCC': 0,
                                         'DDD': 6}}


class MockScores(object):
    def __init__(self):
        self.knockout = MockKnockout()
        self.league = MockLeague()


def test_first():
    eq_(compute_awards(MockScores(), KNOCKOUT_ROUNDS, TEAMS).get(Award.first),
        'BBB')

def test_second():
    eq_(compute_awards(MockScores(), KNOCKOUT_ROUNDS, TEAMS).get(Award.second),
        'DDD')

def test_third():
    eq_(compute_awards(MockScores(), KNOCKOUT_ROUNDS, TEAMS).get(Award.third),
        'AAA')

