"""Consistent accessible dark theme and lightweight presentation helpers.

All card markup contains app-controlled strings only; no user-generated HTML.
Use Streamlit widgets for every interactive element.
"""
import streamlit as st


STYLE = """
<style>
:root { color-scheme: dark; }
.stApp {
  background:
    radial-gradient(ellipse 680px 340px at 78% -170px, rgba(27,171,160,.14),transparent 80%),
    linear-gradient(180deg,#090f1b 0%,#0c1422 100%);
  color: #eef5ff;
}
.block-container { max-width:1120px !important;padding:1.15rem 1.85rem 4rem !important; }
header[data-testid="stHeader"] {background:transparent;}
div[data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
h1,h2,h3 {letter-spacing:-.03em;color:#f5f8ff !important;}
h2 {font-size:1.43rem !important;font-weight:760 !important;}
h3 {font-size:1.12rem !important;font-weight:720 !important;}
[data-testid="stMarkdownContainer"] p, .stCaption {line-height:1.55;}
[data-testid="stCaptionContainer"] {color:#9baec6 !important;}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border:1px solid #27374b !important;border-radius:17px !important;
  background-color:rgba(18,31,49,.45) !important;
}
[data-testid="stMetric"] {
  border:1px solid #24364b;
  border-radius:15px;
  background:#121e30;
  padding:15px 17px;
  min-height:93px;
}
[data-testid="stMetricLabel"] {color:#a6b7cc;font-size:.82rem;}
[data-testid="stMetricValue"] {color:#f5fbff;font-size:1.62rem;font-weight:760;letter-spacing:-.03em;}
[data-testid="stDataFrame"] {border:1px solid #27394b;border-radius:12px;overflow:hidden;}
[data-testid="stAlert"] {border-radius:12px;border-width:1px;}
[data-testid="stExpander"] {border:1px solid #2a3b51 !important;border-radius:13px !important;}
[data-testid="stExpander"] details summary {min-height:42px;}
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  border-radius:10px !important;min-height:42px;font-weight:620;
  border:1px solid #354b60;transition:background-color .15s ease,border-color .15s ease;
}
.stButton>button:hover, .stFormSubmitButton>button:hover {border-color:#62d7bb;}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{
  background:#3de1b4 !important;color:#061621 !important;border-color:#3de1b4 !important;font-weight:760 !important;
}
.stButton>button[kind="primary"]:hover,.stFormSubmitButton>button[kind="primary"]:hover{background:#73e9cb !important;}
[data-baseweb="select"]>div,[data-baseweb="input"]>div {border-radius:10px !important;}
[data-testid="stSegmentedControl"] {width:100%;}
[data-testid="stSegmentedControl"]>div {background:#101b2b;border:1px solid #293a50;border-radius:13px;padding:5px;gap:5px;overflow-x:auto;}
[data-testid="stSegmentedControl"] button {border-radius:9px !important;white-space:nowrap;min-height:42px;}
[data-testid="stSegmentedControl"] button[aria-checked="true"],[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
  background:#234e4c !important;color:#b9f9e5 !important;
}
.nba-hero {
  border:1px solid #2b5157;background:
    radial-gradient(circle at 86% 23%,rgba(37,205,159,.14),transparent 34%),
    linear-gradient(120deg,#172c46 0%,#102336 75%,#103a3d 100%);
  border-radius:19px;padding:24px 27px 23px;margin-bottom:21px;
}
.nba-kicker{font-size:.68rem;letter-spacing:.16em;font-weight:800;color:#84efcb;text-transform:uppercase;}
.nba-heading{font-size:clamp(1.82rem,4vw,2.53rem);font-weight:860;letter-spacing:-.045em;color:#fff;line-height:1.12;margin:10px 0 7px;}
.nba-heading span {color:#6cefc7;}
.nba-desc{color:#b8cddd;font-size:.88rem;margin:0;max-width:680px;}
.nba-brandline {display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.nba-brandmark {height:32px;width:32px;display:inline-flex;align-items:center;justify-content:center;
 border:1px solid rgba(125,244,201,.45);background:rgba(57,211,167,.14);border-radius:11px;font-size:17px;}
.nba-build{display:inline-flex;align-items:center;gap:6px;border:1px solid #4bccb5;
  border-radius:999px;padding:5px 11px;background:rgba(36,175,147,.13);
  color:#a7ffe0;font-weight:780;font-size:.69rem;letter-spacing:.045em;}
.nba-tag{display:inline-flex;align-items:center;border-radius:100px;border:1px solid #32545a;
 background:#143b3f;color:#8fe9d1;font-size:.77rem;padding:5px 10px;font-weight:720;white-space:nowrap;}
.nba-muted{color:#9fb2ca;font-size:.82rem;line-height:1.6;}
.nba-section {font-size:.7rem;letter-spacing:.15em;font-weight:800;color:#90a8c6;text-transform:uppercase;margin:18px 0 9px;}
.nba-divider {height:1px;background:#24354a;margin:24px 0 16px;}
.nba-footer {font-size:.76rem;color:#8297b3;line-height:1.6;}
.nba-inline-meta {display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:9px;}
.nba-smallcard {padding:12px 15px;background:#142033;border:1px solid #2b4056;border-radius:12px;}
.nba-smallcard b {font-size:1.02rem;color:#f3fbff;}
.nba-smallcard span {font-size:.76rem;color:#97abc3;}
@media(max-width:700px) {
  .block-container {padding:.5rem .85rem 3rem !important;}
  .nba-hero{padding:18px 16px;border-radius:15px;margin-bottom:16px;}
  .nba-heading{font-size:1.81rem;}
  .nba-kicker{font-size:.62rem;letter-spacing:.1em;}
  .nba-brandline {gap:7px;}
  .nba-build {font-size:.61rem;padding:4px 8px;}
  .nba-desc{font-size:.81rem;}
  [data-testid="stMetric"] {padding:11px 12px;min-height:80px;}
  [data-testid="stMetricValue"] {font-size:1.27rem !important;}
  [data-testid="stMetricLabel"] {font-size:.72rem;}
  h2{font-size:1.24rem !important;}
  h3{font-size:1.06rem !important;}
  [data-testid="stHorizontalBlock"]{gap:.6rem;}
  [data-testid="stSegmentedControl"] button{min-height:39px;padding:6px 8px;font-size:.78rem;}
  [data-testid="stSegmentedControl"]>div{gap:2px;}
  [data-testid="stDataFrame"] {max-width:100%;overflow:hidden;}
  .nba-section{margin-top:12px;}
}
@media(max-width:365px) {
  [data-testid="stMetricLabel"]{font-size:.65rem;}
  [data-testid="stSegmentedControl"] button{font-size:.72rem;padding:6px;}
}

/* UI V3: unmistakably different editorial + court-inspired interface */
.stApp {
  background: radial-gradient(ellipse 760px 560px at 95% -150px,rgba(134,79,255,.18),transparent 68%),
              radial-gradient(ellipse 600px 500px at -22% 42%,rgba(34,200,164,.075),transparent 60%),
              #080e19 !important;
}
.block-container {max-width:1190px !important;}
.nba-hero {
  min-height:232px;
  display:grid;
  grid-template-columns:minmax(0,1fr) 310px;
  align-items:center;
  gap:24px;
  background:linear-gradient(112deg,#15233d 0%,#131b34 56%,#171d37 100%) !important;
  border:1px solid rgba(138,162,224,.35);
  box-shadow:0 20px 55px rgba(0,0,0,.20),inset 0 1px 0 rgba(255,255,255,.045);
  padding:28px 32px;
  position:relative;overflow:hidden;
}
.nba-hero:before {content:"";position:absolute;inset:0 0 auto;height:3px;
 background:linear-gradient(90deg,#3be2b3 0%,#7c86ff 65%,#c886f4 100%);}
.nba-brandcopy {position:relative;z-index:1;}
.nba-heading {font-size:clamp(2.35rem,4.6vw,3.55rem) !important;line-height:1.02 !important;margin:13px 0 11px !important;}
.nba-heading span {color:#6ce9cb !important;}
.nba-desc {font-size:.91rem !important;max-width:440px;}
.nba-build {background:#2a2550;border-color:#6564c2;color:#c8c6ff;letter-spacing:.055em;}
.nba-court {
  width:288px;height:176px;position:relative;overflow:hidden;
  border:1px solid rgba(118,165,221,.38);
  background:linear-gradient(135deg,rgba(36,69,103,.72),rgba(13,33,63,.18));
  border-radius:13px;box-shadow:inset 0 0 35px rgba(0,0,0,.18);
  transform:rotate(-5deg);
}
.nba-court:after{content:"";position:absolute;inset:15px 15px;
 border:1.5px solid rgba(157,208,224,.40);border-radius:2px;}
.nba-half-line{position:absolute;top:15px;bottom:15px;left:50%;width:1.5px;background:rgba(157,208,224,.33);}
.nba-center-circle{position:absolute;width:62px;height:62px;border-radius:50%;border:1.5px solid rgba(157,208,224,.35);left:50%;top:50%;transform:translate(-50%,-50%);}
.nba-paint-left,.nba-paint-right{position:absolute;width:64px;height:78px;border:1.5px solid rgba(157,208,224,.33);top:50%;transform:translateY(-50%);}
.nba-paint-left{left:15px;border-left:0}.nba-paint-right{right:15px;border-right:0}
.nba-court-ball {position:absolute;left:54%;top:39%;height:34px;width:34px;display:flex;
 align-items:center;justify-content:center;font-size:27px;transform:rotate(5deg);
 filter:drop-shadow(0 5px 8px rgba(0,0,0,.40));z-index:3;}
.nba-court-pill {position:absolute;right:25px;bottom:18px;color:#b6ffe9;font-size:11px;
 font-weight:800;letter-spacing:.1em;background:#122a34a8;padding:6px 10px;
 border:1px solid #56bdad55;border-radius:10px;z-index:4;transform:rotate(5deg);}
.nba-team-overview{border:1px solid #31415b;border-radius:17px;
 background:linear-gradient(108deg,#142139 0%,#171d31 100%);
 padding:18px 20px;margin:10px 0 20px;display:grid;grid-template-columns:2fr repeat(3,minmax(0,1fr));gap:18px;align-items:center;}
.nba-summary-team{min-width:0}.nba-overline{color:#839fbf;font-size:.66rem;letter-spacing:.13em;font-weight:800;display:block;margin-bottom:6px;}
.nba-summary-title{font-size:1.18rem;font-weight:800;color:#f4f9ff;overflow-wrap:anywhere;}
.nba-summary-info{color:#8fdcc8;font-size:.77rem;margin-top:6px;}
.nba-summary-stat{border-left:1px solid #39485e;padding-left:17px;}
.nba-summary-stat strong{display:block;color:#fafbff;font-size:1.36rem;line-height:1.28;white-space:nowrap;}
.nba-summary-stat em{display:block;font-style:normal;font-size:.70rem;color:#9caec5;margin-top:4px;}
.nba-summary-track{height:5px;background:#26344c;border-radius:999px;margin-top:9px;overflow:hidden;}
.nba-summary-fill{display:block;height:100%;background:linear-gradient(90deg,#21bdab,#69e7cd);border-radius:999px;}
.nba-empty-state{background:linear-gradient(118deg,#121e32,#132b32);
 border:1px dashed #3b7776;border-radius:16px;padding:28px 22px;text-align:center;}
.nba-empty-state .symbol{font-size:2.0rem;line-height:1.3;margin-bottom:7px;}
.nba-empty-state h3{margin:6px 0 4px;font-size:1.2rem;}
.nba-empty-state p{color:#a6c1ca;margin:0;font-size:.84rem;}
.nba-player-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:13px 0 12px;}
.nba-player-item{display:flex;align-items:center;gap:12px;background:#111e2f;
 border:1px solid #2b4056;border-radius:12px;padding:12px 13px;min-width:0;}
.nba-player-index{height:34px;min-width:34px;display:flex;align-items:center;justify-content:center;
 border-radius:10px;background:#1a3540;color:#6ff1d0;font-weight:800;font-size:.73rem;}
.nba-player-text{min-width:0;flex:1}
.nba-player-name{color:#eef6ff;font-weight:750;font-size:.86rem;line-height:1.25;overflow-wrap:anywhere;}
.nba-player-sub{color:#839bb9;font-size:.67rem;margin-top:3px;}
.nba-player-flag{color:#ffcf93;border:1px solid #665239;background:#392e20;
 border-radius:8px;padding:4px 8px;font-size:.66rem;font-weight:800;}
.nba-section-header{display:flex;align-items:center;justify-content:space-between;gap:14px;
 padding-bottom:12px;border-bottom:1px solid #273751;margin:20px 0 15px;}
.nba-section-header h2{font-weight:820;color:#f8fbff;font-size:1.4rem;margin:0;}
.nba-section-header p{font-size:.79rem;color:#94abc7;margin:6px 0 0;}
.nba-ranking-podium{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:10px 0 20px;}
.nba-podium-item{background:linear-gradient(155deg,#17243e,#101d31);border:1px solid #32435d;
 padding:15px;border-radius:13px;min-width:0;}
.nba-podium-index{font-size:.73rem;font-weight:900;letter-spacing:.1em;color:#84e6cf;}
.nba-podium-name{font-weight:780;color:#f3f8ff;font-size:1.0rem;margin:8px 0 6px;overflow-wrap:anywhere;}
.nba-podium-meta{font-size:.72rem;color:#91a7c0;}
.nba-podium-score{font-size:1.44rem;font-weight:820;color:#fff;margin-top:12px;letter-spacing:-.03em;}
.nba-podium-score small{font-size:.63rem;font-weight:580;color:#7fcdb7;margin-left:5px;}
.nba-podium-item:first-child{border-color:#32bfab;background:linear-gradient(155deg,#1c3442,#113039);}
.nba-podium-item:nth-child(2){border-color:#6661a9;}
.nba-podium-item:nth-child(3){border-color:#415b82;}
[data-testid="stSegmentedControl"]>div{background:#121d32 !important;border:1px solid #3a4565 !important;
 box-shadow:0 8px 24px rgba(0,0,0,.13);}
[data-testid="stSegmentedControl"] button[aria-checked="true"],
[data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:#31596a !important;color:white !important;}
@media(max-width:780px) {
 .nba-hero{grid-template-columns:1fr;min-height:0;padding:20px 19px;}
 .nba-court{display:none;}
 .nba-heading{font-size:2rem !important;}
 .nba-team-overview{grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:13px 14px;}
 .nba-summary-team{grid-column:1/-1;padding-bottom:9px;border-bottom:1px solid #2c3c56;}
 .nba-summary-stat{padding-left:0;border:0;}
 .nba-summary-stat strong{font-size:1.14rem;}
 .nba-player-grid{grid-template-columns:1fr;}
 .nba-ranking-podium{gap:6px;}
 .nba-podium-item{padding:10px 9px;}
 .nba-podium-name{font-size:.80rem;min-height:2.4em;}
 .nba-podium-score{font-size:1.13rem;}
}
@media(max-width:400px) {
 .nba-heading{font-size:1.76rem !important;}
 .nba-summary-stat strong{font-size:1.0rem;}
 .nba-summary-stat em{font-size:.62rem;}
 .nba-podium-score small{display:block;margin:0;}
}


/* Premium navigation: four independently clickable Streamlit buttons.
   Unlike segmented_control, selection is a filled pill, never an outline. */
.st-key-premium_nav {max-width:640px;margin:10px 0 23px;}
.st-key-premium_nav .nba-nav-label {
 font-size:.67rem;font-weight:820;letter-spacing:.15em;color:#829ab6;
 margin-bottom:8px;
}
.st-key-premium_nav [data-testid="stHorizontalBlock"] {
 display:flex !important;flex-wrap:nowrap !important;
 gap:4px !important;
 padding:6px !important;
 border:1px solid rgba(128,158,207,.22);
 border-radius:20px;
 background:linear-gradient(135deg,#121d30 0%,#172237 100%);
 box-shadow:0 8px 24px rgba(0,0,0,.14),inset 0 1px rgba(255,255,255,.03);
}
.st-key-premium_nav [data-testid="stColumn"] {min-width:0 !important;}
.st-key-premium_nav .stButton {width:100%;}
.st-key-premium_nav .stButton > button {
 width:100% !important;
 min-height:45px !important;
 border:0 !important;
 border-radius:14px !important;
 font-size:.88rem !important;
 font-weight:720 !important;
 white-space:nowrap !important;
 box-shadow:none !important;
 transition:background .18s ease,color .18s ease,transform .18s ease;
}
.st-key-premium_nav .stButton > button[kind="secondary"] {
 background:transparent !important;
 color:#a4b6ce !important;
}
.st-key-premium_nav .stButton > button[kind="secondary"]:hover {
 background:#24334a !important;color:#f4f8ff !important;
}
.st-key-premium_nav .stButton > button[kind="primary"] {
 background:linear-gradient(115deg,#46e6bf 0%,#21c5a7 100%) !important;
 color:#092032 !important;
 box-shadow:0 4px 13px rgba(25,195,149,.18),inset 0 1px 0 rgba(255,255,255,.30) !important;
}
.st-key-premium_nav .stButton > button[kind="primary"]:hover {
 background:linear-gradient(115deg,#75eed0,#3adabc) !important;
}
.st-key-premium_nav .stButton > button:focus-visible {
 outline:2px solid #b8fbe2 !important;outline-offset:2px !important;
}
@media(max-width:700px) {
 .st-key-premium_nav{max-width:100%;margin:7px 0 17px;}
 .st-key-premium_nav [data-testid="stHorizontalBlock"]{gap:2px !important;padding:4px !important;border-radius:16px;}
 .st-key-premium_nav .stButton > button{
   min-height:40px !important;font-size:.78rem !important;
   font-weight:730 !important;padding:6px 3px !important;border-radius:12px !important;
 }
 .st-key-premium_nav .nba-nav-label{font-size:.61rem;margin-bottom:7px;}
}
@media(max-width:360px) {
 .st-key-premium_nav .stButton > button{font-size:.69rem !important;letter-spacing:-.025em;}
}
</style>
"""


