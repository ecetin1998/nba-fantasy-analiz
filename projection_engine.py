"""2026-27 projection ingest (FantasyPros consensus) and player-level actual blending.

Primary source: https://www.fantasypros.com/nba/projections/avg-overall.php
Data is fetched directly at runtime, attributed, and cached locally only.
Shot attempts are NOT in the source's public table: estimate temporary proxies,
mark them and replace with true projected/actual FGA/FTA when supplied.
"""
from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
import re

import numpy as np
import pandas as pd

from analysis import normalize
from roster_catalog import bundled_catalog, clean_name

SOURCE_URL = "https://www.fantasypros.com/nba/projections/avg-overall.php"
PROJECTION_SEASON = "2026-27"
CACHE_FILE = Path(__file__).resolve().parent / "data" / "projection_2026-27.csv"
REQUIRED_PROJECTION = ("PLAYER_NAME", "GP", "MIN_PG", "PTS_PG", "REB_PG", "AST_PG",
                       "STL_PG", "BLK_PG", "FG3M_PG", "TOV_PG", "FG_PCT", "FT_PCT")
RATE_STATS = ("PTS", "REB", "AST", "STL", "BLK", "FG3M", "TOV",
              "FGM", "FGA", "FTM", "FTA", "MIN")


def _find_table(html: str) -> pd.DataFrame:
    tables = pd.read_html(StringIO(html), displayed_only=False)
    for table in tables:
        table.columns = [str(col[-1] if isinstance(col, tuple) else col).strip().upper() for col in table.columns]
        col_names = set(table.columns)
        if {"PLAYER", "PTS", "REB", "AST", "FG%", "FT%", "3PM", "GP", "MIN", "TO"} <= col_names and len(table) >= 30:
            return table
    raise ValueError("FantasyPros sayfasında beklenen 2026-27 projeksiyon tablosu bulunamadı")


def _fraction(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series.astype(str).str.replace("%", "", regex=False), errors="coerce")
    return values / 100 if values.median() > 1 else values


def _clean_player(text: str) -> tuple[str, str]:
    name = str(text).strip()
    # "Player (BOS - PG,SG)" format used by FantasyPros.
    match = re.match(r"^(.*?)\s+\(([A-Z]{2,4})\s*[-–]\s*[^)]*\)", name)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    name = re.sub(r"\s+(DTD|OUT|INJ|GTD)\s*$", "", name, flags=re.I)
    return name, "UNK"


def fantasypros_html_to_projection(html: str, catalog: dict[str, str] | None = None) -> pd.DataFrame:
    """Parse the publicly visible per-game consensus table (not a paid API)."""
    table = _find_table(html)
    names, teams = zip(*(_clean_player(v) for v in table["PLAYER"].astype(str)))
    if catalog is None:
        catalog = bundled_catalog()
    by_name = {clean_name(name): str(pid) for pid, name in catalog.items()}
    out = pd.DataFrame({
        "PLAYER_NAME": names,
        "TEAM_ABBREVIATION": teams,
        "PLAYER_ID": [by_name.get(clean_name(name), f"custom:{name}") for name in names],
        "GP": pd.to_numeric(table["GP"], errors="coerce"),
        "MIN_PG": pd.to_numeric(table["MIN"], errors="coerce"),
        "FG_PCT": _fraction(table["FG%"]),
        "FT_PCT": _fraction(table["FT%"]),
        "PTS_PG": pd.to_numeric(table["PTS"], errors="coerce"),
        "REB_PG": pd.to_numeric(table["REB"], errors="coerce"),
        "AST_PG": pd.to_numeric(table["AST"], errors="coerce"),
        "STL_PG": pd.to_numeric(table["STL"], errors="coerce"),
        "BLK_PG": pd.to_numeric(table["BLK"], errors="coerce"),
        "FG3M_PG": pd.to_numeric(table["3PM"], errors="coerce"),
        "TOV_PG": pd.to_numeric(table["TO"], errors="coerce"),
    })
    out = out.dropna(subset=list(REQUIRED_PROJECTION))
    out = out[(out["GP"] > 0) & (out["MIN_PG"] >= 1)
              & out["FG_PCT"].between(.2, .85) & out["FT_PCT"].between(.2, 1)].copy()
    if len(out) < 30:
        raise ValueError("Projeksiyon kaynağından yeterli oyuncu gelmedi")
    # FantasyPros public table lacks FGA/FTA; clearly flagged shot-volume proxies.
    # 22% FTA/PTS is a neutral heuristic (NOT a sourced player projection).
    # FGM follows the scoring identity PTS = 2*FGM + 3PM + FTM.
    out["FTA_PG"] = np.maximum(.3, out["PTS_PG"] * .22)
    out["FTM_PG"] = out["FTA_PG"] * out["FT_PCT"]
    out["FGM_PG"] = (out["PTS_PG"] - out["FG3M_PG"] - out["FTM_PG"]) / 2
    out = out[out["FGM_PG"] > 0].copy()
    out["FGA_PG"] = out["FGM_PG"] / out["FG_PCT"]
    out["FGA_PROXY"] = True
    out["FTA_PROXY"] = True
    out["PROJECTION_SOURCE"] = "FantasyPros consensus 2026-27"
    out["PROJECTION_URL"] = SOURCE_URL
    out["PROJECTION_RETRIEVED_UTC"] = datetime.now(timezone.utc).isoformat()
    return out.reset_index(drop=True)


