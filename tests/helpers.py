
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class FakeScorer(object):
    def __init__(self, score_data):
        self.score_data = score_data

    def calculate_scores(self):
        scores = {}
        for team, info in self.score_data.items():
            scores[team] = info['score']
        return scores
