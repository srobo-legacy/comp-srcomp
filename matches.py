"Match schedule library"
from collections import namedtuple
import datetime
import time
import yaml

try:
    from yaml import CLoader as YAML_Loader
except ImportError:
    from yaml import Loader as YAML_Loader

MatchPeriod = namedtuple("MatchPeriod",
                         ["start_time","end_time"])

Match = namedtuple("Match",
                   ["num", "arena", "teams", "start_time", "end_time"])

class MatchSchedule(object):
    def __init__(self, config_fname):
        with open(config_fname, "r") as f:
            y = yaml.load(f.read(), Loader = YAML_Loader)

        self.match_periods = []
        for e in y["match_sets"]:
            self.match_periods.append(MatchPeriod(e["start_time"],
                                                 e["end_time"]))

        self.match_period = datetime.timedelta(0, y["match_period_length_seconds"])
        self.current_delay = datetime.timedelta(0, y["current_delay"])

        self.matches = {}
        for num, info in y["matches"].iteritems():
            self.matches[num] = {}

            for arena_name, teams in info.iteritems():
                start_time = self._find_match_start(num)
                end_time = start_time + self.match_period

                match = Match(num, arena_name, teams, start_time, end_time)
                self.matches[num][arena_name] = match

    def _find_match_start(self, num):
        "Find match num's start time"
        n = 0

        # Find the period this match features in
        for period in self.match_periods:
            n += self.matches_in_period(period)
            if num < n:
                "Match is in this period"
                break

        if num >= n:
            "This match never starts"
            return None

        # Number of the first match in the period:
        period_first_match = n - self.matches_in_period(period)

        # Offset of this match within this period
        offset_in_period = num - period_first_match

        return period.start_time + (offset_in_period * self.match_period)

    def n_matches(self):
        total = 0
        for period in self.match_periods:
            total += self.matches_in_period(period)

        return total

    def current_match(self):
        t = datetime.datetime.now() - self.current_delay
        match_num = 0

        # Find the period that we are currently int
        for period in self.match_periods:
            if t < period.end_time:
                break
            match_num += self.matches_in_period(period)

        if t < period.start_time:
            "We're before the beginning of the competition"
            return None

        # Partial period from beginning of current period until now
        partial = MatchPeriod(period.start_time,t)
        match_num += self.matches_in_period(partial)

        return self.matches[match_num]

    def matches_in_period(self, period):
        return (period.end_time - period.start_time).seconds/self.match_period.seconds
