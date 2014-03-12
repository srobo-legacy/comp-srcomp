from collections import namedtuple
import yaml

try:
    from yaml import CLoader as YAML_Loader
except ImportError:
    from yaml import Loader as YAML_Loader

Arena = namedtuple("Arena", ["name"])

def load_arenas(fname):
    "Load arenas from a YAML file"

    with open(fname, "r") as f:
        y = yaml.load(f, Loader = YAML_Loader)

    arenas = []
    for name in y["arenas"]:
        arenas.append(name)

    return arenas
