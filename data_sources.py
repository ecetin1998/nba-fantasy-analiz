"""NBA player season totals from nba_api with CSV fallback."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from analysis import normalize

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def cache_path(season: str) -> Path:
    if not (len(season) == 7 and season[:4].isdigit() and season[4] == "-" and season[5:].isdigit()):
        raise ValueError("Geçersiz sezon")
    return DATA_DIR / f"nba_totals_{season}.csv"


def load_cache(season: str) -> pd.DataFrame | None:
    path = cache_path(season)
    return normalize(pd.read_csv(path)) if path.exists() else None


def save_csv(season: str, raw: pd.DataFrame) -> pd.DataFrame:
    result = normalize(raw)
    result.to_csv(cache_path(season), index=False)
    return result


def fetch_nba_totals(season: str) -> pd.DataFrame:
    """The public stats.nba.com endpoint may intermittently block requests."""
    from nba_api.stats.endpoints import leaguedashplayerstats

    request = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season, season_type_all_star="Regular Season",
        per_mode_detailed="Totals", timeout=35,
    )
    raw = request.get_data_frames()[0]
    if raw.empty:
        raise RuntimeError("NBA bu sezon için henüz normal sezon verisi döndürmedi")
    return save_csv(season, raw)


def last_updated(season: str) -> str | None:
    path = cache_path(season)
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
