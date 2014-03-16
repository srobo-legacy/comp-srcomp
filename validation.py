
import sys

def report_errors(type_, id_, errors):
    if len(errors) == 0:
        return

    print >>sys.stderr, "{0} {1} has the following errors:".format(type_, id_)
    for error in errors:
        print >>sys.stderr, "    {0}".format(error)

def validate(comp):
    count = 0
    count += validate_schedule(comp.schedule, comp.teams.keys())
    return count

def validate_schedule(schedule, possible_teams):
    count = 0
    for num, match in enumerate(schedule.matches):
        errors = validate_match(match, possible_teams)
        count += len(errors)
        report_errors('Match', num, errors)

    planned = schedule.n_planned_matches
    actual = schedule.n_matches()
    if planned != actual:
        count += 1
        msg = "Only contains enough time for {0} matches, {1} are planned" \
                .format(planned, actual)
        report_errors('Schedule', '', [msg])

    return count

def validate_match(match, possible_teams):
    errors = []
    all_teams = []

    for a in match.values():
        all_teams += a.teams

    teams = set(all_teams)
    for t in teams:
        all_teams.remove(t)

    if len(all_teams):
        duplicates = ", ".join(set(all_teams))
        errors.append("Teams {0} appear more than once.".format(duplicates))

    extras = teams - set(possible_teams)

    if len(extras):
        extras = ", ".join(extras)
        errors.append("Teams {0} do not exist.".format(extras))

    return errors
