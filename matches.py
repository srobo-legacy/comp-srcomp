"Match schedule library"
from collections import namedtuple
from datetime import timedelta
import datetime

import yaml_loader

MatchPeriod = namedtuple("MatchPeriod",
                         ["start_time","end_time", "max_end_time"])

Match = namedtuple("Match",
                   ["num", "arena", "teams", "start_time", "end_time"])

Delay = namedtuple("Delay",
                   ["delay", "time"])

class MatchSchedule(object):
    def __init__(self, config_fname):
        y = yaml_loader.load(config_fname)

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
        if yamldata is None:
            "No delays, hurrah"
            self.delays = delays
            return

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
        self.matches = []
        if yamldata is None:
            self.n_planned_matches = 0
            return

        match_numbers = sorted(yamldata.keys())
        self.n_planned_matches = len(match_numbers)

        if match_numbers != range(len(match_numbers)):
            raise Exception("Matches are not a complete 0-N range")

        # Effectively just the .values(), except that it's ordered by number
        arena_info = [yamldata[m] for m in match_numbers]

        # We'll pop items off this list as we go
        delays = list(self.delays)

        match_n = 0

        for period in self.match_periods:
            # Fill this period with matches
            start = period.start_time
            delay = timedelta()

            # Fill this match period with matches
            while True:
                while len(delays) and delays[0].time <= start:
                    delay += delays.pop(0).delay

                try:
                    arenas = arena_info.pop(0)
                except IndexError:
                    "No more matches left"
                    break

                m = {}

                for arena_name, teams in arenas.iteritems():
                    start_time = start + delay
                    end_time = start_time + self.match_period
                    match = Match(match_n, arena_name, teams, start_time, end_time)
                    m[arena_name] = match

                self.matches.append(m)

                start += self.match_period
                match_n += 1

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

    def match_at(self, arena, when):
        for arenas in self.matches:
            match = arenas[arena]

            if when >= match.start_time and when < match.end_time:
                return match

        # No match at that time
        return None

    def current_match(self, arena):
        now = datetime.datetime.now()
        return self.match_at(arena, now)

    def match_after(self, arena, when):
        """Return the next match starting after the given time

        If there's no next match, returns None."""
        for arenas in self.matches:
            match = arenas[arena]

            if match.start_time > when:
                return match

        return None
