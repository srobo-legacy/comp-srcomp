"""Calculation of winners of awards.

The awards calculated are:

 * 1st place,
 * 2nd place,
 * 3rd place,
 * Rookie award (rookie team with highest league position)."""

from collections import namedtuple
from enum import Enum, unique

@unique
class Award(Enum):
    """Award types.

    These correspond with awards as specified in the rulebook."""
    first = 1
    second = 2
    third = 3
    rookie = 4


def _compute_main_awards(scores, knockout_rounds, teams):
    """Compute awards resulting from the grand finals."""
    last_match_info = knockout_rounds[-1][0]
    last_match_key = (last_match_info.arena, last_match_info.num)
    try:
        last_match_points = scores.knockout.ranked_points[last_match_key]
    except KeyError:
        # We haven't scored the finals yet
        return {}
    teams = last_match_info.teams[:]
    teams.sort(key=lambda k: last_match_points[k],
               reverse=True)
    return {Award.first:  teams[0],
            Award.second: teams[1],
            Award.third:  teams[2]}


def compute_awards(scores, knockout_rounds, teams):
    """Compute the awards handed out from configuration.

    ``scores`` is a ``Scores`` object. ``knockout_rounds`` is a list of
    knockout rounds as produced by a scheduler. ``teams`` is a mapping from
    TLAs to ``Team`` objects.

    A dictionary of ``Award`` types to TLAs is returned. This may not have a
    key for any award type that has not yet been determined."""
    awards = {}
    awards.update(_compute_main_awards(scores, knockout_rounds, teams))
    return awards
