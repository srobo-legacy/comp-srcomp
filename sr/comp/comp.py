
import os
from subprocess import check_output

from . import arenas
from . import matches
from . import scores
from . import teams

from scorer import Scorer

class SRComp(object):
    def __init__(self, root):
        self.root = root
        self.state = check_output("git rev-parse HEAD", shell=True, cwd=root).strip()
        self.teams = teams.load_teams(os.path.join(root, "teams.yaml"))
        self.scores = scores.Scores(root, self.teams.keys(), Scorer)
        self.arenas = arenas.load_arenas(os.path.join(root, "arenas.yaml"))
        schedule_fname = os.path.join(root, "schedule.yaml")
        self.schedule = matches.MatchSchedule.create(schedule_fname,
                                                     self.scores, self.arenas)
        self.corners = arenas.load_corners(os.path.join(root, "arenas.yaml"))
