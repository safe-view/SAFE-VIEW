# pages/3_이벤트_다시보기.py — 이벤트 캘린더 조회 및 미리보기

import streamlit as st
import cv2
import os
import sys
import csv
import calendar
import subprocess
from datetime import datetime, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import EVENTS_DIR, LOG_FILE
from core.event_saver import delete_event

# ── 페이지 설정 ────────────────────────────────────────
# st.set_page_config는 app.py에서 1회만 호출

# 🚀 [스트림릿 뼈대 파괴 CSS] 버튼을 진짜 달력 칸으로, 이벤트를 알림 카드로 개조
st.markdown("""
    <style>
    /* 1. 전체 배경색: 맥북 스타일의 아주 연한 회색 */
    .stApp { background-color: #F1F5F9; font-family: 'Noto Sans KR', sans-serif; }
    
    /* 2. 상단 여백 다이어트 */
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    
    /* 3. 스트림릿 컬럼 갭(Gap) 압축: 캘린더 틈새를 좁혀 한 덩어리처럼 */
    [data-testid="column"] { padding: 0 4px !important; }
    
    /* 4. 요일 헤더 디자인: 캘린더 윗부분 */
    .day-header {
        text-align: center; font-weight: 700; font-size: 0.9rem;
        padding-bottom: 10px; margin-bottom: 5px;
        color: #64748B; text-transform: uppercase; letter-spacing: 1px;
    }
    
    /* 5. ⭐️ 핵심: 알약 버튼을 진짜 [캘린더 칸(Cell)]으로 개조 */
    button {
        width: 100% !important;
        height: 75px !important; /* 높이를 확 키워서 캘린더 칸처럼 만듦 */
        border-radius: 8px !important; /* 살짝만 둥근 모던한 사각형 */
        font-size: 1.1rem !important;
        margin: 0 !important;
    }
    
    /* 일반 날짜 칸 */
    button[kind="secondary"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        color: #334155 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease-in-out !important;
        display: flex; align-items: flex-start; justify-content: flex-start;
    }
    
    /* 날짜 칸에 마우스 올렸을 때 (호버) */
    button[kind="secondary"]:hover {
        background-color: #F0F9FF !important; /* 아주 연한 스카이블루 */
        border: 2px solid #0EA5E9 !important;
        color: #0284C7 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15) !important;
        z-index: 10;
    }
    
    /* 선택된 날짜 (딥 네이비 관제 시스템 컬러) */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0F172A 0%, #334155 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 800 !important;
        box-shadow: 0 6px 15px rgba(15, 23, 42, 0.3) !important;
    }
    
    /* 6. ⭐️ 이벤트 목록 상세 박스 (Expander)를 보안 알림 카드로 개조 */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        border: none !important;
        border-left: 6px solid #EF4444 !important; /* 좌측에 강렬한 빨간색 경고 띠 */
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03) !important;
        margin-bottom: 15px !important;
        overflow: hidden;
    }
    
    /* 7. 메트릭 통계 박스 */
    [data-testid="metric-container"] {
        background: #FFFFFF; border-radius: 12px; padding: 15px;
        border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    </style>
""", unsafe_allow_html=True)


