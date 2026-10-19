"""Yahoo Fantasy NBA independent roster analyzer — MVP v0.1.

Run: streamlit run app.py
No Yahoo credentials required. nba_api supplies season totals when reachable.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from analysis import (CATEGORIES, POINTS_FIELDS, category_punt_view, category_team_fit,
                      category_scores, normalize, points_scores, roster_analysis)
from data_sources import fetch_nba_totals, last_updated, load_cache, save_csv
from storage import (TEAMS, YAHOO_DEFAULT_POINTS, get_roster, get_weights,
                     init, reset_weights, save_roster, save_weights)

st.set_page_config(page_title="NBA Fantasy | 5 Takım Analizi", page_icon="🏀", layout="wide")
init()

st.title("🏀 NBA Fantasy — Kadro Analizi")
st.caption("5 takım, 2 farklı lig formatı · Yahoo API olmadan · MVP v0.2")

season = st.sidebar.selectbox("Sezon", ["2025-26", "2026-27"], index=0,
    help="2026-27 normal sezonu henüz başlamadıysa 2025-26 referans alınır.")
team_names = [t[0] for t in TEAMS]
team_name = st.sidebar.selectbox("Fantasy takımım", team_names)
team_meta = next(t for t in TEAMS if t[0] == team_name)
team_type = team_meta[2]
st.sidebar.markdown(f"**{team_name}** · {'Standart 9-cat' if team_type == 'CAT' else 'Standart Yahoo Points'} · Lig {team_meta[1]}")
st.sidebar.info("Her takımın kadrosu ayrı saklanır. Yahoo liginin rakip kadroları bilinmiyor.")

with st.expander("📥 Oyuncu verisi · NBA'den yenile / CSV yükle", expanded=False):
    left, right = st.columns(2)
    with left:
        st.markdown("**NBA istatistikleri**")
        st.caption("Seçili sezonun normal sezon toplamlarını stats.nba.com üzerinden alır. Bazen 403 / zaman aşımı olabilir.")
        if st.button("NBA verisini çek / yenile", use_container_width=True):
            try:
                with st.spinner("NBA oyuncu verileri alınıyor..."):
                    result = fetch_nba_totals(season)
                st.session_state.pop("demo_data", None)
                st.success(f"{len(result)} oyuncu indirildi ve yerel diske kaydedildi.")
                st.rerun()
            except Exception as exc:
                st.error(f"NBA bağlantısı başarısız: {exc}")
                st.info("Aşağıdaki CSV yükleme yöntemiyle uygulamayı kullanabilirsin.")
    with right:
        st.markdown("**CSV alternatif kaynak**")
        file = st.file_uploader("Sezon toplamlarını CSV olarak içe aktar", type=["csv"])
        st.caption("İlk satırdaki kolon adlarını örnek şablondan al. Değerler maç başı değil, sezon toplamı olmalı.")
        if file is not None and st.button("CSV'yi kaydet ve kullan"):
            try:
                result = save_csv(season, pd.read_csv(file))
                st.session_state.pop("demo_data", None)
                st.success(f"{len(result)} oyuncu kaydedildi")
                st.rerun()
            except Exception as exc:
                st.error(f"CSV yüklenemedi: {exc}")
    demo_path = Path(__file__).resolve().parent / "sample_data" / "demo_season_totals.csv"
    if demo_path.exists() and st.button("Sadece sistemi denemek için ÖRNEK veriyi aç"):
        st.session_state["demo_data"] = pd.read_csv(demo_path)
        st.rerun()

try:
    if "demo_data" in st.session_state:
        raw = normalize(st.session_state["demo_data"])
        st.warning("DEMO MODU — Bu oyuncular ve istatistikler tamamen yapaydır. Gerçek NBA analizi değildir.")
    else:
        raw = load_cache(season)
except Exception as exc:
    raw = None
    st.error(f"Sezon verisi okunamadı: {exc}")

if raw is None:
    st.info("Başlamak için yukarıdan 'NBA verisini çek / yenile' butonuna bas veya CSV yükle. NBA API yanıt vermezse örnek veriyle arayüzü test edebilirsin.")
    sample = Path(__file__).resolve().parent / "sample_data" / "season_totals_template.csv"
    st.download_button("Boş CSV şablonunu indir", data=sample.read_bytes(),
                       file_name="nba_season_totals_template.csv", mime="text/csv")
    st.stop()

st.caption(f"Kaynak: {'SENTETİK DEMO' if 'demo_data' in st.session_state else 'NBA API veya içe aktarılan CSV'} · "
           f"Sezon: {season} · Son kayıt: {last_updated(season) or 'Demo / bilinmiyor'} · "
           f"{len(raw)} oyuncu")

if team_type == "CAT":
    players, reference_info = category_scores(raw)
else:
    players = None
    reference_info = {}

roster_ids, il_ids = get_roster(team_name)
ids = raw["PLAYER_ID"].astype(str).tolist()
name_by_id = dict(zip(raw["PLAYER_ID"], raw["PLAYER_NAME"]))
team_by_id = dict(zip(raw["PLAYER_ID"], raw["TEAM_ABBREVIATION"]))
show_name = lambda pid: f"{name_by_id.get(pid, 'Bilinmeyen ID: ' + pid)} · {team_by_id.get(pid, '?')}"
missing_roster = [pid for pid in roster_ids if pid not in name_by_id]
if missing_roster:
    st.warning(f"Kadroda seçili veri setinde bulunamayan {len(missing_roster)} oyuncu var. Bunlar analiz dışında kalır: {', '.join(missing_roster)}")

st.subheader(f"{team_name} · {'H2H Categories' if team_type == 'CAT' else 'H2H Points'}")
tab_roster, tab_analysis, tab_rankings, tab_candidates = st.tabs(
    ["👥 Kadrom", "📊 Kadro analizi", "🏆 Oyuncu sıralaması", "🔎 Aday oyuncular"])

with tab_roster:
    st.write("Oyuncuları seç, varsa IL listesini işaretle ve kadroyu kaydet. Aynı NBA oyuncusu farklı fantasy takımlarında bulunabilir.")
    roster_sel = st.multiselect("Kadro oyuncuları (en fazla 15)", options=ids,
        default=[pid for pid in roster_ids if pid in name_by_id], format_func=show_name,
        max_selections=15, key=f"roster_input_{team_name}")
    il_sel = st.multiselect("IL · Analizin dışında tut (en fazla 2)",
        options=roster_sel, default=[pid for pid in il_ids if pid in roster_sel],
        format_func=show_name, max_selections=2, key=f"il_input_{team_name}")
    if st.button("💾 Bu takımın kadrosunu kaydet", type="primary"):
        try:
            save_roster(team_name, roster_sel, il_sel)
            st.success("Kadro yerel SQLite veritabanına kaydedildi.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    if roster_ids:
        selected_table = raw[raw["PLAYER_ID"].isin(roster_ids)].copy()
        selected_table["IL"] = selected_table["PLAYER_ID"].isin(il_ids)
        show_cols = ["PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "IL"]
        st.dataframe(selected_table[show_cols].rename(columns={"PLAYER_NAME": "Oyuncu", "TEAM_ABBREVIATION": "NBA takımı", "GP": "Maç"}),
                     hide_index=True, use_container_width=True)
    else:
        st.info("Henüz kadro kaydedilmedi. Oyuncularını seçerek başla.")

if team_type == "PTS":
    st.info("Yahoo standart H2H Points: PTS +1 · REB +1.2 · AST +1.5 · STL +3 · BLK +3 · TO −1. "
            "FG/FT ve 3PM için ekstra puan bulunmuyor. Hesaplamalar otomatik etkin.")
    with st.expander("⚙️ Gelişmiş · Yahoo standart puanlamasını değiştirmek gerekirse"):
        st.caption("İki Points ligi de Yahoo varsayılanlarıyla başlar. Özel lig ayarı yoksa değiştirmene gerek yok.")
        weights = get_weights(team_name)
        if st.button("Yahoo varsayılanına sıfırla", key=f"reset_points_{team_name}"):
            reset_weights(team_name)
            st.rerun()
        with st.form(f"points_weights_{team_name}"):
            columns = st.columns(4)
            new_weights = {}
            for i, field in enumerate(POINTS_FIELDS):
                new_weights[field] = columns[i % 4].number_input(
                    field, min_value=-25.0, max_value=25.0, step=0.25,
                    value=float(weights.get(field, 0.0)), format="%.2f")
            st.caption("3PM = FG3M · Double-double = DD2 · Triple-double = TD3. Standartta hepsi 0.")
            if st.form_submit_button("Özel katsayıları kaydet"):
                save_weights(team_name, new_weights)
                st.success("Özel puanlama kuralları kaydedildi.")
                st.rerun()
    weights = get_weights(team_name)
    valid_weights = any(float(v) != 0 for v in weights.values())
    if valid_weights:
        players = points_scores(raw, weights)
    else:
        with tab_analysis:
            st.warning("Analiz için Points puanlama katsayılarını önce kaydet.")
        with tab_rankings:
            st.warning("Oyuncu puan sıralaması için puanlama katsayıları gerekli.")
        with tab_candidates:
            st.warning("Aday oyuncular için puanlama katsayıları gerekli.")

if players is not None:
    selected = players[players["PLAYER_ID"].isin(set(roster_ids) - set(il_ids))].copy()

    if team_type == "CAT":
        with tab_analysis:
            st.caption("Yahoo standart 9-cat: PTS, REB, AST, STL, BLK, 3PM, FG%, FT%, TO.")
            st.info(f"Referans havuz: {reference_info['reference_n']} NBA oyuncusu · "
                    f"FG% referansı: %{100*reference_info['fg_baseline']:.1f} · "
                    f"FT% referansı: %{100*reference_info['ft_baseline']:.1f}. "
                    "Bunlar Yahoo liginin 12 takımlı ortalaması değil, NBA oyuncu havuzu karşılaştırmasıdır.")
            if selected.empty:
                st.warning("Analiz görmek için önce 'Kadrom' sekmesinden oyuncu ekle.")
            else:
                result, details = roster_analysis(players, roster_ids, il_ids)
                c1, c2, c3 = st.columns(3)
                c1.metric("Analize dahil oyuncu", details["players"])
                c2.metric("Hacim ağırlıklı FG%", f"%{100 * details['fgm_pg'] / details['fga_pg']:.1f}" if details["fga_pg"] else "—")
                c3.metric("Hacim ağırlıklı FT%", f"%{100 * details['ftm_pg'] / details['fta_pg']:.1f}" if details["fta_pg"] else "—")
                st.bar_chart(result.set_index("Kategori")["Ortalama z-score"])
                out = result.copy()
                out["Kadro değeri (maç başı toplam)"] = out.apply(
                    lambda r: f"{r['Kadro değeri (maç başı toplam)']*100:.1f}%" if r["Kategori"] in ("FG%", "FT%") else f"{r['Kadro değeri (maç başı toplam)']:.2f}", axis=1)
                st.dataframe(out, hide_index=True, use_container_width=True)
                st.markdown("**Punt ön değerlendirmesi**")
                st.dataframe(category_punt_view(players, roster_ids, il_ids).head(5), hide_index=True, use_container_width=True)
                st.caption("Bu punt sıralaması yalnızca kalan sekiz kategorideki z toplamıdır; rakip ve kazanma olasılığı içermez. "
                           "Bench oyuncular potansiyel olarak oynayabilir varsayılır, IL hariç tutulur.")

        with tab_rankings:
            table = players.sort_values("Z_TOTAL", ascending=False).copy()
            table.insert(0, "Sıra", range(1, len(table) + 1))
            st.dataframe(table[["Sıra", "PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN_PG", "Z_TOTAL"] + [f"Z_{c}" for c in CATEGORIES]].rename(
                columns={"PLAYER_NAME": "Oyuncu", "TEAM_ABBREVIATION": "NBA takımı", "MIN_PG": "DK/maç", "Z_TOTAL": "9-cat z toplamı"}),
                hide_index=True, use_container_width=True)
            st.caption("Hacim bazlı % etkisi, TO ters z-score ve NBA referans havuzu üzerinden hesaplanır. Bu sıralama pozisyon/sakatlık/projeksiyon içermez.")

        with tab_candidates:
            exclude = set(roster_ids)
            fit_ranked, weights_used = category_team_fit(players, roster_ids, il_ids)
            all_ranked = fit_ranked.sort_values("Z_TOTAL", ascending=False).copy()
            all_ranked["Genel sıra"] = range(1, len(all_ranked) + 1)
            # Scout list: start outside the overall top 35, then sort by *this* team's needs.
            mid = all_ranked[(all_ranked["Genel sıra"].between(36, 185)) & ~all_ranked["PLAYER_ID"].isin(exclude)].copy()
            mid = mid.sort_values("TAKIMA_UYUM", ascending=False)
            st.write("**Takımıma özel radar listesi** · genel sıralamanın 36–185. basamaklarından takım ihtiyaçlarına göre seçilenler")
            st.caption("İhtiyaç ağırlıkları: " + ", ".join(f"{k} ×{v:.1f}" for k, v in weights_used.items()))
            st.dataframe(mid[["Genel sıra", "PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN_PG", "TAKIMA_UYUM", "Z_TOTAL"] + [f"Z_{c}" for c in CATEGORIES]].head(50),
                         hide_index=True, use_container_width=True)
            st.caption("Takıma uyum skoru kategori z-score'larının kadronun zayıflıklarına göre ağırlıklı toplamıdır. "
                       "Bu liste Yahoo'da boşta olma, son haftalarda yükseliş veya gerçek piyasa değerinin altında olma garantisi vermez. "
                       "Gerçek form trendi ve waiver durumu sonraki sürümde eklenecek.")

    elif team_type == "PTS":
        with tab_analysis:
            if selected.empty:
                st.warning("Kadro analizi için oyuncu ekle.")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Analize dahil oyuncu", len(selected))
                c2.metric("Maç başı FPTS toplamı", f"{selected['FPTS_PG'].sum():.1f}")
                c3.metric("Oyuncu başına ortalama FPTS", f"{selected['FPTS_PG'].mean():.1f}")
                st.dataframe(selected[["PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN_PG", "FPTS_PG"]].sort_values("FPTS_PG", ascending=False),
                             hide_index=True, use_container_width=True)
                st.caption("Bu değerler tüm kadro oyuncuları birer maç oynadığında oluşan toplamdır; haftalık fikstür/aktif slot/IL dışındaki bench kısıtları hesaba katılmaz.")
        with tab_rankings:
            table = players.sort_values("FPTS_PG", ascending=False).copy()
            table.insert(0, "Sıra", range(1, len(table) + 1))
            st.dataframe(table[["Sıra", "PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN_PG", "FPTS_PG", "FPTS_TOTAL"]],
                         hide_index=True, use_container_width=True)
        with tab_candidates:
            all_ranked = players.sort_values("FPTS_PG", ascending=False).copy()
            all_ranked["Genel sıra"] = range(1, len(all_ranked) + 1)
            available = all_ranked[(all_ranked["Genel sıra"].between(36, 185)) & ~all_ranked["PLAYER_ID"].isin(roster_ids)].copy()
            weakest = float(selected["FPTS_PG"].min()) if not selected.empty else None
            if weakest is not None:
                available["En düşük kadro oyuncusuna göre fark"] = available["FPTS_PG"] - weakest
            st.write("**İkinci kademe aday oyuncular** · kendi kadron hariç, FPTS sırasındaki 36–185. isimler")
            if weakest is not None:
                st.caption(f"Kadronun en düşük maç başı üretimi {weakest:.1f} FPTS; aşağıdaki farklar yalnızca ham maç başı karşılaştırmadır.")
            st.dataframe(available[["Genel sıra", "PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN_PG", "FPTS_PG"] +
                         (["En düşük kadro oyuncusuna göre fark"] if weakest is not None else [])].head(50),
                         hide_index=True, use_container_width=True)
            st.caption("Oyuncuların Yahoo waiver durumu bilinmiyor; bu liste roster dışındaki adayları sıralar.")

st.divider()
st.caption("MVP v0.2 · Henüz yok: gerçek Yahoo waiver sahipliği, canlı sakatlık, 7/15/30 gün formu, NBA haftalık fikstür ve rakip tahmini. "
           "NBA API kesintisinde manuel CSV yedeği kullanılabilir. Veri uygulamayı çalıştırdığın bilgisayarda tutulur.")
