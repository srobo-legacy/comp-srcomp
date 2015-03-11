"""Team metadata library."""

from collections import namedtuple

from sr.comp import yaml_loader


Team = namedtuple('Team', ['tla', 'name', 'rookie', 'dropped_out'])


def load_teams(filename):
    """
    Load teams from a YAML file.

    :param str filename: The filename of the YAML file to load.
    :return: A dictionary mapping TLAs to :class:`Team` objects.
    """

    data = yaml_loader.load(filename)

    teams = {}
    for tla, info in data['teams'].items():
        tla = tla.upper()
        teams[tla] = Team(tla=tla,
                          name=info['name'],
                          rookie=info.get('rookie', False),
                          dropped_out=info.get('dropped_out', False))

    return teams
