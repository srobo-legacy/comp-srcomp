"""Classes that are useful for dealing with match periods."""

from collections import namedtuple
from enum import Enum, unique


MatchPeriod = namedtuple('MatchPeriod', ['start_time', 'end_time',
                                         'max_end_time', 'description',
                                         'matches', 'type'])
Match = namedtuple('Match', ['num', 'display_name', 'arena', 'teams',
                             'start_time', 'end_time', 'type'])


@unique
class MatchType(Enum):
    league = 'league'
    knockout = 'knockout'
    tiebreaker = 'tiebreaker'
