
import os
import mock

# Hack the path
import helpers as test_helpers

from scores import LeagueScores

def get_basic_data():
    the_data = {
        'match_number': 123,
        'arena_id': 'A',
        'teams': {
            'JMS': {
                'zone_tokens': {0: 0, 1: 0, 2: 0, 3: 2},
                'slot_bottoms': {0: 0, 1: 0, 2: 0, 3: 1, 4: 0, 5: 1, 6: 0, 7: 0},
                'robot_moved': False,
                'upright_tokens': 1,
                'disqualified': True,
                'zone': 3
            },
            'PAS': {
                'zone_tokens': {0: 0, 1: 0, 2: 0, 3: 0},
                'slot_bottoms': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0},
                'robot_moved': True,
                'upright_tokens': 0,
                'zone': 4
            },
            'RUN': {
                'zone_tokens': {0: 0, 1: 0, 2: 0, 3: 0},
                'slot_bottoms': {0: 1, 1: 1, 2: 1, 3: 0, 4: 1, 5: 0, 6: 0, 7: 0},
                'robot_moved': False,
                'upright_tokens': 1,
                'zone': 1
            },
            'ICE': {'zone_tokens': {0: 0, 1: 0, 2: 0, 3: 0},
                'slot_bottoms': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 1},
                'robot_moved': True,
                'upright_tokens': 0,
                'zone': 2
            }
        }
    }
    return the_data

def load_data(the_data):
    with mock.patch('matches.yaml_loader.load') as mock_loader, \
            mock.patch('scores.results_finder') as mock_finder:

        mock_finder.return_value = ['whatever.yaml']
        mock_loader.return_value = the_data

        teams = the_data['teams'].keys()

        scores = LeagueScores('somewhere', teams)
        return scores

def load_basic_data():
    return load_data(get_basic_data())

def test_game_points():
    scores = load_basic_data()

    games = scores.game_points
    assert len(games) == 1

    id_ = ('A', 123)
    assert id_ in games

    game = games[id_]

    assert game == {'JMS': 4, 'PAS': 1, 'RUN': 8, 'ICE': 2}

def test_league_points():
    scores = load_basic_data()

    leagues = scores.match_league_points
    assert len(leagues) == 1

    id_ = ('A', 123)
    assert id_ in leagues

    league = leagues[id_]

    assert league == {'JMS': 0.0, 'PAS': 2.0, 'RUN': 4.0, 'ICE': 3.0}
