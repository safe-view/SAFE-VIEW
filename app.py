# app.py — Streamlit 앱 진입점
# `streamlit run app.py` 로 실행합니다.

import streamlit as st
import os, sys, base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import EVENTS_DIR, LOGS_DIR, ROI_DIR, DATA_DIR

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="세이프뷰",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 필요한 폴더 자동 생성
for d in [EVENTS_DIR, LOGS_DIR, ROI_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

# ── 로고 이미지 base64 로드 ──────────────────────────────
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
LOGO_B64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode()

# ── 사이드바 로고 (CSS 가상 요소) + Streamlit 헤더 숨기기 ──
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800;900&display=swap');

:root {{
    --sv-navy: #0F172A;
    --sv-sidebar: #0B1220;
    --sv-slate: #64748B;
    --sv-muted: #94A3B8;
    --sv-blue: #38BDF8;
    --sv-danger: #DC2626;
    --sv-safe: #10B981;
    --sv-bg: #F1F5F9;
    --sv-surface: #FFFFFF;
    --sv-border: #E2E8F0;
}}

html, body {{
    font-family: 'Noto Sans KR', sans-serif;
}}
[data-testid="stAppViewContainer"] {{
    background: var(--sv-bg);
}}
header[data-testid="stHeader"] {{
    display: none !important;
}}
.block-container {{
    padding-top: 0.75rem !important;
    padding-bottom: 2rem !important;
    max-width: 1600px;
}}
/* 소스 설정 카드가 있는 페이지는 카드 내부 여백과 어울리는 좌측 여유를 둔다. */
.block-container:has(.sv-source-panel-marker) {{
    padding-left: 20px !important;
}}
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

/* Streamlit 내부 data-testid 기반 선택자: 버전 업그레이드 시 우선 점검. */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarNav"] {{
    background: var(--sv-sidebar) !important;
}}
[data-testid="stSidebar"] {{
    border-right: 1px solid #1E293B;
}}
[data-testid="stSidebarNavLink"] {{
    color: #E2E8F0 !important;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 0.55rem 0.75rem;
    transition: background-color 0.15s ease, color 0.15s ease;
}}
[data-testid="stSidebarNavLinkContainer"] {{
    margin: 3px 10px;
}}
[data-testid="stSidebarNavLink"] > * {{
    color: inherit !important;
}}
/* 줄바꿈이 없어야 하는 라벨형 위젯을 새로 추가하면 이 선택자 목록에도 추가할 것. */
[data-testid="stSidebarNavLink"],
[data-testid="stSidebarNavLink"] *,
[data-testid="stButton"] button,
[data-testid="stButton"] button *,
[data-testid="stFormSubmitButton"] button,
[data-testid="stFormSubmitButton"] button *,
[data-testid="stRadio"] div[role="radiogroup"] > label,
[data-testid="stRadio"] div[role="radiogroup"] > label *,
[data-testid="stSidebarNav"]::before {{
    white-space: nowrap !important;
}}
[data-testid="stSidebarNavLink"]:hover {{
    color: #FFFFFF !important;
    background: #1E293B !important;
}}
[data-testid="stSidebarNavLink"][aria-current="page"] {{
    color: #FFFFFF !important;
    background: rgba(56, 189, 248, 0.16) !important;
    border-color: rgba(56, 189, 248, 0.72);
    box-shadow: inset 3px 0 0 var(--sv-blue);
    font-weight: 700;
}}
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {{
    color: #CBD5E1 !important;
}}
/* Streamlit 1.55의 헤더가 로고와 내비게이션 사이에서 높이와 하단 여백을 차지하므로,
   접기 버튼은 유지한 채 문서 흐름에서만 분리한다. */
[data-testid="stSidebarHeader"] {{
    position: absolute !important;
    top: 12px;
    right: 0;
    height: auto !important;
    margin-bottom: 0 !important;
    z-index: 1;
}}
[data-testid="stLogoSpacer"] {{
    display: none !important;
}}

/* 사이드바 상단 로고 */
[data-testid="stSidebar"] > div:first-child::before {{
    content: "";
    display: block;
    width: 70px; height: 70px;
    margin: 18px auto 8px auto;
    background-image: url("data:image/png;base64,{LOGO_B64}");
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
}}
[data-testid="stSidebarNav"]::before {{
    content: "SAFEVIEW  ·  세이프뷰";
    display: block;
    text-align: center;
    font-size: 1.1rem;
    font-weight: 800;
    color: #F8FAFC;
    padding-bottom: 14px;
    margin-bottom: 8px;
    border-bottom: 1px solid #1E293B;
}}

h1, h2, h3 {{ color: var(--sv-navy); letter-spacing: -0.025em; }}
[data-testid="stMetric"] {{
    background: var(--sv-surface);
    border: 1px solid var(--sv-border);
    border-radius: 14px;
    padding: 1rem 1.1rem;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05);
}}
[data-testid="stExpander"], [data-testid="stForm"] {{
    background: var(--sv-surface);
    border: 1px solid var(--sv-border) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    overflow: hidden;
}}

