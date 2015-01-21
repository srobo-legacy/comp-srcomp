from collections import namedtuple

from . import yaml_loader


Arena = namedtuple('Arena', ['name', 'display_name'])
Corner = namedtuple("Corner", ["number", "colour"])

def load_arenas(fname):
    "Load arenas from a YAML file"

    y = yaml_loader.load(fname)

    arenas = []
    for name in y["arenas"]:
        arena = Arena(name, name)
        arenas.append(arena)

    return arenas

def load_corners(fname):
    "Load corner colours from a YAML file"

    y = yaml_loader.load(fname)

    corners = {}
    for n, colour in y["corner_colours"].items():
        c = Corner(n, colour)
        corners[n] = c

    return corners
