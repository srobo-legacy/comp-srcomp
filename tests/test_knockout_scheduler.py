
from datetime import datetime, timedelta
import mock

# Hack the path
import helpers as test_helpers

from scores import TeamScore
from matches import KnockoutScheduler, KNOCKOUT_MATCH, UNKNOWABLE_TEAM

def get_scheduler(matches = None, team_scores = None, \
                    knockout_points = None, delays = None):
    matches = matches or []
    delays = delays or []
    team_scores = team_scores or {
        'ABC': TeamScore(4, 0),
        'DEF': TeamScore(10, 0),
    }
    match_period = timedelta(minutes = 5)
    knockout_points = knockout_points or {}

    league_schedule = mock.Mock(matches = matches, delays = delays, \
                                match_period = match_period)
    league_scores = mock.Mock(teams = team_scores)
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

def test_team_seed_simple_1():
    scheduler = get_scheduler([])

    scores = {
        'ABC': TeamScore(0, 0),
        'DEF': TeamScore(5, 5)
    }

    expected = ['DEF', 'ABC']

    teams = scheduler.seed_teams(scores)

    assert teams == expected

def test_team_seed_simple_2():
    scheduler = get_scheduler([])

    scores = {
        'ABC': TeamScore(10, 10),
        'DEF': TeamScore(5, 5)
    }

    expected = ['ABC', 'DEF']

    teams = scheduler.seed_teams(scores)

    assert teams == expected

def test_team_seed_league_tie_1():
    scheduler = get_scheduler([])

    scores = {
        'ABC': TeamScore(5, 0),
        'DEF': TeamScore(5, 5)
    }

    expected = ['DEF', 'ABC']

    teams = scheduler.seed_teams(scores)

    assert teams == expected

def test_team_seed_league_tie_2():
    scheduler = get_scheduler([])

    scores = {
        'ABC': TeamScore(5, 10),
        'DEF': TeamScore(5, 5)
    }

    expected = ['ABC', 'DEF']

    teams = scheduler.seed_teams(scores)

    assert teams == expected


def test_first_round():
    team_scores = {
        'ABC': TeamScore(1, 0),
        'CDE': TeamScore(2, 0),
        'EFG': TeamScore(3, 0),
        'GHI': TeamScore(5, 0),
        'IJK': TeamScore(5, 3),
        'KLM': TeamScore(6, 0),
        'MNO': TeamScore(7, 0),
        'OPQ': TeamScore(8, 0),
    }
    # Fake a couple of league matches
    matches = [{},{}]
    scheduler = get_scheduler(matches, team_scores = team_scores)

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
    expected_0_teams = sorted(team_scores.keys(), reverse=True)[:4]

    assert semi_0.num == 2, "Match number should carry on above league matches"
    assert semi_0.type == KNOCKOUT_MATCH
    assert semi_0_teams == expected_0_teams

    period_matches = period.matches
    expected_matches = [{'A':m} for r in knockout_rounds for m in r]

    assert period_matches == expected_matches
    final = period_matches[2]['A']
    final_teams = final.teams

    assert final_teams == [UNKNOWABLE_TEAM] * 4
