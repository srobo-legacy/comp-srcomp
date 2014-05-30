
from collections import namedtuple
import imp
import os
from subprocess import check_output

import arenas
import matches
import scores
import teams

_scorer = None

def _get_scorer():
    global _scorer
    if _scorer is None:
        mydir = os.path.dirname(os.path.abspath(__file__))
        root = os.path.join(mydir, "scoring-2014/lib")
        imp.load_source("score_logic", os.path.join(root, "score_logic.py"))
        m = imp.load_source("scorer", os.path.join(root, "scorer.py"))
        _scorer = getattr(m, "Scorer")
    return _scorer

class SRComp(object):
    def __init__(self, root):
        self.root = root
        self.state = check_output("git rev-parse HEAD", shell=True, cwd=root).strip()
        self.teams = teams.load_teams(os.path.join(root, "teams.yaml"))
        self.scores = scores.Scores(root, self.teams.keys(), _get_scorer())
        self.arenas = arenas.load_arenas(os.path.join(root, "arenas.yaml"))
        schedule_fname = os.path.join(root, "schedule.yaml")
        self.schedule = matches.MatchSchedule.create(schedule_fname,
                                                     self.scores, self.arenas)
        self.corners = arenas.load_corners(os.path.join(root, "arenas.yaml"))
