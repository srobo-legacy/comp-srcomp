"""Calculation of winners of awards.

The awards calculated are:

 * 1st place,
 * 2nd place,
 * 3rd place,
 * Rookie award (rookie team with highest league position)."""

from collections import namedtuple
from enum import Enum, unique

from sr.comp.ranker import calc_positions

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
        last_match_points = scores.knockout.game_points[last_match_key]
        last_match_ranked_points = scores.knockout.ranked_points[last_match_key]
    except KeyError:
        # We haven't scored the finals yet
        return {}
    positions = calc_positions(last_match_points, [tla for tla, rp in last_match_ranked_points.items() if rp == 0])
    awards = {}
    for award, key in ((Award.first, 1),
                       (Award.second, 2),
                       (Award.third, 3)):
        candidates = positions.get(key, ())
        if len(candidates) == 1:
            winner, = candidates
            awards[award] = winner
    return awards


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
