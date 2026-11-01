# pages/5_탐지_정산.py — 탐지 정산 페이지
# logs/events_log.csv 에 쌓인 실제 위험 관측 기록을 종합해 보여준다. (읽기 전용)
# RTSP 실시간 모니터링 기록만 집계한다. (로컬 녹화영상 파일에서 나온 기록은 제외)
# 기록이 없어도 축·격자 틀은 그대로 보이도록 빈 상태를 따로 그린다.

import streamlit as st
import os, sys, html, json, re
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import EVENTS_DIR, LOG_FILE

PRESET_FILE = os.path.join(ROOT, "rtsp_presets.json")


def rtsp_preset_names() -> set:
    """rtsp_presets.json 에 등록된 CCTV 이름 모음. 파일이 없거나 깨지면 빈 집합."""
    try:
        with open(PRESET_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return {str(p.get("name", "")).strip() for p in data if isinstance(p, dict)} - {""}
    except Exception:
        return set()


def is_rtsp(source: str, names: set) -> bool:
    """RTSP 실시간 소스인지 판별한다. rtsp:// 주소이거나 등록된 프리셋 이름이면 True."""
    s = str(source).strip()
    return s.lower().startswith("rtsp://") or s in names


def mask(source: str) -> str:
    """소스에 rtsp://아이디:비밀번호@ 가 섞여 있어도 화면에는 계정 정보를 드러내지 않는다."""
    return re.sub(r"(rtsp://)[^@/\s]+@", r"\1***@", str(source), flags=re.I)


WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
GREEN = "#4D9F50"
DANGER = "#C0392B"
MUTED = "#D5DCE3"

st.markdown("""
<style>
.td-top { display:flex; align-items:center; justify-content:space-between; margin:0 0 1rem; }
.td-top h1 { font-size:1.6rem; font-weight:800; color:#0F172A; margin:0; }
.td-badge { padding:.3rem .8rem; border-radius:999px; font-size:.85rem; font-weight:700;
    background:#EEF8EE; color:#3F8A43; border:1px solid #CFE8D0; }
.td-badge.idle { background:#F3F4F6; color:#64748B; border-color:#E2E8F0; }
.td-range { color:#64748B; font-size:.9rem; text-align:right; padding-top:.55rem; }
.td-kpi { padding:1.1rem 1.3rem; border-radius:20px; background:#fff; min-height:150px;
    border:1px solid #E2E8F0; box-shadow:0 4px 16px rgba(15,23,42,.04); }
.td-kpi.red { border-color:#F5D0CC; } .td-kpi.amber { border-color:#F3E3B5; }
.td-kpi.green { border-color:#CFE8D0; }
.td-kpi-label { color:#475569; font-size:.9rem; font-weight:600; }
.td-kpi-label i { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:.5rem; }
.td-kpi-value { color:#0F172A; font-size:2.4rem; font-weight:900; margin:.5rem 0 .3rem; line-height:1.1; }
.td-kpi-value small { font-size:1rem; font-weight:500; color:#94A3B8; margin-left:.3rem; }
.td-kpi-sub { color:#64748B; font-size:.88rem; }
.td-card { padding:1rem 1.4rem 1.2rem; border-radius:20px; background:#fff; border:1px solid #E2E8F0;
    box-shadow:0 4px 16px rgba(15,23,42,.04); }
.td-card-title { font-size:1.05rem; font-weight:800; color:#0F172A; padding-bottom:.7rem;
    border-bottom:1px solid #EEF2F6; margin-bottom:.9rem; }
.td-card-title:before { content:""; display:inline-block; width:5px; height:18px; border-radius:3px;
    background:#4D9F50; margin-right:.6rem; vertical-align:-3px; }
.td-card-title span { font-weight:400; font-size:.85rem; color:#94A3B8; margin-left:.6rem; }
.td-empty { color:#94A3B8; text-align:center; padding:3.2rem 0; font-size:1rem; }
.td-rank { display:flex; align-items:center; gap:.8rem; margin:.7rem 0; }
.td-rank b { width:2.6rem; color:#0F172A; }
.td-bar { flex:1; height:12px; border-radius:6px; background:#F1F2F4; overflow:hidden; }
.td-bar div { height:100%; border-radius:6px; }
.td-rank em { width:4.2rem; text-align:right; font-style:normal; color:#475569; font-size:.88rem; }
.td-legend { color:#64748B; font-size:.85rem; }
.td-legend i { display:inline-block; width:11px; height:11px; border-radius:3px; margin:0 .35rem 0 .9rem; }
.td-case { border-radius:14px; border:1px solid #E2E8F0; background:#fff; padding:.8rem .9rem; margin-top:.5rem;
    font-size:.88rem; color:#475569; }
.td-case strong { color:#0F172A; }
.td-tag { display:inline-block; padding:.1rem .5rem; border-radius:999px; font-size:.78rem;
    background:#EEF8EE; color:#3F8A43; margin-left:.3rem; }
.td-tag.no { background:#F3F4F6; color:#94A3B8; }
</style>
""", unsafe_allow_html=True)


# ── 데이터 로드 ──────────────────────────────────────
def load_events() -> pd.DataFrame:
    """이벤트 로그를 읽어 시간 파생 컬럼을 붙여 반환한다. 없거나 깨지면 빈 DataFrame."""
    cols = ["timestamp", "source", "status", "image_file", "clip_file"]
    empty = pd.DataFrame(columns=cols + ["ts", "date", "hour", "weekday"])
    if not os.path.exists(LOG_FILE):
        return empty
    try:
        df = pd.read_csv(LOG_FILE, encoding="utf-8-sig", dtype=str).fillna("")
    except Exception:
        return empty
    if "timestamp" not in df.columns:
        return empty
    for col in cols:
        if col not in df.columns:
            df[col] = ""
    names = rtsp_preset_names()
    df = df[df["source"].map(lambda s: is_rtsp(s, names))].copy()  # 녹화영상(로컬 파일) 기록 제외
    df["ts"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["ts"]).copy()
    df["date"] = df["ts"].dt.date
    df["hour"] = df["ts"].dt.hour
    df["weekday"] = df["ts"].dt.weekday
    return df.sort_values("ts").reset_index(drop=True)


def card(title: str, sub: str, body: str) -> str:
    sub_html = f"<span>{sub}</span>" if sub else ""
    return f'<div class="td-card"><div class="td-card-title">{title}{sub_html}</div>{body}</div>'


def kpi(color: str, dot: str, label: str, value: str, unit: str, sub: str) -> str:
    unit_html = f"<small>{unit}</small>" if unit else ""
    return (f'<div class="td-kpi {color}"><div class="td-kpi-label"><i style="background:{dot}"></i>{label}</div>'
            f'<div class="td-kpi-value">{value}{unit_html}</div><div class="td-kpi-sub">{sub}</div></div>')


def style(chart):
    return chart.configure_view(strokeWidth=0).configure_axis(
        labelColor="#94A3B8", titleColor="#94A3B8", gridColor="#E9EEF3", gridDash=[3, 3], domainColor="#E2E8F0",
    )


# 모니터링(RTSP)이 새 위험을 기록하면 새로고침 없이 반영되도록 일정 간격으로 이 영역만 다시 그린다.
@st.fragment(run_every="10s")
def render():
    all_events = load_events()
    today = datetime.now().date()

    # ── 상단: 제목 / 기간 / 새로고침 ──────────────────────
    badge = ('<span class="td-badge">● RTSP 실시간 집계 중</span>' if len(all_events)
             else '<span class="td-badge idle">● RTSP 실시간 대기 중</span>')
    st.markdown(f'<div class="td-top"><h1>탐지 정산 · RTSP</h1>{badge}</div>', unsafe_allow_html=True)

    c_period, c_src, c_range = st.columns([2.2, 2.4, 4])
    period = c_period.segmented_control("집계 기간", ["최근 7일", "최근 30일", "전체"],
                                        default="최근 30일", label_visibility="collapsed") or "최근 30일"
    sources = sorted(s for s in all_events["source"].unique() if s)
    picked = c_src.multiselect("영상 소스", sources, default=sources, placeholder="RTSP 소스 (전체)",
                               format_func=mask, label_visibility="collapsed", disabled=not sources)

    events = all_events[all_events["source"].isin(picked)] if sources and picked else all_events
    if period == "전체":
        start = events["date"].min() if len(events) else today
        n_days = max((today - start).days + 1, 1)
    else:
        n_days = 7 if period == "최근 7일" else 30
        start = today - timedelta(days=n_days - 1)
    view = events[(events["date"] >= start) & (events["date"] <= today)]

    c_range.markdown(
        f'<div class="td-range">{start} ~ {today} · 집계 {datetime.now():%H:%M}</div>', unsafe_allow_html=True)

    # ── 집계 ─────────────────────────────────────────────
    total = len(view)
    today_cnt = int((events["date"] == today).sum())
    yest_cnt = int((events["date"] == today - timedelta(days=1)).sum())
    hour_counts = view["hour"].value_counts().reindex(range(24), fill_value=0)
    daily = view.groupby("date").size()
    active_days = len(daily)

    if today_cnt == yest_cnt:
        delta_txt = f"어제 {yest_cnt}건 대비 변동 없음"
    else:
        delta_txt = f"어제 {yest_cnt}건 대비 {today_cnt - yest_cnt:+d}건"

    if total:
        peak_hour = int(hour_counts.idxmax())
        peak_val = f"{peak_hour:02d}~{(peak_hour + 1) % 24:02d}<small>시</small>"
        peak_sub = f"{int(hour_counts.max())}건 발생 · 전체의 {hour_counts.max() / total * 100:.0f}%"
        worst_day, worst_cnt = daily.idxmax(), int(daily.max())
        worst_val, worst_sub = f"{worst_day:%m/%d}", f"하루 {worst_cnt}건 · {WEEKDAYS[worst_day.weekday()]}요일"
    else:
        peak_val, peak_sub = "—", "관측 데이터 없음"
        worst_val, worst_sub = "—", "관측 데이터 없음"

    k = st.columns(4)
    k[0].markdown(kpi("red", "#C0392B", "오늘 위험 발생", str(today_cnt), "건", delta_txt), unsafe_allow_html=True)
    k[1].markdown(kpi("amber", "#D08A2E", "최대 취약 시간", peak_val, "", peak_sub), unsafe_allow_html=True)
    k[2].markdown(kpi("green", "#4D9F50", f"{period} 총 탐지", str(total), "건",
                      f"일 평균 {total / n_days:.1f}건 · 발생일 {active_days}/{n_days}일"), unsafe_allow_html=True)
    k[3].markdown(kpi("", "#94A3B8", "최다 발생일", worst_val, "", worst_sub), unsafe_allow_html=True)

    st.write("")

    # ── 시간대별 + 취약 시간 분석 ─────────────────────────
    left, right = st.columns([1.55, 1])
    with left:
        with st.container(border=True):
            h1, h2 = st.columns([3, 1.3])
            h1.markdown(f'<div class="td-card-title" style="border:0;margin:0">시간대별 위험 발생<span>{period}</span></div>',
                        unsafe_allow_html=True)
            scope = h2.segmented_control("범위", ["기간", "오늘"], default="기간",
                                         label_visibility="collapsed") or "기간"
            src_df = events[events["date"] == today] if scope == "오늘" else view
            hc = src_df["hour"].value_counts().reindex(range(24), fill_value=0)
            top3 = set(hc[hc > 0].sort_values(ascending=False, kind="stable").head(3).index)
            hdf = pd.DataFrame({"시": range(24), "건수": hc.values})
            hdf["구분"] = hdf["시"].map(lambda h: "취약 시간 Top 3" if h in top3 else "발생 건수")
            hdf["bg"] = max(int(hc.max()), 1)
            base = alt.Chart(hdf).encode(x=alt.X("시:O", title=None, axis=alt.Axis(labelAngle=0, labelOverlap=True,
                                                  values=list(range(0, 24, 3)))))
            ghost = base.mark_bar(color="#F1F2F4", size=6, cornerRadius=3).encode(
                y=alt.Y("bg:Q", title=None, scale=alt.Scale(domain=[0, max(int(hc.max()), 1)])))
            bars = base.mark_bar(size=10, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                y=alt.Y("건수:Q", title=None, axis=alt.Axis(tickMinStep=1, format="d")),
                color=alt.Color("구분:N", legend=None, scale=alt.Scale(
                    domain=["발생 건수", "취약 시간 Top 3"], range=[GREEN, DANGER])),
                tooltip=[alt.Tooltip("시:O", title="시각"), alt.Tooltip("건수:Q", title="발생 건수")])
            st.altair_chart(style((ghost + bars).properties(height=260)), width="stretch")
            st.markdown(f'<div class="td-legend"><i style="background:{GREEN}"></i>발생 건수'
                        f'<i style="background:{DANGER}"></i>취약 시간 Top 3</div>', unsafe_allow_html=True)

    with right:
        if total:
            ranks = hour_counts[hour_counts > 0].sort_values(ascending=False, kind="stable").head(3)
            mx = int(ranks.max())
            body = "".join(
                f'<div class="td-rank"><b>{h:02d}시</b><div class="td-bar"><div style="width:{c / mx * 100:.0f}%;'
                f'background:{DANGER}"></div></div><em>{c}건 ({c / total * 100:.0f}%)</em></div>'
                for h, c in ranks.items())
            bands = [("새벽 00~06", 0, 6), ("오전 06~12", 6, 12), ("오후 12~18", 12, 18), ("저녁·밤 18~24", 18, 24)]
            bc = [(n, int(hour_counts.loc[lo:hi - 1].sum())) for n, lo, hi in bands]
            pk = max(bc, key=lambda x: x[1])
            body += '<div style="height:.6rem"></div>' + "".join(
                f'<div class="td-rank"><b style="width:7.5rem;font-weight:500">{n}시</b><div class="td-bar"><div style="width:{c / total * 100:.0f}%;'
                f'background:{GREEN if n != pk[0] else "#D08A2E"}"></div></div><em>{c}건</em></div>'
                for n, c in bc)
            body += (f'<div class="td-kpi-sub" style="margin-top:.6rem">가장 위험한 시간 구간은 '
                     f'<b style="color:#0F172A">{pk[0]}시</b> ({pk[1] / total * 100:.0f}%)입니다.</div>')
        else:
            body = '<div class="td-empty">해당 기간에 관측된 위험이 없습니다</div>'
        st.markdown(card("취약 시간 분석", period, body), unsafe_allow_html=True)

    st.write("")

    # ── 일별 추이 + 소스별 탐지 ───────────────────────────
    left, right = st.columns([1.55, 1])
    with left:
        with st.container(border=True):
            st.markdown(f'<div class="td-card-title" style="border:0;margin:0">일별 위험 추이<span>{period}</span></div>',
                        unsafe_allow_html=True)
            days = pd.date_range(start, today)
            ddf = pd.DataFrame({"날짜": days})
            ddf["건수"] = [int(daily.get(d.date(), 0)) for d in days]
            dmax = max(int(ddf["건수"].max()), 1)
            line = alt.Chart(ddf).mark_area(
                line={"color": GREEN}, color=alt.Gradient(
                    gradient="linear", stops=[alt.GradientStop(color="#4D9F5040", offset=0),
                                              alt.GradientStop(color="#4D9F5005", offset=1)],
                    x1=1, x2=1, y1=1, y2=0), interpolate="monotone",
            ).encode(
                x=alt.X("날짜:T", title=None, axis=alt.Axis(format="%m/%d", labelAngle=0, tickCount=8)),
                y=alt.Y("건수:Q", title=None, scale=alt.Scale(domain=[0, dmax]),
                        axis=alt.Axis(tickMinStep=1, format="d")),
                tooltip=[alt.Tooltip("날짜:T", format="%Y-%m-%d"), alt.Tooltip("건수:Q", title="발생 건수")])
            st.altair_chart(style(line.properties(height=220)), width="stretch")

    with right:
        if total and (view["source"] != "").any():
            sc = view[view["source"] != ""].groupby("source").size().sort_values(ascending=False)
            mx = int(sc.max())
            body = "".join(
                f'<div class="td-rank"><b style="width:7rem;font-weight:500;overflow:hidden;text-overflow:ellipsis;'
                f'white-space:nowrap" title="{html.escape(mask(s))}">{html.escape(mask(s))}</b><div class="td-bar"><div style="width:{c / mx * 100:.0f}%;'
                f'background:{GREEN}"></div></div><em>{c}건</em></div>' for s, c in sc.head(8).items())
        else:
            body = '<div class="td-empty">데이터 없음</div>'
        st.markdown(card("소스별 탐지", period, body), unsafe_allow_html=True)

    st.write("")

    # ── 최근 관측 사례 ───────────────────────────────────
    with st.container(border=True):
        t1, t2, t3 = st.columns([3, 1.6, 1.4])
        t1.markdown(f'<div class="td-card-title" style="border:0;margin:0">최근 관측 사례<span>{period}</span></div>',
                    unsafe_allow_html=True)
        show_cases = t2.toggle("사례 보기", value=False, key="td_show_cases")
        try:
            t3.page_link("pages/3_이벤트_다시보기.py", label="이벤트 전체 보기 →")
        except Exception:  # 내비게이션 밖에서 단독 실행될 때는 링크만 생략
            pass
        if not show_cases:
            pass  # 토글을 켜기 전에는 이미지·사례를 읽지 않는다
        elif total:
            recent = view.sort_values("ts", ascending=False).head(6)
            cols = st.columns(3)
            for i, (_, ev) in enumerate(recent.iterrows()):
                with cols[i % 3]:
                    img = os.path.join(EVENTS_DIR, ev["image_file"]) if ev["image_file"] else ""
                    if img and os.path.exists(img):
                        st.image(img, width="stretch")
                    else:
                        st.caption("🖼️ 이미지 파일 없음")
                    has_clip = bool(ev["clip_file"]) and os.path.exists(os.path.join(EVENTS_DIR, ev["clip_file"]))
                    tag = '<span class="td-tag">클립 있음</span>' if has_clip else '<span class="td-tag no">클립 없음</span>'
                    st.markdown(
                        f'<div class="td-case"><strong>{ev["ts"]:%Y-%m-%d %H:%M:%S}</strong> '
                        f'({WEEKDAYS[int(ev["weekday"])]}){tag}<br>{html.escape(mask(ev["source"])) or "-"}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="td-empty">관측된 사례가 없습니다</div>', unsafe_allow_html=True)


render()