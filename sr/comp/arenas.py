from collections import namedtuple, OrderedDict

from . import yaml_loader


Arena = namedtuple('Arena', ['name', 'display_name', 'colour'])
Corner = namedtuple("Corner", ["number", "colour"])


def load_arenas(fname):
    "Load arenas from a YAML file"

    y = yaml_loader.load(fname)

    arenas_data = y['arenas']

    arenas = OrderedDict()
    for name in sorted(arenas_data.keys()):
        d = arenas_data[name]
        arenas[name] = Arena(name, d['display_name'],
                             d.get('colour', '#FFFFFF'))

    return arenas


def load_corners(fname):
    "Load corner colours from a YAML file"

    y = yaml_loader.load(fname)

    corners = OrderedDict()
    for number, corner in y['corners'].items():
        corners[number] = Corner(number, corner['colour'])

    return corners
