
from collections import namedtuple
import os

# Hack the path
import helpers as test_helpers

from validation import validate_match

Match = namedtuple("Match", ["teams"])

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
