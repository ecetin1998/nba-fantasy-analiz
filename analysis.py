"""Independent NBA fantasy 9-cat and Points models; all raw input stats are season TOTALS."""
from __future__ import annotations

import numpy as np
import pandas as pd

COUNTING = ["PTS", "REB", "AST", "STL", "BLK", "FG3M", "TOV"]
VOLUME = ["FGM", "FGA", "FTM", "FTA"]
OPTIONAL = ["DD2", "TD3", "FG3A", "OREB", "DREB", "PF", "PFD"]
REQUIRED = ["PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN", *COUNTING, *VOLUME]
CATEGORIES = ["PTS", "REB", "AST", "STL", "BLK", "3PM", "FG%", "FT%", "TO"]
GOOD_UP = {"PTS": "PTS", "REB": "REB", "AST": "AST", "STL": "STL", "BLK": "BLK", "3PM": "FG3M", "FG%": "FG_IMPACT", "FT%": "FT_IMPACT", "TO": "TOV"}
POINTS_FIELDS = ["PTS", "REB", "AST", "STL", "BLK", "FG3M", "FG3A", "FGM", "FGA", "FTM", "FTA", "TOV", "OREB", "DREB", "PF", "PFD", "MIN", "DD2", "TD3"]


def normalize(raw: pd.DataFrame) -> pd.DataFrame:
    """Validates NBA season totals and deduplicates player IDs."""
    df = raw.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    if "3PM" in df.columns and "FG3M" not in df.columns:
        df = df.rename(columns={"3PM": "FG3M"})
    missing = sorted(set(REQUIRED) - set(df.columns))
    if missing:
        raise ValueError("Eksik CSV sütunları: " + ", ".join(missing))
    for field in COUNTING + VOLUME + ["GP", "MIN", *OPTIONAL]:
        if field not in df.columns:
            df[field] = 0.0
        df[field] = pd.to_numeric(df[field], errors="coerce").fillna(0.0)
        if (df[field] < 0).any():
            raise ValueError(f"{field} negatif olamaz")
    df["PLAYER_ID"] = df["PLAYER_ID"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    df["PLAYER_NAME"] = df["PLAYER_NAME"].astype(str).str.strip()
    df["TEAM_ABBREVIATION"] = df["TEAM_ABBREVIATION"].astype(str).str.strip()
    df = df[(df["GP"] > 0) & df["PLAYER_NAME"].ne("") & df["PLAYER_ID"].ne("")].copy()
    df["_total_line"] = df["TEAM_ABBREVIATION"].eq("TOT").astype(int)
    df = (df.sort_values(["_total_line", "GP"], ascending=False)
            .drop_duplicates("PLAYER_ID", keep="first")
            .drop(columns="_total_line").reset_index(drop=True))
    if df.empty:
        raise ValueError("Geçerli oyuncu bulunamadı; GP > 0 olmalı")
    if (df["FGM"] > df["FGA"]).any() or (df["FTM"] > df["FTA"]).any():
        raise ValueError("İsabet sayısı denemeden büyük olamaz")
    return df


def with_per_game(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for field in COUNTING + VOLUME + OPTIONAL:
        result[f"{field}_PG"] = result[field] / result["GP"]
    result["MIN_PG"] = result["MIN"] / result["GP"]
    result["FG_PCT"] = np.where(result["FGA"] > 0, result["FGM"] / result["FGA"], np.nan)
    result["FT_PCT"] = np.where(result["FTA"] > 0, result["FTM"] / result["FTA"], np.nan)
    return result


def _reference_mask(frame: pd.DataFrame) -> pd.Series:
    minimum_games = min(10, max(1, int(frame["GP"].max())))
    mask = frame["GP"].ge(minimum_games) & frame["MIN_PG"].ge(15)
    if mask.sum() < 12:
        mask = frame["GP"].ge(1) & frame["MIN_PG"].ge(10)
    if mask.sum() < 5:
        mask = frame["GP"].ge(1)
    return mask


def category_scores(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    frame = with_per_game(normalize(raw))
    ref = _reference_mask(frame)
    eligible = frame.loc[ref]
    fg_base = eligible["FGM"].sum() / eligible["FGA"].sum() if eligible["FGA"].sum() else 0
    ft_base = eligible["FTM"].sum() / eligible["FTA"].sum() if eligible["FTA"].sum() else 0
    frame["FG_IMPACT"] = (frame["FGM"] - fg_base * frame["FGA"]) / frame["GP"]
    frame["FT_IMPACT"] = (frame["FTM"] - ft_base * frame["FTA"]) / frame["GP"]
    for cat in CATEGORIES:
        col = GOOD_UP[cat] if GOOD_UP[cat].endswith("IMPACT") else f"{GOOD_UP[cat]}_PG"
        mean, std = frame.loc[ref, col].mean(), frame.loc[ref, col].std(ddof=0)
        sign = -1 if cat == "TO" else 1
        frame[f"Z_{cat}"] = sign * (frame[col] - mean) / std if pd.notna(std) and std > 0 else 0.0
    frame["Z_TOTAL"] = frame[[f"Z_{c}" for c in CATEGORIES]].sum(axis=1)
    return frame, {"fg_baseline": fg_base, "ft_baseline": ft_base, "reference_n": int(ref.sum())}


def roster_analysis(players: pd.DataFrame, roster_ids: list[str], unavailable_ids: list[str] | None = None) -> tuple[pd.DataFrame, dict]:
    active = set(map(str, roster_ids)) - set(map(str, unavailable_ids or []))
    selected = players[players["PLAYER_ID"].isin(active)].copy()
    if selected.empty:
        raise ValueError("Analize dahil edilecek oyuncu yok")
    fgm, fga = selected["FGM_PG"].sum(), selected["FGA_PG"].sum()
    ftm, fta = selected["FTM_PG"].sum(), selected["FTA_PG"].sum()
    values = {cat: float(selected[f"{GOOD_UP[cat]}_PG"].sum()) for cat in CATEGORIES if cat not in ("FG%", "FT%")}
    values["FG%"] = float(fgm / fga) if fga else float("nan")
    values["FT%"] = float(ftm / fta) if fta else float("nan")
    rows = []
    for cat in CATEGORIES:
        z = float(selected[f"Z_{cat}"].mean())
        rows.append({"Kategori": cat, "Kadro değeri (maç başı toplam)": values[cat], "Ortalama z-score": z,
                     "Değerlendirme": "Güçlü" if z > 0.35 else "Zayıf" if z < -0.35 else "Dengeli"})
    return pd.DataFrame(rows), {"players": len(selected), "fgm_pg": fgm, "fga_pg": fga, "ftm_pg": ftm, "fta_pg": fta}


def points_scores(raw: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    if not weights or not any(float(weights.get(f, 0)) != 0 for f in POINTS_FIELDS):
        raise ValueError("Points ligi puanlama katsayılarını gir")
    result = with_per_game(normalize(raw))
    result["FPTS_PG"] = sum(result[f"{field}_PG"] * float(weights.get(field, 0)) for field in POINTS_FIELDS)
    result["FPTS_TOTAL"] = result["FPTS_PG"] * result["GP"]
    return result


def category_punt_view(scores: pd.DataFrame, roster_ids: list[str], excluded: list[str] | None = None) -> pd.DataFrame:
    selected = scores[scores["PLAYER_ID"].isin(set(map(str, roster_ids)) - set(map(str, excluded or [])))]
    if selected.empty:
        return pd.DataFrame()
    rows = []
    for punt in CATEGORIES:
        others = [cat for cat in CATEGORIES if cat != punt]
        avg_z = float(selected[[f"Z_{c}" for c in others]].sum(axis=1).mean())
        rows.append({"Bırakılan kategori": punt, "Kalan 8 kategori z toplamı / oyuncu": avg_z})
    return pd.DataFrame(rows).sort_values("Kalan 8 kategori z toplamı / oyuncu", ascending=False).reset_index(drop=True)


def category_team_fit(players: pd.DataFrame, roster_ids: list[str], excluded: list[str] | None = None) -> tuple[pd.DataFrame, dict[str, float]]:
    active = set(map(str, roster_ids)) - set(map(str, excluded or []))
    selected = players[players["PLAYER_ID"].isin(active)]
    if selected.empty:
        weights = {c: 1.0 for c in CATEGORIES}
    else:
        weaknesses = selected[[f"Z_{c}" for c in CATEGORIES]].mean()
        weights = {c: float(np.clip(1.0 - weaknesses[f"Z_{c}"], 0.25, 2.5)) for c in CATEGORIES}
    result = players.copy()
    result["TAKIMA_UYUM"] = (sum(result[f"Z_{c}"] * weights[c] for c in CATEGORIES) / sum(weights.values())) * 9
    return result, weights
