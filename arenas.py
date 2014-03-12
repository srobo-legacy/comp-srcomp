from collections import namedtuple
import yaml

try:
    from yaml import CLoader as YAML_Loader
except ImportError:
    from yaml import Loader as YAML_Loader

Corner = namedtuple("Corner", ["number", "colour"])

def load_arenas(fname):
    "Load arenas from a YAML file"

    with open(fname, "r") as f:
        y = yaml.load(f, Loader = YAML_Loader)

    arenas = []
    for name in y["arenas"]:
        arenas.append(name)

    return arenas

def load_corners(fname):
    "Load corner colours from a YAML file"

    with open(fname, "r") as f:
        y = yaml.load(f, Loader = YAML_Loader)

    corners = {}
    for n, colour in y["corner_colours"].iteritems():
        c = Corner(n, colour)
        corners[n] = c

    return corners
