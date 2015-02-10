
import os
import os.path
from subprocess import check_output
import sys
from copy import copy
import imp

from . import arenas
from . import matches
from . import scores
from . import teams


def load_scorer(root):
    # Deep path hacks
    score_directory = os.path.join(root, 'scoring')
    score_source = os.path.join(score_directory, 'score.py')

    saved_path = copy(sys.path)
    sys.path.append(score_directory)

    imported_library = imp.load_source('score.py', score_source)

    sys.path = saved_path

    return imported_library.Scorer


class SRComp(object):
    def __init__(self, root):
        self.root = root
        self.state = check_output(('git', 'rev-parse', 'HEAD'),
                                  universal_newlines=True,
                                  cwd=root).strip()
        self.teams = teams.load_teams(os.path.join(root, "teams.yaml"))
        scorer = load_scorer(root)
        self.scores = scores.Scores(root, self.teams.keys(), scorer)
        self.arenas = arenas.load_arenas(os.path.join(root, "arenas.yaml"))
        schedule_fname = os.path.join(root, "schedule.yaml")
        self.schedule = matches.MatchSchedule.create(schedule_fname,
                                                     self.scores, self.arenas)
        self.timezone = self.schedule.timezone
        self.corners = arenas.load_corners(os.path.join(root, "arenas.yaml"))
