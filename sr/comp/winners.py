"""Calculation of winners of awards.

The awards calculated are:

 * 1st place,
 * 2nd place,
 * 3rd place,
 * Rookie award (rookie team with highest league position)."""

from collections import namedtuple
from enum import Enum, unique
import os.path

from sr.comp.ranker import calc_positions
from . import yaml_loader

@unique
class Award(Enum):
    """Award types.

    These correspond with awards as specified in the rulebook."""
    first     = "first"        # First place
    second    = "second"       # Second place
    third     = "third"        # Third place
    rookie    = "rookie"       # Rookie award
    committee = "committee"    # Committee award
    image     = "image"        # Robot and Team Image award
    movement  = "movement"     # First Movement award
    web       = "web"          # Online Presence award


def _compute_main_awards(scores, knockout_rounds, teams):
    """Compute awards resulting from the grand finals."""
    last_match_info = knockout_rounds[-1][0]
    last_match_key = (last_match_info.arena, last_match_info.num)
    try:
        positions = scores.knockout.game_positions[last_match_key]
    except KeyError:
        # We haven't scored the finals yet
        return {}
    awards = {}
    for award, key in ((Award.first, 1),
                       (Award.second, 2),
                       (Award.third, 3)):
        candidates = positions.get(key, ())
        awards[award] = list(sorted(candidates))
    return awards


def _compute_rookie_award(scores, teams):
    """Compute the winner of the rookie award."""
    rookie_positions = {team: position
                         for team, position in scores.league.positions.items()
                         if teams[team].rookie}
    # It's possible there are no rookie teams, in which case nobody gets
    # the award.
    if not rookie_positions:
        return {Award.rookie: []}
    # Position go from 1 upwards (1 being first), so the best is the minimum
    best_position = min(rookie_positions.values())
    return {Award.rookie: list(sorted(team for team, position in rookie_positions.items()
                                       if position == best_position))}


def _compute_explicit_awards(path):
    """Compute awards explicitly provided in the compstate repo."""
    if not os.path.exists(path):
        return {}
    explicit_awards = yaml_loader.load(path)
    return {Award(key): [value] if isinstance(value, str) else value
              for key, value in explicit_awards.items()}


def compute_awards(scores, knockout_rounds, teams, path=None):
    """Compute the awards handed out from configuration.

    ``scores`` is a ``Scores`` object. ``knockout_rounds`` is a list of
    knockout rounds as produced by a scheduler. ``teams`` is a mapping from
    TLAs to ``Team`` objects.

    A dictionary of ``Award`` types to TLAs is returned. This may not have a
    key for any award type that has not yet been determined."""
    awards = {}
    awards.update(_compute_main_awards(scores, knockout_rounds, teams))
    awards.update(_compute_rookie_award(scores, teams))
    if path is not None:
        awards.update(_compute_explicit_awards(path))
    return awards
