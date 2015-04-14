# -*- coding: utf-8 -*-

from datetime import datetime
from sr.comp.match_period import MatchPeriod

def test_period_str():
    start = datetime(2014, 01, 01, 13, 12, 14)
    end = datetime(2014, 01, 01, 20, 06, 35)
    period = MatchPeriod(start, end, None, "desc", None, None)

    string = str(period)

    assert "desc (13:12–20:06)" == string, "Wrong string"