def _projection_pg_to_totals(projected: pd.DataFrame) -> pd.DataFrame:
    p = projected.copy()
    # Accept either normalized projection CSV or native per-game FantasyPros-style format.
    if set(("PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "GP",
            "MIN", "PTS", "REB", "AST", "STL", "BLK", "FG3M", "TOV",
            "FGM", "FGA", "FTM", "FTA")) <= set(p.columns):
        return normalize(p)
    missing = set(REQUIRED_PROJECTION) - set(p.columns)
    if missing:
        raise ValueError("Projeksiyon sütunları eksik: " + ", ".join(sorted(missing)))
    if "PLAYER_ID" not in p.columns:
        by_name = {clean_name(n): str(i) for i, n in bundled_catalog().items()}
        p["PLAYER_ID"] = p["PLAYER_NAME"].map(lambda name: by_name.get(clean_name(name), f"custom:{name}"))
    if "TEAM_ABBREVIATION" not in p.columns:
        p["TEAM_ABBREVIATION"] = "UNK"
    if "FGA_PG" not in p.columns or "FTA_PG" not in p.columns:
        raise ValueError("Yüzde ağırlığı için FGA_PG ve FTA_PG gereklidir")
    if "FGM_PG" not in p.columns:
        p["FGM_PG"] = p["FG_PCT"] * p["FGA_PG"]
    if "FTM_PG" not in p.columns:
        p["FTM_PG"] = p["FT_PCT"] * p["FTA_PG"]
    for field in RATE_STATS:
        p[field] = pd.to_numeric(p[f"{field}_PG"], errors="coerce") * pd.to_numeric(p["GP"], errors="coerce")
    p = normalize(p)
    p["BASIS"] = "PROJECTION"
    p["GP_ACTUAL"] = 0
    p["ACTUAL_WEIGHT"] = 0.0
    p["FGA_PROXY"] = p.get("FGA_PROXY", False)
    p["FTA_PROXY"] = p.get("FTA_PROXY", False)
    return p


def load_projection() -> pd.DataFrame | None:
    if not CACHE_FILE.exists():
        return None
    return _projection_pg_to_totals(pd.read_csv(CACHE_FILE))


def save_projection(frame: pd.DataFrame) -> pd.DataFrame:
    result = _projection_pg_to_totals(frame)
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Preserve the source fields and provenance; do not commit imported data.
    result.to_csv(CACHE_FILE, index=False)
    return result


def fetch_fantasypros(timeout: int = 16) -> pd.DataFrame:
    import requests

    response = requests.get(
        SOURCE_URL, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (compatible; NBAFantasyProjectionTool/0.4; personal-use)",
            "Accept": "text/html",
        })
    response.raise_for_status()
    projected = fantasypros_html_to_projection(response.text)
    return save_projection(projected)


def actual_weight(games: float) -> float:
    """Explicit cold-start schedule; player-specific observed GP, capped at 85%."""
    return float(np.interp(max(0, float(games)), [0, 5, 10, 20, 30],
                           [0.0, .2, .4, .65, .85]))


def blend_with_actual(projections: pd.DataFrame, actual: pd.DataFrame | None) -> pd.DataFrame:
    """Blend per-game rates separately, then aggregate using projected games to retain analyzer contract."""
    projected = normalize(projections)
    if actual is None or len(actual) == 0:
        return projected
    real = normalize(actual)
    by_id = {str(row["PLAYER_ID"]): row for _, row in real.iterrows()}
    by_name = {clean_name(row["PLAYER_NAME"]): row for _, row in real.iterrows()}
    results: list[dict] = []
    matched_real_ids = set()
    for _, p in projected.iterrows():
        aid = str(p["PLAYER_ID"])
        r = by_id.get(aid)
        if r is None:
            r = by_name.get(clean_name(p["PLAYER_NAME"]))
        record = p.to_dict()
        if r is None:
            results.append(record)
            continue
        matched_real_ids.add(str(r["PLAYER_ID"]))
        weight = actual_weight(r["GP"])
        for stat in RATE_STATS:
            rate_proj = float(p[stat]) / float(p["GP"])
            rate_actual = float(r[stat]) / float(r["GP"])
            record[stat] = (rate_proj * (1.0 - weight) + rate_actual * weight) * float(p["GP"])
        record["GP_ACTUAL"] = int(r["GP"])
        record["ACTUAL_WEIGHT"] = weight
        record["BASIS"] = "BLEND" if weight < 1 else "ACTUAL"
        if weight >= .4:
            record["FGA_PROXY"] = False
            record["FTA_PROXY"] = False
        results.append(record)
    # New players without any projection: real game stats, small-sample warning in UI.
    for _, r in real.iterrows():
        if str(r["PLAYER_ID"]) not in matched_real_ids:
            item = r.to_dict()
            item.update({"BASIS": "ACTUAL_ONLY", "GP_ACTUAL": int(r["GP"]),
                         "ACTUAL_WEIGHT": 1.0, "FGA_PROXY": False, "FTA_PROXY": False})
            results.append(item)
    return normalize(pd.DataFrame(results))