def apply_style():
    st.markdown(STYLE, unsafe_allow_html=True)


def hero():
    st.markdown(
        """
<section class="nba-hero">
  <div class="nba-brandcopy">
    <div class="nba-brandline">
      <span class="nba-brandmark">🏀</span>
      <span class="nba-kicker">YAHOO FANTASY · 2026–27</span>
      <span class="nba-build">UI V3 · YENİ TASARIM</span>
    </div>
    <div class="nba-heading">OYUNUNU <span>VERİYLE</span><br>KAZAN.</div>
    <p class="nba-desc">Beş kadronu tek yerde yönet. Sezon projeksiyonlarını incele,
    doğru oyuncuyu doğru zamanda keşfet.</p>
  </div>
  <div class="nba-court" aria-hidden="true">
    <span class="nba-half-line"></span><span class="nba-center-circle"></span>
    <span class="nba-paint-left"></span><span class="nba-paint-right"></span>
    <span class="nba-court-ball">🏀</span>
    <span class="nba-court-pill">2026 / 27</span>
  </div>
</section>
""", unsafe_allow_html=True)


def section_header(title: str, subtitle: str):
    from html import escape
    st.markdown(
        '<div class="nba-section-header"><div><h2>' + escape(title)
        + '</h2><p>' + escape(subtitle) + '</p></div></div>',
        unsafe_allow_html=True,
    )


