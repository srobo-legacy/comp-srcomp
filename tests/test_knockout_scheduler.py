
from collections import OrderedDict
from datetime import datetime, timedelta
import mock

# Hack the path
import helpers as test_helpers

from scores import TeamScore
from matches import KnockoutScheduler, Match, KNOCKOUT_MATCH, UNKNOWABLE_TEAM

def get_scheduler(matches = None, positions = None, \
                    knockout_points = None, delays = None):
    matches = matches or []
    delays = delays or []
    match_period = timedelta(minutes = 5)
    knockout_points = knockout_points or {}
    if not positions:
        positions = OrderedDict()
        positions['ABC'] = 1
        positions['DEF'] = 2

    league_schedule = mock.Mock(matches = matches, delays = delays, \
                                match_period = match_period)
    league_scores = mock.Mock(positions = positions)
    knockout_scores = mock.Mock(ranked_points = knockout_points)
    scores = mock.Mock(league = league_scores, knockout = knockout_scores)

    period_config = {
        "description": "A description of the period",
        "start_time":   datetime(2014, 03, 27,  13),
        "end_time":     datetime(2014, 03, 27,  17, 30),
    }
    knockout_config = {
        'round_spacing': 300,
        'final_delay': 300,
        'single_arena': {
            'rounds': 3,
            'arenas': ["A"],
        },
    }
    config = {
        'match_periods': { 'knockout': [period_config] },
        'knockout': knockout_config,
    }
    arenas = ['A']
    scheduler = KnockoutScheduler(league_schedule, scores, arenas, config)
    return scheduler


def test_knockout_match_winners_empty():
    scheduler = get_scheduler()
    game = Match(2, 'A', [], None, None, None)
    winners = scheduler.get_winners(game)
    assert winners == [UNKNOWABLE_TEAM] * 2

def test_knockout_match_winners_simple():
    knockout_points = {
        ('A', 2): {
            'ABC': 1.0,
            'DEF': 2.0,
            'GHI': 3.0,
            'JKL': 4.0,
        }
    }
    scheduler = get_scheduler(knockout_points = knockout_points)

    game = Match(2, 'A', [], None, None, None)
    winners = scheduler.get_winners(game)

    assert set(winners) == set(['GHI', 'JKL'])

def test_knockout_match_winners_irrelevant_tie_1():
    knockout_points = {
        ('A', 2): {
            'ABC': 1.5,
            'DEF': 1.5,
            'GHI': 3,
            'JKL': 4,
        }
    }
    scheduler = get_scheduler(knockout_points = knockout_points)

    game = Match(2, 'A', [], None, None, None)
    winners = scheduler.get_winners(game)

    assert set(winners) == set(['GHI', 'JKL'])

def test_knockout_match_winners_irrelevant_tie_1():
    knockout_points = {
        ('A', 2): {
            'ABC': 1,
            'DEF': 2,
            'GHI': 3.5,
            'JKL': 3.5,
        }
    }
    scheduler = get_scheduler(knockout_points = knockout_points)

    game = Match(2, 'A', [], None, None, None)
    winners = scheduler.get_winners(game)

    assert set(winners) == set(['GHI', 'JKL'])


def test_first_round():
    positions = OrderedDict()
    positions['ABC'] = 1
    positions['CDE'] = 2
    positions['EFG'] = 3
    positions['GHI'] = 4
    positions['IJK'] = 5
    positions['KLM'] = 6
    positions['MNO'] = 7
    positions['OPQ'] = 8

    # Fake a couple of league matches
    matches = [{},{}]
    scheduler = get_scheduler(matches, positions = positions)

    def seeder(*args):
        assert args[0] == 8, "Wrong number of teams"
        return [[0,1,2,3],[4,5,6,7]]

    # Mock the random (even thought it's not really random)
    scheduler.R = mock.Mock()
    # Mock the seeder to make it less interesting
    with mock.patch('knockout.first_round_seeding') as first_round_seeding:
        first_round_seeding.side_effect = seeder
        scheduler.add_knockouts()

    knockout_rounds = scheduler.knockout_rounds
    period = scheduler.period

    assert len(knockout_rounds) == 2, "Should be semis and finals"
    semis = knockout_rounds[0]

    assert len(semis) == 2, "Should be two semis"
    semi_0 = semis[0]
    semi_0_teams = semi_0.teams
    # Thanks to our mocking of the seeder...
    expected_0_teams = positions.keys()[:4]

    assert semi_0.num == 2, "Match number should carry on above league matches"
    assert semi_0.type == KNOCKOUT_MATCH
    assert semi_0_teams == expected_0_teams

    period_matches = period.matches
    expected_matches = [{'A':m} for r in knockout_rounds for m in r]

    assert period_matches == expected_matches
    final = period_matches[2]['A']
    final_teams = final.teams

    assert final_teams == [UNKNOWABLE_TEAM] * 4
