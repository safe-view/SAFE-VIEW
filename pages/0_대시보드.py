# pages/0_대시보드.py — 대시보드 (홈 화면)

import streamlit as st
import os, sys, base64, json, re
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import EVENTS_DIR, ROI_DIR, DATA_DIR, LOG_FILE

RTSP_PRESET_FILE = os.path.join(ROOT, "rtsp_presets.json")
CHART_GREEN = "#4D9F50"
CHART_DANGER = "#C0392B"
CHART_AMBER = "#D08A2E"
WEEKDAY_BANDS = [("새벽 00~06", 0, 6), ("오전 06~12", 6, 12), ("오후 12~18", 12, 18), ("저녁·밤 18~24", 18, 24)]


def _rtsp_preset_names() -> set:
    """rtsp_presets.json 에 등록된 CCTV 이름 모음. 파일이 없거나 깨지면 빈 집합."""
    try:
        with open(RTSP_PRESET_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return {str(p.get("name", "")).strip() for p in data if isinstance(p, dict)} - {""}
    except Exception:
        return set()


def _is_rtsp(source: str, names: set) -> bool:
    s = str(source).strip()
    return s.lower().startswith("rtsp://") or s in names


def _load_rtsp_hour_counts(days: int) -> "pd.Series":
    """최근 N일 RTSP 실시간 위험 기록을 시간대별로 집계한다. (녹화영상 기록 제외)"""
    empty = pd.Series(0, index=range(24))
    if not os.path.exists(LOG_FILE):
        return empty
    try:
        df = pd.read_csv(LOG_FILE, encoding="utf-8-sig", dtype=str).fillna("")
    except Exception:
        return empty
    if "timestamp" not in df.columns:
        return empty
    if "source" not in df.columns:
        df["source"] = ""
    names = _rtsp_preset_names()
    df = df[df["source"].map(lambda s: _is_rtsp(s, names))].copy()
    df["ts"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["ts"]).copy()
    today = datetime.now().date()
    start = today - timedelta(days=days - 1)
    df = df[(df["ts"].dt.date >= start) & (df["ts"].dt.date <= today)]
    return df["ts"].dt.hour.value_counts().reindex(range(24), fill_value=0)

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
.sv-section-title span { font-weight: 400; font-size: .85rem; color: #94A3B8; margin-left: .6rem; }
.sv-chart-legend { color: #64748B; font-size: .85rem; }
.sv-chart-legend i { display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin: 0 .35rem 0 .9rem; }
.sv-info-card { padding: 1rem 1.4rem 1.2rem; border-radius: 20px; background: #FFFFFF; border: 1px solid #E2E8F0;
    box-shadow: 0 4px 16px rgba(15, 23, 42, .04); height: 100%; }
.sv-info-card-title { font-size: 1.05rem; font-weight: 800; color: #0F172A; padding-bottom: .7rem;
    border-bottom: 1px solid #EEF2F6; margin-bottom: .9rem; }
.sv-info-card-title span { font-weight: 400; font-size: .85rem; color: #94A3B8; margin-left: .6rem; }
.sv-rank { display: flex; align-items: center; gap: .8rem; margin: .7rem 0; }
.sv-rank b { width: 2.6rem; color: #0F172A; }
.sv-rank-bar { flex: 1; height: 12px; border-radius: 6px; background: #F1F2F4; overflow: hidden; }
.sv-rank-bar div { height: 100%; border-radius: 6px; }
.sv-rank em { width: 4.2rem; text-align: right; font-style: normal; color: #475569; font-size: .88rem; }
.sv-info-sub { color: #64748B; font-size: .88rem; }
.sv-empty { color: #94A3B8; text-align: center; padding: 3.2rem 0; font-size: 1rem; }
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

# 탐지정산 페이지와 동일하게, 새 위험이 기록되면 새로고침 없이 반영되도록 일정 간격으로 이 영역만 다시 그린다.
@st.fragment(run_every="10s")
def render_hourly_risk_chart():
    hour_counts = _load_rtsp_hour_counts(days=7)
    total = int(hour_counts.sum())
    top3 = set(hour_counts[hour_counts > 0].sort_values(ascending=False, kind="stable").head(3).index)
    chart_df = pd.DataFrame({"시": range(24), "건수": hour_counts.values})
    chart_df["구분"] = chart_df["시"].map(lambda h: "취약 시간 Top 3" if h in top3 else "발생 건수")
    chart_df["bg"] = max(int(hour_counts.max()), 1)

    st.markdown('<div class="sv-section-title">실시간 시간대별 위험 통계<span>최근 7일</span></div>', unsafe_allow_html=True)
    left, right = st.columns([1.55, 1])
    with left:
        with st.container(border=True):
            base = alt.Chart(chart_df).encode(x=alt.X("시:O", title=None, axis=alt.Axis(
                labelAngle=0, labelOverlap=True, values=list(range(0, 24, 3)))))
            ghost = base.mark_bar(color="#F1F2F4", size=6, cornerRadius=3).encode(
                y=alt.Y("bg:Q", title=None, scale=alt.Scale(domain=[0, max(int(hour_counts.max()), 1)])))
            bars = base.mark_bar(size=10, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                y=alt.Y("건수:Q", title=None, axis=alt.Axis(tickMinStep=1, format="d")),
                color=alt.Color("구분:N", legend=None, scale=alt.Scale(
                    domain=["발생 건수", "취약 시간 Top 3"], range=[CHART_GREEN, CHART_DANGER])),
                tooltip=[alt.Tooltip("시:O", title="시각"), alt.Tooltip("건수:Q", title="발생 건수")])
            chart = (ghost + bars).properties(height=260).configure_view(strokeWidth=0).configure_axis(
                labelColor="#94A3B8", titleColor="#94A3B8", gridColor="#E9EEF3", gridDash=[3, 3], domainColor="#E2E8F0")
            st.altair_chart(chart, width="stretch")
            st.markdown(f'<div class="sv-chart-legend"><i style="background:{CHART_GREEN}"></i>발생 건수'
                        f'<i style="background:{CHART_DANGER}"></i>취약 시간 Top 3</div>', unsafe_allow_html=True)

    with right:
        if total:
            ranks = hour_counts[hour_counts > 0].sort_values(ascending=False, kind="stable").head(3)
            mx = int(ranks.max())
            body = "".join(
                f'<div class="sv-rank"><b>{h:02d}시</b><div class="sv-rank-bar"><div style="width:{c / mx * 100:.0f}%;'
                f'background:{CHART_DANGER}"></div></div><em>{c}건 ({c / total * 100:.0f}%)</em></div>'
                for h, c in ranks.items())
            bc = [(n, int(hour_counts.loc[lo:hi - 1].sum())) for n, lo, hi in WEEKDAY_BANDS]
            pk = max(bc, key=lambda x: x[1])
            body += '<div style="height:.6rem"></div>' + "".join(
                f'<div class="sv-rank"><b style="width:7.5rem;font-weight:500">{n}시</b><div class="sv-rank-bar">'
                f'<div style="width:{c / total * 100:.0f}%;background:{CHART_GREEN if n != pk[0] else CHART_AMBER}">'
                f'</div></div><em>{c}건</em></div>' for n, c in bc)
            body += (f'<div class="sv-info-sub" style="margin-top:.6rem">가장 위험한 시간 구간은 '
                     f'<b style="color:#0F172A">{pk[0]}시</b> ({pk[1] / total * 100:.0f}%)입니다.</div>')
        else:
            body = '<div class="sv-empty">해당 기간에 관측된 위험이 없습니다</div>'
        st.markdown(
            f'<div class="sv-info-card"><div class="sv-info-card-title">취약 시간 분석<span>최근 7일</span></div>{body}</div>',
            unsafe_allow_html=True)


render_hourly_risk_chart()

st.markdown('<div class="sv-section-title" style="margin-top:1.8rem;">사용 방법</div>', unsafe_allow_html=True)
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