def team_overview(name: str, fmt: str, league_id: str, roster_count: int, il_count: int,
                  data_label: str):
    from html import escape
    fmt_label = "H2H · 9-CAT" if fmt == "CAT" else "H2H · POINTS"
    fill = max(0, min(100, roster_count / 15 * 100))
    html = (
        '<section class="nba-team-overview">'
        '<div class="nba-summary-team"><span class="nba-overline">AKTİF FANTASY TAKIMIN</span>'
        '<div class="nba-summary-title">' + escape(name) + '</div>'
        '<div class="nba-summary-info">' + fmt_label + ' · Lig ' + escape(str(league_id)) + '</div></div>'
        '<div class="nba-summary-stat"><strong>' + str(roster_count) + '/15</strong>'
        '<em>Oyuncu</em><div class="nba-summary-track"><span class="nba-summary-fill" style="width:'
        + f'{fill:.1f}%' + '"></span></div></div>'
        '<div class="nba-summary-stat"><strong>' + str(il_count) + '/2</strong><em>IL</em></div>'
        '<div class="nba-summary-stat"><strong>' + escape(data_label)
        + '</strong><em>Veri durumu</em></div>'
        '</section>'
    )
    st.markdown(html, unsafe_allow_html=True)


def roster_cards(roster: list[str], inactive: list[str], catalog: dict[str, str]):
    from html import escape
    if not roster:
        st.markdown(
            '<div class="nba-empty-state"><div class="symbol">🏀</div>'
            '<h3>Henüz kadro oluşturmadın</h3>'
            '<p>Yukarıdan oyuncu seçerek ilk takımını oluştur.</p></div>',
            unsafe_allow_html=True,
        )
        return
    from roster_catalog import display_name
    items = []
    for i, pid in enumerate(roster, start=1):
        safe_name = escape(display_name(pid, catalog))
        is_il = pid in set(inactive)
        items.append(
            '<div class="nba-player-item"><div class="nba-player-index">'
            + f'{i:02}' + '</div><div class="nba-player-text">'
            + '<div class="nba-player-name">' + safe_name + '</div>'
            + '<div class="nba-player-sub">' + ("Sakat listesi" if is_il else "Fantasy kadrom")
            + '</div></div>' + ('<span class="nba-player-flag">IL</span>' if is_il else '') + '</div>'
        )
    st.markdown('<div class="nba-player-grid">' + ''.join(items) + '</div>', unsafe_allow_html=True)


