"""Projection source parser, volume assumptions and per-player blends."""
import pandas as pd
import pytest

from projection_engine import (actual_weight, fantasypros_html_to_projection,
                               blend_with_actual, _projection_pg_to_totals)


def fake_fantasypros_table():
    rows = []
    for i in range(36):
        rows.append({"Player": f"Player {i} (BOS - PG)", "PTS": 20.0+i*.1,
                     "REB": 4.2, "AST": 5.1, "BLK": .5, "STL": 1.2,
                     "FG%": .47, "FT%": .83, "3PM": 2.1, "GP": 72,
                     "MIN": 32.5, "TO": 2.4})
    return pd.DataFrame(rows).to_html(index=False)


def test_parser_gets_2026_27_player_lines_without_network():
    pg = fantasypros_html_to_projection(fake_fantasypros_table(), catalog={})
    assert len(pg) == 36
    assert pg.iloc[0]["PLAYER_NAME"] == "Player 0"
    assert pg.iloc[0]["PLAYER_ID"] == "custom:Player 0"
    assert pg.iloc[0]["FG_PCT"] == pytest.approx(.47)
    assert bool(pg.iloc[0]["FGA_PROXY"])
    assert bool(pg.iloc[0]["FTA_PROXY"])
    totals = _projection_pg_to_totals(pg)
    assert len(totals) == 36
    assert totals.iloc[0]["PTS"] / totals.iloc[0]["GP"] == pytest.approx(20)
    assert totals.iloc[0]["FGA"] > totals.iloc[0]["FGM"]
    assert totals.iloc[0]["FTM"] <= totals.iloc[0]["FTA"]


@pytest.mark.parametrize("games,weight", [(0,0),(5,.2),(10,.4),(20,.65),(30,.85),(45,.85)])
def test_smooth_actual_weights(games, weight):
    assert actual_weight(games) == pytest.approx(weight)


def test_blend_preserves_player_identity_and_uses_actual_gp():
    pg = fantasypros_html_to_projection(fake_fantasypros_table(), catalog={})
    prior = _projection_pg_to_totals(pg)
    actual = prior.head(1).copy()
    actual["GP"] = 10
    actual["PTS"] = 30 * 10
    actual["MIN"] = 33 * 10
    for stat in ("REB", "AST", "STL", "BLK", "FG3M", "TOV", "FGM", "FGA", "FTM", "FTA"):
        actual[stat] = (prior.iloc[0][stat] / prior.iloc[0]["GP"]) * 10
    blend = blend_with_actual(prior, actual)
    p = blend.iloc[0]
    assert p["GP_ACTUAL"] == 10
    assert p["ACTUAL_WEIGHT"] == pytest.approx(.4)
    assert p["PTS"]/p["GP"] == pytest.approx(20*.6+30*.4)
    assert len(blend) == len(prior)


def test_projection_only_without_actuals():
    pg = fantasypros_html_to_projection(fake_fantasypros_table(), catalog={})
    p = _projection_pg_to_totals(pg)
    out = blend_with_actual(p, None)
    assert len(out) == len(p)
    assert set(out["BASIS"]) == {"PROJECTION"}