/* Streamlit 1.55 위젯 DOM 선택자: 업그레이드 시 data-testid/BaseWeb 구조 점검. */
[data-testid="stColumn"]:has(.sv-source-panel-marker) {{
    background: var(--sv-surface);
    border: 1px solid var(--sv-border);
    border-radius: 16px;
    padding: 1rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.07);
}}
.sv-source-panel-marker {{ display: none; }}
[data-testid="stElementContainer"]:has(.sv-source-panel-marker) {{ display: none; }}

[data-testid="stRadio"] div[role="radiogroup"] {{
    width: 100%;
    gap: 4px;
    padding: 4px;
    background: var(--sv-border);
    border-radius: 12px;
}}
[data-testid="stRadio"] div[role="radiogroup"] > label {{
    flex: 1;
    justify-content: center;
    min-height: 38px;
    margin: 0;
    padding: 0.4rem 0.65rem;
    color: var(--sv-slate);
    border-radius: 9px;
    transition: background-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}}
[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {{
    color: var(--sv-navy);
    background: var(--sv-surface);
    box-shadow: 0 2px 7px rgba(15, 23, 42, 0.12);
}}
[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {{
    display: none;
}}

[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {{
    background: var(--sv-surface) !important;
    border-color: #CBD5E1 !important;
    border-radius: 10px !important;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-testid="stTextInput"] > div > div:focus-within,
[data-testid="stNumberInput"] > div > div:focus-within,
[data-testid="stTextArea"] > div:focus-within {{
    border-color: var(--sv-blue) !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.18) !important;
}}

[data-testid="stFileUploaderDropzone"] {{
    background: #F8FAFC !important;
    border: 1px solid var(--sv-border) !important;
    border-radius: 12px !important;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
    border-color: var(--sv-blue) !important;
    background: #F0F9FF !important;
}}
[data-testid="stExpander"] details > summary {{
    padding: 0.75rem 1rem;
    color: var(--sv-navy);
    font-weight: 600;
}}

/* ── 버튼 글자 가운데 정렬 + 여백 제거 ────────────── */
[data-testid="stButton"] > button,
[data-testid="stFormSubmitButton"] > button {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 38px !important;
    padding: 6px 10px !important;
    line-height: 1 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease;
}}
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"] {{
    color: #082F49 !important;
    background: var(--sv-blue) !important;
    border-color: var(--sv-blue) !important;
}}
[data-testid="stButton"] > button:not([kind="primary"]),
[data-testid="stFormSubmitButton"] > button:not([kind="primary"]) {{
    color: #F8FAFC !important;
    background: var(--sv-navy) !important;
    border-color: var(--sv-navy) !important;
}}
[data-testid="stButton"] > button:hover:not(:disabled),
[data-testid="stFormSubmitButton"] > button:hover:not(:disabled) {{
    transform: translateY(-1px);
    box-shadow: 0 5px 12px rgba(15, 23, 42, 0.18);
}}
[data-testid="stButton"] > button:disabled,
[data-testid="stFormSubmitButton"] > button:disabled {{
    color: var(--sv-muted) !important;
    background: var(--sv-border) !important;
    border-color: var(--sv-border) !important;
    opacity: 0.75;
}}
</style>
""", unsafe_allow_html=True)

# ── 최상단 배너 ──────────────────────────────────────────
st.markdown(f"""
<div style="background:#FFFFFF; border-bottom:2px solid #E2E8F0; padding:10px 24px;
            display:flex; align-items:center; gap:14px; margin:0 0 1.5rem 0; border-radius:12px;
            box-shadow:0 4px 16px rgba(15,23,42,0.05);">
    <img src="data:image/png;base64,{LOGO_B64}" style="width:38px; height:38px; border-radius:6px;">
    <div>
        <span style="font-size:1.15rem; font-weight:800; color:#0F172A;">SAFE<span style="color:#10B981;">VIEW</span></span>
        <span style="color:#64748B; font-size:0.9rem; margin-left:4px;">도로변 사각지대 보행자 위험 감지 및 시청각 경고 시스템</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 네비게이션 ───────────────────────────────────────────
pg = st.navigation([
    st.Page("pages/0_대시보드.py",          title="홈",             icon="🏠"),
    st.Page("pages/1_모니터링.py",          title="모니터링",        icon="🎥"),
    st.Page("pages/2_ROI_설정.py",          title="ROI 설정",       icon="🗺️"),
    st.Page("pages/3_이벤트_다시보기.py",    title="세이프뷰 다시보기",  icon="📋"),
    st.Page("pages/4_성능_평가.py",          title="성능 평가",         icon="📊"),
])

pg.run()
