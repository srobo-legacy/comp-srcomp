from __future__ import print_function

from collections import defaultdict
import sys

from .knockout_scheduler import UNKNOWABLE_TEAM
NO_TEAM = None

META_TEAMS = set([NO_TEAM, UNKNOWABLE_TEAM])


def report_errors(type_, id_, errors):
    if len(errors) == 0:
        return

    print("{0} {1} has the following errors:".format(type_, id_),
          file=sys.stderr)
    for error in errors:
        print("    {0}".format(error), file=sys.stderr)


def validate(comp):
    count = 0
    count += validate_schedule(comp.schedule, comp.teams.keys())
    count += validate_scores(comp.scores.league, comp.schedule.matches)
    warn_missing_scores(comp.scores.league, comp.schedule.matches)
    return count


def validate_schedule(schedule, possible_teams):
    """Check that the schedule contains enough time for all the matches,
    and that the matches themselves are valid."""
    count = 0
    for num, match in enumerate(schedule.matches):
        errors = validate_match(match, possible_teams)
        count += len(errors)
        report_errors('Match', num, errors)

    warnings = validate_schedule_count(schedule)
    report_errors('Schedule', '', warnings)

    errors = validate_schedule_timings(schedule.matches, schedule.match_duration)
    count += len(errors)
    if len(errors):
        errors.append("This usually indicates that the scheduled periods "
                      "overlap.")
    report_errors('Schedule', 'timing', errors)

    return count


def validate_schedule_count(schedule):
    planned = schedule.n_planned_league_matches
    actual = schedule.n_league_matches
    errors = []
    if planned > actual:
        msg = "Only contains enough time for {0} matches, {1} are planned" \
                .format(actual, planned)
        errors.append(msg)
    if planned == 0:
        errors.append("Doesn't contain any matches")

    return errors


def validate_schedule_timings(scheduled_matches, match_duration):
    timing_map = defaultdict(list)
    for match in scheduled_matches:
        game = list(match.values())[0]
        time = game.start_time
        timing_map[time].append(game.num)

    errors = []
    last_time = None
    for time, match_numbers in sorted(timing_map.items()):
        if len(match_numbers) != 1:
            ids = ", ".join(str(num) for num in match_numbers)
            errors.append("Multiple matches scheduled for {0}:"
                          " {1}.".format(time, ids))

        if last_time is not None and time - last_time < match_duration:
            prev_ids = ", ".join(str(num) for num in timing_map[last_time])
            ids = ", ".join(str(num) for num in match_numbers)
            errors.append("Matches {0} start at {1} "
                          "before matches {2} have finished.".format(ids,
                                                                     time,
                                                                     prev_ids))

        last_time = time

    return errors


def validate_match(match, possible_teams):
    """Check that the teams featuring in a match exist and are only
    required in one arena at a time."""
    errors = []
    all_teams = []

    for a in match.values():
        all_teams += a.teams

    teams = set(all_teams) - META_TEAMS
    for t in teams:
        all_teams.remove(t)

    duplicates = set(all_teams) - META_TEAMS
    if len(duplicates):
        duplicates = ", ".join(duplicates)
        errors.append("Teams {0} appear more than once.".format(duplicates))

    extras = teams - set(possible_teams)

    if len(extras):
        extras = ", ".join(extras)
        errors.append("Teams {0} do not exist.".format(extras))

    return errors


def validate_scores(scores, schedule):
    # NB: more specific validation is already done during the scoring,
    # so all we need to do is check that the right teams are being awarded
    # points

    count = 0

    def get_scheduled_match(match_id, type_):
        """Check that the requested match was scheduled, return it if so."""
        num = match_id[1]
        if num < 0 or num >= len(schedule):
            report_errors(type_, match_id, ['Match not scheduled'])
            return None

        arena = match_id[0]
        match = schedule[num]
        if arena not in match:
            report_errors(type_, match_id, ['Arena not in this match'])
            return None

        return match[arena]

    def check(type_, match_id, match):
        scheduled_match = get_scheduled_match(match_id, type_)
        if scheduled_match is None:
            return 1

        errors = validate_match_score(match, scheduled_match)
        report_errors(type_, match_id, errors)
        return len(errors)

    for match_id, match in scores.game_points.items():
        count += check('Game Score', match_id, match)

    for match_id, match in scores.ranked_points.items():
        count += check('League Points', match_id, match)

    return count


def validate_match_score(match_score, scheduled_match):
    """Check that the match awards points to the right teams, by checking
    that the teams with points were scheduled to appear in the match."""
    # only remove the empty corner marker -- we shouldn't have unknowable
    # teams in the match schedule by the time there's a score for it.
    expected_teams = set(scheduled_match.teams) - set([NO_TEAM])
    # don't remove meta teams from the score's teams -- they shouldn't
    # be there to start with.
    actual_teams = set(match_score.keys())

    extra = actual_teams - expected_teams
    missing = expected_teams - actual_teams

    errors = []
    if len(missing):
        missing = ', '.join(missing)
        errors.append("Teams {0} missing from this match.".format(missing))

    if len(extra):
        extra = ', '.join(extra)
        errors.append("Teams {0} not scheduled in this match.".format(extra))

    return errors


def warn_missing_scores(scores, schedule):
    """Check that the scores up to the most recent are all present."""
    match_ids = scores.ranked_points.keys()
    last_match = scores.last_scored_match

    missing = find_missing_scores(match_ids, last_match, schedule)
    if len(missing) == 0:
        return

    print("The following scores are missing:", file=sys.stderr)
    print("Match   | Arena ", file=sys.stderr)
    for m in missing:
        arenas = ", ".join(sorted(m[1]))
        print(" {0:>3}    | {1}".format(m[0], arenas), file=sys.stderr)


def find_missing_scores(match_ids, last_match, schedule):
    # If no matches have been scored, no scores can be missing.
    if last_match is None:
        return ()

    expected = set()
    for num, match in enumerate(schedule):
        if num > last_match:
            break
        for arena in match.keys():
            id_ = (arena, num)
            expected.add(id_)

    missing_ids = expected - set(match_ids)
    missing = defaultdict(set)
    for id_ in missing_ids:
        arena = id_[0]
        num = id_[1]
        missing[num].add(arena)

    missing_items = sorted(missing.items())
    return missing_items