def ranking_podium(records: list[tuple[int, str, str, float]], score_label: str):
    from html import escape
    if not records:
        return
    cards = []
    for rank, name, club, score in records[:3]:
        cards.append(
            '<div class="nba-podium-item"><div class="nba-podium-index">#'
            + str(rank) + ' · TOP 3</div><div class="nba-podium-name">'
            + escape(str(name)) + '</div><div class="nba-podium-meta">'
            + escape(str(club)) + '</div><div class="nba-podium-score">'
            + f'{float(score):.1f}' + '<small>' + escape(score_label) + '</small></div></div>'
        )
    st.markdown('<div class="nba-ranking-podium">' + ''.join(cards) + '</div>', unsafe_allow_html=True)


def section_kicker(label: str):
    # Only use developer-authored fixed labels here, no user-provided HTML.
    st.markdown(f'<div class="nba-section">{label}</div>', unsafe_allow_html=True)


def footer():
    st.markdown(
        '<div class="nba-divider"></div><div class="nba-footer">'
        'Bağımsız fantasy analiz aracı · Yahoo veya NBA tarafından geliştirilen resmi bir ürün değildir.'
        ' · Veriler öncelikle 2026–27 projeksiyonlarına dayanır.'
        '</div>', unsafe_allow_html=True)
