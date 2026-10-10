# pages/2_ROI_설정.py — ROI(관심구역) 직접 그리기 화면
#
# 사용 흐름:
#   1. 영상 소스 선택 → 첫 프레임 불러오기
#   2. 영상 위에 마우스로 클릭 → 꼭짓점 추가
#   3. 꼭짓점 3개 이상 → 💾 ROI 저장 클릭

import streamlit as st
import cv2
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import DATA_DIR
from core.video_source import VideoSource
from core.roi_manager  import save_roi, load_roi, list_saved_rois, delete_roi

try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    LIB_OK = True
except ImportError:
    LIB_OK = False

# st.set_page_config는 app.py에서 1회만 호출

if not LIB_OK:
    st.error(
        "❌ `streamlit-image-coordinates` 라이브러리가 없습니다.\n\n"
        "터미널에서 실행하세요:\n```\npip install streamlit-image-coordinates\n```"
    )
    st.stop()

st.markdown("""
<style>
.roi-heading h1 { color:#0F172A; font-size:2.2rem; font-weight:800; margin-bottom:.2rem; }
.roi-heading p { color:#64748B; font-size:1rem; margin:0 0 1.5rem; }
[data-testid="stFileUploader"], [data-testid="stImage"] {
    background:#FFFFFF; border:1px solid #E2E8F0; border-radius:14px;
    padding:.65rem; box-shadow:0 4px 16px rgba(15,23,42,.04);
}
[data-testid="stTextInput"] input, [data-baseweb="select"] > div {
    border-color:#CBD5E1 !important; border-radius:10px !important;
}
div[role="radiogroup"] { background:#E2E8F0; padding:4px 8px; border-radius:10px; }
</style>
<div class="roi-heading">
    <h1>🗺️ ROI 영역 설정</h1>
    <p>영상에서 위험을 감시할 관심구역을 직접 지정하고 소스별로 저장합니다.</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# session_state 초기화
# ══════════════════════════════════════════════════════
if "roi_points"   not in st.session_state: st.session_state.roi_points   = []
if "roi_frame"    not in st.session_state: st.session_state.roi_frame    = None
if "last_click"   not in st.session_state: st.session_state.last_click   = None
if "roi_src_label" not in st.session_state: st.session_state.roi_src_label = ""

# ══════════════════════════════════════════════════════
# 헬퍼
# ══════════════════════════════════════════════════════
DISPLAY_W = 800

def render_frame(frame_bgr, points: list, scale: float) -> Image.Image:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    orig_h, orig_w = frame_bgr.shape[:2]
    disp_w = DISPLAY_W
    disp_h = int(orig_h * scale)
    pil = pil.resize((disp_w, disp_h), Image.LANCZOS)

    if not points:
        return pil

    draw = ImageDraw.Draw(pil)
    disp_pts = [(int(x * scale), int(y * scale)) for x, y in points]

    if len(disp_pts) >= 3:
        draw.polygon(disp_pts, fill=(0, 255, 180, 60), outline=(0, 255, 180))
    for i in range(len(disp_pts) - 1):
        draw.line([disp_pts[i], disp_pts[i+1]], fill=(0, 255, 180), width=2)
    for i, (px, py) in enumerate(disp_pts):
        r = 7
        draw.ellipse([(px-r, py-r), (px+r, py+r)], fill=(255, 80, 80), outline="white")
        draw.text((px + 9, py - 8), f"P{i+1}", fill="white")
    return pil

def get_video_files() -> list:
    if not os.path.exists(DATA_DIR):
        return []
    return [f for f in os.listdir(DATA_DIR)
            if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))]


# ══════════════════════════════════════════════════════
# 레이아웃: 왼쪽(설정) + 오른쪽(캔버스)
# ══════════════════════════════════════════════════════
settings_col, canvas_col = st.columns([1, 2.5])

# ── 왼쪽: 소스 선택 + ROI 저장 설정 ───────────────────
with settings_col:
    st.markdown('<span class="sv-source-panel-marker" aria-hidden="true"></span>', unsafe_allow_html=True)
    # 소스 선택 카드
    st.markdown("### 소스 선택")
    source_type = st.radio("영상 소스", ["📁 파일", "📡 RTSP"], horizontal=True, label_visibility="collapsed")

    selected_source = None
    auto_label      = ""

    if source_type == "📁 파일":
        # 영상 파일 업로드 (PC 어디서나 빠르게 불러오기)
        uploaded = st.file_uploader(
            "💾 영상 파일 불러오기",
            type=["mp4", "avi", "mov", "mkv"],
            help="PC에서 영상을 선택하면 data 폴더에 자동 저장되어 다음에도 그대로 사용할 수 있습니다.",
        )
        if uploaded is not None:
            os.makedirs(DATA_DIR, exist_ok=True)
            save_path = os.path.join(DATA_DIR, uploaded.name)
            if not os.path.exists(save_path):
                with open(save_path, "wb") as f:
                    f.write(uploaded.getbuffer())
                st.success(f"✅ '{uploaded.name}' 저장 완료")

        files = get_video_files()
        if files:
            default_idx = 0
            if uploaded is not None and uploaded.name in files:
                default_idx = files.index(uploaded.name)
            chosen          = st.selectbox("파일 선택", files, index=default_idx)
            selected_source = os.path.join(DATA_DIR, chosen)
            auto_label      = os.path.splitext(chosen)[0]

            # 영상 파일 삭제 관리
            with st.expander("🗑️ 저장된 영상 삭제"):
                pending = st.session_state.get("video_pending_delete")
                if pending and pending in files:
                    st.warning(f"⚠️ **'{pending}'** 영상을 정말 삭제하시겠습니까?")
                    yc, nc = st.columns(2)
                    if yc.button("✅ 확인", type="primary", use_container_width=True, key="vid_del_yes_roi"):
                        try:
                            os.remove(os.path.join(DATA_DIR, pending))
                            st.session_state.video_pending_delete = None
                            st.success(f"'{pending}' 삭제 완료")
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 실패: {e}")
                    if nc.button("❌ 취소", use_container_width=True, key="vid_del_no_roi"):
                        st.session_state.video_pending_delete = None
                        st.rerun()
                else:
                    for vf in files:
                        vc1, vc2 = st.columns([5, 1])
                        vc1.markdown(f"📹 `{vf}`")
                        if vc2.button("🗑️", key=f"del_vid_roi_{vf}", help="이 영상 삭제"):
                            st.session_state.video_pending_delete = vf
                            st.rerun()
        else:
            st.warning("위에서 영상 파일을 업로드하거나 `data/` 폴더에 영상 파일을 넣어주세요.")
    else:
        # 모니터링 페이지와 동일한 프리셋 토글 사용
        from core.rtsp_presets import load_presets

        presets = load_presets()
        if presets:
            preset_names = [p["name"] for p in presets]
            selected_name = st.selectbox("📡 카메라 선택", preset_names)
            selected_preset = next(p for p in presets if p["name"] == selected_name)
            selected_source = selected_preset["url"]
            auto_label      = selected_name   # ROI 이름을 카메라 이름과 자동 매칭
        else:
            st.info(
                "등록된 카메라가 없습니다.\n\n"
                "**모니터링 페이지** → 📡 RTSP → '➕ 카메라 등록 / 삭제'에서 먼저 추가하세요."
            )

    if st.button("📷 기준 프레임 불러오기", type="primary",
                 disabled=selected_source is None, use_container_width=True):
        with st.spinner("프레임 불러오는 중..."):
            vs    = VideoSource(selected_source)
            frame = vs.get_first_frame()
        if frame is not None:
            st.session_state.roi_frame  = frame
            st.session_state.roi_points = []
            st.session_state.last_click = None
            h, w = frame.shape[:2]
            st.success(f"✅ 완료 ({w}×{h})")
        else:
            st.error("❌ 프레임을 가져올 수 없습니다.")

    st.markdown("---")

    # ROI 저장 카드
    st.markdown("### ROI 저장")
    # 영상이 바뀌면 text_input의 key가 바뀌어 새 박스로 다시 그려짐
    # → 영상 변경 시 항상 auto_label로 초기화되어 매칭 어긋남 방지
    label_input = st.text_input(
        "ROI 이름",
        value=auto_label,
        key=f"roi_label_input_{auto_label}",
        help="모니터링 페이지에서 같은 이름의 영상을 선택하면 자동 로드됩니다. 영상 파일명과 동일하게 두는 것을 권장합니다.",
    )
    st.session_state.roi_src_label = label_input

    pts = st.session_state.roi_points

    bc1, bc2 = st.columns(2)
    if bc1.button("↩️ 마지막 취소", use_container_width=True):
        if pts:
            st.session_state.roi_points.pop()
            st.session_state.last_click = None
        st.rerun()
    if bc2.button("🗑️ 전체 초기화", use_container_width=True):
        st.session_state.roi_points = []
        st.session_state.last_click = None
        st.rerun()

    save_clicked = st.button(
        f"💾 ROI 저장 ({len(pts)}개 꼭짓점)",
        type="primary",
        use_container_width=True,
        disabled=len(pts) < 3,
    )

    st.markdown("---")

    # 꼭짓점 좌표
    if pts:
        st.markdown("### 꼭짓점 좌표")
        for i, p in enumerate(pts):
            st.markdown(f"**{i+1}** &nbsp;&nbsp; ({p[0]}, {p[1]})")

    st.markdown("---")

    # 저장된 ROI 목록
    st.markdown("### 📂 저장된 ROI")
    saved = list_saved_rois()
    if saved:
        sel = st.selectbox("ROI 선택", ["— 선택 —"] + saved)
        if sel != "— 선택 —":
            loaded_pts = load_roi(sel)
            if loaded_pts is not None:
                st.success(f"{len(loaded_pts)}개 꼭짓점")

            # 삭제 (확인 절차 포함)
            confirm_key = f"confirm_del_roi_{sel}"
            if st.session_state.get(confirm_key, False):
                st.warning(f"⚠️ **'{sel}'** ROI를 정말로 삭제하시겠습니까?")
                yc, nc = st.columns(2)
                if yc.button("확인", key=f"yes_del_roi_{sel}", type="primary", use_container_width=True):
                    if delete_roi(sel):
                        st.session_state[confirm_key] = False
                        st.success(f"'{sel}' 삭제됨")
                        st.rerun()
                if nc.button("취소", key=f"no_del_roi_{sel}", use_container_width=True):
                    st.session_state[confirm_key] = False
                    st.rerun()
            else:
                if st.button("🗑️ ROI 삭제", use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()
    else:
        st.caption("저장된 ROI 없음")


# ── 오른쪽: 캔버스 (영상 + 클릭) ─────────────────────
with canvas_col:
    frame = st.session_state.roi_frame

    if frame is None:
        st.markdown("### 클릭하여 꼭짓점 추가")
        st.info(
            "👈 왼쪽에서 영상 소스를 선택하고\n\n"
            "**📷 기준 프레임 불러오기** 버튼을 누르면 여기에 영상이 표시됩니다."
        )
        st.stop()

    orig_h, orig_w = frame.shape[:2]
    scale = DISPLAY_W / orig_w

    st.markdown(f"### 클릭하여 꼭짓점 추가 &nbsp;&nbsp;&nbsp; `{orig_w} × {orig_h}`")

    pil_img = render_frame(frame, st.session_state.roi_points, scale)
    click = streamlit_image_coordinates(pil_img, key="roi_click")

    # 새로운 클릭 → 꼭짓점 추가
    if click is not None:
        new_coord = (click["x"], click["y"])
        if new_coord != st.session_state.last_click:
            st.session_state.last_click = new_coord
            orig_x = int(click["x"] / scale)
            orig_y = int(click["y"] / scale)
            st.session_state.roi_points.append([orig_x, orig_y])
            st.rerun()

# ── 저장 처리 ────────────────────────────────────────
if save_clicked:
    label = st.session_state.roi_src_label
    if not label:
        st.error("❌ **ROI 이름**을 입력하세요.")
    elif len(pts) < 3:
        st.error("❌ 꼭짓점이 3개 이상이어야 합니다.")
    else:
        path = save_roi(label, pts)
        st.success(
            f"✅ ROI 저장 완료!\n\n"
            f"- 이름: **{label}**\n"
            f"- 꼭짓점: {len(pts)}개\n"
            f"- 파일: `{path}`\n\n"
            f"모니터링 페이지에서 **{label}** 소스를 선택하면 자동으로 적용됩니다."
        )
