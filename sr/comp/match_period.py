"""Classes that are useful for dealing with match periods."""

from collections import namedtuple
from enum import Enum, unique


_MatchPeriod = namedtuple('MatchPeriod', ['start_time', 'end_time',
                                          'max_end_time', 'description',
                                          'matches', 'type'])


class MatchPeriod(_MatchPeriod):
    def __str__(self):
        return '{} ({} to {})'.format(self.description, self.start_time, self.end_time)


Match = namedtuple('Match', ['num', 'display_name', 'arena', 'teams',
                             'start_time', 'end_time', 'type'])


@unique
class MatchType(Enum):
    league = 'league'
    knockout = 'knockout'
    tiebreaker = 'tiebreaker'
