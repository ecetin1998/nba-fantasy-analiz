"""NBA Fantasy Scout · 2026–27 · Five independently managed Yahoo Fantasy teams."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from analysis import (CATEGORIES, POINTS_FIELDS, category_punt_view, category_team_fit,
                      category_scores, normalize, points_scores, roster_analysis)
from data_sources import fetch_nba_totals, last_updated, load_cache, save_csv
from projection_engine import (SOURCE_URL, blend_with_actual, fetch_fantasypros,
                               load_projection, projection_cache_age_hours, save_projection)
from roster_catalog import bundled_catalog, display_name, find_catalog_player, resolve_roster_ids
from storage import TEAMS, get_roster, get_weights, init, reset_weights, save_roster, save_weights
from ui_theme import apply_style, hero, section_kicker, footer


SEASON = "2026-27"  # This app is for 2026–27 only. Previous-season selector removed.
ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title="NBA Fantasy Scout · 2026–27", page_icon="🏀",
                   layout="wide", initial_sidebar_state="collapsed")
init()

apply_style()
hero()

names = [team[0] for team in TEAMS]
team_names_map = {name: (league_id, league_format) for name, league_id, league_format in TEAMS}
col_team, col_meta = st.columns([1.65, 1], vertical_alignment="bottom")
with col_team:
    team_name = st.selectbox("Fantasy takımın", names, key="active_team")
with col_meta:
    league_id, fmt = team_names_map[team_name]
    st.markdown(
        '<div class="nba-inline-meta"><span class="nba-tag">'
        + ("9 KATEGORİ · H2H" if fmt == "CAT" else "POINTS · H2H")
        + '</span><span class="nba-muted">Lig #' + league_id + "</span></div>",
        unsafe_allow_html=True,
    )

roster_ids, il_ids = get_roster(team_name)
section_kicker("TAKIM ÖZETİ")
proj_exists = (ROOT / "data" / "projection_2026-27.csv").exists()
actual_exists = (ROOT / "data" / "nba_totals_2026-27.csv").exists()
source_health = "Gerçek + Tahmin" if actual_exists and proj_exists else (
    "Projeksiyon" if proj_exists else "Hazır değil"
)
stats_cols = st.columns(3)
stats_cols[0].metric("Kadro", f"{len(roster_ids)} / 15")
stats_cols[1].metric("IL", f"{len(il_ids)} / 2")
stats_cols[2].metric("Veri", source_health)

# Short visible navigation labels are readable on narrow phones.
NAV = {
    "Kadrom": "👥 Kadrom",
    "Analiz": "📊 Kadro Analizi",
    "Radar": "🔎 Oyuncu Radarı",
    "Veri": "⚙️ Veri Merkezi",
}
st.session_state.setdefault("nav_v2", "Kadrom")
selected_nav = st.segmented_control(
    "Bölüm", list(NAV), default="Kadrom", key="nav_v2",
    label_visibility="collapsed", selection_mode="single",
)
page = NAV[selected_nav or "Kadrom"]


@st.cache_data(show_spinner=False)
def player_directory() -> dict[str, str]:
    return bundled_catalog()


def backup_json() -> bytes:
    payload = {}
    for name in names:
        selected, injured = get_roster(name)
        payload[name] = {"roster": selected, "il": injured}
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def data_for_analysis() -> tuple[pd.DataFrame | None, str, str | None]:
    """Only load or fetch data on analysis/radar pages, not roster editor."""
    if "demo_data" in st.session_state:
        return normalize(st.session_state["demo_data"]), "SENTETİK DEMO", None
    try:
        projected = load_projection()
        age = projection_cache_age_hours()
        if (projected is None or (age is not None and age > 24)) and not st.session_state.get("projection_checked"):
            st.session_state["projection_checked"] = True
            if os.getenv("FANTASY_OFFLINE_TEST") != "1":
                try:
                    with st.spinner("2026–27 projeksiyonları getiriliyor..."):
                        projected = fetch_fantasypros(timeout=9)
                except Exception as exc:
                    projected = load_projection()
                    st.session_state["projection_error"] = str(exc)
        real = load_cache(SEASON)
        if projected is None:
            if real is not None:
                return real, "Gerçek NBA maçları (projeksiyon bulunamadı)", None
            return None, "Veri bulunamadı", st.session_state.get("projection_error")
        blended = blend_with_actual(projected, real)
        return blended, ("Projeksiyon + gerçek maçlar" if real is not None else "2026–27 projeksiyonu"), None
    except Exception as exc:
        return None, "Veri okunamadı", str(exc)


def go_to_data_center():
    # Callbacks run before widgets are instantiated; do not mutate live nav widget state.
    st.session_state["nav_v2"] = "Veri"


def activate_demo():
    st.session_state["demo_data"] = pd.read_csv(ROOT / "sample_data" / "demo_season_totals.csv")
    st.session_state["nav_v2"] = "Analiz"


def no_data_message(error: str | None):
    st.warning("Analiz için henüz projeksiyon yüklenmemiş. Kadron kayıtlı kalır.")
    if error:
        st.caption("Kaynak bağlantısı: " + str(error)[:220])
    st.button("Projeksiyon kaynağına git →", type="primary",
              on_click=go_to_data_center)


if page == "👥 Kadrom":
    st.subheader("Kadrom")
    st.caption("Oyuncularını ara, ekle ve kaydet. Her fantasy takımının kadrosu ayrı tutulur.")
    catalog = player_directory()
    roster_key = f"roster_input_{team_name}"
    il_key = f"il_input_{team_name}"
    for pid in list(roster_ids) + list(st.session_state.get(roster_key, [])):
        if pid not in catalog:
            catalog[pid] = display_name(pid, catalog)
    catalog = dict(sorted(catalog.items(), key=lambda item: item[1].casefold()))
    with st.container(border=True):
        with st.expander("➕ Listede olmayan oyuncu ekle", expanded=False):
            with st.form(f"add_custom_{team_name}", clear_on_submit=True):
                c_name, c_btn = st.columns([2.5, 1], vertical_alignment="bottom")
                with c_name:
                    typed = st.text_input("Listede bulamazsan buraya yaz", placeholder="Oyuncunun tam adı")
                with c_btn:
                    add = st.form_submit_button("➕ Oyuncu ekle", use_container_width=True)
                if add:
                    if not typed.strip():
                        st.warning("Önce oyuncunun adını yaz.")
                    else:
                        current = list(st.session_state.get(roster_key, roster_ids))
                        new_pid = find_catalog_player(typed.strip(), catalog)
                        if new_pid in current:
                            st.info("Bu oyuncu zaten seçili.")
                        elif len(current) >= 15:
                            st.error("Kadro sınırı 15 oyuncu.")
                        else:
                            st.session_state[roster_key] = current + [new_pid]
                            st.rerun()
        selected = st.multiselect(
            "Oyuncularım (isim yazarak ara · en fazla 15)",
            list(catalog),
            default=[pid for pid in roster_ids if pid in catalog],
            format_func=lambda pid: display_name(pid, catalog),
            max_selections=15, placeholder="İsim ara ve seç…", key=roster_key,
        )
        injured = st.multiselect(
            "IL / sakat listesi (en fazla 2)",
            selected, default=[pid for pid in il_ids if pid in selected],
            format_func=lambda pid: display_name(pid, catalog), max_selections=2,
            placeholder="IL oyuncularını seç…", key=il_key,
        )
        pending = set(selected) != set(roster_ids) or set(injured) != set(il_ids)
        st.progress(min(len(selected) / 15, 1.0), text=f"{len(selected)}/15 oyuncu seçildi")
        st.caption(f"IL listesi: {len(injured)}/2 · Sadece değişiklik olduğunda kaydetme butonu aktif olur.")
        if st.button("💾 Kadroyu kaydet", type="primary", use_container_width=True,
                     disabled=not pending):
            save_roster(team_name, selected, injured)
            st.session_state[f"saved_{team_name}"] = True
            st.rerun()
        if st.session_state.pop(f"saved_{team_name}", False):
            st.success("Kadron kaydedildi.")

    if roster_ids:
        st.markdown('<div class="nba-section">KAYITLI OYUNCULAR</div>', unsafe_allow_html=True)
        roster_table = pd.DataFrame({
            "Oyuncu": [display_name(pid, catalog) for pid in roster_ids],
            "Durum": ["IL" if pid in il_ids else "Kadromda" for pid in roster_ids],
        })
        st.dataframe(roster_table, hide_index=True, use_container_width=True, height=min(600, 85+35*len(roster_table)))
    st.caption("Önemli: Kadrolar henüz kalıcı bulut veritabanında değil. Veri > Yedekler bölümünden JSON yedeği alabilirsin.")


elif page in ("📊 Kadro Analizi", "🔎 Oyuncu Radarı"):
    raw, source_label, error = data_for_analysis()
    if raw is None:
        no_data_message(error)
        st.stop()

    resolved, resolved_il, missing = resolve_roster_ids(roster_ids, il_ids, raw)
    if fmt == "CAT":
        players, info = category_scores(raw)
        sort_col = "Z_TOTAL"
    else:
        players = points_scores(raw, get_weights(team_name))
        info = {}
        sort_col = "FPTS_PG"
    selected = players[players["PLAYER_ID"].isin(set(resolved) - set(resolved_il))].copy()
    st.caption(f"Kaynak: {source_label} · {len(players)} oyuncu · "
               f"Gerçek maç verisi: {last_updated(SEASON) or 'Henüz yok'}")
    if source_label == "SENTETİK DEMO":
        st.warning("Örnek veri açıktır. Bu sayılar gerçek NBA oyuncularına ait değildir.")
    if missing:
        st.warning(f"{len(missing)} oyuncun projeksiyon havuzuyla eşleşmedi: "
                   + ", ".join(display_name(pid, player_directory()) for pid in missing))
    if "FGA_PROXY" in raw.columns and raw["FGA_PROXY"].astype(str).str.lower().eq("true").any() and fmt == "CAT":
        st.caption("FG% ve FT% hacimleri kısmen yaklaşık tahmindir. Ayrıntılı FGA/FTA geldiğinde netleşir.")

    if page == "📊 Kadro Analizi":
        st.subheader(f"{team_name} · Kadro analizi")
        if selected.empty:
            st.info("Henüz bu kadroya eklenmiş ve istatistikle eşleşen oyuncu yok. 👥 Kadrom bölümünden ekleyebilirsin.")
            st.stop()

        if fmt == "CAT":
            result, meta = roster_analysis(players, resolved, resolved_il)
            c1, c2, c3 = st.columns(3)
            c1.metric("Analiz edilen", str(len(selected)))
            c2.metric("FG%", f"%{100 * meta['fgm_pg'] / meta['fga_pg']:.1f}" if meta["fga_pg"] else "—")
            c3.metric("FT%", f"%{100 * meta['ftm_pg'] / meta['fta_pg']:.1f}" if meta["fta_pg"] else "—")
            st.markdown("#### Kategori dengesi")
            st.caption("Pozitif z-score güçlü, negatif z-score gelişime açık kategoriyi gösterir.")
            st.bar_chart(result.set_index("Kategori")["Ortalama z-score"],
                         horizontal=True, height=340)
            show_result = result.copy()
            show_result["Kadro değeri (maç başı toplam)"] = show_result.apply(
                lambda r: f"%{100*r['Kadro değeri (maç başı toplam)']:.1f}"
                if r["Kategori"] in ("FG%", "FT%") else f"{r['Kadro değeri (maç başı toplam)']:.2f}", axis=1)
            st.dataframe(show_result, hide_index=True, use_container_width=True,
                         column_config={"Ortalama z-score": st.column_config.NumberColumn(
                             "Z-score", format="%.2f")},
                         height=375)
            st.markdown("#### Punt seçenekleri")
            st.dataframe(category_punt_view(players, resolved, resolved_il).head(4),
                         hide_index=True, use_container_width=True,
                         column_config={"Kalan 8 kategori z toplamı / oyuncu": st.column_config.NumberColumn(
                             "Kalan 8 kategori z", format="%.2f")})
            st.caption("Kategori z-score kıyası NBA oyuncu havuzuna göredir, Yahoo ligindeki 12 takıma değil. "
                       "Punt puanı rakibi ve kazanma olasılığını henüz içermez.")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Oyuncu", str(len(selected)))
            c2.metric("Toplam maç başı FPTS", f"{selected['FPTS_PG'].sum():.1f}")
            ptable = selected[["PLAYER_NAME", "TEAM_ABBREVIATION", "MIN_PG", "GP", "FPTS_PG"]].copy()
            st.dataframe(ptable.sort_values("FPTS_PG", ascending=False).rename(columns={
                "PLAYER_NAME": "Oyuncu", "TEAM_ABBREVIATION": "NBA",
                "MIN_PG": "Dakika/maç", "GP": "Beklenen maç",
                "FPTS_PG": "FPTS/maç"}), hide_index=True, use_container_width=True,
                column_config={"FPTS/maç": st.column_config.NumberColumn("FPTS/maç",format="%.1f")})
            st.caption("Yahoo standart Points katsayıları kullanılır. Maç fikstürü ve aktif slot kısıtları "
                       "henüz dahil edilmedi.")

        st.markdown("#### Beklenen süre ve rol")
        roles = selected[["PLAYER_NAME", "TEAM_ABBREVIATION", "MIN_PG", "GP"]].copy()
        roles["Rol"] = pd.cut(
            roles["MIN_PG"], bins=[-1, 15, 23, 29, 100],
            labels=["Sınırlı", "Rotasyon", "Yüksek rotasyon", "Ana rotasyon"],
        )
        if "ROLE_SIGNAL" in selected.columns:
            roles["Dakika trendi"] = selected["ROLE_SIGNAL"].values
        if "GP_ACTUAL" in selected.columns:
            roles["Oynanan maç"] = selected["GP_ACTUAL"].values
        st.dataframe(roles.sort_values("MIN_PG", ascending=False).rename(columns={
            "PLAYER_NAME": "Oyuncu", "TEAM_ABBREVIATION": "NBA",
            "MIN_PG": "Dakika / maç", "GP": "Beklenen maç"}),
            hide_index=True, use_container_width=True)
        st.caption("Rol etiketleri beklenen dakikadan hesaplanır; kesin ilk beş tahmini değildir.")

    else:
        st.subheader("Oyuncu Radarı")
        st.caption("2026–27 tüm oyuncu projeksiyonları · 1. sıradan son oyuncuya kadar. "
                   "Yahoo'da boşta olma durumu bilinmiyor.")
        ranked = players.sort_values(sort_col, ascending=False).copy()
        ranked.insert(0, "Sıra", range(1, len(ranked) + 1))
        ranking_tab, fit_tab = st.tabs(["🏆 Tüm oyuncular", "🎯 Kadroma uygun adaylar"])
        with ranking_tab:
            st.caption(f"Projeksiyon havuzu: {len(ranked)} oyuncu · "
                       f"{'9-cat z-score' if fmt == 'CAT' else 'Yahoo Points'} bazlı genel sıralama.")
            query = st.text_input("Oyuncu ara", key=f"ranking_search_{team_name}",
                                  placeholder="Örn. Tyrese Maxey")
            ranking_view = ranked[
                ranked["PLAYER_NAME"].str.contains(query.strip(), case=False, regex=False, na=False)
            ] if query.strip() else ranked
            cols = ["Sıra", "PLAYER_NAME", "TEAM_ABBREVIATION", "MIN_PG", "GP", sort_col]
            st.dataframe(ranking_view[cols].rename(columns={
                "PLAYER_NAME": "Oyuncu", "TEAM_ABBREVIATION": "NBA",
                "MIN_PG": "DK/maç", "GP": "Beklenen maç",
                "Z_TOTAL": "9-cat z", "FPTS_PG": "FPTS/maç"}),
                hide_index=True, use_container_width=True, height=560,
                column_config={
                    "9-cat z": st.column_config.NumberColumn("9-cat z", format="%.2f"),
                    "FPTS/maç": st.column_config.NumberColumn("FPTS/maç", format="%.1f"),
                    "DK/maç": st.column_config.NumberColumn("DK/maç", format="%.1f"),
                })
        with fit_tab:
            st.caption("Kadronun dışında kalan tüm oyuncular değerlendirilir. "
                       "İlk 35 veya 185 sınırı yok; oyuncular aşağıdaki öneri sırasına göre dizilir.")
            query_candidate = st.text_input("Aday oyuncu ara", key=f"candidate_search_{team_name}",
                                             placeholder="İsimle filtrele…")
            if fmt == "CAT":
                fit_scores, _ = category_team_fit(players, resolved, resolved_il)
                general_ranks = ranked[["PLAYER_ID", "Sıra"]]
                candidates = fit_scores.loc[~fit_scores["PLAYER_ID"].isin(resolved)].copy()
                candidates = candidates.merge(general_ranks, on="PLAYER_ID", how="left")
                candidates = candidates.sort_values("TAKIMA_UYUM", ascending=False).reset_index(drop=True)
                candidates.insert(0, "Öneri sırası", range(1, len(candidates) + 1))
                if query_candidate.strip():
                    candidates = candidates[candidates["PLAYER_NAME"].str.contains(
                        query_candidate.strip(), case=False, regex=False, na=False)]
                st.caption("Takıma uyum: kadronun zayıf 9-cat kategorilerine ağırlık verilir; "
                           "sıralama gerçek waiver uygunluğu veya güncel yükseliş garantisi değildir.")
                st.dataframe(candidates[["Öneri sırası", "Sıra", "PLAYER_NAME",
                                         "TEAM_ABBREVIATION", "MIN_PG", "GP",
                                         "TAKIMA_UYUM", "Z_TOTAL"]].rename(columns={
                    "Sıra": "Genel sıra", "PLAYER_NAME": "Oyuncu", "TEAM_ABBREVIATION": "NBA",
                    "MIN_PG": "DK/maç", "GP": "Beklenen maç",
                    "TAKIMA_UYUM": "Takıma uyum", "Z_TOTAL": "9-cat z"}),
                    hide_index=True, use_container_width=True, height=560,
                    column_config={
                        "Takıma uyum": st.column_config.NumberColumn("Takıma uyum", format="%.2f"),
                        "9-cat z": st.column_config.NumberColumn("9-cat z", format="%.2f"),
                    })
            else:
                candidates = ranked.loc[~ranked["PLAYER_ID"].isin(resolved)].copy()
                candidates.insert(0, "Öneri sırası", range(1, len(candidates) + 1))
                if query_candidate.strip():
                    candidates = candidates[candidates["PLAYER_NAME"].str.contains(
                        query_candidate.strip(), case=False, regex=False, na=False)]
                st.caption("Points liginde tüm kadro dışı oyuncular beklenen maç başı fantasy "
                           "puanına göre sıralanır; Yahoo waiver sahipliği bilinmez.")
                st.dataframe(candidates[["Öneri sırası", "Sıra", "PLAYER_NAME",
                                         "TEAM_ABBREVIATION", "MIN_PG", "GP", "FPTS_PG"]].rename(columns={
                    "Sıra": "Genel sıra", "PLAYER_NAME": "Oyuncu", "TEAM_ABBREVIATION": "NBA",
                    "MIN_PG": "DK/maç", "GP": "Beklenen maç",
                    "FPTS_PG": "FPTS/maç"}),
                    hide_index=True, use_container_width=True, height=560,
                    column_config={"FPTS/maç": st.column_config.NumberColumn("FPTS/maç", format="%.1f")})


elif page == "⚙️ Veri Merkezi":
    st.subheader("Veri Merkezi")
    st.caption("Günlük kullanımda bu bölümü açman gerekmiyor. Kaynaklar, güncellemeler ve yedekler burada.")

    proj_age = projection_cache_age_hours()
    project_count = 0
    try:
        existing_projection = load_projection()
        if existing_projection is not None:
            project_count = len(existing_projection)
    except Exception:
        pass
    st.metric("Projeksiyondaki oyuncu", project_count)
    st.caption("Kaynak: FantasyPros konsensüs · "
               + (f"En son {proj_age:.0f} saat önce yenilendi" if proj_age is not None else "Henüz yüklenmedi"))
    with st.container(border=True):
        st.markdown("#### 🔮 Sezon projeksiyonları")
        st.markdown(f"[FantasyPros kaynağı]({SOURCE_URL})")
        if st.button("Projeksiyonları güncelle", type="primary", use_container_width=True):
            try:
                with st.spinner("2026–27 projeksiyonları indiriliyor..."):
                    fetched = fetch_fantasypros(timeout=15)
                st.session_state.pop("projection_error", None)
                st.session_state["projection_checked"] = True
                st.success(f"{len(fetched)} oyuncu güncellendi.")
                st.rerun()
            except Exception as exc:
                st.error(f"Projeksiyon alınamadı: {exc}")
        with st.expander("Projeksiyon CSV yükle / şablon indir"):
            upload = st.file_uploader("Projeksiyon CSV dosyası", type=["csv"], key="projection_csv")
            if upload is not None and st.button("Projeksiyon CSV'sini kaydet"):
                try:
                    saved = save_projection(pd.read_csv(upload))
                    st.success(f"{len(saved)} oyuncu yüklendi.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"CSV hatası: {exc}")
            st.download_button("Boş projeksiyon şablonu", (ROOT / "sample_data" / "projection_template.csv").read_bytes(),
                               "2026_27_projeksiyon_sablonu.csv", mime="text/csv")
            st.caption("FantasyPros ücretsiz tablo FGA/FTA vermez; ilk versiyonda yüzdeler için "
                       "tahmini hacimler kullanılır. Kendi CSV'nde gerçek şut hacimlerini verebilirsin.")

    with st.expander("🏀 Gerçek NBA istatistikleri · CSV / API"):
        st.caption("stats.nba.com Streamlit Cloud üzerinden zaman aşımına uğrayabilir. "
                   "Sezon başlangıcında projeksiyonlar kullanılır.")
        if st.button("2026–27 gerçek sezon verisini çek"):
            try:
                with st.spinner("NBA verileri alınıyor..."):
                    fetched = fetch_nba_totals(SEASON)
                st.success(f"{len(fetched)} oyuncunun gerçek sezon verisi kaydedildi.")
                st.rerun()
            except Exception as exc:
                st.error(f"NBA API yanıt vermedi: {exc}")
        uploaded_stats = st.file_uploader("Sezon toplamları CSV", type=["csv"], key="actual_csv")
        if uploaded_stats is not None and st.button("Gerçek sezon CSV'sini kaydet"):
            try:
                saved = save_csv(SEASON, pd.read_csv(uploaded_stats))
                st.success(f"{len(saved)} oyuncu kaydedildi.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        st.download_button("Gerçek sezon CSV şablonu",
                           (ROOT / "sample_data" / "season_totals_template.csv").read_bytes(),
                           "nba_2026_27_sezon_toplamlari.csv", mime="text/csv")

    with st.expander("💾 Kadroları yedekle / geri yükle"):
        st.caption("Streamlit ücretsiz sunucusunda yerel SQLite kayıtları sıfırlanabilir. "
                   "Beş takımını tek JSON dosyasına yedekleyebilirsin.")
        st.download_button("Beş kadromun yedeğini indir", backup_json(),
                           "nba_5_takim_kadro_yedek.json", mime="application/json",
                           use_container_width=True)
        restore = st.file_uploader("Kadro yedeği yükle", type=["json"], key="restore_upload")
        if restore is not None and st.button("Yedeği geri yükle"):
            try:
                if restore.size > 250000:
                    raise ValueError("Dosya çok büyük")
                saved = json.loads(restore.getvalue().decode("utf-8"))
                if not isinstance(saved, dict) or set(saved) != set(names):
                    raise ValueError("Beş takımın tümünü içeren bir yedek yükle")
                checked = {}
                for name in names:
                    row = saved[name]
                    ids, il = row["roster"], row["il"]
                    if (not isinstance(ids, list) or not isinstance(il, list)
                        or not all(isinstance(pid, str) and len(pid) < 150 for pid in ids + il)
                        or len(ids) > 15 or len(set(ids)) != len(ids)
                        or len(il) > 2 or not set(il).issubset(set(ids))):
                        raise ValueError(f"{name} kadrosu geçersiz")
                    checked[name] = (ids, il)
                for name, (ids, il) in checked.items():
                    save_roster(name, ids, il)
                    st.session_state.pop(f"roster_input_{name}", None)
                    st.session_state.pop(f"il_input_{name}", None)
                st.success("Tüm kadrolar geri yüklendi.")
                st.rerun()
            except Exception as exc:
                st.error(f"Yedek yüklenemedi: {exc}")

    if fmt == "PTS":
        with st.expander("⚙️ Points ligine özel puan ayarları"):
            st.caption("Yahoo varsayılan puanları otomatik tanımlı; özel ayar gerekmiyorsa değiştirme.")
            weights = get_weights(team_name)
            if st.button("Yahoo standart puanlarına sıfırla"):
                reset_weights(team_name)
                st.rerun()
            with st.form(f"point_form_{team_name}"):
                values = {}
                cols = st.columns(3)
                for i, stat in enumerate(POINTS_FIELDS):
                    values[stat] = cols[i % 3].number_input(stat, value=float(weights.get(stat, 0)),
                                                           step=.25, format="%.2f")
                if st.form_submit_button("Puanları kaydet"):
                    save_weights(team_name, values)
                    st.success("Özel katsayılar kaydedildi.")
                    st.rerun()

    with st.expander("🧪 Test amaçlı örnek veri"):
        st.warning("Buradaki veriler sentetiktir; NBA istatistikleri değildir.")
        st.button("Örnek veriyi aç", on_click=activate_demo)
        if st.button("Örnek veri modunu kapat"):
            st.session_state.pop("demo_data", None)
            st.rerun()

footer()
