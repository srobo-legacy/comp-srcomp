
import os

# Hack the path
import helpers as test_helpers

from comp import SRComp

def test_load():
    "Test that loading the dummy state works"
    my_dir = os.path.dirname(os.path.abspath(__file__))
    instance = SRComp(my_dir + '/dummy')

    assert instance.root
    assert instance.teams
    assert instance.schedule
    assert instance.scores
    assert instance.arenas
    assert instance.corners
