# pages/0_대시보드.py — 대시보드 (홈 화면)

import streamlit as st
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import EVENTS_DIR, ROI_DIR, DATA_DIR

st.markdown("""
<style>
.sv-hero {
    position: relative; overflow: hidden;
    padding: 2.4rem 2.6rem; margin-bottom: 1.5rem;
    border-radius: 20px; color: #F8FAFC;
    background: linear-gradient(125deg, #0B1220 0%, #0F172A 62%, #164E63 100%);
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
}
.sv-hero::after {
    content: ""; position: absolute; width: 280px; height: 280px;
    right: -70px; top: -120px; border-radius: 50%;
    background: rgba(56, 189, 248, 0.12);
}
.sv-eyebrow { color: #38BDF8; font-size: .82rem; font-weight: 800; letter-spacing: .16em; }
.sv-hero h1 { color: #FFFFFF; font-size: 2.65rem; margin: .35rem 0 .55rem; }
.sv-hero h2 { color: #F8FAFC; font-size: 1.05rem; margin: 1.15rem 0 .45rem; }
.sv-hero p { color: #CBD5E1; font-size: 1rem; margin: 0; max-width: 920px; line-height: 1.75; }
.sv-section-title { margin: .3rem 0 1rem; color: #0F172A; font-size: 1.35rem; font-weight: 800; }
.sv-stat {
    min-height: 138px; padding: 1.25rem 1.35rem; border-radius: 16px;
    background: #FFFFFF; border: 1px solid #E2E8F0;
    box-shadow: 0 6px 20px rgba(15, 23, 42, .06);
}
.sv-stat-icon { color: #0284C7; font-size: 1.45rem; }
.sv-stat-label { color: #64748B; font-size: .88rem; font-weight: 600; margin-top: .65rem; }
.sv-stat-value { color: #0F172A; font-size: 1.8rem; font-weight: 900; margin-top: .1rem; }
.sv-step {
    min-height: 170px; padding: 1.35rem; border-radius: 16px;
    background: #FFFFFF; border: 1px solid #E2E8F0;
}
.sv-step-no {
    display: inline-flex; width: 32px; height: 32px; align-items: center; justify-content: center;
    border-radius: 10px; background: #E0F2FE; color: #0369A1; font-weight: 900;
}
.sv-step p { color: #64748B; font-size: .95rem; line-height: 1.65; margin: .8rem 0 0; }
.sv-step p strong { color: #0F172A; }
.sv-rule {
    margin-top: 1.5rem; padding: 1.15rem 1.3rem; border-radius: 14px;
    background: #FFFFFF; border-left: 4px solid #EF4444; color: #475569;
}
.sv-rule table { width: 100%; margin-top: .8rem; border-collapse: collapse; }
.sv-rule th, .sv-rule td { padding: .65rem .75rem; border-bottom: 1px solid #E2E8F0; text-align: left; }
.sv-rule th { color: #0F172A; background: #F8FAFC; }
.sv-rule tr:last-child td { border-bottom: 0; }
.sv-tech {
    height: 100%; padding: 1.15rem 1.3rem; border-radius: 14px;
    background: #FFFFFF; border: 1px solid #E2E8F0; color: #475569;
}
.sv-tech ul { margin: .65rem 0 0; padding-left: 1.3rem; line-height: 1.85; }
.sv-preflight {
    height: 100%; padding: 1.15rem 1.3rem; border-radius: 14px;
    background: #F0F9FF; border: 1px solid #BAE6FD; color: #334155; line-height: 1.7;
}
</style>

<section class="sv-hero">
    <div class="sv-eyebrow">SAFEVIEW · AI SAFETY MONITORING</div>
    <h1>세이프뷰</h1>
    <h2>프로젝트 개요</h2>
    <p>생활도로·골목·주차장·도로변 주차 구간에서 <strong>주차 차량 및 구조물</strong>로 인해 시야가 제한되는 환경에서 CCTV 또는 저장 영상으로 <strong>사람과 차량을 실시간 인식</strong>하고, 사용자가 지정한 <strong>ROI(관심구역) 내 위험 상황</strong>을 감지하여 화면 및 청각 경고와 이벤트 클립 영상을 저장하는 프로토타입입니다.</p>
</section>
""", unsafe_allow_html=True)

roi_count = len([f for f in os.listdir(ROI_DIR) if f.endswith(".json")]) if os.path.exists(ROI_DIR) else 0
event_count = len([f for f in os.listdir(EVENTS_DIR) if f.endswith(".jpg")]) if os.path.exists(EVENTS_DIR) else 0
data_count = len([f for f in os.listdir(DATA_DIR) if f.endswith((".mp4", ".avi", ".mov"))]) if os.path.exists(DATA_DIR) else 0

st.markdown('<div class="sv-section-title">시스템 현황</div>', unsafe_allow_html=True)
stat_cols = st.columns(3)
stats = [
    ("🗺️", "저장된 ROI", roi_count),
    ("🚨", "저장된 이벤트", event_count),
    ("🎬", "사용 가능한 영상", data_count),
]
for col, (icon, label, value) in zip(stat_cols, stats):
    col.markdown(
        f'<div class="sv-stat"><div class="sv-stat-icon">{icon}</div>'
        f'<div class="sv-stat-label">{label}</div>'
        f'<div class="sv-stat-value">{value}개</div></div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="sv-section-title" style="margin-top:1.8rem;">사용 방법</div>', unsafe_allow_html=True)
step_cols = st.columns(3)
steps = [
    ("1.", "<strong>👈 왼쪽 사이드바</strong>에서 페이지를 선택하세요."),
    ("2.", "<strong>🗺️ ROI 설정</strong> 페이지에서 관심구역을 먼저 설정하세요."),
    ("3.", "<strong>🎥 모니터링</strong> 페이지에서 영상을 선택하고 감지를 시작하세요."),
]
for col, (number, description) in zip(step_cols, steps):
    col.markdown(
        f'<div class="sv-step"><span class="sv-step-no">{number}</span>'
        f'<p>{description}</p></div>',
        unsafe_allow_html=True,
    )

st.markdown("""
<div class="sv-rule">
    <strong style="color:#0F172A;">위험 판단 규칙</strong>
    <table>
        <thead><tr><th>조건</th><th>상태</th></tr></thead>
        <tbody>
            <tr><td>아무것도 없음</td><td>🟢 정상</td></tr>
            <tr><td>사람만 있음</td><td>🟢 정상</td></tr>
            <tr><td>자동차만 있음</td><td>🟢 정상</td></tr>
            <tr><td>사람 + 자동차, 사람이 ROI 밖에 위치</td><td>🟢 정상</td></tr>
            <tr><td><strong>사람 + 자동차, 사람이 ROI 안에 위치</strong></td><td>🔴 <strong>위험</strong></td></tr>
        </tbody>
    </table>
</div>
""", unsafe_allow_html=True)

info_cols = st.columns(2)
info_cols[0].markdown("""
<div class="sv-tech">
    <strong style="color:#0F172A;">기술 스택</strong>
    <ul>
        <li>🐍 Python + Streamlit</li>
        <li>👁️ YOLOv8 (Ultralytics)</li>
        <li>📹 OpenCV</li>
    </ul>
</div>
""", unsafe_allow_html=True)
info_cols[1].markdown("""
<div class="sv-preflight">
    <strong style="color:#0F172A;">💡 시작 전 확인</strong><br>
    테스트용 영상 파일(.mp4)은 미리 <code>data/</code> 폴더에 넣어주세요. YOLOv8 모델은 처음 실행할 때 자동으로 다운로드됩니다.
</div>
""", unsafe_allow_html=True)
