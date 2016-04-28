"""Knockout schedule generation."""

import math
from datetime import timedelta

from sr.comp import knockout, stable_random
from sr.comp.match_period import MatchPeriod, Match, MatchType
from sr.comp.match_period_clock import MatchPeriodClock


# Use '???' as the "we don't know yet" marker
UNKNOWABLE_TEAM = '???'


class KnockoutScheduler(object):
    """
    A class that can be used to generate a knockout schedule.

    :param schedule: The league schedule.
    :param scores: The scores.
    :param dict arenas: The arenas.
    :param dict teams: The teams.
    :param config: Custom configuration for the knockout scheduler.
    """

    def __init__(self, schedule, scores, arenas, teams, config):
        self.schedule = schedule
        self.scores = scores
        self.arenas = arenas
        self.teams = teams
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
        """
        Check if all league matches have been played.

        :return: :py:bool:`True` if we've played all league matches.
        """

        for arena_matches in self.schedule.matches:
            for match in arena_matches.values():
                if match.type != MatchType.league:
                    continue

                if (match.arena, match.num) not in \
                        self.scores.league.game_points:
                    return False

        return True

    @staticmethod
    def get_match_display_name(rounds_remaining, round_num, global_num):
        """
        Get a human-readable match display name.

        :param rounds_remaining: The number of knockout rounds remaining.
        :param knockout_num: The match number within the knockout round.
        :param global_num: The global match number.
        """

        if rounds_remaining == 0:
            display_name = 'Final (#{global_num})'
        elif rounds_remaining == 1:
            display_name = 'Semi {round_num} (#{global_num})'
        elif rounds_remaining == 2:
            display_name = 'Quarter {round_num} (#{global_num})'
        else:
            display_name = 'Match {global_num}'
        return display_name.format(round_num=round_num + 1,
                                   global_num=global_num)

    def _add_round_of_matches(self, matches, arenas, rounds_remaining):
        """
        Add a whole round of matches.

        :param list matches: A list of lists of teams for each match.
        """

        self.knockout_rounds += [[]]

        round_num = 0
        while len(matches):
            # Deliberately not using iterslots since we need to ensure
            # that the time advances even after we've run out of matches
            start_time = self.clock.current_time
            end_time = start_time + self.schedule.match_duration

            new_matches = {}
            for arena in arenas:
                teams = matches.pop(0)

                if len(teams) < 4:
                    "Fill empty zones with None"
                    teams += [None] * (4 - len(teams))

                # Randomise the zones
                self.R.shuffle(teams)

                num = len(self.schedule.matches)
                display_name = self.get_match_display_name(rounds_remaining,
                                                           round_num, num)

                match = Match(num, display_name, arena, teams,
                              start_time, end_time, MatchType.knockout,
                              # Just the finals don't use the resolved ranking
                              use_resolved_ranking = rounds_remaining != 0)

                self.knockout_rounds[-1].append(match)
                new_matches[arena] = match

                if len(matches) == 0:
                    break

            self.clock.advance_time(self.schedule.match_duration)
            self.schedule.matches.append(new_matches)
            self.period.matches.append(new_matches)

            round_num += 1

    def get_ranking(self, game):
        """
        Get a ranking of the given match's teams.

        :param game: A game.
        """
        desc = (game.arena, game.num)

        # Get the resolved positions if present (will be a tla -> position map)
        positions = self.scores.knockout.resolved_positions.get(desc, None)

        if positions is None:
            "Given match hasn't been scored yet"
            return [UNKNOWABLE_TEAM] * 4

        # Extract just TLAs
        return list(positions.keys())

    def get_winners(self, game):
        """
        Find the parent match's winners.

        :param game: A game.
        """

        ranking = self.get_ranking(game)
        return ranking[:2]

    def _add_round(self, arenas, rounds_remaining):
        prev_round = self.knockout_rounds[-1]
        matches = []

        for i in range(0, len(prev_round), 2):
            winners = []
            for parent in prev_round[i:i + 2]:
                winners += self.get_winners(parent)

            matches.append(winners)

        self._add_round_of_matches(matches, arenas, rounds_remaining)

    def _get_non_dropped_out_teams(self, for_match):
        teams = list(self.scores.league.positions.keys())
        teams = [tla for tla in teams
                 if self.teams[tla].is_still_around(for_match)]
        return teams

    def _add_first_round(self, conf_arity=None):
        next_match_num = len(self.schedule.matches)
        teams = self._get_non_dropped_out_teams(next_match_num)
        if not self._played_all_league_matches():
            teams = [UNKNOWABLE_TEAM] * len(teams)

        arity = len(teams)
        if conf_arity is not None and conf_arity < arity:
            arity = conf_arity

        # Seed the random generator with the seeded team list
        # This makes it unpredictable which teams will be in which zones
        # until the league scores have been established
        self.R.seed("".join(teams).encode("utf-8"))

        matches = []

        for seeds in knockout.first_round_seeding(arity):
            match_teams = [teams[seed] for seed in seeds]
            matches.append(match_teams)

        rounds_remaining = self.get_rounds_remaining(matches)
        self._add_round_of_matches(matches, self.arenas, rounds_remaining)

    @staticmethod
    def get_rounds_remaining(prev_matches):
        return int(math.log(len(prev_matches), 2))

    def add_knockouts(self):
        """Add the knockouts to the schedule."""

        period = self.config["match_periods"]["knockout"][0]

        self.period = MatchPeriod(period["start_time"], period["end_time"],
                                  period["end_time"], period["description"],
                                  [], MatchType.knockout)

        self.clock = MatchPeriodClock(self.period, self.schedule.delays)

        knockout_conf = self.config["knockout"]
        round_spacing = timedelta(seconds=knockout_conf["round_spacing"])

        self._add_first_round(conf_arity=knockout_conf.get('arity'))

        while len(self.knockout_rounds[-1]) > 1:

            # Add the delay between rounds
            self.clock.advance_time(round_spacing)

            # Number of rounds remaining to be added
            rounds_remaining = self.get_rounds_remaining(self.knockout_rounds[-1])

            if rounds_remaining <= knockout_conf["single_arena"]["rounds"]:
                arenas = knockout_conf["single_arena"]["arenas"]
            else:
                arenas = self.arenas

            if len(self.knockout_rounds[-1]) == 2:
                "Extra delay before the final match"
                final_delay = timedelta(seconds=knockout_conf["final_delay"])
                self.clock.advance_time(final_delay)

            self._add_round(arenas, rounds_remaining - 1)
