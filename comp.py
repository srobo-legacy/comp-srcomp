import matches
import os
import scores
import teams


class SRComp(object):
    def __init__(self, root):
        self.root = root
        self.teams = teams.load_teams(os.path.join(root, "teams.yaml"))
        self.schedule = matches.MatchSchedule(os.path.join(root, "config.yml"))
        self.scores = scores.Scores(os.path.join(root, "league"),
                                    self.teams)

