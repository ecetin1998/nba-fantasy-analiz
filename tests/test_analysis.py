import pandas as pd
import pytest

from analysis import category_scores, normalize, points_scores, roster_analysis, category_punt_view


def sample():
    return pd.DataFrame([
        dict(PLAYER_ID='1', PLAYER_NAME='High pct tiny volume', TEAM_ABBREVIATION='A', GP=1, MIN=20, PTS=2, REB=1, AST=1, STL=0, BLK=0, FG3M=0, TOV=1, FGM=1, FGA=1, FTM=1, FTA=1),
        dict(PLAYER_ID='2', PLAYER_NAME='Volume', TEAM_ABBREVIATION='B', GP=1, MIN=30, PTS=24, REB=8, AST=5, STL=2, BLK=1, FG3M=2, TOV=3, FGM=8, FGA=20, FTM=6, FTA=8),
        dict(PLAYER_ID='3', PLAYER_NAME='Low pct', TEAM_ABBREVIATION='C', GP=1, MIN=20, PTS=10, REB=2, AST=2, STL=0, BLK=0, FG3M=1, TOV=0, FGM=4, FGA=10, FTM=1, FTA=2),
        dict(PLAYER_ID='4', PLAYER_NAME='Solid', TEAM_ABBREVIATION='D', GP=1, MIN=25, PTS=15, REB=4, AST=3, STL=1, BLK=0, FG3M=2, TOV=1, FGM=5, FGA=11, FTM=3, FTA=4),
        dict(PLAYER_ID='5', PLAYER_NAME='Other', TEAM_ABBREVIATION='E', GP=1, MIN=23, PTS=8, REB=3, AST=2, STL=2, BLK=1, FG3M=1, TOV=1, FGM=3, FGA=9, FTM=1, FTA=2),
    ])


def test_fg_ft_weighted_aggregation_not_mean_of_percentages():
    players, _ = category_scores(sample())
    result, info = roster_analysis(players, ['1', '2'])
    fg = result.set_index('Kategori').loc['FG%', 'Kadro değeri (maç başı toplam)']
    ft = result.set_index('Kategori').loc['FT%', 'Kadro değeri (maç başı toplam)']
    assert fg == pytest.approx(9 / 21)
    assert ft == pytest.approx(7 / 9)
    assert info['fga_pg'] == pytest.approx(21)


def test_il_excluded():
    players, _ = category_scores(sample())
    _, info = roster_analysis(players, ['1', '2'], ['1'])
    assert info['players'] == 1
    assert info['fgm_pg'] == pytest.approx(8)


def test_points_do_not_guess_league_scoring():
    with pytest.raises(ValueError):
        points_scores(sample(), {})
    result = points_scores(sample(), {'PTS': 1, 'REB': 2, 'TOV': -1})
    assert result.set_index('PLAYER_ID').loc['2', 'FPTS_PG'] == pytest.approx(37)


def test_to_zscore_is_inverted():
    players, _ = category_scores(sample())
    z = players.set_index('PLAYER_ID')['Z_TO']
    assert z.loc['3'] > z.loc['2']


def test_fg_impact_cares_about_attempts():
    players, info = category_scores(sample())
    assert 0 < info['fg_baseline'] < 1
    player = players.set_index('PLAYER_ID')
    assert player.loc['1', 'FG_IMPACT'] == pytest.approx(1 - info['fg_baseline'])
    assert player.loc['2', 'FG_IMPACT'] == pytest.approx(8 - 20 * info['fg_baseline'])


def test_punt_has_nine_rows():
    players, _ = category_scores(sample())
    assert len(category_punt_view(players, ['1', '2'])) == 9


def test_reject_wrong_csv():
    with pytest.raises(ValueError):
        normalize(pd.DataFrame({'PLAYER_NAME': ['Foo'], 'GP': [1]}))


def test_team_fit_changes_with_roster_weaknesses():
    from analysis import category_team_fit
    players, _ = category_scores(sample())
    _, a = category_team_fit(players, ['1'])
    _, b = category_team_fit(players, ['2'])
    assert a != b
