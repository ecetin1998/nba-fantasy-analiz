import storage


def test_five_leagues_and_separate_rosters(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DB_PATH', tmp_path / 'fantasy.sqlite3')
    storage.init()
    assert len(storage.TEAMS) == 5
    assert sum(t[2] == 'CAT' for t in storage.TEAMS) == 3
    assert sum(t[2] == 'PTS' for t in storage.TEAMS) == 2
    storage.save_roster('2fe2d', ['1', '2'], ['2'])
    storage.save_roster('myopia', ['1', '3'], [])
    assert storage.get_roster('2fe2d') == (['1', '2'], ['2'])
    assert storage.get_roster('myopia') == (['1', '3'], [])
    storage.save_weights('benny bilanço', {'PTS': 1.0, 'TOV': -2.0})
    storage.save_weights('emo361', {'PTS': 2.0})
    assert storage.get_weights('benny bilanço')['TOV'] == -2.0
    assert storage.get_weights('emo361')['PTS'] == 2.0
