
import os

import arenas
import matches
import scores
import teams


class SRComp(object):
    def __init__(self, root):
        self.root = root
        self.teams = teams.load_teams(os.path.join(root, "teams.yaml"))
        self.schedule = matches.MatchSchedule(os.path.join(root, "schedule.yaml"))
        self.scores = scores.Scores(os.path.join(root, "league"),
                                    self.teams.keys())
        self.arenas = arenas.load_arenas(os.path.join(root, "arenas.yaml"))
        self.corners = arenas.load_corners(os.path.join(root, "arenas.yaml"))
