from collections import namedtuple, OrderedDict

from . import yaml_loader


Arena = namedtuple('Arena', ['name', 'display_name'])
Corner = namedtuple("Corner", ["number", "colour"])


def load_arenas(fname):
    "Load arenas from a YAML file"

    y = yaml_loader.load(fname)

    arenas_data = y['arenas']

    arenas = OrderedDict()
    for name in sorted(arenas_data.keys()):
        arenas[name] = Arena(name, arenas_data[name]['display_name'])

    return arenas


def load_corners(fname):
    "Load corner colours from a YAML file"

    y = yaml_loader.load(fname)

    corners = OrderedDict()
    for number, corner in y['corners'].items():
        corners[number] = Corner(number, corner['colour'])

    return corners
