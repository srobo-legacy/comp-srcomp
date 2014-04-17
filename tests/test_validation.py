
from collections import namedtuple
import os
import subprocess

# Hack the path
import helpers as test_helpers

import matches
from validation import validate_match, validate_match_score, \
                        find_missing_scores

Match = namedtuple("Match", ["teams"])

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
    teams_a = [matches.UNKNOWABLE_TEAM] * 4
    teams_b = [matches.UNKNOWABLE_TEAM] * 4
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
