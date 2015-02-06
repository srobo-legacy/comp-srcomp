from collections import namedtuple

MatchPeriod = namedtuple('MatchPeriod', 'start_time end_time max_end_time '
                                        'description matches')
Match = namedtuple('Match', 'num arena teams '
                            'start_time end_time type')