# 💡 텍스트 수정: 통합 관제 대시보드 -> 감시 기록 다시보기
st.markdown("<h1 style='color: #0F172A; font-size: 2.2rem; font-weight: 800;'>🛡️ 세이프뷰 다시보기</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748B; font-size: 1.05rem;'>보안 시스템에 기록된 위험 이벤트를 캘린더 기반으로 추적하고 분석합니다.</p>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #E2E8F0; margin-top: 10px; margin-bottom: 30px;'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# 데이터 로딩
# ══════════════════════════════════════════════════════
def load_all_events():
    if not os.path.exists(LOG_FILE): return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except Exception: return []

def get_events_by_date(events, target):
    s = target.strftime("%Y-%m-%d")
    return [ev for ev in events if ev.get("timestamp", "").startswith(s)]

def get_dates_with_events(events):
    dates = set()
    for ev in events:
        ts = ev.get("timestamp", "")
        if len(ts) >= 10:
            try: dates.add(datetime.strptime(ts[:10], "%Y-%m-%d").date())
            except ValueError: pass
    return dates

# ── 영상 변환 ──────
CONVERTED_DIR = os.path.join(EVENTS_DIR, "_converted")
os.makedirs(CONVERTED_DIR, exist_ok=True)

def get_playable_video(clip_path: str) -> str | None:
    filename = os.path.basename(clip_path)
    converted_path = os.path.join(CONVERTED_DIR, filename)
    if os.path.exists(converted_path): return converted_path
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg = get_ffmpeg_exe()
        subprocess.run([ffmpeg, "-y", "-i", clip_path, "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-movflags", "+faststart", "-an", converted_path], capture_output=True, timeout=30)
        return converted_path if os.path.exists(converted_path) else None
    except Exception: return None

all_events = load_all_events()
event_dates = get_dates_with_events(all_events)

if not all_events:
    st.info("📭 저장된 이벤트가 없습니다. 모니터링에서 위험 감지가 발생하면 기록됩니다.")
    st.stop()

if "sel_date" not in st.session_state:
    st.session_state.sel_date = date.today()

# ══════════════════════════════════════════════════════
# 레이아웃: 왼쪽(필터) + 오른쪽(캘린더+이벤트)
# ══════════════════════════════════════════════════════
filter_col, content_col = st.columns([1, 3])

with filter_col:
    st.markdown("### 📅 날짜 검색")
    new_date = st.date_input("날짜 선택", value=st.session_state.sel_date)
    if new_date != st.session_state.sel_date:
        st.session_state.sel_date = new_date
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 위험 요약")
    st.metric("누적 위험 감지", f"{len(all_events)}건")
    st.metric("위험 감지 일수", f"{len(event_dates)}일")

sel = st.session_state.sel_date

# ══════════════════════════════════════════════════════
# 오른쪽: 캘린더 + 이벤트 목록
# ══════════════════════════════════════════════════════
with content_col:
    st.markdown(f"<h3 style='color: #0F172A; margin-bottom: 20px;'>🗓️ {sel.year}년 {sel.month}월 세이프뷰</h3>", unsafe_allow_html=True)

    cal_obj = calendar.Calendar(firstweekday=6)
    weeks = cal_obj.monthdayscalendar(sel.year, sel.month)

    day_names = ["일", "월", "화", "수", "목", "금", "토"]
    hcols = st.columns(7)

    for i, name in enumerate(day_names):
        if i == 0: color = "#EF4444"
        elif i == 6: color = "#3B82F6"
        else: color = "#64748B"
        hcols[i].markdown(f"<div class='day-header' style='color:{color};'>{name}</div>", unsafe_allow_html=True)

    for week in weeks:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("")
                continue
            d = date(sel.year, sel.month, day)
            has = d in event_dates
            is_sel = d == sel
            label = f"{day} 🔴" if has else f"{day}"

            if cols[i].button(
                label,
                key=f"c_{sel.year}_{sel.month}_{day}",
                use_container_width=True,
                type="primary" if is_sel else "secondary",
            ):
                st.session_state.sel_date = d
                st.rerun()

    st.caption("🔴 = 위험 상황 감지됨  |  짙은 네이비 = 현재 선택된 날짜")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #0F172A; border-bottom: 2px solid #E2E8F0; padding-bottom: 10px;'>🚨 {sel.strftime('%Y-%m-%d')} 상세 감시 기록</h3>", unsafe_allow_html=True)

    day_events = get_events_by_date(all_events, sel)

    if not day_events:
        st.info("해당 일자에 기록된 보안 이벤트가 없습니다.")
        st.stop()

    st.markdown(f"**<span style='color:#EF4444; font-size:1.1rem;'>총 {len(day_events)}건</span>**의 위험 상황이 타임라인에 기록되었습니다.", unsafe_allow_html=True)
    st.write("")

    for idx, ev in enumerate(day_events):
        timestamp = ev.get("timestamp", "")
        source    = ev.get("source", "")
        status    = ev.get("status", "")
        img_file  = ev.get("image_file", "")
        clip_file = ev.get("clip_file", "")
        time_str  = timestamp[11:19] if len(timestamp) >= 19 else timestamp

        thumb_col2, info_col2 = st.columns([1, 4])

        with thumb_col2:
            img_path = os.path.join(EVENTS_DIR, img_file) if img_file else ""
            has_img = img_file and os.path.exists(img_path)
            if has_img:
                st.image(img_path, use_container_width=True)

        with info_col2:
            confirm_key = f"confirm_del_{idx}"

            # 제목 + 삭제 버튼 오른쪽
            t_c, d_c = st.columns([5, 1])
            t_c.markdown(f"<h4 style='color:#0F172A; margin:0;'>⏱ {time_str}</h4>", unsafe_allow_html=True)

            if st.session_state.get(confirm_key, False):
                # 확인 모드: 경고 + 확인/취소 가로 배치
                st.markdown(
                    f"<div style='background:#FEF2F2; border:1px solid #FECACA; border-radius:8px; "
                    f"padding:10px 14px; margin:6px 0;'>"
                    f"<b style='color:#991B1B;'>⚠️ 이 이벤트를 삭제하시겠습니까?</b><br>"
                    f"<span style='color:#6B7280; font-size:0.85rem;'>이미지, 영상 클립, 로그가 모두 삭제됩니다.</span>"
                    f"</div>", unsafe_allow_html=True)
                y_c, n_c, _ = st.columns([1, 1, 4])
                if y_c.button("삭제", key=f"yes_{idx}", type="primary", use_container_width=True):
                    delete_event(timestamp)
                    st.session_state[confirm_key] = False
                    st.rerun()
                if n_c.button("취소", key=f"no_{idx}", use_container_width=True):
                    st.session_state[confirm_key] = False
                    st.rerun()
            else:
                if d_c.button("삭제", key=f"del_{idx}", use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()

            st.markdown(f"<p style='margin-top:5px;'><span style='background-color:#FEE2E2; color:#DC2626; padding:3px 8px; border-radius:4px; font-weight:bold; font-size:0.85rem;'>{status}</span> &nbsp; | &nbsp; <b>채널:</b> {source}</p>", unsafe_allow_html=True)

        with st.expander(f"🔍 [ {time_str} ] 원본 영상", expanded=False):
            tab_img, tab_clip, tab_info = st.tabs(["📷 스냅샷", "🎬 클립 재생", "ℹ️ 데이터"])

            with tab_img:
                if has_img: st.image(img_path, use_container_width=True)
                else: st.caption("이미지 없음")

            with tab_clip:
                if clip_file:
                    clip_path = os.path.join(EVENTS_DIR, clip_file)
                    if os.path.exists(clip_path):
                        with st.spinner("미디어 로딩 중..."):
                            playable = get_playable_video(clip_path)
                        if playable:
                            with open(playable, "rb") as vf: st.video(vf.read())
                        else:
                            st.error("스트리밍 변환 실패. 다운로드하여 확인하세요.")
                            with open(clip_path, "rb") as vf:
                                st.download_button("💾 파일 다운로드", data=vf, file_name=clip_file, mime="video/mp4", key=f"dl_{idx}")
                else:
                    st.caption("영상 클립 없음")

            with tab_info:
                st.markdown(f"""
| 속성 | 값 |
|------|-----------|
| **타임스탬프** | `{timestamp}` |
| **감지 소스** | `{source}` |
| **상태 코드** | `{status}` |
                """)

        st.write("")

    with st.expander("🗂️ 스토리지 관리", expanded=False):
        if os.path.exists(EVENTS_DIR):
            files = [f for f in os.listdir(EVENTS_DIR) if not f.startswith("_")]
            total = sum(os.path.getsize(os.path.join(EVENTS_DIR, f)) for f in files if os.path.isfile(os.path.join(EVENTS_DIR, f)))
            c1, c2, c3 = st.columns(3)
            c1.metric("JPG 에셋", f"{len([f for f in files if f.endswith('.jpg')])}개")
            c2.metric("MP4 에셋", f"{len([f for f in files if f.endswith('.mp4')])}개")
            c3.metric("점유 용량", f"{total/(1024*1024):.1f} MB")
