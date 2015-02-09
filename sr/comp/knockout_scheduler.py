import math
from datetime import timedelta

from . import stable_random
from . import knockout
from .match_period import MatchPeriod, Match, MatchType

# Use '???' as the "we don't know yet" marker
UNKNOWABLE_TEAM = '???'

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
                if match.type != MatchType.league:
                    continue

                if (match.arena, match.num) not in self.scores.league.game_points:
                    return False

        return True

    def _add_round_of_matches(self, matches, arenas):
        """Add a whole round of matches

        matches is a list of lists of teams for each match"""

        self.knockout_rounds += [[]]

        while len(matches):
            while len(self.delays) and self.delays[0].time <= self.next_time:
                self.delay += self.delays.pop(0).delay

            new_matches = {}
            for arena in arenas:
                teams = matches.pop(0)

                if len(teams) < 4:
                    "Fill empty zones with None"
                    teams += [None] * (4-len(teams))

                # Randomise the zones
                self.R.shuffle(teams)

                start_time = self.next_time + self.delay
                end_time = start_time + self.schedule.match_period
                num = len(self.schedule.matches)

                match = Match(num, arena, teams, start_time, end_time, MatchType.knockout)
                self.knockout_rounds[-1].append(match)
                new_matches[arena] = match

                if len(matches) == 0:
                    break

            self.next_time += self.schedule.match_period
            self.schedule.matches.append(new_matches)
            self.period.matches.append(new_matches)

    def get_ranking(self, game):
        "Get a ranking of the given match's teams"
        desc = (game.arena, game.num)
        positions = self.scores.league.positions

        # Get the score if present (will be a tla -> 'league points' map)
        points = self.scores.knockout.ranked_points.get(desc, None)

        if points is None:
            "Given match hasn't been scored yet"
            return [UNKNOWABLE_TEAM] * 4

        def key(item):
            # Lexicographically sort by game result, then by league position
            # League positions are sorted in the opposite direction
            return item[1], -positions.get(item[0], 0)

        # Sort by points with tie resolution
        # Note that this list is upside down compared to what might be
        # expected, ie the winner is at the end of the list
        with_points = sorted(points.items(), key=key)

        # Extract just TLAs
        ranking = [x[0] for x in with_points]

        return ranking

    def get_winners(self, game):
        "Find the parent match's winners"

        ranking = self.get_ranking(game)
        return ranking[-2:]

    def _add_round(self, arenas):
        prev_round = self.knockout_rounds[-1]
        matches = []

        for i in range(0,len(prev_round),2):
            winners = []
            for parent in prev_round[i:i+2]:
                winners += self.get_winners(parent)

            matches.append(winners)

        self._add_round_of_matches(matches, arenas)

    def _add_first_round(self, arity):
        teams = list(self.scores.league.positions.keys())

        if not self._played_all_league_matches():
            teams = [UNKNOWABLE_TEAM] * len(teams)

        # Seed the random generator with the seeded team list
        # This makes it unpredictable which teams will be in which zones
        # until the league scores have been established
        self.R.seed("".join(teams).encode("utf-8"))

        matches = []

        for seeds in knockout.first_round_seeding(arity):
            match_teams = [teams[seed] for seed in seeds]
            matches.append( match_teams )

        self._add_round_of_matches(matches, self.arenas)

    def add_knockouts(self):
        period = self.config["match_periods"]["knockout"][0]
        self.next_time = period["start_time"]

        self.period = MatchPeriod(self.next_time, period["end_time"], \
                                  period["end_time"], period["description"], \
                                  [])

        self.delays = []
        for delay in self.schedule.delays:
            "Find delays that occur in the knockouts period"
            if delay.time < self.period.start_time:
                continue
            self.delays.append(delay)

        # The current delay
        self.delay = timedelta()

        knockout_conf = self.config["knockout"]

        n_teams = len(self.scores.league.positions)
        if 'arity' in knockout_conf:
            arity = min(n_teams, knockout_conf['arity'])
        else:
            arity = n_teams
        self._add_first_round(arity)

        while len(self.knockout_rounds[-1]) > 1:

            # Add the delay between rounds
            self.next_time += timedelta(seconds=knockout_conf["round_spacing"])

            # Number of rounds remaining to be added
            rounds_remaining = int(math.log(len(self.knockout_rounds[-1]), 2))

            if rounds_remaining <= knockout_conf["single_arena"]["rounds"]:
                arenas = knockout_conf["single_arena"]["arenas"]
            else:
                arenas = self.arenas

            if len(self.knockout_rounds[-1]) == 2:
                "Extra delay before the final match"
                self.next_time += timedelta(seconds=knockout_conf["final_delay"])

            self._add_round(arenas)
