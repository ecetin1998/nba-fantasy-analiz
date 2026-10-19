"""Yahoo Fantasy NBA independent roster analyzer — MVP v0.1.

Run: streamlit run app.py
No Yahoo credentials required. nba_api supplies season totals when reachable.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from analysis import (CATEGORIES, POINTS_FIELDS, category_punt_view, category_team_fit,
                      category_scores, normalize, points_scores, roster_analysis)
from data_sources import fetch_nba_totals, last_updated, load_cache, save_csv
from projection_engine import PROJECTION_SEASON, SOURCE_URL, blend_with_actual, fetch_fantasypros, load_projection, projection_cache_age_hours, save_projection
from roster_catalog import bundled_catalog, display_name, find_catalog_player, resolve_roster_ids
from storage import (TEAMS, YAHOO_DEFAULT_POINTS, get_roster, get_weights,
                     init, reset_weights, save_roster, save_weights)

st.set_page_config(page_title="NBA Fantasy | 5 Takım Analizi", page_icon="🏀", layout="wide")
init()

st.title("🏀 NBA Fantasy — Kadro Analizi")
st.caption("5 takım · 2026–27 projeksiyon + gerçek maç verisi · MVP v0.4")

season = st.sidebar.selectbox("Analiz sezonu", ["2026-27", "2025-26"], index=0,
    help="Yeni sezonda önce projeksiyon, maçlar oynandıkça gerçek istatistikler.")
team_names = [t[0] for t in TEAMS]
team_name = st.sidebar.selectbox("Fantasy takımım", team_names)
team_meta = next(t for t in TEAMS if t[0] == team_name)
team_type = team_meta[2]
st.sidebar.markdown(f"**{team_name}** · {'Standart 9-cat' if team_type == 'CAT' else 'Standart Yahoo Points'} · Lig {team_meta[1]}")
st.sidebar.info("Her takımın kadrosu ayrı saklanır. Yahoo liginin rakip kadroları bilinmiyor.")

with st.sidebar.expander("💾 Kadrolarımı yedekle / geri yükle"):
    backup = {}
    for saved_team in team_names:
        ids, il = get_roster(saved_team)
        backup[saved_team] = {"roster": ids, "il": il}
    st.download_button(
        "⬇️ Beş kadronun JSON yedeğini indir",
        data=json.dumps(backup, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="nba_fantasy_5_kadro_yedek.json",
        mime="application/json",
        use_container_width=True,
    )
    saved_file = st.file_uploader("JSON kadro yedeğini geri yükle", type=["json"], key="restore_json")
    if saved_file is not None and st.button("📥 Yedekten geri yükle", key="restore_submit"):
        try:
            if saved_file.size > 250_000:
                raise ValueError("Yedek dosyası çok büyük")
            loaded = json.loads(saved_file.getvalue().decode("utf-8"))
            if not isinstance(loaded, dict) or set(loaded) != set(team_names):
                raise ValueError("Yedekte beş takımın tamamı bulunmalı")
            checked = {}
            for saved_team in team_names:
                row = loaded[saved_team]
                if not isinstance(row, dict):
                    raise ValueError(f"{saved_team}: hatalı kayıt")
                ids, il = row.get("roster"), row.get("il")
                if not isinstance(ids, list) or not isinstance(il, list):
                    raise ValueError(f"{saved_team}: liste bekleniyor")
                if not all(isinstance(pid, str) and len(pid) < 150 for pid in ids + il):
                    raise ValueError(f"{saved_team}: hatalı oyuncu kaydı")
                if len(set(ids)) > 15 or len(set(il)) > 2 or not set(il).issubset(set(ids)):
                    raise ValueError(f"{saved_team}: kadro/IL limitini aşıyor")
                checked[saved_team] = (ids, il)
            for saved_team, (ids, il) in checked.items():
                save_roster(saved_team, ids, il)
                st.session_state.pop(f"roster_input_{saved_team}", None)
                st.session_state.pop(f"il_input_{saved_team}", None)
            st.toast("Beş takımın kadrosu yedekten geri yüklendi.", icon="✅")
            st.rerun()
        except Exception as exc:
            st.error(f"Yedek yüklenemedi: {exc}")



# Kadro girmek, NBA istatistikleri indirilemese bile çalışır.
@st.cache_data(show_spinner=False)
def player_directory() -> dict[str, str]:
    return bundled_catalog()


roster_ids, il_ids = get_roster(team_name)
catalog = player_directory()
roster_widget_key = f"roster_input_{team_name}"
manual_widget_key = f"manual_player_{team_name}"
for stored_id in list(roster_ids) + list(st.session_state.get(roster_widget_key, [])):
    if stored_id not in catalog:
        catalog[stored_id] = display_name(stored_id, catalog)
catalog = dict(sorted(catalog.items(), key=lambda item: item[1].casefold()))

with st.container(border=True):
    st.subheader(f"👥 Kadrom · {team_name}")
    st.caption("NBA verilerini beklemeden oyuncularını seçebilirsin. "
               "Beş takım birbirinden bağımsız. Takım seçimi sol üstteki « menüsünde.")
    manual_name = st.text_input("Oyuncu listede yoksa adını yaz", key=manual_widget_key,
                                placeholder="Örn. yeni bir çaylağın tam adı")
    if st.button("➕ İsmini yazdığım oyuncuyu kadroya ekle", key=f"manual_add_{team_name}"):
        if not manual_name.strip():
            st.warning("Önce oyuncunun adını yaz.")
        else:
            existing = list(st.session_state.get(roster_widget_key, roster_ids))
            new_id = find_catalog_player(manual_name.strip(), catalog)
            if new_id in existing:
                st.info("Bu oyuncu zaten seçili.")
            elif len(existing) >= 15:
                st.error("En fazla 15 oyuncu seçilebilir.")
            else:
                st.session_state[roster_widget_key] = existing + [new_id]
                st.rerun()

    selected_roster = st.multiselect(
        "Oyuncularım (isim yazarak ara · en fazla 15)",
        options=list(catalog),
        default=[pid for pid in roster_ids if pid in catalog],
        format_func=lambda pid: display_name(pid, catalog),
        max_selections=15, key=roster_widget_key,
        placeholder="Oyuncu ara / seç",
    )
    selected_il = st.multiselect(
        "IL / sakat listesi (en fazla 2)",
        options=selected_roster,
        default=[pid for pid in il_ids if pid in selected_roster],
        format_func=lambda pid: display_name(pid, catalog),
        max_selections=2, key=f"il_input_{team_name}",
    )
    st.caption(f"Seçilen: {len(selected_roster)}/15 · IL: {len(selected_il)}/2")
    if st.button("💾 Kadroyu kaydet", type="primary", key=f"save_roster_{team_name}", use_container_width=True):
        try:
            save_roster(team_name, selected_roster, selected_il)
            st.session_state[f"just_saved_{team_name}"] = len(selected_roster)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
    if st.session_state.pop(f"just_saved_{team_name}", None) is not None:
        st.success(f"{team_name} kadrosu kaydedildi.")
    if roster_ids:
        st.markdown("**Son kaydedilen kadro**")
        st.dataframe(pd.DataFrame({
            "Oyuncu": [display_name(pid, catalog) for pid in roster_ids],
            "IL": [pid in il_ids for pid in roster_ids],
        }), hide_index=True, use_container_width=True)
    else:
        st.info("Henüz kaydedilmiş oyuncu yok.")
    st.caption("⚠️ Streamlit Cloud üzerindeki yerel kayıt sistemi geçicidir: "
               "sunucu yeniden başladığında kadrolar sıfırlanabilir. Sol menüden JSON yedeğini indir. Kalıcı veritabanı sonraki geliştirmedir.")

if season == PROJECTION_SEASON:
    with st.container(border=True):
        st.subheader("🔮 2026–27 Sezon Projeksiyonları")
        st.caption("Ana kaynak: FantasyPros uzman konsensüsü. NBA'in ilk maçlarını beklemeden "
                   "oyuncu tahminleriyle analiz yapabilirsin. Veri kaynağına erişim "
                   "olmazsa CSV yükleme kullanılabilir.")
        st.markdown(f"[FantasyPros tahminlerini gör]({SOURCE_URL})")
        colp1, colp2 = st.columns(2)
        with colp1:
            if st.button("🔄 Projeksiyonları getir / güncelle", use_container_width=True):
                try:
                    with st.spinner("Projeksiyon tablosu okunuyor..."):
                        loaded = fetch_fantasypros()
                    st.success(f"{len(loaded)} oyuncunun projeksiyonu alındı.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Projeksiyon alınamadı: {exc}")
        with colp2:
            upload = st.file_uploader("Projeksiyon CSV yükle (alternatif)", type=["csv"], key="projection_upload")
            if upload is not None and st.button("Projeksiyon CSV'sini kullan", key="use_projection_csv"):
                try:
                    loaded = save_projection(pd.read_csv(upload))
                    st.success(f"{len(loaded)} oyuncunun projeksiyonu kaydedildi.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Projeksiyon CSV'si geçersiz: {exc}")
        projection_template = Path(__file__).resolve().parent / "sample_data" / "projection_template.csv"
        st.download_button(
            "📄 Projeksiyon CSV şablonunu indir",
            data=projection_template.read_bytes(),
            file_name="nba_2026_27_projection_template.csv",
            mime="text/csv",
        )
        st.caption("FG%/FT% notu: FantasyPros'un ücretsiz tablosunda şut denemeleri yok. "
                   "FGA/FTA için geçici tahmini hacim kullanılır; bu değerler kaynak tahmini değildir.")

with st.expander("📥 Oyuncu verisi · NBA'den yenile / CSV yükle", expanded=False):
    left, right = st.columns(2)
    with left:
        st.markdown("**NBA istatistikleri**")
        st.caption("Seçili sezonun normal sezon toplamlarını stats.nba.com üzerinden alır. Bazen 403 / zaman aşımı olabilir.")
        if st.button("Gerçek sezon maçlarını çek / yenile", use_container_width=True):
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
    basis = "Gerçek NBA sezon toplamları"
    if "demo_data" in st.session_state:
        raw = normalize(st.session_state["demo_data"])
        basis = "SENTETİK DEMO"
        st.warning("DEMO MODU — Bu oyuncular ve istatistikler tamamen yapaydır. Gerçek NBA analizi değildir.")
    elif season == PROJECTION_SEASON:
        projected = load_projection()
        hours_old = projection_cache_age_hours()
        needs_refresh = projected is None or (hours_old is not None and hours_old > 24)
        if needs_refresh and not st.session_state.get("auto_projection_checked"):
            st.session_state["auto_projection_checked"] = True
            try:
                with st.spinner("2026–27 uzman projeksiyonları güncelleniyor..."):
                    projected = fetch_fantasypros(timeout=12)
            except Exception as exc:
                st.warning(f"Projeksiyon kaynağına erişilemedi: {exc}. "
                           "Önceki önbellek varsa korunur; yoksa yukarıdaki CSV seçeneğini kullan.")
                projected = load_projection()
        if projected is not None and hours_old is not None and hours_old > 36:
            st.warning(f"Son başarılı projeksiyon yenilemesi yaklaşık {hours_old:.0f} saat önce. "
                       "İnternet kaynağı yanıt vermezse bu veri kullanılmaya devam eder.")
        actual = load_cache(PROJECTION_SEASON)
        raw = blend_with_actual(projected, actual) if projected is not None else actual
        basis = ("2026–27 FantasyPros projeksiyon + gerçek NBA verisi" if actual is not None
                 else "2026–27 FantasyPros projeksiyon") if projected is not None else "Gerçek 2026–27 maçları"
    else:
        raw = load_cache(season)
except Exception as exc:
    raw = None
    st.error(f"Sezon verisi okunamadı: {exc}")

if raw is None:
    st.info("Kadronu üstteki 👥 Kadrom bölümünden hemen girebilirsin. "
            "Analiz için projeksiyonları yükle. Gerçek maçları beklemene gerek yok.")
    sample = Path(__file__).resolve().parent / "sample_data" / "season_totals_template.csv"
    st.download_button("Boş CSV şablonunu indir", data=sample.read_bytes(),
                       file_name="nba_season_totals_template.csv", mime="text/csv")
    st.stop()

st.caption(f"Kaynak: {basis} · Sezon: {season} · {len(raw)} oyuncu · "
           f"Gerçek verilerin son kaydı: {last_updated(season) or 'Yok'}")
if season == PROJECTION_SEASON and "demo_data" not in st.session_state:
    if "ACTUAL_WEIGHT" in raw.columns:
        matches = int((pd.to_numeric(raw["GP_ACTUAL"], errors="coerce").fillna(0) > 0).sum())
        st.info(f"Projeksiyon / gerçekleşen: {matches} oyuncuda gerçek maç var. "
                "5 maçta %20, 10 maçta %40, 20 maçta %65, 30+ maçta %85 gerçek veri ağırlığı.")
    if "FGA_PROXY" in raw.columns and raw["FGA_PROXY"].astype(str).str.lower().eq("true").any():
        st.warning("FG%/FT% için şut denemelerinin bir kısmı tahmini hacim. "
                   "Yüzdelerin gerçek kategori etkisini şimdilik yaklaşık hesaplıyoruz.")


if team_type == "CAT":
    players, reference_info = category_scores(raw)
else:
    players = None
    reference_info = {}

resolved_roster_ids, resolved_il_ids, missing_ids = resolve_roster_ids(roster_ids, il_ids, raw)
if missing_ids:
    st.warning(f"Sezon verisinde bulunamayan {len(missing_ids)} oyuncu analiz dışında kalıyor: "
               + ", ".join(display_name(pid, catalog) for pid in missing_ids))
st.subheader(f"{team_name} · {'H2H Categories' if team_type == 'CAT' else 'H2H Points'}")
tab_analysis, tab_rankings, tab_candidates = st.tabs(
    ["📊 Kadro analizi", "🏆 Oyuncu sıralaması", "🔎 Aday oyuncular"])

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
    selected = players[players["PLAYER_ID"].isin(set(resolved_roster_ids) - set(resolved_il_ids))].copy()

    if season == PROJECTION_SEASON:
        with tab_analysis:
            st.markdown("**⏱️ Beklenen rol ve dakika**")
            if selected.empty:
                st.caption("Oyuncularını üstteki Kadrom alanından eklediğinde rol tahminlerini burada görebilirsin.")
            else:
                role_frame = selected.copy()
                role_frame["Dakika profili"] = pd.cut(role_frame["MIN_PG"], bins=[-1, 15, 23, 29, 100],
                    labels=["Sınırlı", "Rotasyon", "Yüksek rotasyon", "Yüksek dakika"])
                if "GP_ACTUAL" not in role_frame.columns:
                    role_frame["GP_ACTUAL"] = 0
                role_frame["GP_ACTUAL"] = pd.to_numeric(role_frame["GP_ACTUAL"], errors="coerce").fillna(0)
                role_cols = ["PLAYER_NAME", "TEAM_ABBREVIATION", "MIN_PG", "GP",
                             "Dakika profili", "GP_ACTUAL"]
                if "ROLE_SIGNAL" in role_frame.columns:
                    role_cols.append("ROLE_SIGNAL")
                if "MIN_DELTA" in role_frame.columns:
                    role_cols.append("MIN_DELTA")
                st.dataframe(role_frame[role_cols].rename(columns={
                    "PLAYER_NAME": "Oyuncu", "TEAM_ABBREVIATION": "NBA Takımı",
                    "MIN_PG": "Tahmini/Karma DK", "GP": "Tahmini maç",
                    "GP_ACTUAL": "Oynanan maç", "ROLE_SIGNAL": "Dakika sinyali",
                    "MIN_DELTA": "Gerçek − tahmin DK"}).sort_values("Tahmini/Karma DK", ascending=False),
                    hide_index=True, use_container_width=True)
                st.caption("Dakika profili yalnızca tahmini maç başına süreye göre sınıflanır; "
                           "kesin ilk beş veya sağlık garantisi değildir.")

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
                result, details = roster_analysis(players, resolved_roster_ids, resolved_il_ids)
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
                st.dataframe(category_punt_view(players, resolved_roster_ids, resolved_il_ids).head(5), hide_index=True, use_container_width=True)
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
            exclude = set(resolved_roster_ids)
            fit_ranked, weights_used = category_team_fit(players, resolved_roster_ids, resolved_il_ids)
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
            available = all_ranked[(all_ranked["Genel sıra"].between(36, 185)) & ~all_ranked["PLAYER_ID"].isin(resolved_roster_ids)].copy()
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
st.caption("MVP v0.3 · Henüz yok: gerçek Yahoo waiver sahipliği, canlı sakatlık, 7/15/30 gün formu, NBA haftalık fikstür ve rakip tahmini. "
           "NBA API kesintisinde manuel CSV yedeği kullanılabilir. Veri uygulamayı çalıştırdığın bilgisayarda tutulur.")
