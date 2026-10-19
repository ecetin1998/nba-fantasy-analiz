import pytest
import pandas as pd

import storage
from analysis import points_scores


def test_yahoo_default_points_are_automatically_loaded(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DB_PATH', tmp_path / 'fantasy.sqlite3')
    storage.init()
    assert storage.get_weights('benny bilanço') == storage.YAHOO_DEFAULT_POINTS
    assert storage.get_weights('emo361') == storage.YAHOO_DEFAULT_POINTS
    assert storage.get_weights('myopia') == {}


def test_standard_yahoo_points_computes_only_six_categories(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DB_PATH', tmp_path / 'fantasy.sqlite3')
    storage.init()
    from test_analysis import sample
    weights = storage.get_weights('benny bilanço')
    frame = points_scores(sample(), weights)
    p = frame.set_index('PLAYER_ID').loc['2', 'FPTS_PG']
    # 24 PTS, 8 REB, 5 AST, 2 STL, 1 BLK, 3 TOV
    expected = 24 + 8*1.2 + 5*1.5 + 2*3 + 1*3 - 3
    assert p == pytest.approx(expected)
    assert p == pytest.approx(47.1)


def test_can_override_then_reset_to_default(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DB_PATH', tmp_path / 'fantasy.sqlite3')
    storage.init()
    storage.save_weights('emo361', {'PTS': 3.0})
    assert storage.get_weights('emo361') == {'PTS': 3.0}
    storage.reset_weights('emo361')
    assert storage.get_weights('emo361') == storage.YAHOO_DEFAULT_POINTS
