from nose.tools import eq_
import datetime
import mock

from sr.comp.matches import MatchSchedule
from sr.comp.match_period import MatchType, Match
from sr.comp.ranker import get_ranked_points

def make_schedule():
    settings = {'match_periods': {'league': [], 'knockout': []},
                'match_slot_lengths': {'pre': 90,
                                       'match': 180,
                                       'post': 30,
                                       'total': 300},
                'delays': []}
    schedule = MatchSchedule(settings, {})

    finals = Match(num=0,
                   arena='A',
                   teams=['AAA', 'BBB', 'CCC', 'DDD'],
                   start_time=datetime.datetime(2014, 4, 25, 12, 0),
                   end_time=datetime.datetime(2014, 4, 25, 12, 5),
                   type=MatchType.knockout)
    schedule.knockout_rounds = [[finals]]
    schedule.matches.append(finals)

    return schedule

def make_finals_score(game_points):
    ko_scores = mock.Mock()
    ko_scores.game_points = {('A', 0): game_points}
    ko_scores.ranked_points = {('A', 0): get_ranked_points(game_points)}
    scores = mock.Mock()
    scores.knockout = ko_scores
    return scores

def test_tiebreaker():
    schedule = make_schedule()
    scores = make_finals_score({'AAA': 1,
                                'BBB': 1,
                                'CCC': 1,
                                'DDD': 0})

    schedule.add_tie_breaker(scores, datetime.datetime(2014, 4, 25, 13, 0))

    eq_(schedule.matches[-1], {'A': Match(num=1,
                                          arena='A',
                                          teams=[None, 'CCC', 'BBB', 'AAA'],
                                          start_time=datetime.datetime(2014, 4, 25, 13,  0),
                                          end_time=datetime.datetime(2014, 4, 25, 13,  5),
                                          type=MatchType.tie_breaker)})

def test_no_tiebreaker_if_winner():
    schedule = make_schedule()
    scores = make_finals_score({'AAA': 2,
                                'BBB': 1,
                                'CCC': 1,
                                'DDD': 0})

    schedule.add_tie_breaker(scores, datetime.datetime(2014, 4, 25, 13, 0))
    eq_(schedule.n_matches(), 1)

def test_no_tiebreaker_if_no_final():
    schedule = make_schedule()
    scores = mock.Mock()
    scores.knockout = mock.Mock()
    scores.knockout.game_points = {}
    scores.knockout.ranked_points = {}

    schedule.add_tie_breaker(scores, datetime.datetime(2014, 4, 25, 13, 0))
    eq_(schedule.n_matches(), 1)
