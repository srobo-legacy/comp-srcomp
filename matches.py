"Match schedule library"

from collections import namedtuple
from datetime import timedelta
import datetime
import math
import sys

import knockout
import stable_random
import yaml_loader

MatchPeriod = namedtuple("MatchPeriod",
                         ["start_time", "end_time", "max_end_time", \
                            "description", "matches"])

LEAGUE_MATCH = "league"
KNOCKOUT_MATCH = "knockout"

Match = namedtuple("Match",
                   ["num", "arena", "teams", "start_time", "end_time", "type"])

Delay = namedtuple("Delay",
                   ["delay", "time"])

class KnockoutScheduler(object):
    def __init__(self, schedule, scores, arenas, config):
        self.schedule = schedule
        self.scores = scores
        self.arenas = arenas
        self.config = config

        # The knockout matches appear in the normal matches list
        # but this list provides them in groups of rounds.
        # e.g. self.knockout_rounds[-2] gives the semi-final matches
        # and self.knockout_rounds[-1] gives the final match (in a list)
        # Note that the ordering of the matches within the rounds
        # in this list is important (e.g. self.knockout_rounds[0][0] is
        # will involve the top seed, whilst self.knockout_rounds[0][-1] will
        # involve the second seed).
        self.knockout_rounds = []

        self.R = stable_random.Random()

    def _played_all_league_matches(self):
        "Returns True if we've played all league matches"
        for arena_matches in self.schedule.matches:
            for match in arena_matches.values():
                if match.type != LEAGUE_MATCH:
                    continue

                if (match.arena, match.num) not in self.scores.league.game_points:
                    return False

        return True

    def _seed_teams(self):
        "Sort teams by their league scores"
        team_scores = self.scores.league.teams

        if not self._played_all_league_matches():
            # Use "???" as the "we don't know yet marker"
            return ["???"] * len(team_scores)

        def score_cmp(x,y):
            return cmp(x[1].league_points,y[1].league_points)

        seeded_teams = sorted(team_scores.items(), cmp=score_cmp, reverse=True)
        return [x[0] for x in seeded_teams]

    def _add_round_of_matches(self, matches):
        """Add a whole round of matches

        matches is a list of lists of teams for each match"""

        self.knockout_rounds += [[]]

        while len(matches):
            new_matches = {}
            for arena in self.arenas:
                teams = matches.pop(0)

                # Randomise the zones
                self.R.shuffle(teams)

                start_time = self.next_time
                end_time = start_time + self.schedule.match_period
                num = len(self.schedule.matches)

                match = Match(num, arena, teams, start_time, end_time, KNOCKOUT_MATCH)
                self.knockout_rounds[-1].append(match)
                new_matches[arena] = match

                if len(matches) == 0:
                    break

            self.next_time += self.schedule.match_period
            self.schedule.matches.append(new_matches)

    def _add_round(self):
        prev_round = self.knockout_rounds[-1]
        matches = []

        for i in range(0,len(prev_round),2):
            winners = []
            for parent in prev_round[i:i+2]:
                "Find the parent match's winners"
                desc = (parent.arena, parent.num)

                if desc not in self.scores.knockout.ranked_points:
                    "Parent match hasn't been scored yet"
                    winners += [ "???", "???" ]
                else:
                    s = self.scores.knockout.ranked_points[desc].items()

                    def srt(x,y):
                        return cmp(x[1],y[1])

                    w = sorted(s, cmp=srt)[-2:]
                    winners += [x[0] for x in w]

            matches.append(winners)

        self._add_round_of_matches(matches)

    def _add_first_round(self):
        teams = self._seed_teams()

        # Seed the random generator with the seeded team list
        # This makes it unpredictable which teams will be in which zones
        # until the league scores have been established
        self.R.seed(tuple(teams))

        matches = []

        for seeds in knockout.first_round_seeding(len(teams)):
            match_teams = [teams[seed] for seed in seeds]
            matches.append( match_teams )

        self._add_round_of_matches(matches)

    def add_knockouts(self):
        self.next_time = self.config["match_periods"]["knockout"][0]["start_time"]

        self._add_first_round()

        while len(self.knockout_rounds[-1]) > 1:

            # Add the delay between rounds
            self.next_time += timedelta(seconds=self.config["knockout"]["round_spacing"])

            if len(self.knockout_rounds[-1]) == 2:
                "Extra delay before the final match"
                self.next_time += timedelta(seconds=self.config["knockout"]["final_delay"])

            self._add_round()

class MatchSchedule(object):
    @classmethod
    def create(cls, config_fname, scores, arenas):
        y = yaml_loader.load(config_fname)

        schedule = cls(y)

        k = KnockoutScheduler(schedule, scores, arenas, y)
        k.add_knockouts()

        schedule.knockout_rounds = k.knockout_rounds

        return schedule

    def __init__(self, y):
        self.match_periods = []
        for e in y["match_periods"]["league"]:
            if "max_end_time" in e:
                max_end_time = e["max_end_time"]
            else:
                max_end_time = e["end_time"]

            period = MatchPeriod(e["start_time"], e["end_time"], max_end_time, \
                                    e["description"], [])
            self.match_periods.append(period)

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
                    match = Match(match_n, arena_name, teams, start_time, end_time, LEAGUE_MATCH)
                    m[arena_name] = match

                period.matches.append(m)
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
            if arena in arenas:
                match = arenas[arena]

                if when >= match.start_time and when < match.end_time:
                    return match

        # No match at that time
        return None

    def current_match(self, arena):
        now = datetime.datetime.utcnow()
        return self.match_at(arena, now)

    def match_after(self, arena, when):
        """Return the next match starting after the given time

        If there's no next match, returns None."""
        for arenas in self.matches:
            match = arenas[arena]

            if match.start_time > when:
                return match

        return None
