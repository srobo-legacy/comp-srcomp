"""Match schedule library"""

from collections import namedtuple
from datetime import timedelta
import datetime
from dateutil.tz import gettz

from . import yaml_loader
from .match_period import MatchPeriod, Match, MatchType
from .knockout_scheduler import KnockoutScheduler
from sr.comp.ranker import calc_positions
from .stable_random import Random as StableRandom

Delay = namedtuple("Delay",
                   ["delay", "time"])


class MatchSchedule(object):
    @classmethod
    def create(cls, config_fname, league_fname, scores, arenas,
                    knockout_scheduler = KnockoutScheduler):
        y = yaml_loader.load(config_fname)

        league = yaml_loader.load(league_fname)['matches']

        schedule = cls(y, league)

        k = knockout_scheduler(schedule, scores, arenas, y)
        k.add_knockouts()

        schedule.knockout_rounds = k.knockout_rounds
        schedule.match_periods.append(k.period)

        if 'tiebreaker' in y:
            schedule.add_tie_breaker(scores, y['tiebreaker'])

        return schedule

    def __init__(self, y, league):
        self.match_periods = []
        for e in y["match_periods"]["league"]:
            if "max_end_time" in e:
                max_end_time = e["max_end_time"]
            else:
                max_end_time = e["end_time"]

            period = MatchPeriod(e["start_time"], e["end_time"], max_end_time, \
                                    e["description"], [])
            self.match_periods.append(period)

        self._configure_match_slot_lengths(y)

        self._build_delaylist(y["delays"])
        self._build_matchlist(league)

        self.timezone = gettz(y.get('timezone', 'UTC'))

        self.n_league_matches = self.n_matches()

    def _configure_match_slot_lengths(self, yamldata):
        raw_data = yamldata['match_slot_lengths']
        durations = {key: datetime.timedelta(0, value) for key, value in raw_data.items()}
        pre = durations['pre']
        post = durations['post']
        match = durations['match']
        total = durations['total']
        if total != pre + post + match:
            raise ValueError('Match slot lengths are inconsistent.')
        self.match_slot_lengths = durations
        self.match_duration = total

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

        delays.sort(key=lambda x: x.time)
        self.delays = delays

    def _build_matchlist(self, yamldata):
        "Build the match list"
        self.matches = []
        if yamldata is None:
            self.n_planned_league_matches = 0
            return

        match_numbers = sorted(yamldata.keys())
        self.n_planned_league_matches = len(match_numbers)

        if tuple(match_numbers) != tuple(range(len(match_numbers))):
            raise Exception("Matches are not a complete 0-N range")

        # Effectively just the .values(), except that it's ordered by number
        arena_info = [yamldata[m] for m in match_numbers]

        # We'll pop items off this list as we go
        delays = list(self.delays)

        match_n = 0

        for period in self.match_periods:
            # Fill this period with matches

            # The start time for the current match slot we're looking to
            # fill. This value includes all of the relevant delays.
            start = period.start_time

            # The total delay so far. Needed so that we can tell when we
            # get to the end of the original slot for the period.
            total_delay = timedelta()

            # Fill this match period with matches
            while True:
                while len(delays) and delays[0].time <= start:
                    delay = delays.pop(0).delay
                    total_delay += delay
                    start += delay

                try:
                    arenas = arena_info.pop(0)
                except IndexError:
                    # no more matches left
                    break

                m = {}

                end_time = start + self.match_duration
                for arena_name, teams in arenas.items():
                    match = Match(match_n, arena_name, teams, start, end_time, MatchType.league)
                    m[arena_name] = match

                period.matches.append(m)
                self.matches.append(m)

                start += self.match_duration
                match_n += 1

                # Ensure we haven't exceeded the maximum time limit
                # (if we have then matches will get pushed into the next period)
                if start > period.max_end_time:
                    # we've filled this up to the maximum end time
                    break

                # Ensure we haven't attempted to pack in more matches than will
                # fit in this period
                if start - total_delay > period.end_time:
                    # we've filled up this period
                    break

    def matches_at(self, date):
        """Get all the matches that occur around a specific ``date``."""
        for slot in self.matches:
            for match in slot.values():
                if match.start_time <= date < match.end_time:
                    yield match

    def n_matches(self):
        return len(self.matches)

    def add_tie_breaker(self, scores, time):
        finals_info = self.knockout_rounds[-1][0]
        finals_key = (finals_info.arena, finals_info.num)
        try:
            finals_points = scores.knockout.game_points[finals_key]
            finals_ranked = scores.knockout.ranked_points[finals_key]
        except KeyError:
            return
        finals_dsq = [tla for tla, rp in finals_ranked.items() if rp == 0]
        positions = calc_positions(finals_points, finals_dsq)
        winners = positions.get(1)
        if not winners:
            raise AssertionError('The only winning move is not to play.')
        if len(winners) > 1:  # Act surprised!
            tie_breaker_teams = list(sorted(winners))
            while len(tie_breaker_teams) < 4:
                tie_breaker_teams.append(None)
            # Stably shuffle the team order
            rng = StableRandom()
            seed = ''.join(finals_info.teams).encode('utf-8')
            rng.seed(seed)
            rng.shuffle(tie_breaker_teams)
            arena = finals_info.arena
            match = Match(num=self.n_matches(),
                          arena=arena,
                          teams=tie_breaker_teams,
                          type=MatchType.tie_breaker,
                          start_time=time,
                          end_time=time+self.match_duration)
            self.matches.append({arena: match})
