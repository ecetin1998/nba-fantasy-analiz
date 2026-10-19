"""Yahoo fantasy NBA positional eligibility and lineup optimization.

Yahoo eligibility is NOT the same as an NBA player's listed position; users enter it
per fantasy roster. G accepts PG/SG, F accepts SF/PF, and UTIL accepts any.
"""
from __future__ import annotations

import re
from typing import Mapping, Sequence

BASE_POSITIONS = ("PG", "SG", "SF", "PF", "C")
STARTERS = ("PG", "SG", "G", "SF", "PF", "F", "C1", "C2", "UTIL1", "UTIL2")
BENCH = ("BN1", "BN2", "BN3")
INJURED = ("IL1", "IL2")
SLOTS = ("", *STARTERS, *BENCH, *INJURED)


def normalize_positions(value: Sequence[str] | str | None) -> list[str]:
    """Canonical Yahoo eligibility tokens; unknown is [] not fictitious all-position eligibility."""
    if value is None:
        return []
    if isinstance(value, str):
        values = re.split(r"[,;/|\s]+", value.strip().upper()) if value.strip() else []
    else:
        values = [str(v).strip().upper() for v in value]
    unknown = [p for p in values if p and p not in BASE_POSITIONS]
    if unknown:
        raise ValueError(f"Geçersiz oyuncu pozisyonu: {', '.join(unknown)}. PG, SG, SF, PF veya C kullan.")
    seen: set[str] = set()
    return [p for p in BASE_POSITIONS if p in values and not (p in seen or seen.add(p))]


def validate_slot(slot: str) -> None:
    if slot not in SLOTS:
        raise ValueError(f"Geçersiz Yahoo kadro slotu: {slot}")


def slot_is_compatible(eligible: Sequence[str] | str | None, slot: str) -> bool:
    positions = set(normalize_positions(eligible))
    validate_slot(slot)
    if not slot:
        return True
    if slot in BENCH or slot in INJURED:
        return True
    if not positions:
        return False
    if slot.startswith("UTIL"):
        return True
    if slot.startswith("C"):
        return "C" in positions
    if slot == "G":
        return bool(positions.intersection(("PG", "SG")))
    if slot == "F":
        return bool(positions.intersection(("SF", "PF")))
    return slot in positions


def best_lineup(roster: Sequence[str], in_il: Sequence[str],
                eligibility: Mapping[str, Sequence[str] | str],
                values: Mapping[str, float]) -> list[dict]:
    """Maximum filled starting slots, then total projections. Excludes IL.

    Dynamic programming over ten active Yahoo slots: O(players * 2^10 * 10).
    Missing position eligibility is treated as unknown and never assigned automatically.
    """
    active = [str(pid) for pid in roster if str(pid) not in set(map(str, in_il))]
    states: dict[int, tuple[float, list[tuple[str, str]]]] = {0: (0.0, [])}
    for pid in active:
        positions = eligibility.get(pid, [])
        if not normalize_positions(positions):
            continue
        new_states = states.copy()
        for mask, (score, lineup) in states.items():
            for slot_idx, slot in enumerate(STARTERS):
                bit = 1 << slot_idx
                if mask & bit or not slot_is_compatible(positions, slot):
                    continue
                new_mask = mask | bit
                new_score = score + float(values.get(pid, 0.0))
                previous = new_states.get(new_mask)
                if previous is None or new_score > previous[0]:
                    new_states[new_mask] = (new_score, lineup + [(slot, pid)])
        states = new_states
    best_mask, (_best_score, assigned) = max(
        states.items(), key=lambda item: (
            item[0].bit_count(), item[1][0]
        )
    )
    by_slot = dict(assigned)
    return [
        {"slot": slot, "player_id": by_slot.get(slot), "value": (
            float(values.get(by_slot[slot], 0)) if slot in by_slot else None
        )}
        for slot in STARTERS
    ]
