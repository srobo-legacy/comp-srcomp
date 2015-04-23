
from collections import OrderedDict
from datetime import datetime, timedelta
import mock

from sr.comp.match_period import Match, MatchType
from sr.comp.knockout_scheduler import UNKNOWABLE_TEAM
from sr.comp.static_knockout_scheduler import StaticScheduler

def get_config():
    return {
        0: {
            0: {
                'arena': 'A',
                'start_time': datetime(2014, 4, 27, 14, 30),
                'teams': ['S3', 'S5', 'S8', 'S10']
            },
            1: {
                'arena': 'A',
                'start_time': datetime(2014, 4, 27, 14, 35),
                'teams': ['S4', 'S6', 'S7', 'S9']
            }
        },
        1: {
            0: {
                'arena': 'A',
                'start_time': datetime(2014, 4, 27, 14, 45),
                'teams': ['S2', '000', '002', '011']
            },
            1: {
                'arena': 'A',
                'start_time': datetime(2014, 4, 27, 14, 50),
                'teams': ['S1', '001', '010', '012']
            }
        },
        2: {
            0: {
                'arena': 'A',
                'start_time': datetime(2014, 4, 27, 15, 0),
                'teams': ['100', '101', '110', '111']
            }
        }
    }

def get_scheduler(matches = None, positions = None, \
                    knockout_positions = None, league_game_points = None, \
                    delays = None):
    matches = matches or []
    delays = delays or []
    match_duration = timedelta(minutes = 5)
    league_game_points = league_game_points or {}
    knockout_positions = knockout_positions or {}
    if not positions:
        positions = OrderedDict()
        positions['AAA'] = 1
        positions['BBB'] = 2
        positions['CCC'] = 3
        positions['DDD'] = 4
        positions['EEE'] = 5
        positions['FFF'] = 6
        positions['GGG'] = 7
        positions['HHH'] = 8
        positions['III'] = 9
        positions['JJJ'] = 10

    league_schedule = mock.Mock(matches = matches, delays = delays, \
                                match_duration = match_duration)
    league_scores = mock.Mock(positions = positions, game_points = league_game_points)
    knockout_scores = mock.Mock(resolved_positions = knockout_positions)
    scores = mock.Mock(league = league_scores, knockout = knockout_scores)

    period_config = {
        "description": "A description of the period",
        "start_time":   datetime(2014, 3, 27,  13),
        "end_time":     datetime(2014, 3, 27,  17, 30),
    }
    config = {
        'match_periods': { 'knockout': [period_config] },
        'static_knockout': get_config(),
    }
    arenas = ['A']

    teams = None  # static schedule shouldn't use teams
    scheduler = StaticScheduler(league_schedule, scores, arenas, teams, config)
    return scheduler, league_schedule

def helper(places, knockout_positions = None):
    scheduler, league_schedule = get_scheduler(knockout_positions = knockout_positions)
    scheduler.add_knockouts()

    period = scheduler.period

    expected = [
        {'A': Match(0, 'Quarter 1 (#0)', 'A', places[0], league_schedule.build_match_times(datetime(2014, 4, 27, 14, 30), datetime(2014, 4, 27, 14, 35)), MatchType.knockout, use_resolved_ranking=True) },
        {'A': Match(1, 'Quarter 2 (#1)', 'A', places[1], league_schedule.build_match_times(datetime(2014, 4, 27, 14, 35), datetime(2014, 4, 27, 14, 40)), MatchType.knockout, use_resolved_ranking=True) },
        {'A': Match(2, 'Semi 1 (#2)', 'A', places[2], league_schedule.build_match_times(datetime(2014, 4, 27, 14, 45), datetime(2014, 4, 27, 14, 50)), MatchType.knockout, use_resolved_ranking=True) },
        {'A': Match(3, 'Semi 2 (#3)', 'A', places[3], league_schedule.build_match_times(datetime(2014, 4, 27, 14, 50), datetime(2014, 4, 27, 14, 55)), MatchType.knockout, use_resolved_ranking=True) },
        {'A': Match(4, 'Final (#4)', 'A', places[4], league_schedule.build_match_times(datetime(2014, 4, 27, 15,  0), datetime(2014, 4, 27, 15,  5)), MatchType.knockout, use_resolved_ranking=False) },
    ]

    for i in range(len(expected)):
        e = expected[i]
        a = period.matches[i]

        assert e == a, "Match {0} in the knockouts".format(i)

