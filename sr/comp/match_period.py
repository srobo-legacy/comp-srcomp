# -*- coding: utf-8 -*-

"""Classes that are useful for dealing with match periods."""

from collections import namedtuple
from enum import Enum, unique


class MatchPeriod(namedtuple('MatchPeriod', ['start_time', 'end_time',
                                             'max_end_time', 'description',
                                             'matches', 'type'])):

    __slots__ = ()

    def __str__(self):
        return '{} ({}–{})'.format(self.description,
                                   self.start_time.strftime('%H:%M'),
                                   self.end_time.strftime('%H:%M'))


_Match = namedtuple('Match', ['num', 'display_name', 'arena', 'teams',
                              'times', 'type', 'use_resolved_ranking'])


class Match(_Match):

    __slots__ = ()

    @property
    def start_time(self):
        return self.times['slot']['start']

    @property
    def end_time(self):
        return self.times['slot']['end']


@unique
class MatchType(Enum):
    league = 'league'
    knockout = 'knockout'
    tiebreaker = 'tiebreaker'
