
from collections import namedtuple
from datetime import datetime, timedelta
import os
import subprocess

# Hack the path
import helpers as test_helpers

from sr.comp import matches
from sr.comp.validation import validate_match, validate_schedule_timings, \
                        validate_match_score, find_missing_scores

from sr.comp.knockout_scheduler import UNKNOWABLE_TEAM

Match = namedtuple("Match", ["teams"])
Match2 = namedtuple("Match2", ["num", "start_time"])

def test_dummy_is_valid():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(test_dir)
    validate = os.path.join(root, 'validate')
    dummy_compstate = os.path.join(test_dir, 'dummy')
    try:
        subprocess.check_output([validate, dummy_compstate], \
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        assert cpe.returncode == 0, cpe.output

def test_validate_match_unknowable_entrants():
    teams_a = [UNKNOWABLE_TEAM] * 4
    teams_b = [UNKNOWABLE_TEAM] * 4
    teams = set()
    knockout_match = {
        'A': Match(teams_a),
        'B': Match(teams_b)
    }

    errors = validate_match(knockout_match, teams)
    assert len(errors) == 0

def test_validate_match_empty_corners():
    """ Empty corner zones are represented by 'None' """
    teams_a = ['ABC', 'DEF', None, 'JKL']
    teams_b = ['LMN', 'OPQ', None, None]
    teams = set(['ABC', 'DEF', 'JKL', 'LMN', 'OPQ'])
    knockout_match = {
        'A': Match(teams_a),
        'B': Match(teams_b)
    }

    errors = validate_match(knockout_match, teams)
    assert len(errors) == 0

def test_validate_match_duplicate_entrant():
    teams_a = ['ABC', 'DEF', 'GHI', 'JKL']
    teams_b = ['LMN', 'OPQ', 'GHI', 'JKL']
    teams = set(teams_a + teams_b)
    bad_match = {
        'A': Match(teams_a),
        'B': Match(teams_b)
    }

    errors = validate_match(bad_match, teams)
    assert len(errors) == 1
    error = '\n'.join(errors)

    assert 'more than once' in error
    assert 'GHI' in error
    assert 'JKL' in error

def test_validate_match_nonexistant_entrant():
    teams_a = ['ABC', 'DEF', 'GHI', 'JKL']
    teams_b = ['LMN', 'OPQ', 'RST', 'UVW']
    bad_match = {
        'A': Match(teams_a),
        'B': Match(teams_b)
    }

    errors = validate_match(bad_match, teams_a)
    assert len(errors) == 1
    error = '\n'.join(errors)

    assert 'not exist' in error
    for t in teams_b:
        assert t in error

def test_validate_match_all():
    teams_a = ['ABC', 'DEF', 'GHI', 'JKL']
    teams_b = ['LMN', 'OPQ', 'GHI', 'GHI']
    bad_match = {
        'A': Match(teams_a),
        'B': Match(teams_b)
    }

    errors = validate_match(bad_match, teams_a)
    assert len(errors) == 2
    error = '\n'.join(errors)

    assert 'more than once' in error
    assert 'not exist' in error


def test_validate_match_score_empty_corner():
    match = Match([None, 'ABC', 'DEF', 'GHI'])

    ok_score = {
        'ABC': 1,
        'DEF': 1,
        'GHI': 1,
    }

    errors = validate_match_score(ok_score, match)
    assert len(errors) == 0

def test_validate_match_score_empty_corner_2():
    match = Match([None, 'ABC', 'DEF', 'GHI'])

    bad_score = {
        'ABC': 1,
        'DEF': 1,
        'GHI': 1,
        'NOP': 1,
    }

    errors = validate_match_score(bad_score, match)
    assert len(errors) == 1
    error = '\n'.join(errors)

    assert 'not scheduled in this match' in error
    assert 'NOP' in error

def test_validate_match_score_extra_team():
    match = Match(['ABC', 'DEF', 'GHI', 'JKL'])

    bad_score = {
        'ABC': 1,
        'DEF': 1,
        'GHI': 1,
        'NOP': 1,
    }

    errors = validate_match_score(bad_score, match)
    assert len(errors) == 2
    error = '\n'.join(errors)

    assert 'not scheduled in this match' in error
    assert 'NOP' in error
    assert 'missing from this match' in error
    assert 'JKL' in error

def test_validate_match_score_extra_team_2():
    match = Match(['ABC', 'DEF', 'GHI', 'JKL'])

    bad_score = {
        'ABC': 1,
        'DEF': 1,
        'GHI': 1,
        'JKL': 1,
        'NOP': 1,
    }

    errors = validate_match_score(bad_score, match)
    assert len(errors) == 1
    error = '\n'.join(errors)

    assert 'not scheduled in this match' in error
    assert 'NOP' in error

def test_validate_match_score_missing_team():
    match = Match(['ABC', 'DEF', 'GHI', 'JKL'])

    bad_score = {
        'ABC': 1,
        'DEF': 1,
        'GHI': 1,
    }

    errors = validate_match_score(bad_score, match)
    assert len(errors) == 1
    error = '\n'.join(errors)

    assert 'missing from this match' in error
    assert 'JKL' in error

def test_validate_match_score_swapped_team():
    match = Match(['ABC', 'DEF', 'GHI', 'JKL'])

    bad_score = {
        'ABC': 1,
        'DEF': 1,
        'GHI': 1,
        'NOP': 1,
    }

    errors = validate_match_score(bad_score, match)
    assert len(errors) == 2
    error = '\n'.join(errors)

    assert 'not scheduled in this match' in error
    assert 'missing from this match' in error
    assert 'JKL' in error
    assert 'NOP' in error


def test_find_missing_scores_arena():
    match_ids = [
        ('A', 0)
    ]
    last_match = 0
    schedule = [
        {'A': None, 'B': None}
    ]

    missing = find_missing_scores(match_ids, last_match, schedule)

    expected = [ (0, set(['B'])) ]
    assert missing == expected

def test_find_missing_scores_match():
    match_ids = [
        ('A', 1)
    ]
    last_match = 1
    schedule = [
        {'A': None},
        {'A': None}
    ]

    missing = find_missing_scores(match_ids, last_match, schedule)

    expected = [ (0, set(['A'])) ]
    assert missing == expected

def test_find_missing_scores_many_matches():
    match_ids = [
        ('A', 0),
        ('A', 2),
        ('A', 4)
    ]
    last_match = 4
    schedule = [
        {'A': None},
        {'A': None},
        {'A': None},
        {'A': None},
        {'A': None}
    ]

    missing = find_missing_scores(match_ids, last_match, schedule)

    expected = [
        (1, set(['A'])),
        (3, set(['A']))
    ]
    assert missing == expected

def test_find_missing_scores_ignore_future_matches():
    match_ids = [
        ('A', 0),
        ('A', 1),
        ('A', 2)
    ]
    last_match = 2
    schedule = [
        {'A': None},
        {'A': None},
        {'A': None},
        {'A': None},
        {'A': None}
    ]

    missing = find_missing_scores(match_ids, last_match, schedule)

    assert missing == []

def test_find_missing_scores_ignore_no_matches():
    schedule = [
        {'A': None},
        {'A': None},
        {'A': None},
        {'A': None},
        {'A': None}
    ]

    missing = find_missing_scores([], None, schedule)

    assert not len(missing), "Cannot be any missing scores when none entered"

def test_validate_schedule_timings_ok():

    matches = [{'A': Match2(1, datetime(2014, 4, 1, 12, 0, 0))},
               {'A': Match2(2, datetime(2014, 4, 1, 13, 0, 0))}]
    match_duration = timedelta(minutes = 5)

    errors = validate_schedule_timings(matches, match_duration)
    assert len(errors) == 0

def test_validate_schedule_timings_same_time():

    time = datetime(2014, 4, 3, 12, 0, 0)
    time = datetime(2014, 4, 3, 12, 0, 0)
    match_duration = timedelta(minutes = 5)
    # choose match ids not in the date
    matches = [{'A': Match2(8, time)},
               {'A': Match2(9, time)}]

    errors = validate_schedule_timings(matches, match_duration)

    assert len(errors) == 1
    error = errors[0]
    assert "Multiple matches" in error
    assert str(time) in error
    assert "8" in error
    assert "9" in error

def test_validate_schedule_timings_overlap():

    time_8 = datetime(2014, 4, 3, 12, 0, 0)
    time_9 = datetime(2014, 4, 3, 12, 0, 1)
    match_duration = timedelta(minutes = 5)
    # choose match ids not in the date
    matches = [{'A': Match2(8, time_8)},
               {'A': Match2(9, time_9)}]

    errors = validate_schedule_timings(matches, match_duration)

    assert len(errors) == 1
    error = errors[0]
    assert "Matches 9 start" in error
    assert "before matches 8 have finished" in error
    assert str(time_9) in error

def test_validate_schedule_timings_overlap_2():

    time_7 = datetime(2014, 4, 3, 12, 0, 0)
    time_8 = datetime(2014, 4, 3, 12, 0, 3)
    time_9 = datetime(2014, 4, 3, 12, 0, 6)
    match_duration = timedelta(minutes = 5)
    # choose match ids not in the date
    matches = [{'A': Match2(7, time_7)},
               {'A': Match2(8, time_8)},
               {'A': Match2(9, time_9)}]

    errors = validate_schedule_timings(matches, match_duration)

    assert len(errors) == 2
    error = errors[0]
    assert "Matches 8 start" in error
    assert "before matches 7 have finished" in error
    assert str(time_8) in error

    error = errors[1]
    assert "Matches 9 start" in error
    assert "before matches 8 have finished" in error
    assert str(time_9) in error
