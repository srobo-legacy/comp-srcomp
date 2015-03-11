"""Arena and corner loading routines."""

from collections import namedtuple, OrderedDict

from sr.comp import yaml_loader


Arena = namedtuple('Arena', ['name', 'display_name', 'colour'])
Corner = namedtuple("Corner", ["number", "colour"])


def load_arenas(filename):
    """
    Load arenas from a YAML file.

    :param str filename: The filename of the YAML file to load arenas from.
    :return: A :class:`collections.OrderedDict` mapping arena names to
             :class:`Arena` objects.
    """

    y = yaml_loader.load(filename)

    arenas_data = y['arenas']

    arenas = OrderedDict()
    for name in sorted(arenas_data.keys()):
        d = arenas_data[name]
        arenas[name] = Arena(name, d['display_name'],
                             d.get('colour', '#FFFFFF'))

    return arenas


def load_corners(filename):
    """
    Load corner colours from a YAML file.

    :param str filename: The filename of the YAML file to load corners from.
    :return: An :class:`collections.OrderedDict` mapping corner numbers to
             :class:`Corner` objects.
    """

    y = yaml_loader.load(filename)

    corners = OrderedDict()
    for number, corner in y['corners'].items():
        corners[number] = Corner(number, corner['colour'])

    return corners
