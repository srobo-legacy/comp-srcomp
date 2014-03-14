"Team metadata library"
from collections import namedtuple

import yaml_loader

Team = namedtuple("Team",
                  ["tla", "name"])

def load_teams(fname):
    "Load teams from a YAML file"

    y = yaml_loader.load(fname)

    teams = {}
    for tla, info in y["teams"].iteritems():
        tla = tla.upper()
        teams[tla] = Team(tla,info["name"])

    return teams

