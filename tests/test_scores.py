
import mock

from sr.comp.scores import Scores

def test_last_scored_match_none():

    def check(league_lsm, knockout_lsm, expected):
        with mock.patch('sr.comp.scores.LeagueScores') as ls, \
             mock.patch('sr.comp.scores.KnockoutScores') as ks:
            ls.return_value = mock.Mock(last_scored_match = league_lsm)
            ks.return_value = mock.Mock(last_scored_match = knockout_lsm)

            scores = Scores('', None, None)

            lsm = scores.last_scored_match
            assert expected == lsm

    # No scores yet
    yield check, None, None, None

    # League only
    yield check, 13, None, 13

    # Knokcout only (not actually vaild)
    yield check, None, 42, 42

    # Both present -- always choose knockout value
    yield check, 13, 42, 42
    yield check, 42, 13, 13
