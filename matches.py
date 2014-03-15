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
                         ["start_time","end_time", "max_end_time"])

Match = namedtuple("Match",
                   ["num", "arena", "teams", "start_time", "end_time"])

Delay = namedtuple("Delay",
                   ["delay", "time"])

class MatchSchedule(object):
    def __init__(self, config_fname):
        with open(config_fname, "r") as f:
            y = yaml.load(f.read(), Loader = YAML_Loader)

        self.match_periods = []
        for e in y["match_periods"]["league"]:
            if "max_end_time" in e:
                max_end_time = e["max_end_time"]
            else:
                max_end_time = e["end_time"]

            self.match_periods.append(MatchPeriod(e["start_time"],
                                                  e["end_time"],
                                                  max_end_time))

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

        # We'll pop items off this list as we go
        delays = list(self.delays)

        for period in self.match_periods:
            # Fill this period with matches
            start = period.start_time
            delay = timedelta()

            # Fill this match period with matches
            while True:
                while len(delays) and delays[0].time <= start:
                    delay += delays.pop(0).delay

                try:
                    matchnum = match_numbers.pop(0)
                except IndexError:
                    "No more matches left"
                    break
                self.matches[matchnum] = {}

                for arena_name, teams in yamldata[matchnum].iteritems():
                    start_time = start + delay
                    end_time = start_time + self.match_period
                    match = Match(matchnum, arena_name, teams, start_time, end_time)
                    self.matches[matchnum][arena_name] = match

                start += self.match_period

                # Ensure we haven't exceeded the maximum time limit
                # (if we have then matches will get pushed into the next period)
                if start + delay > period.max_end_time:
                    "We've filled this up to the maximum end time"
                    break

                # Ensure we haven't attempted to pack in more matches than will
                # fit in this period
                if start > period.end_time:
                    "We've filled up this period"
                    break


    def n_matches(self):
        return len(self.matches)

    def current_match(self, arena):
        now = datetime.datetime.now()

        for arenas in self.matches.values():
            match = arenas[arena]

            if now >= match.start_time and now < match.end_time:
                return match

        # No current match
        return None
