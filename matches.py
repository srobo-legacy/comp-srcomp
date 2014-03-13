"Match schedule library"
from collections import namedtuple
from datetime import timedelta
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

Delay = namedtuple("Delay",
                   ["delay", "time"])

class MatchSchedule(object):
    def __init__(self, config_fname):
        with open(config_fname, "r") as f:
            y = yaml.load(f.read(), Loader = YAML_Loader)

        self.match_periods = []
        for e in y["match_sets"]:
            self.match_periods.append(MatchPeriod(e["start_time"],
                                                 e["end_time"]))

        self.match_period = datetime.timedelta(0, y["match_period_length_seconds"])

        self._build_delaylist(y["delays"])
        self._build_matchlist(y["matches"])

    def _build_delaylist(self, yamldata):
        delays = []
        for info in yamldata:
            d = Delay(timedelta(seconds = info["delay"]),
                      info["time"])
            delays.append(d)

        # Ensure the delays are sorted by time
        def cmpdelay(x,y):
            return cmp(x.time, y.time)

        self.delays = sorted(delays, cmp = cmpdelay)

    def _build_matchlist(self, yamldata):
        "Build the match list"
        self.matches = {}
        match_numbers = sorted(yamldata.keys())

        # First match starts at this point
        current_start = self.match_periods[0].start_time

        # The current delay
        current_delay = datetime.timedelta()

        # We'll pop items off this list as we go
        delays = list(self.delays)

        for period in self.match_periods:
            # Fill this period with matches
            start = period.start_time

            while len(delays) and delays[0].time <= start:
                start += delays.pop(0).delay

            # Fill this match period with matches
            while start < period.end_time:
                try:
                    matchnum = match_numbers.pop(0)
                except IndexError:
                    "No more matches left"
                    break
                self.matches[matchnum] = {}

                for arena_name, teams in yamldata[matchnum].iteritems():
                    end_time = start + self.match_period
                    match = Match(matchnum, arena_name, teams, start, end_time)
                    self.matches[matchnum][arena_name] = match

                start += self.match_period
                while len(delays) and delays[0].time <= start:
                    start += delays.pop(0).delay

    def n_matches(self):
        return len(self.matches)

    def current_match(self):
        now = datetime.datetime.now()

        for arenas in self.matches.values():
            match = arenas.values()[0]

            if now >= match.start_time and now < match.end_time:
                return match

        # No current match
        return None
