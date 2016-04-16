"""Venue layout metadata library."""

from collections import Counter
from itertools import chain

from sr.comp import yaml_loader


class InvalidRegionException(Exception):
    """
    An exception that occurs when there are invalid regions mentioned in
    the shepherding data.
    """
    def __init__(self, region, area):
        tpl = "Invalid region '{0}' found in shepherding area '{1}'"
        super(InvalidRegionException, self).__init__(tpl.format(region, area))

        self.region = region
        self.area = area


class LayoutTeamsException(Exception):
    """
    An exception that occurs when there are duplicate, extra or missing
    teams in a layout.
    """
    def __init__(self, duplicate_teams, extra_teams, missing_teams):
        details = []

        for label, teams in (('duplicate', duplicate_teams),
                             ('extra', extra_teams),
                             ('missing', missing_teams)):
            if teams:
                details.append('{0}: '.format(label) + ', '.join(teams))

        assert details, "No bad teams given to LayoutTeamsException!"

        detail = '; '.join(details)
        tpl = "Duplicate, extra or missing teams in the layout! ({0})"
        super(LayoutTeamsException, self).__init__(tpl.format(detail))

        self.duplicate_teams = duplicate_teams
        self.extra_teams = extra_teams
        self.missing_teams = missing_teams


class Venue(object):
    """A class providing information about the layout within the venue."""

    @staticmethod
    def check_teams(teams, teams_layout):
        """
        Check that the given layout of teams contains the same set of
        teams as the reference.

        Will throw a LayoutTeamsException if there are any missing,
        extra or duplicate teams found.

        :param list teans: The reference list of teams in the competition.
        :param list teams_layout: A list of maps with a list of teams
                                  under the ``teams`` key.
        """

        layout_teams = list(chain.from_iterable(r['teams'] for r in teams_layout))
        duplicate_teams = [team for team, count in Counter(layout_teams).items() if count > 1]

        teams_set = set(teams)
        layout_teams_set = set(layout_teams)

        extra_teams = layout_teams_set - teams_set
        missing_teams = teams_set - layout_teams_set

        if duplicate_teams or extra_teams or missing_teams:
            raise LayoutTeamsException(duplicate_teams, extra_teams, missing_teams)


    def __init__(self, teams, layout_file, shepherding_file):

        layout_data = yaml_loader.load(layout_file)
        teams_layout = layout_data['teams']
        self.check_teams(teams, teams_layout)

        shepherding_data = yaml_loader.load(shepherding_file)
        shepherds = shepherding_data['shepherds']

        self.locations = {r['name']: r for r in teams_layout}
        """
        A :class:`dict` of location names (from the layout file) to location
        information, including which teams are in that location and the
        shepherding region which contains that location.
        """

        self._team_locations = {}

        for location in teams_layout:
            for team in location['teams']:
                self._team_locations[team] = location

        for area in shepherds:
            for region in area.get('regions', []):
                location = self.locations.get(region)
                if not location:
                    raise InvalidRegionException(region, area['name'])

                location['shepherds'] = {
                    "name": area['name'],
                    "colour": area['colour'],
                }


    def get_team_location(self, team):
        """
        Get the name of the location allocated to the given team within
        the venue.

        :param str tean: The TLA of the team in question.
        :returns: The name of the location allocated to the team.
        """

        return self._team_locations[team]['name']
