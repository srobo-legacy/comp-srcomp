"""Match schedule library."""

from collections import namedtuple
import datetime
from datetime import timedelta

from dateutil.tz import gettz

from . import yaml_loader
from .match_period import MatchPeriod, Match, MatchType
from .match_period_clock import MatchPeriodClock
from .knockout_scheduler import KnockoutScheduler, StaticScheduler


class WrongNumberOfTeams(Exception):
    def __init__(self, match_n, arena_name, teams, num_teams_per_arena):
        message = "Match {0}{1} has {2} teams but must have {3}".format(
            arena_name,
            match_n,
            len(teams),
            num_teams_per_arena,
        )
        super(WrongNumberOfTeams, self).__init__(message)


Delay = namedtuple("Delay",
                   ["delay", "time"])

def parse_ranges(ranges):
    """
    Parse a comma seprated list of numbers which may include ranges
    specified as hyphen-separated numbers.

    From http://stackoverflow.com/questions/6405208/how-to-convert-numeric-string-ranges-to-a-list-in-python
    """
    result = []
    for part in ranges.split(','):
        if '-' in part:
            a, b = part.split('-')
            a, b = int(a), int(b)
            result.extend(range(a, b + 1))
        else:
            a = int(part)
            result.append(a)
    return set(result)

class MatchSchedule(object):
    """
    A match schedule.
    """

    @classmethod
    def create(cls, config_fname, league_fname, scores, arenas, num_teams_per_arena, teams):
        """
        Create a new match schedule around the given config data.

        :param str config_fname: The filename of the main config file.
        :param str league_fname: The filename of the file containing the league matches.
        :param `.Scores` scores: The scores for the competition.
        :param dict arenas: A mapping of arena ids to :class:`.Arena` instances.
        :param int num_teams_per_arena: The usual number of teams per arena.
        :param dict teams: A mapping of TLAs to :class:`.Team` instances.
        """

        y = yaml_loader.load(config_fname)

        league = yaml_loader.load(league_fname)['matches']

        schedule = cls(y, league, teams, num_teams_per_arena)

        if y['knockout'].get('static', False):
            knockout_scheduler = StaticScheduler
        else:
            knockout_scheduler = KnockoutScheduler

        k = knockout_scheduler(schedule, scores, arenas, num_teams_per_arena, teams, y)
        k.add_knockouts()

        schedule.knockout_rounds = k.knockout_rounds
        schedule.match_periods.append(k.period)

        if 'tiebreaker' in y:
            schedule.add_tiebreaker(scores, y['tiebreaker'])

        return schedule

    def __init__(self, y, league, teams, num_teams_per_arena):
        self._num_corners = num_teams_per_arena

        self.teams = teams
        """A mapping of TLAs to :class:`.Team` instances."""

        self.match_periods = []
        """
        A list of the :class:`.MatchPeriod` s which contain the matches
        for the competition.
        """

        self.knockout_rounds = []
        """
        A list of the knockout matches by round. Each entry in the list
        represents a round of knockout matches, such that `knockout_rounds[-1]`
        contains a list with only one match -- the final.
        """

        for e in y["match_periods"]["league"]:
            if "max_end_time" in e:
                max_end_time = e["max_end_time"]
            else:
                max_end_time = e["end_time"]

            period = MatchPeriod(e["start_time"], e["end_time"], max_end_time,
                                 e["description"], [], MatchType.league)
            self.match_periods.append(period)

        self._load_match_slot_lengths(y["match_slot_lengths"])
        self._load_staging_times(y["staging"])

        self._build_extra_spacing(y["league"]['extra_spacing'])
        self._build_delaylist(y["delays"])

        self.matches = []
        """
        A list of match slots in the schedule. Each match slot is a dict of
        arena to the :class:`.Match` occuring in that arena.
        """

        self.n_planned_league_matches = 0
        """The number of planned league matches."""

        self._build_matchlist(league)

        self.timezone = gettz(y.get('timezone', 'UTC'))

        self.n_league_matches = self.n_matches()

    def _load_match_slot_lengths(self, yamldata):
        durations = {key: datetime.timedelta(0, value)
                     for key, value in yamldata.items()}
        pre = durations['pre']
        post = durations['post']
        match = durations['match']
        total = durations['total']
        if total != pre + post + match:
            raise ValueError('Match slot lengths are inconsistent.')
        self.match_slot_lengths = durations
        self.match_duration = total

    def _load_staging_times(self, yamldata):
        def to_timedeltas(item):
            if isinstance(item, dict):
                return {key: to_timedeltas(value)
                        for key, value in item.items()}
            else:
                return datetime.timedelta(seconds=item)

        durations = to_timedeltas(yamldata)

        opens = durations['opens']
        closes = durations['closes']
        duration = durations['duration']
        if duration != opens - closes:
            raise ValueError('Staging timings are inconsistent.')

        for other in ('signal_teams', 'signal_shepherds'):
            if other not in durations:
                msg = "Staging times missing '{0}' key.".format(other)
                raise ValueError(msg)

        self.staging_times = durations

    def get_staging_times(self, match):
        pre = self.match_slot_lengths['pre']
        match_start = match.start_time + pre
        offsets = self.staging_times

        signal_shepherds = {area: match_start - offset
                            for area, offset in offsets['signal_shepherds'].items()}

        return  {
            'opens':            match_start - offsets['opens'],
            'closes':           match_start - offsets['closes'],
            'duration':         self.staging_times['duration'],
            'signal_shepherds': signal_shepherds,
            'signal_teams':     match_start - offsets['signal_teams'],
        }

    def _build_extra_spacing(self, yamldata):
        spacing = {}
        if not yamldata:
            self._spacing = spacing
            return

        for info in yamldata:
            match_numbers = parse_ranges(info['match_numbers'])
            duration = timedelta(seconds=info['duration'])
            for num in match_numbers:
                assert num not in spacing
                spacing[num] = duration

        self._spacing = spacing

    def _build_delaylist(self, yamldata):
        delays = []
        if yamldata is None:
            # No delays, hurrah
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
        """
        Build the match list.

        :param dict yamldata: The matches data from the league file, formatted
        as a dict of match numbers to dicts of arena to lists of TLAs.
        """

        if yamldata is None:
            return

        match_numbers = sorted(yamldata.keys())
        self.n_planned_league_matches = len(match_numbers)

        if tuple(match_numbers) != tuple(range(len(match_numbers))):
            raise Exception("Matches are not a complete 0-N range")

        # Effectively just the .values(), except that it's ordered by number
        raw_matches = [yamldata[m] for m in match_numbers]

        match_n = 0

        for period in self.match_periods:
            # Fill this period with matches

            clock = MatchPeriodClock(period, self.delays)

            # No extra spacing for matches at the start of a period

            # Fill this match period with matches
            for start in clock.iterslots(self.match_duration):
                try:
                    arenas = raw_matches.pop(0)
                except IndexError:
                    # no more matches left
                    break

                match_slot = self._create_league_match_slot(start, arenas, match_n)
                period.matches.append(match_slot)
                self.matches.append(match_slot)

                match_n += 1

                extra_spacing = self._spacing.get(match_n)
                if extra_spacing:
                    clock.advance_time(extra_spacing)

    def _create_league_match_slot(self, start_time, arenas, match_n):
        """
        Returns a dict of arena to :class:`.Match` for the given start time,
        arenas dict and match number.
        """
        match_slot = {}

        end_time = start_time + self.match_duration
        for arena_name, teams in arenas.items():
            teams = self.remove_drop_outs(teams, match_n)
            display_name = 'Match {n}'.format(n=match_n)

            if len(teams) != self._num_corners:
                raise WrongNumberOfTeams(match_n, arena_name, teams, self._num_corners)

            match = Match(match_n, display_name, arena_name, teams,
                          start_time, end_time, MatchType.league,
                          use_resolved_ranking=False)
            match_slot[arena_name] = match

        return match_slot

    def delay_at(self, date):
        """
        Calculates the active delay at a given ``date``. Intended for use
        only in exposing the current delay value -- scheduling should be
        done using a :class:`.MatchPeriodClock` instead.

        :param datetime date: The date to find the delay for.
        :return: A :class:`datetime.timedelta` specifying the active delay.
        """

        total = timedelta()
        period = self.period_at(date)
        if not period:
            # No current period, no delays active
            return total

        delays = MatchPeriodClock.delays_for_period(period, self.delays)
        for delay in delays:
            if delay.time > date:
                break

            total += delay.delay

        return total

    def matches_at(self, date):
        """
        Get all the matches that occur around a specific ``date``.

        :param datetime date: The date at which matches occur.
        :return: An iterable list of matches.
        """

        for slot in self.matches:
            for match in slot.values():
                if match.start_time <= date < match.end_time:
                    yield match

    def period_at(self, date):
        """
        Get the match period that occur around a specific ``date``.

        :param datetime date: The date at which period occurs.
        :return: The period at that time or ``None``.
        """

        for period in self.match_periods:
            if period.start_time <= date < period.max_end_time:
                return period

        return None

    def n_matches(self):
        """
        Get the number of matches.

        :return: The number of matches.
        """

        return len(self.matches)

    @property
    def final_match(self):
        """
        Get the :class:`.Match` for the last match of the competition.

        This is the info for the 'finals' of the competition (i.e: the
        last of the knockout matches) unless there is a tiebreaker.
        """
        last_match_slot = self.matches[-1]
        last_matches = list(last_match_slot.values())
        assert len(last_matches) == 1, last_match_slot
        return last_matches[0]

    def add_tiebreaker(self, scores, time):
        """
        Add a tie breaker to the league if required. Also set a ``tiebreaker``
        attribute if necessary.

        :param `.Scores` scores: The scores for the competition.
        :param datetime.datetime time: The time to have the tiebreaker match.
        """
        # pylint: disable=too-many-locals

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
            tiebreaker_teams = [team if team in winners else None
                                for team in finals_info.teams]
            # Use a static permutation
            permutation = [3, 2, 0, 1]
            tiebreaker_teams = [tiebreaker_teams[permutation[n]]
                                for n in permutation]
            # Inject new match
            end_time = time + self.match_duration
            num = self.n_matches()
            arena = finals_info.arena
            match = Match(num=num,
                          display_name="Tiebreaker (#{0})".format(num),
                          arena=arena,
                          teams=tiebreaker_teams,
                          type=MatchType.tiebreaker,
                          start_time=time,
                          end_time=end_time,
                          use_resolved_ranking=False)
            slot = {arena: match}
            self.matches.append(slot)
            match_period = MatchPeriod(time, end_time, end_time,
                                       'Tiebreaker', [slot], MatchType.tiebreaker)
            self.match_periods.append(match_period)

            # pylint: disable=attribute-defined-outside-init
            self.tiebreaker = match

    @property
    def datetime_now(self):
        """Get the current date and time, with the correct timezone."""
        return datetime.datetime.now(self.timezone)
