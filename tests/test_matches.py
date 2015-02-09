
from datetime import datetime, timedelta

# Hack the path
import helpers as test_helpers

from sr.comp.matches import MatchSchedule

def assert_times(expected, matches, message):
    def times(dts):
        return [dt.strftime("%H:%M") for dt in dts]

    starts = [m['A'].start_time for m in matches]
    expected_times = times(expected)
    start_times = times(starts)

    # Times alone are easier to debug
    assert expected_times == start_times, message + " (times)"

    assert expected == starts, message + " (datetimes)"

def get_basic_data():
    the_data = {
        "match_period_lengths": {
            "pre": 90,
            "match": 180,
            "post": 30,
            "total": 300
        },
        "delays": [ {
            "delay": 15,
            "time":         datetime(2014, 3, 26,  13, 2)
        } ],
        "match_periods": {
            "league": [ {
                "description": "A description of the period",
                "start_time":   datetime(2014, 3, 26,  13),
                "end_time":     datetime(2014, 3, 26,  17, 30),
                "max_end_time": datetime(2014, 3, 26,  17, 40, 0)
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
            },
            2: {
                "A": ["WYC", "QMS", "LSS", "EMM"]
            }
        }
    }
    return the_data

def load_data(the_data):
    matches = MatchSchedule(the_data)
    return matches

def load_basic_data():
    matches = load_data(get_basic_data())
    assert len(matches.match_periods) == 1
    assert len(matches.matches) == 3
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
    assert a_start == datetime(2014, 3, 26,  13)
    assert a_start == b_start

    a_end = a.end_time
    b_end = b.end_time
    assert a_end == datetime(2014, 3, 26,  13, 5)
    assert a_end == b_end

def test_no_matches():
    the_data = get_basic_data()
    the_data['matches'] = None
    matches = load_data(the_data)

    assert matches, "Should have at least loaded the data"

    n_matches = matches.n_matches()
    assert n_matches == 0, "Number actually scheduled"

    n_planned_matches = matches.n_planned_league_matches
    assert n_planned_matches == 0, "Number originally planned for the league"

    n_league_matches = matches.n_league_matches
    assert n_league_matches == 0, "Number actually scheduled for the league"

def test_basic_delay():
    matches = load_basic_data()

    second = matches.matches[1]

    a = second['A']
    b = second['B']

    a_start = a.start_time
    b_start = b.start_time
    assert a_start == datetime(2014, 3, 26,  13, 5, 15)
    assert a_start == b_start

    a_end = a.end_time
    b_end = b.end_time
    assert a_end == datetime(2014, 3, 26,  13, 10, 15)
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
    assert a_start == datetime(2014, 3, 26,  13)
    assert a_start == b_start

    a_end = a.end_time
    b_end = b.end_time
    assert a_end == datetime(2014, 3, 26,  13, 5)
    assert a_end == b_end

def test_two_overlapping_delays():
    the_data = get_basic_data()
    the_data['delays'] = [
        { "delay": 5*60, "time": datetime(2014, 3, 26,  13, 2) },
        # Second delay 'starts' part-way through the first
        { "delay": 5*60, "time": datetime(2014, 3, 26,  13, 6) },
    ]
    the_data["matches"][3] = { "A": ["SRZ", "SRZ1", "SRZ2", "SRZ3"] }
    matches = load_data(the_data)

    expected = [
        datetime(2014, 3, 26,  13, 0), # first match unaffected by delays
        datetime(2014, 3, 26,  13, 15), # second match gets both delays
        datetime(2014, 3, 26,  13, 20),
        datetime(2014, 3, 26,  13, 25),
    ]

    assert_times(expected, matches.matches, "Wrong compound match delays")

def test_two_sepearate_delays():
    the_data = get_basic_data()
    the_data['delays'] = [
        { "delay": 5*60, "time": datetime(2014, 3, 26,  13, 2) },
        { "delay": 5*60, "time": datetime(2014, 3, 26,  13, 12) },
    ]
    the_data["matches"][3] = { "A": ["SRZ", "SRZ1", "SRZ2", "SRZ3"] }
    matches = load_data(the_data)

    expected = [
        datetime(2014, 3, 26,  13, 0), # first match unaffected by delays
        datetime(2014, 3, 26,  13, 10), # second match gets first delay
        datetime(2014, 3, 26,  13, 20), # third match gets first and second delays
        datetime(2014, 3, 26,  13, 25), # fourth match gets no extra delays
    ]

    assert_times(expected, matches.matches, "Wrong compound match delays")

def test_period_end_simple():
    the_data = get_basic_data()
    # Don't care about delays for now
    the_data["delays"] = None
    # for a total of 4 matches
    the_data["matches"][3] = { "A": ["SRZ", "SRZ1", "SRZ2", "SRZ3"] }

    # Period is 12 minutes long. Since we measure by the start of matches
    # this is enough time to start 3 matches (at 5 minutes each)
    league = the_data['match_periods']['league'][0]
    start_time = league['start_time']
    league['end_time'] = start_time + timedelta(minutes=12)
    del league['max_end_time']

    matches = load_data(the_data)

    expected = [
        start_time,
        start_time + timedelta(minutes=5),
        start_time + timedelta(minutes=10),
    ]

    assert_times(expected, matches.matches, "4 matches planned in a 12 minute period, no delay")

def test_period_end_with_delay():
    the_data = get_basic_data()
    # Simple delay
    the_data["delays"] = [
        { "delay": 60, "time": datetime(2014, 3, 26,  13, 2) },
    ]
    # for a total of 4 matches
    the_data["matches"][3] = { "A": ["SRZ", "SRZ1", "SRZ2", "SRZ3"] }

    # Period is 12 minutes long. Since we measure by the start of matches
    # this is enough time to start 3 matches (at 5 minutes each)
    league = the_data['match_periods']['league'][0]
    start_time = league['start_time']
    league['end_time'] = start_time + timedelta(minutes=12)
    del league['max_end_time']

    matches = load_data(the_data)

    expected = [
        start_time,
        # 5 minute matches, 1 minute delay
        start_time + timedelta(minutes=6),
        start_time + timedelta(minutes=11),
    ]

    assert_times(expected, matches.matches, "4 matches planned in a 12 minute period, simple delay")

def test_period_end_with_large_delay():
    the_data = get_basic_data()
    # Simple delay
    the_data["delays"] = [
        { "delay": 300, "time": datetime(2014, 3, 26,  13, 1) },
    ]
    # for a total of 4 matches
    the_data["matches"][3] = { "A": ["SRZ", "SRZ1", "SRZ2", "SRZ3"] }

    # Period is 12 minutes long. Since we measure by the start of matches
    # this is enough time to start 3 matches (at 5 minutes each)
    league = the_data['match_periods']['league'][0]
    start_time = league['start_time']
    league['end_time'] = start_time + timedelta(minutes=12)
    del league['max_end_time']

    matches = load_data(the_data)

    expected = [
        start_time,
        # 5 minute matches, 5 minute delay
        start_time + timedelta(minutes=10),
    ]

    assert_times(expected, matches.matches, "4 matches planned in a 12 minute period, large delay")

def test_period_max_end_simple():
    the_data = get_basic_data()
    # Don't care about delays for now
    the_data["delays"] = None
    # for a total of 4 matches
    the_data["matches"][3] = { "A": ["SRZ", "SRZ1", "SRZ2", "SRZ3"] }

    # Period is 12 minutes long. Since we measure by the start of matches
    # this is enough time to start 3 matches (at 5 minutes each)
    league = the_data['match_periods']['league'][0]
    start_time = league['start_time']
    league['end_time'] = start_time + timedelta(minutes=12)
    # Allow 5 minutes for overrun
    league['max_end_time'] =  start_time + timedelta(minutes=17)

    matches = load_data(the_data)

    expected = [
        start_time,
        start_time + timedelta(minutes=5),
        start_time + timedelta(minutes=10),
    ]

    assert_times(expected, matches.matches, "4 matches planned in a 12 minute period, overrun allowed, no delay")

def test_period_max_end_with_delay():
    the_data = get_basic_data()
    # Simple delay
    the_data["delays"] = [
        { "delay": 60, "time": datetime(2014, 3, 26,  13, 2) },
    ]
    # for a total of 4 matches
    the_data["matches"][3] = { "A": ["SRZ", "SRZ1", "SRZ2", "SRZ3"] }

    # Period is 12 minutes long. Since we measure by the start of matches
    # this is enough time to start 3 matches (at 5 minutes each)
    league = the_data['match_periods']['league'][0]
    start_time = league['start_time']
    league['end_time'] = start_time + timedelta(minutes=12)
    # Allow 5 minutes for overrun
    league['max_end_time'] =  start_time + timedelta(minutes=17)

    matches = load_data(the_data)

    expected = [
        start_time,
        # 5 minute matches, 1 minute delay
        start_time + timedelta(minutes=6),
        start_time + timedelta(minutes=11),
    ]

    assert_times(expected, matches.matches, "4 matches planned in a 12 minute period, overrun allowed, simple delay")

def test_period_max_end_with_large_delay():
    the_data = get_basic_data()
    # Simple delay
    the_data["delays"] = [
        { "delay": 300, "time": datetime(2014, 3, 26,  13, 1) },
    ]
    # for a total of 4 matches
    the_data["matches"][3] = { "A": ["SRZ", "SRZ1", "SRZ2", "SRZ3"] }

    # Period is 12 minutes long. Since we measure by the start of matches
    # this is enough time to start 3 matches (at 5 minutes each)
    league = the_data['match_periods']['league'][0]
    start_time = league['start_time']
    league['end_time'] = start_time + timedelta(minutes=12)
    # Allow 5 minutes for overrun
    league['max_end_time'] =  start_time + timedelta(minutes=17)

    matches = load_data(the_data)

    expected = [
        start_time,
        # 5 minute matches, 5 minute delay
        start_time + timedelta(minutes=10),
        # Third match would have originally been at start+10, so is allowed to occur in the overrun period
        start_time + timedelta(minutes=15),
    ]

    assert_times(expected, matches.matches, "4 matches planned in a 12 minute period, overrun allowed, large delay")


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

    n_planned_matches = matches.n_planned_league_matches
    assert n_planned_matches == 3, "Number originally planned for the league"

    n_league_matches = matches.n_league_matches
    assert n_league_matches == 2, "Number actually scheduled for the league"
