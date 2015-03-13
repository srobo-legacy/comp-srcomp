"""Match schedule library."""

from collections import namedtuple
import datetime
from datetime import timedelta

from dateutil.tz import gettz

from sr.comp import yaml_loader
from sr.comp.match_period import MatchPeriod, Match, MatchType
from sr.comp.match_period_clock import MatchPeriodClock
from sr.comp.knockout_scheduler import KnockoutScheduler


Delay = namedtuple("Delay",
                   ["delay", "time"])


class MatchSchedule(object):
    """
    A match schedule.
    """
    @classmethod
    def create(cls, config_fname, league_fname, scores, arenas, teams,
               knockout_scheduler=KnockoutScheduler):
        y = yaml_loader.load(config_fname)

        league = yaml_loader.load(league_fname)['matches']

        schedule = cls(y, league, teams)

        k = knockout_scheduler(schedule, scores, arenas, teams, y)
        k.add_knockouts()

        schedule.knockout_rounds = k.knockout_rounds
        schedule.match_periods.append(k.period)

        if 'tiebreaker' in y:
            schedule.add_tie_breaker(scores, y['tiebreaker'])

        return schedule

    def __init__(self, y, league, teams):
        self.teams = teams

        self.match_periods = []
        for e in y["match_periods"]["league"]:
            if "max_end_time" in e:
                max_end_time = e["max_end_time"]
            else:
                max_end_time = e["end_time"]

            period = MatchPeriod(e["start_time"], e["end_time"], max_end_time,
                                 e["description"], [])
            self.match_periods.append(period)

        self._configure_match_slot_lengths(y)

        self._build_delaylist(y["delays"])
        self._build_matchlist(league)

        self.timezone = gettz(y.get('timezone', 'UTC'))

        self.n_league_matches = self.n_matches()

    def _configure_match_slot_lengths(self, yamldata):
        raw_data = yamldata['match_slot_lengths']
        durations = {key: datetime.timedelta(0, value)
                     for key, value in raw_data.items()}
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
            d = Delay(timedelta(seconds=info["delay"]), info["time"])
            delays.append(d)

        delays.sort(key=lambda x: x.time)
        self.delays = delays

    def remove_drop_outs(self, teams, since_match):
        """
        Take a list of TLAs and replace the teams that have dropped out with
        ``None`` values.

        :param list teams: A list of TLAs.
        :param int since_match: The match number to check for drop outs from.
        :return: A new list containing the approriate teams.
        """
        new_teams = []
        for tla in teams:
            if tla is None:
                new_teams.append(None)
            else:
                if self.teams[tla].is_still_around(since_match):
                    new_teams.append(tla)
                else:
                    new_teams.append(None)
        return new_teams

    def _build_matchlist(self, yamldata):
        """Build the match list."""
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

        match_n = 0

        for period in self.match_periods:
            # Fill this period with matches

            clock = MatchPeriodClock(period, self.delays)

            # Fill this match period with matches
            for start in clock.iterslots(self.match_duration):
                try:
                    arenas = arena_info.pop(0)
                except IndexError:
                    # no more matches left
                    break

                m = {}

                end_time = start + self.match_duration
                for arena_name, teams in arenas.items():
                    teams = self.remove_drop_outs(teams, match_n)
                    display_name = 'Match {n}'.format(n=match_n)
                    match = Match(match_n, display_name, arena_name, teams,
                                  start, end_time, MatchType.league)
                    m[arena_name] = match

                period.matches.append(m)
                self.matches.append(m)

                match_n += 1

    def matches_at(self, date):
        """
        Get all the matches that occur around a specific ``date``.

        :param date datetime: The date at which matches occur.
        :return: An iterable list of matches.
        """

        for slot in self.matches:
            for match in slot.values():
                if match.start_time <= date < match.end_time:
                    yield match

    def n_matches(self):
        """
        Get the number of matches.

        :return: The number of matches.
        """

        return len(self.matches)

    def add_tie_breaker(self, scores, time):
        """
        Add a tie breaker to the league if required.

        :param scores: The scores.
        :param time: The time.
        """

        finals_info = self.knockout_rounds[-1][0]
        finals_key = (finals_info.arena, finals_info.num)
        try:
            finals_positions = scores.knockout.game_positions[finals_key]
        except KeyError:
            return
        winners = finals_positions.get(1)
        if not winners:
            raise AssertionError('The only winning move is not to play.')
        if len(winners) > 1:  # Act surprised!
            # Start with the winning teams in the same order as in the finals
            tie_breaker_teams = [team if team in winners else None
                                 for team in finals_info.teams]
            # Use a static permutation
            permutation = [3, 2, 0, 1]
            tie_breaker_teams = [tie_breaker_teams[permutation[n]]
                                 for n in permutation]
            # Inject new match
            arena = finals_info.arena
            match = Match(num=self.n_matches(),
                          display_name='Tiebreaker',
                          arena=arena,
                          teams=tie_breaker_teams,
                          type=MatchType.tie_breaker,
                          start_time=time,
                          end_time=time + self.match_duration)
            self.matches.append({arena: match})
