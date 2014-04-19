
from datetime import datetime, timedelta
import mock
import os

# Hack the path
import helpers as test_helpers

from scores import TeamScore
from matches import KnockoutScheduler

def get_scheduler(matches):
    league_schedule = mock.Mock(matches = matches)
    scheduler = KnockoutScheduler(league_schedule, None, None, None)
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
