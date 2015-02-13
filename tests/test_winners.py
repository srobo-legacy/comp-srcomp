from datetime import datetime
from dateutil.tz import tzutc
from collections import OrderedDict

from sr.comp.winners import Award, compute_awards
from sr.comp.match_period import Match, MatchType
from sr.comp.teams import Team
from sr.comp.scores import TeamScore
from sr.comp.ranker import calc_positions, calc_ranked_points

from nose.tools import eq_
import mock


KNOCKOUT_ROUNDS = [[Match(num=1, arena='A',
                          teams=['AAA', 'BBB', 'CCC', 'DDD'],
                          start_time=datetime(2014, 4, 26, 16, 30, tzinfo=tzutc()),
                          end_time=datetime(2014, 4, 26, 16, 35, tzinfo=tzutc()),
                          type=MatchType.knockout)]]

TEAMS = {'AAA': Team(tla='AAA', name='AAA Squad', rookie=True),
         'BBB': Team(tla='BBB', name='BBBees', rookie=False),
         'CCC': Team(tla='CCC', name='Team CCC', rookie=True),
         'DDD': Team(tla='DDD', name='DDD Robotics', rookie=False)}

class MockScoreSet(object):
    def __init__(self, arena, game, scores, dsq=()):
        positions = calc_positions(scores, dsq)
        league_points = calc_ranked_points(positions, dsq)
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
        self.positions = OrderedDict()
        for position, teams in positions.items():
            for team in teams:
                self.positions[team] = position


class MockScores(object):
    def __init__(self, league={'AAA': 1, 'BBB': 2, 'CCC': 0, 'DDD': 0},
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

def test_tied():
    eq_(compute_awards(MockScores(knockout={'AAA': 1, 'BBB': 1, 'CCC': 1, 'DDD': 1},
                                  knockout_dsq=()), KNOCKOUT_ROUNDS, TEAMS).get(Award.first),
        None)

def test_tied_partial():
    eq_(compute_awards(MockScores(knockout={'AAA': 2, 'BBB': 1, 'CCC': 1, 'DDD': 1},
                                  knockout_dsq=()), KNOCKOUT_ROUNDS, TEAMS).get(Award.first),
        'AAA')

def test_rookie():
    eq_(compute_awards(MockScores(), KNOCKOUT_ROUNDS, TEAMS).get(Award.rookie),
        'AAA')

def test_override():
    with mock.patch('sr.comp.yaml_loader.load') as yaml_load:
        yaml_load.return_value = {'third': 'DDD'}
        eq_(compute_awards(MockScores(), KNOCKOUT_ROUNDS, TEAMS, '.').get(Award.third),
            'DDD')
        yaml_load.assert_called_with('.')

def test_manual():
    with mock.patch('sr.comp.yaml_loader.load') as yaml_load:
        yaml_load.return_value = {'web': 'BBB'}
        eq_(compute_awards(MockScores(), KNOCKOUT_ROUNDS, TEAMS, '.').get(Award.web),
            'BBB')
        yaml_load.assert_called_with('.')

def test_no_overrides_file():
    with mock.patch('sr.comp.yaml_loader.load') as yaml_load:
        yaml_load.side_effect = FileNotFoundError()
        eq_(compute_awards(MockScores(), KNOCKOUT_ROUNDS, TEAMS, '.').get(Award.third),
            'AAA')
