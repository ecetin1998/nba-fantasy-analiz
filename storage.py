"""Local SQLite for five independent fantasy NBA rosters and scoring rules."""
from __future__ import annotations

import json
import sqlite3
from typing import Mapping, Sequence
from pathlib import Path

from lineup import BASE_POSITIONS, SLOTS, normalize_positions, validate_slot, slot_is_compatible

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
        # Non-destructive migration: existing saved teams and player rows are untouched.
        columns = {row[1] for row in db.execute("PRAGMA table_info(rosters)").fetchall()}
        if "positions" not in columns:
            db.execute("ALTER TABLE rosters ADD COLUMN positions TEXT NOT NULL DEFAULT ''")
        if "slot" not in columns:
            db.execute("ALTER TABLE rosters ADD COLUMN slot TEXT NOT NULL DEFAULT ''")


def get_roster(team: str) -> tuple[list[str], list[str]]:
    with _db() as db:
        rows = db.execute("SELECT player_id, is_il FROM rosters WHERE team=?", (team,)).fetchall()
    return [r[0] for r in rows], [r[0] for r in rows if r[1]]


def get_roster_details(team: str) -> dict[str, dict]:
    """Yahoo eligibility (manual) and unique daily lineup slot for this fantasy team."""
    with _db() as db:
        rows = db.execute(
            "SELECT player_id, positions, slot FROM rosters WHERE team=?", (team,)
        ).fetchall()
    return {str(pid): {"positions": normalize_positions(pos) if pos else [],
                        "slot": slot or ""} for pid, pos, slot in rows}


def save_roster(team: str, selected: list[str], il: list[str],
                positions: Mapping[str, Sequence[str] | str] | None = None,
                slots: Mapping[str, str] | None = None) -> None:
    """Save roster and metadata transactionally; legacy calls preserve existing positions/slots."""
    roster = list(dict.fromkeys(map(str, selected)))
    inactive = set(map(str, il))
    if len(roster) > 15:
        raise ValueError("Kadro sınırı 15 oyuncu")
    if len(inactive) > 2 or not inactive.issubset(set(roster)):
        raise ValueError("IL en fazla 2 oyuncu ve kadronun bir parçası olmalı")
    previous = get_roster_details(team)
    positions = positions or {}
    slots = slots or {}
    metadata = []
    taken_slots: set[str] = set()
    il_order = [pid for pid in roster if pid in inactive]
    for pid in roster:
        old = previous.get(pid, {})
        eligible = normalize_positions(positions.get(pid, old.get("positions", [])))
        requested = str(slots.get(pid, old.get("slot", ""))).strip().upper()
        if pid in inactive:
            assigned = "IL" + str(il_order.index(pid) + 1)
        else:
            assigned = "" if requested.startswith("IL") else requested
        validate_slot(assigned)
        if assigned in taken_slots and assigned:
            raise ValueError(f"Aynı kadro slotuna iki oyuncu atanamaz: {assigned}")
        if assigned and assigned not in ("BN1", "BN2", "BN3", "IL1", "IL2"):
            if not eligible:
                raise ValueError(f"{pid}: aktif slota atamak için Yahoo pozisyonlarını gir")
            if not slot_is_compatible(eligible, assigned):
                raise ValueError(f"{pid}: {','.join(eligible)} oyuncusu {assigned} slotuna uygun değil")
        if assigned:
            taken_slots.add(assigned)
        metadata.append((team, pid, int(pid in inactive), ",".join(eligible), assigned))
    with _db() as db:
        db.execute("DELETE FROM rosters WHERE team=?", (team,))
        db.executemany(
            "INSERT INTO rosters(team, player_id, is_il, positions, slot) VALUES (?,?,?,?,?)",
            metadata,
        )


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