def test_before():
    league_matches = [{'A': Match(0, 'Match 0', 'A', [], {'slot': {'start': datetime(2014, 4, 27, 12, 30), 'end': datetime(2014, 4, 27, 12, 35)}}, MatchType.league, use_resolved_ranking=False) }]

    scheduler, league_schedule = get_scheduler(matches = league_matches)
    scheduler.add_knockouts()

    period = scheduler.period

    expected = [
        {'A': Match(1, 'Quarter 1 (#1)', 'A', [UNKNOWABLE_TEAM] * 4, league_schedule.build_match_times(datetime(2014, 4, 27, 14, 30), datetime(2014, 4, 27, 14, 35)), MatchType.knockout, use_resolved_ranking=True) },
        {'A': Match(2, 'Quarter 2 (#2)', 'A', [UNKNOWABLE_TEAM] * 4, league_schedule.build_match_times(datetime(2014, 4, 27, 14, 35), datetime(2014, 4, 27, 14, 40)), MatchType.knockout, use_resolved_ranking=True) },
        {'A': Match(3, 'Semi 1 (#3)', 'A', [UNKNOWABLE_TEAM] * 4, league_schedule.build_match_times(datetime(2014, 4, 27, 14, 45), datetime(2014, 4, 27, 14, 50)), MatchType.knockout, use_resolved_ranking=True) },
        {'A': Match(4, 'Semi 2 (#4)', 'A', [UNKNOWABLE_TEAM] * 4, league_schedule.build_match_times(datetime(2014, 4, 27, 14, 50), datetime(2014, 4, 27, 14, 55)), MatchType.knockout, use_resolved_ranking=True) },
        {'A': Match(5, 'Final (#5)', 'A', [UNKNOWABLE_TEAM] * 4, league_schedule.build_match_times(datetime(2014, 4, 27, 15,  0), datetime(2014, 4, 27, 15,  5)), MatchType.knockout, use_resolved_ranking=False) },
    ]

    for i in range(len(expected)):
        e = expected[i]
        a = period.matches[i]

        assert e == a, "Match {0} in the knockouts".format(i)

def test_start():
    helper([
        ['CCC', 'EEE', 'HHH', 'JJJ'],
        ['DDD', 'FFF', 'GGG', 'III'],
        ['BBB'] + [UNKNOWABLE_TEAM] * 3,
        ['AAA'] + [UNKNOWABLE_TEAM] * 3,
        [UNKNOWABLE_TEAM] * 4,
    ])

def test_partial_1():
    helper([
        ['CCC', 'EEE', 'HHH', 'JJJ'],
        ['DDD', 'FFF', 'GGG', 'III'],
        ['BBB', 'JJJ', 'EEE', UNKNOWABLE_TEAM],
        ['AAA', 'HHH', UNKNOWABLE_TEAM, UNKNOWABLE_TEAM],
        [UNKNOWABLE_TEAM] * 4,
    ], {
        # QF 1
        ('A', 0): OrderedDict([
                    ('JJJ', 1),
                    ('HHH', 2),
                    ('EEE', 3),
                    ('CCC', 4)
                ])
    })

def test_partial_2():
    helper([
        ['CCC', 'EEE', 'HHH', 'JJJ'],
        ['DDD', 'FFF', 'GGG', 'III'],
        ['BBB', 'JJJ', 'EEE', 'GGG'],
        ['AAA', 'HHH', 'III', 'FFF'],
        [UNKNOWABLE_TEAM] * 4,
    ], {
        # QF 1
        ('A', 0): OrderedDict([
                ('JJJ', 1),
                ('HHH', 2),
                ('EEE', 3),
                ('CCC', 4)
            ]),
        # QF 2
        ('A', 1): OrderedDict([
                ('III', 1),
                ('GGG', 2),
                ('FFF', 3),
                ('DDD', 4)
            ])
    })
