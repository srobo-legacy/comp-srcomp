"Team metadata library"
from collections import namedtuple
import yaml

try:
    from yaml import CLoader as YAML_Loader
except ImportError:
    from yaml import Loader as YAML_Loader

Team = namedtuple("Team",
                  ["tla", "name"])

def load_teams(fname):
    "Load teams from a YAML file"

    with open(fname, "r") as f:
        y = yaml.load(f, Loader = YAML_Loader)

    teams = {}
    for tla, info in y["teams"].iteritems():
        tla = tla.upper()
        teams[tla] = Team(tla,info["name"])

    return teams

