"""Local SQLite for five independent fantasy NBA rosters and scoring rules."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "fantasy.sqlite3"
# Official Yahoo 2026-27 Express Settings, Head-to-Head Points:
# https://basketball.fantasysports.yahoo.com/nba/express_settings?type=head_point
# No bonus for 3PM, shooting volume or percentages in the default format.
YAHOO_DEFAULT_POINTS = {"PTS": 1.0, "REB": 1.2, "AST": 1.5,
                        "STL": 3.0, "BLK": 3.0, "TOV": -1.0}

TEAMS = [
    ("2fe2d", "27758", "CAT"),
    ("benny bilanço", "9421", "PTS"),
    ("myopia", "47408", "CAT"),
    ("emo361", "227098", "PTS"),
    ("Bilandyczak", "248620", "CAT"),
]


def _db():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init() -> None:
    with _db() as db:
        db.execute("CREATE TABLE IF NOT EXISTS rosters (team TEXT NOT NULL, player_id TEXT NOT NULL, is_il INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(team, player_id))")
        db.execute("CREATE TABLE IF NOT EXISTS config (team TEXT PRIMARY KEY, weights_json TEXT NOT NULL)")


def get_roster(team: str) -> tuple[list[str], list[str]]:
    with _db() as db:
        rows = db.execute("SELECT player_id, is_il FROM rosters WHERE team=?", (team,)).fetchall()
    return [r[0] for r in rows], [r[0] for r in rows if r[1]]


def save_roster(team: str, selected: list[str], il: list[str]) -> None:
    roster, inactive = list(dict.fromkeys(map(str, selected))), set(map(str, il))
    if len(roster) > 15:
        raise ValueError("Kadro sınırı 15 oyuncu")
    if len(inactive.intersection(roster)) > 2:
        raise ValueError("IL en fazla 2 oyuncu")
    with _db() as db:
        db.execute("DELETE FROM rosters WHERE team=?", (team,))
        db.executemany("INSERT INTO rosters(team,player_id,is_il) VALUES(?,?,?)",
                       [(team, pid, int(pid in inactive)) for pid in roster])


def get_weights(team: str) -> dict[str, float]:
    with _db() as db:
        row = db.execute("SELECT weights_json FROM config WHERE team=?", (team,)).fetchone()
    if row:
        return json.loads(row[0])
    if team in {name for name, _, fmt in TEAMS if fmt == "PTS"}:
        return YAHOO_DEFAULT_POINTS.copy()
    return {}


def save_weights(team: str, weights: dict[str, float]) -> None:
    with _db() as db:
        db.execute("INSERT INTO config(team,weights_json) VALUES (?,?) ON CONFLICT(team) DO UPDATE SET weights_json=excluded.weights_json", (team, json.dumps(weights)))


def reset_weights(team: str) -> None:
    """Discard custom rules and use Yahoo's built-in H2H Points rules again."""
    with _db() as db:
        db.execute("DELETE FROM config WHERE team=?", (team,))
