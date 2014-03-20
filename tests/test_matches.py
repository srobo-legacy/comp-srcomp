
from datetime import datetime, timedelta
import mock
import os

# Hack the path
import helpers as test_helpers

from matches import MatchSchedule

def get_basic_data():
    the_data = {
        "match_period_length_seconds": 300,
        "delays": [ {
            "delay": 15,
            "time":         datetime(2014, 03, 26,  13, 02)
        } ],
        "match_periods": {
            "league": [ {
                "start_time":   datetime(2014, 03, 26,  13),
                "end_time":     datetime(2014, 03, 26,  17, 30),
                "max_end_time": datetime(2014, 03, 26,  17, 40, 00)
            } ],
            "knockout": []
        },
        "matches": {
            0: {
                "A": ["CLY", "TTN", "SCC", "DSF"],
                "B": ["GRS", "QMC", "GRD", "BRK"]
            },
            1: {
                "A": ["WYC", "QMS", "LSS", "EMM"],
                "B": ["BPV", "BDF", "NHS", "MEA"]
            }
        }
    }
    return the_data

def load_data(the_data):
    with mock.patch('matches.yaml_loader.load') as mock_loader:
        mock_loader.return_value = the_data

        matches = MatchSchedule('')
        return matches

def load_basic_data():
    matches = load_data(get_basic_data())
    assert len(matches.match_periods) == 1
    assert len(matches.matches) == 2
    return matches

def test_basic_data():
    matches = load_basic_data()

    first = matches.matches[0]
    assert len(first) == 2
    assert 'A' in first
    assert 'B' in first

    a = first['A']
    b = first['B']

    a_start = a.start_time
    b_start = b.start_time
    assert a_start == datetime(2014, 03, 26,  13)
    assert a_start == b_start

    a_end = a.end_time
    b_end = b.end_time
    assert a_end == datetime(2014, 03, 26,  13, 05)
    assert a_end == b_end

def test_basic_delay():
    matches = load_basic_data()

    second = matches.matches[1]

    a = second['A']
    b = second['B']

    a_start = a.start_time
    b_start = b.start_time
    assert a_start == datetime(2014, 03, 26,  13, 05, 15)
    assert a_start == b_start

    a_end = a.end_time
    b_end = b.end_time
    assert a_end == datetime(2014, 03, 26,  13, 10, 15)
    assert a_end == b_end

def test_no_delays():
    the_data = get_basic_data()
    the_data['delays'] = None
    matches = load_data(the_data)

    first = matches.matches[0]
    assert len(first) == 2
    assert 'A' in first
    assert 'B' in first

    a = first['A']
    b = first['B']

    a_start = a.start_time
    b_start = b.start_time
    assert a_start == datetime(2014, 03, 26,  13)
    assert a_start == b_start

    a_end = a.end_time
    b_end = b.end_time
    assert a_end == datetime(2014, 03, 26,  13, 05)
    assert a_end == b_end

def test_match_at():
    the_data = get_basic_data()

    the_data['delays'] = []

    matches = load_data(the_data)

    arena = 'A'

    def check(expected, when):
        actual = matches.match_at(arena, when)
        assert expected == actual

    yield check, None,                      datetime(2014, 03, 26,  12, 59, 59)

    yield check, matches.matches[0][arena], datetime(2014, 03, 26,  13)
    yield check, matches.matches[0][arena], datetime(2014, 03, 26,  13,  4, 59)

    yield check, matches.matches[1][arena], datetime(2014, 03, 26,  13,  5)
    yield check, matches.matches[1][arena], datetime(2014, 03, 26,  13,  9, 59)

    yield check, None,                      datetime(2014, 03, 26,  13, 10)

def test_match_at_with_delays():
    matches = load_basic_data()

    arena = 'A'

    def check(expected, when):
        actual = matches.match_at(arena, when)
        assert expected == actual

    yield check, matches.matches[0][arena], datetime(2014, 03, 26,  13)
    yield check, matches.matches[0][arena], datetime(2014, 03, 26,  13,  4, 59)

    yield check, None,                      datetime(2014, 03, 26,  13,  5, 14)

    yield check, matches.matches[1][arena], datetime(2014, 03, 26,  13,  5, 15)
    yield check, matches.matches[1][arena], datetime(2014, 03, 26,  13, 10, 14)

    yield check, None,                      datetime(2014, 03, 26,  13, 10, 15)

def test_planned_matches():
    the_data = get_basic_data()

    extra_match = {
                "A": ["WYC2", "QMS2", "LSS2", "EMM2"],
                "B": ["BPV2", "BDF2", "NHS2", "MEA2"]
            }
    the_data['matches'][2] = extra_match

    league = the_data['match_periods']['league'][0]
    league['end_time'] = league['start_time'] + timedelta(minutes=10)
    del league['max_end_time']

    matches = load_data(the_data)

    n_matches = matches.n_matches()
    assert n_matches == 2, "Number actually scheduled"

    n_planned_matches = matches.n_planned_matches
    assert n_planned_matches == 3, "Number originally planned"
