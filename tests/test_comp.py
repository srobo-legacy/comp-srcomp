
import os
import datetime

# Hack the path
import helpers as test_helpers

from sr.comp.comp import SRComp

DUMMY_PATH = os.path.dirname(os.path.abspath(__file__)) + '/dummy'
INSTANCE = SRComp(DUMMY_PATH)

def test_load():
    "Test that loading the dummy state works"
    assert INSTANCE.root
    assert INSTANCE.state
    assert INSTANCE.teams
    assert INSTANCE.schedule
    assert INSTANCE.scores
    assert INSTANCE.arenas
    assert INSTANCE.corners

def test_timezone():
    # Test that one can get the timezone from the dummy state
    assert (INSTANCE.timezone.utcoffset(datetime.datetime(2014, 4, 26)) ==
            datetime.timedelta(seconds=3600))
