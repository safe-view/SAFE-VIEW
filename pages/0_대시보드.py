# pages/0_대시보드.py — 대시보드 (홈 화면)

import streamlit as st
import os, sys, base64

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import EVENTS_DIR, ROI_DIR, DATA_DIR

HERO_IMG_PATH = os.path.join(ROOT, "hero_banner.png")
HERO_IMG_B64 = ""
if os.path.exists(HERO_IMG_PATH):
    with open(HERO_IMG_PATH, "rb") as f:
        HERO_IMG_B64 = base64.b64encode(f.read()).decode()

st.markdown("""
<style>
.sv-hero {
    position: relative; overflow: hidden; line-height: 0;
    margin-bottom: 1.5rem; border-radius: 20px;
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
}
.sv-hero img { width: 100%; height: auto; display: block; }
.sv-section-title { margin: .3rem 0 1rem; color: #0F172A; font-size: 1.35rem; font-weight: 800; }
.sv-stat {
    min-height: 90px; padding: 1.1rem 1.35rem; border-radius: 16px;
    background: #FFFFFF; border: 1px solid #E2E8F0;
    box-shadow: 0 6px 20px rgba(15, 23, 42, .06);
    margin-bottom: 1rem;
}
.sv-stat-label { color: #64748B; font-size: .88rem; font-weight: 600; }
.sv-stat-value { color: #0F172A; font-size: 1.8rem; font-weight: 900; margin-top: .1rem; }
.sv-step {
    min-height: 100px; padding: 1.1rem 1.35rem; border-radius: 16px;
    background: #FFFFFF; border: 1px solid #E2E8F0;
    display: flex; align-items: center; gap: .75rem;
}
.sv-step-no {
    display: inline-flex; width: 32px; height: 32px; align-items: center; justify-content: center;
    border-radius: 10px; background: #E0F2FE; color: #0369A1; font-weight: 900;
    flex-shrink: 0;
}
.sv-step p { color: #64748B; font-size: .95rem; line-height: 1.65; margin: 0; }
.sv-step p strong { color: #0F172A; }
.sv-rule-table { width: 100%; border-collapse: collapse; }
.sv-rule-table th, .sv-rule-table td { padding: .65rem .75rem; border-bottom: 1px solid #E2E8F0; text-align: left; }
.sv-rule-table th { color: #0F172A; background: #F8FAFC; }
.sv-rule-table tr:last-child td { border-bottom: 0; }
.sv-tech {
    height: 100%; padding: 1.15rem 1.3rem; border-radius: 14px;
    background: #FFFFFF; border: 1px solid #E2E8F0; color: #475569;
}
.sv-tech ul { margin: .65rem 0 0; padding-left: 1.3rem; line-height: 1.85; }
.sv-rule-expander-marker { display: none; }
[data-testid="stElementContainer"]:has(.sv-rule-expander-marker) { display: none; }
[data-testid="stExpander"]:has(.sv-rule-expander-marker) {
    width: fit-content !important;
    max-width: 100%;
    margin-bottom: 0.5rem;
}
[data-testid="stExpander"]:has(.sv-rule-expander-marker) summary {
    width: fit-content !important;
    min-width: 0 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<section class="sv-hero">
    <img src="data:image/png;base64,{HERO_IMG_B64}" alt="SAFEVIEW — 도로변 사각지대 보행자 위험 감지 및 시청각 경고 시스템">
</section>
""", unsafe_allow_html=True)

roi_count = len([f for f in os.listdir(ROI_DIR) if f.endswith(".json")]) if os.path.exists(ROI_DIR) else 0
event_count = len([f for f in os.listdir(EVENTS_DIR) if f.endswith(".jpg")]) if os.path.exists(EVENTS_DIR) else 0
data_count = len([f for f in os.listdir(DATA_DIR) if f.endswith((".mp4", ".avi", ".mov"))]) if os.path.exists(DATA_DIR) else 0

with st.expander("⚠️ 위험 판단 규칙", expanded=False):
    st.markdown('<span class="sv-rule-expander-marker"></span>', unsafe_allow_html=True)
    st.markdown("""
    <table class="sv-rule-table">
        <thead><tr><th>조건</th><th>상태</th></tr></thead>
        <tbody>
            <tr><td>아무것도 없음</td><td>🟢 정상</td></tr>
            <tr><td>사람만 있음</td><td>🟢 정상</td></tr>
            <tr><td>자동차만 있음</td><td>🟢 정상</td></tr>
            <tr><td>사람 + 자동차, 사람이 ROI 밖에 위치</td><td>🟢 정상</td></tr>
            <tr><td><strong>사람 + 자동차, 사람이 ROI 안에 위치</strong></td><td>🔴 <strong>위험</strong></td></tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

st.markdown('<div class="sv-section-title" style="margin-top:0.5rem;">사용 방법</div>', unsafe_allow_html=True)
step_cols = st.columns(3)
steps = [
    ("1.", "<strong>👈 왼쪽 사이드바</strong>에서 페이지를 선택하세요."),
    ("2.", "<strong>🗺️ ROI 설정</strong> 페이지에서 관심구역을<br>먼저 설정하세요."),
    ("3.", "<strong>🎥 모니터링</strong> 페이지에서 영상을 선택하고<br>감지를 시작하세요."),
]
for col, (number, description) in zip(step_cols, steps):
    col.markdown(
        f'<div class="sv-step"><span class="sv-step-no">{number}</span>'
        f'<p>{description}</p></div>',
        unsafe_allow_html=True,
    )

status_col, tech_col = st.columns(2)

with status_col:
    st.markdown('<div class="sv-section-title" style="margin-top:1.8rem;">시스템 현황</div>', unsafe_allow_html=True)
    stats = [
        ("🗺️", "저장된 ROI", roi_count),
        ("🚨", "저장된 이벤트", event_count),
        ("🎬", "사용 가능한 영상", data_count),
    ]
    for icon, label, value in stats:
        st.markdown(
            f'<div class="sv-stat"><div class="sv-stat-label">{icon} {label}</div>'
            f'<div class="sv-stat-value">{value}개</div></div>',
            unsafe_allow_html=True,
        )

with tech_col:
    st.markdown('<div class="sv-section-title" style="margin-top:1.8rem;">기술 스택</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sv-tech">
        <ul>
            <li>🐍 Python + Streamlit</li>
            <li>👁️ YOLOv8 (Ultralytics)</li>
            <li>📹 OpenCV</li>
            <li>⚡ OpenVINO / CUDA (추론 가속)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
