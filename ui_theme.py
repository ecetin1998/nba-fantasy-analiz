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
</style>
"""


def apply_style():
    st.markdown(STYLE, unsafe_allow_html=True)


def hero():
    st.markdown(
        """
<section class="nba-hero">
  <div class="nba-brandline">
    <span class="nba-brandmark">🏀</span>
    <span class="nba-kicker">2026–27 · FANTASY BASKETBOL</span>
    <span class="nba-build">● UI V2.1 · 19 EKİM</span>
  </div>
  <div class="nba-heading">NBA FANTASY <span>SCOUT</span></div>
  <p class="nba-desc">Takımlarını yönet, oyuncuları karşılaştır, projeksiyonlarla avantaj yakala.</p>
</section>
""", unsafe_allow_html=True)


def section_kicker(label: str):
    # Only use developer-authored fixed labels here, no user-provided HTML.
    st.markdown(f'<div class="nba-section">{label}</div>', unsafe_allow_html=True)


def footer():
    st.markdown(
        '<div class="nba-divider"></div><div class="nba-footer">'
        'Bağımsız fantasy analiz aracı · Yahoo veya NBA tarafından geliştirilen resmi bir ürün değildir.'
        ' · Veriler öncelikle 2026–27 projeksiyonlarına dayanır.'
        '</div>', unsafe_allow_html=True)
