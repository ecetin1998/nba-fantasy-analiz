"""Player catalog + alias resolution independent from NBA statistics access."""
from __future__ import annotations
import unicodedata


def clean_name(name: str) -> str:
    value = unicodedata.normalize("NFKD", str(name))
    return "".join(ch for ch in value if not unicodedata.combining(ch)).casefold().replace(".", "").replace("-", " ").replace("'", "").strip()


def bundled_catalog() -> dict[str, str]:
    """nba_api has a bundled player directory; no stats.nba.com call."""
    try:
        from nba_api.stats.static import players
        return {str(item["id"]): item["full_name"] for item in players.get_active_players()}
    except (ImportError, OSError, KeyError, ValueError):
        return {}


def handwritten_id(name: str) -> str:
    cleaned = " ".join(str(name).strip().split())
    if not cleaned:
        raise ValueError("Oyuncu adı boş olamaz")
    return "custom:" + cleaned


def display_name(pid: str, catalog: dict[str, str]) -> str:
    if str(pid).startswith("custom:"):
        return str(pid)[7:]
    return catalog.get(str(pid), f"NBA Oyuncu ID: {pid}")


def find_catalog_player(name: str, catalog: dict[str, str]) -> str:
    normalized = clean_name(name)
    matches = [pid for pid, full_name in catalog.items() if clean_name(full_name) == normalized]
    return matches[0] if len(matches) == 1 else handwritten_id(name)


def resolve_roster_ids(roster: list[str], inactive: list[str], raw_players) -> tuple[list[str], list[str], list[str]]:
    """Map manually entered names to current dataset's NBA player IDs without modifying saved rosters."""
    if raw_players is None:
        return [], [], list(roster)
    names = {}
    for pid, name in zip(raw_players["PLAYER_ID"], raw_players["PLAYER_NAME"]):
        names.setdefault(clean_name(name), []).append(str(pid))
    live_ids = set(raw_players["PLAYER_ID"].astype(str))
    mapping = {}
    not_found = []
    for stored_id in roster:
        if str(stored_id) in live_ids:
            mapping[str(stored_id)] = str(stored_id)
        elif str(stored_id).startswith("custom:"):
            matches = names.get(clean_name(str(stored_id)[7:]), [])
            if len(matches) == 1:
                mapping[str(stored_id)] = matches[0]
            else:
                not_found.append(str(stored_id))
        else:
            not_found.append(str(stored_id))
    resolved = list(dict.fromkeys(mapping.values()))
    resolved_il = list(dict.fromkeys(mapping[str(pid)] for pid in inactive if str(pid) in mapping))
    return resolved, resolved_il, not_found
