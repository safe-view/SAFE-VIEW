# pages/1_모니터링.py — 실시간 위험 감지 메인 화면

import streamlit as st
import cv2, os, sys, time, threading
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from collections import deque
import wave, struct, math, base64, io
from streamlit.components.v1 import html as components_html


# ══════════════════════════════════════════════════════
# 경고음 wav를 코드에서 직접 생성하여 base64로 임베드
# 880Hz 짧은 비프 2회. 외부 음원 파일 불필요.
# ══════════════════════════════════════════════════════
def _make_beep_b64(freq=880, duration=0.18, volume=0.45, sample_rate=44100,
                   beeps_per_group=2, groups=3, beep_gap=0.1, group_gap=0.35):
    """
    삑삑(휴식) 삑삑(휴식) 삑삑 패턴의 wav를 생성한다.
    - beeps_per_group: 한 묶음 안의 비프 개수
    - groups:          묶음 개수
    - beep_gap:        묶음 내 비프 사이 간격
    - group_gap:       묶음 사이 휴식 시간
    """
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        n_tone     = int(sample_rate * duration)
        n_beep_gap = int(sample_rate * beep_gap)
        n_grp_gap  = int(sample_rate * group_gap)
        for g in range(groups):
            for b in range(beeps_per_group):
                for i in range(n_tone):
                    v = int(volume * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
                    w.writeframes(struct.pack("<h", v))
                if b < beeps_per_group - 1:
                    for _ in range(n_beep_gap):
                        w.writeframes(struct.pack("<h", 0))
            if g < groups - 1:
                for _ in range(n_grp_gap):
                    w.writeframes(struct.pack("<h", 0))
    return base64.b64encode(buf.getvalue()).decode()

ALERT_BEEP_B64 = _make_beep_b64()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import DATA_DIR, FRAME_SKIP, CLIP_PRE_SEC, CLIP_POST_SEC, MAX_CLIP_FPS
from core.detector     import Detector
from core.roi_manager  import load_roi, list_saved_rois
from core.video_source import VideoSource, validate_rtsp_url, test_rtsp_connection
from core.danger_logic import check_danger, draw_detections
from core.event_saver  import (
    save_event_image, save_event_clip,
    log_event, get_recent_events,
)
from core.parked_detector import update as update_parked, reset as reset_parked
from core.image_enhancement import auto_enhance, get_brightness

# ══════════════════════════════════════════════════════
# 페이지 설정 & CSS 애니메이션
# ══════════════════════════════════════════════════════
# st.set_page_config는 app.py에서 1회만 호출

st.markdown("""
    <style>
    @keyframes pulse-danger {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.8); }
        70% { box-shadow: 0 0 0 25px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    @keyframes flash-text {
        0%, 100% { opacity: 1; text-shadow: 0 0 20px #ef4444; }
        50% { opacity: 0.6; text-shadow: none; }
    }
    .status-box-danger {
        background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%);
        padding: 25px 20px; border-radius: 15px; text-align: center;
        border: 4px solid #ef4444; animation: pulse-danger 1s infinite;
    }
    .danger-title {
        color: #f87171; margin: 0; font-size: 1.8rem; font-weight: 900;
        animation: flash-text 1s infinite;
        white-space: nowrap;
    }
    .danger-sub { color: #fca5a5; margin: 5px 0 0; font-size: 1.1rem; font-weight: bold; }
    
    .status-box-safe {
        background: linear-gradient(135deg, #022c22 0%, #064e3b 100%);
        padding: 25px 20px; border-radius: 15px; text-align: center;
        border: 2px solid #10b981;
    }
    /* 정상 글씨가 눈에 확 띄도록 밝은 초록색과 굵기 추가 */
    .safe-title { color: #4ade80 !important; margin: 0; font-size: 2.2rem; font-weight: 900; }
    .safe-sub { color: #a7f3d0 !important; margin: 5px 0 0; font-size: 1.1rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# 🎯 중앙 정렬 & 굵은 한글 출력 도우미 함수
# ══════════════════════════════════════════════════════
# 폰트 캐시 (매 프레임 디스크 로드 방지)
_font_cache = {}
def _get_font(size):
    if size not in _font_cache:
        try:
            _font_cache[size] = ImageFont.truetype("malgunbd.ttf", size)
        except:
            try:
                _font_cache[size] = ImageFont.truetype("malgun.ttf", size)
            except:
                _font_cache[size] = ImageFont.load_default()
    return _font_cache[size]

def draw_text_korean_centered(img, text, y_pos, font_size, color_bgr):
    """OpenCV 이미지의 가로 중앙에 한글을 굵고 선명하게 그리는 함수"""
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = _get_font(font_size)
            
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x_pos = (img_pil.width - text_width) // 2
    
    b, g, r = color_bgr
    
    draw.text((x_pos, y_pos), text, font=font, fill=(r, g, b), stroke_width=5, stroke_fill=(0, 0, 0))
    
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# ══════════════════════════════════════════════════════
# RTSP 백그라운드 스레드 리더
# ══════════════════════════════════════════════════════
class RTSPThreadReader:
    def __init__(self, url: str):
        self._url           = url
        self._latest_frame  = None
        self._lock          = threading.Lock()
        self._stop_event    = threading.Event()
        self._thread        = threading.Thread(target=self._run, daemon=True)
        self._connected     = False
        self._error         = ""
        self._frame_count   = 0

    def start(self) -> tuple[bool, str]:
        self._thread.start()
        for _ in range(60):
            time.sleep(0.1)
            with self._lock:
                if self._latest_frame is not None:
                    return True, ""
            if self._error:
                return False, self._error
        return False, "타임아웃: 6초 내에 첫 프레임을 받지 못했습니다."

    def _run(self):
        vs = VideoSource(self._url)
        if not vs.open():
            self._error = "RTSP 연결 실패 — IP/포트/채널 경로·포트포워딩·방화벽을 확인하세요."
            return

        self._connected = True
        fail_streak = 0

        while not self._stop_event.is_set():
            ret, frame = vs.cap.read()
            if ret and frame is not None:
                fail_streak = 0
                with self._lock:
                    self._latest_frame = frame
                    self._frame_count += 1
            else:
                fail_streak += 1
                if fail_streak >= 20:
                    vs.release()
                    time.sleep(2.0)
                    if vs.open(): fail_streak = 0
                    else:
                        self._error = "재연결 실패"
                        break
                time.sleep(0.05)

        vs.release()
        self._connected = False

    def get_latest_frame(self):
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def stop(self): self._stop_event.set()
    @property
    def is_alive(self) -> bool: return self._thread.is_alive()
    @property
    def error(self) -> str: return self._error


# ══════════════════════════════════════════════════════
# YOLO 비동기 검출 워커
# 메인 루프(영상 디코딩 + 표시)는 그대로 30fps로 돌고
# YOLO 추론만 백그라운드에서 가능한 만큼 돌려서 최신 검출 결과를 캐싱
# 결과: 영상은 모든 프레임 매끄럽게 표시 / 검출 박스만 살짝 지연 가능
# ══════════════════════════════════════════════════════
class AsyncDetectorWorker:
    def __init__(self, detector, conf_threshold: float):
        self._detector = detector
        self._conf = conf_threshold
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._pending_frame = None
        self._latest_detections = []
        self._last_infer_ms = 0.0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def submit(self, frame):
        # 가장 최근 프레임만 유지 (이전 대기 프레임은 자연스럽게 버려짐)
        with self._lock:
            self._pending_frame = frame

    def get_detections(self):
        with self._lock:
            return list(self._latest_detections)

    def get_infer_ms(self) -> float:
        """가장 최근 추론 1회에 걸린 시간(ms). 작을수록 박스가 덜 뒤처집니다."""
        with self._lock:
            return self._last_infer_ms

    def _run(self):
        from core.parked_detector import update as update_parked
        while not self._stop_event.is_set():
            frame = None
            with self._lock:
                if self._pending_frame is not None:
                    frame = self._pending_frame
                    self._pending_frame = None
            if frame is None:
                time.sleep(0.005)
                continue
            try:
                detections = self._detector.detect(frame, conf=self._conf)
                car_centers = [d["center"] for d in detections if d["class_name"] == "car"]
                car_areas = [
                    (d["bbox"][2] - d["bbox"][0]) * (d["bbox"][3] - d["bbox"][1])
                    for d in detections if d["class_name"] == "car"
                ]
                car_ids = [d.get("track_id") for d in detections
                           if d["class_name"] == "car"]
                parked_flags = update_parked(car_centers, car_areas, car_ids)
                car_iter = iter(parked_flags)
                for d in detections:
                    if d["class_name"] == "car":
                        d["is_parked"] = next(car_iter)
                    else:
                        d["is_parked"] = False
                with self._lock:
                    self._latest_detections = detections
                    self._last_infer_ms = getattr(self._detector, "last_infer_ms", 0.0)
            except Exception as e:
                print(f"[AsyncDetector] 추론 실패: {e}")

    def stop(self):
        self._stop_event.set()


def init_state():
    defaults = {
        "running":        False,
        "prev_danger":    False,
        "frame_idx":      0,
        "last_event_ts":  0.0,
        "fps_timer":      time.time(),
        "fps_count":      0,
        "fps_display":    0.0,
        "video_source":   None,
        "rtsp_reader":    None,
        "detector":       None,
        "frame_buffer":   deque(),
        "source_name":    "",
        "is_rtsp":        False,
        "alert_msg":      "",
        "alert_expires":  0.0,
        "last_good_frame": None,
        "last_detections": [],
        "post_recording":  False,
        "post_rec_start":  0.0,
        "pre_frames":      [],
        "post_frames":     [],
        "pending_img_name": "",
        "rtsp_url_saved": "",
        "rtsp_cam_name":  "rtsp_stream",
        "paused":         False,
        "seek_target":    None,
        "last_seek_val":  -1,
        "video_start_time":   0.0,
        "video_fps":          30.0,
        "video_pause_start":  0.0,
        "video_total_paused": 0.0,
        "async_detector":     None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def get_video_files() -> list:
    if not os.path.exists(DATA_DIR): return []
    return [f for f in os.listdir(DATA_DIR) if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))]

def update_fps():
    """1초 단위로 FPS 계산 및 session_state 갱신"""
    st.session_state.fps_count += 1
    elapsed = time.time() - st.session_state.fps_timer
    if elapsed >= 1.0:
        st.session_state.fps_display = round(st.session_state.fps_count / elapsed, 1)
        st.session_state.fps_count = 0
        st.session_state.fps_timer = time.time()

def stop_all():
    if st.session_state.rtsp_reader:
        st.session_state.rtsp_reader.stop()
        st.session_state.rtsp_reader = None
    if st.session_state.video_source:
        st.session_state.video_source.release()
        st.session_state.video_source = None
    if st.session_state.async_detector:
        st.session_state.async_detector.stop()
        st.session_state.async_detector = None
    st.session_state.running        = False
    st.session_state.last_good_frame = None
    st.session_state.paused         = False
    st.session_state.seek_target    = None
    st.session_state.last_seek_val  = -1
    st.session_state.video_start_time   = 0.0
    st.session_state.video_total_paused = 0.0
    st.session_state.video_pause_start  = 0.0
    reset_parked()   # 정지 차량 판단 이력 초기화
    # 추적 ID도 함께 비운다 — 안 비우면 이전 세션의 차량 ID가 새 영상에 섞인다
    detector = st.session_state.get("detector")
    if detector is not None:
        detector.reset_tracker()


# ══════════════════════════════════════════════════════
# 메인 레이아웃: 설정(왼쪽) + 영상(가운데) + 상태(오른쪽)
# ══════════════════════════════════════════════════════
# 진행상황 메시지 표시 영역 (배너 바로 아래, 제목 위)
progress_ph = st.empty()

st.title("🎥 실시간 모니터링")

settings_col, main_col, status_col = st.columns([1, 2.5, 1])

# ── 왼쪽: 영상 소스 설정 ──────────────────────────────
with settings_col:
    st.markdown("### 영상 소스 설정")
    source_type = st.radio("소스", ["📁 파일", "📡 RTSP"], horizontal=True, disabled=st.session_state.running, label_visibility="collapsed")
    selected_source, source_label, source_ready = None, "", False

    if source_type == "📁 파일":
        # 영상 파일 업로드 (PC 어디서나 빠르게 불러오기)
        uploaded = st.file_uploader(
            "💾 영상 파일 불러오기",
            type=["mp4", "avi", "mov", "mkv"],
            disabled=st.session_state.running,
            help="PC에서 영상을 선택하면 data 폴더에 자동 저장되어 다음에도 그대로 사용할 수 있습니다.",
            label_visibility="visible",
        )
        if uploaded is not None and not st.session_state.running:
            os.makedirs(DATA_DIR, exist_ok=True)
            save_path = os.path.join(DATA_DIR, uploaded.name)
            if not os.path.exists(save_path):
                with open(save_path, "wb") as f:
                    f.write(uploaded.getbuffer())
                st.success(f"✅ '{uploaded.name}' 저장 완료")

        video_files = get_video_files()
        if video_files:
            default_idx = 0
            if uploaded is not None and uploaded.name in video_files:
                default_idx = video_files.index(uploaded.name)
            chosen = st.selectbox("영상 파일 선택", video_files, index=default_idx, disabled=st.session_state.running)
            selected_source = os.path.join(DATA_DIR, chosen)
            source_label    = os.path.splitext(chosen)[0]
            source_ready    = True

            # 영상 파일 삭제 관리 (실행 중이 아닐 때만)
            if not st.session_state.running:
                with st.expander("🗑️ 저장된 영상 삭제"):
                    pending = st.session_state.get("video_pending_delete")
                    if pending and pending in video_files:
                        st.warning(f"⚠️ **'{pending}'** 영상을 정말 삭제하시겠습니까?")
                        yc, nc = st.columns(2)
                        if yc.button("✅ 확인", type="primary", use_container_width=True, key="vid_del_yes_mon"):
                            try:
                                os.remove(os.path.join(DATA_DIR, pending))
                                st.session_state.video_pending_delete = None
                                st.success(f"'{pending}' 삭제 완료")
                                st.rerun()
                            except Exception as e:
                                st.error(f"삭제 실패: {e}")
                        if nc.button("❌ 취소", use_container_width=True, key="vid_del_no_mon"):
                            st.session_state.video_pending_delete = None
                            st.rerun()
                    else:
                        for vf in video_files:
                            vc1, vc2 = st.columns([5, 1])
                            vc1.markdown(f"📹 `{vf}`")
                            if vc2.button("🗑️", key=f"del_vid_mon_{vf}", help="이 영상 삭제"):
                                st.session_state.video_pending_delete = vf
                                st.rerun()
        else:
            st.warning("위에서 영상 파일을 업로드하거나 data/ 폴더에 .mp4 파일을 넣어주세요.")
    else:
        # ── RTSP 프리셋 토글 방식 (다중 카메라 지원) ──────
        from core.rtsp_presets import load_presets, add_preset, delete_preset

        presets = load_presets()

        # 1) 저장된 프리셋이 있으면 드롭다운(▼ 토글) 표시
        if presets:
            preset_names = [p["name"] for p in presets]
            # 기본 선택값 (이전에 선택했던 카메라 유지)
            default_idx = 0
            if st.session_state.rtsp_cam_name in preset_names:
                default_idx = preset_names.index(st.session_state.rtsp_cam_name)

            selected_name = st.selectbox(
                "📡 카메라 선택",
                preset_names,
                index=default_idx,
                disabled=st.session_state.running,
            )
            # 선택된 프리셋의 URL 가져오기
            selected_preset = next(p for p in presets if p["name"] == selected_name)
            rtsp_url = selected_preset["url"]
            cam_name = selected_name
            st.session_state.rtsp_url_saved = rtsp_url
            st.session_state.rtsp_cam_name  = cam_name
        else:
            st.info("등록된 카메라가 없습니다. 아래에서 추가하세요.")
            rtsp_url, cam_name = "", ""

        # 2) 프리셋 추가/삭제 (실행 중이 아닐 때만)
        if not st.session_state.running:
            with st.expander("➕ 카메라 등록 / 삭제"):
                # 추가 영역
                st.markdown("**카메라 등록**")
                new_name = st.text_input("이름", placeholder="예: 주차장, 골목, 입구", key="new_preset_name")
                new_url  = st.text_input("RTSP 주소", placeholder="rtsp://admin:1234@IP:554/...", key="new_preset_url")
                if st.button("➕ 추가", use_container_width=True, type="primary"):
                    ok, msg = add_preset(new_name, new_url)
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()

                # 삭제 영역 (확인 절차 포함)
                if presets:
                    st.markdown("---")
                    st.markdown("**카메라 삭제**")
                    del_name = st.selectbox(
                        "삭제할 카메라",
                        [p["name"] for p in presets],
                        key="del_preset_select",
                    )

                    confirm_key = f"confirm_del_preset_{del_name}"

                    if st.session_state.get(confirm_key, False):
                        # 확인 단계
                        st.warning(f"⚠️ **'{del_name}'** 카메라를 정말로 삭제하시겠습니까?")
                        yc, nc = st.columns(2)
                        if yc.button("확인", key=f"yes_del_{del_name}", type="primary", use_container_width=True):
                            if delete_preset(del_name):
                                st.session_state[confirm_key] = False
                                st.success(f"'{del_name}' 삭제됨")
                                st.rerun()
                        if nc.button("취소", key=f"no_del_{del_name}", use_container_width=True):
                            st.session_state[confirm_key] = False
                            st.rerun()
                    else:
                        if st.button("🗑️ 삭제", use_container_width=True):
                            st.session_state[confirm_key] = True
                            st.rerun()

        # 3) URL 검증 + 연결 테스트
        valid, err = validate_rtsp_url(rtsp_url) if rtsp_url else (False, "")
        if rtsp_url and not valid:
            st.error(f"⛔ {err}")

        if rtsp_url and st.button("🔌 연결 테스트", disabled=not valid or st.session_state.running):
            with st.spinner("연결 테스트 중..."):
                ok, msg = test_rtsp_connection(rtsp_url)
            (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {msg}")

        if valid:
            selected_source, source_label, source_ready = rtsp_url, cam_name, True

    # 시작/정지 버튼 (영상 소스 선택 바로 아래로 위치 변경)
    start_btn = st.button("▶ 시작", use_container_width=True, disabled=st.session_state.running or not source_ready, type="primary")
    stop_btn  = st.button("⏹ 정지", use_container_width=True, disabled=not st.session_state.running)

    st.markdown("---")

    # 시스템 상태
    st.markdown("### 시스템 상태")
    roi_polygon = load_roi(source_label) if source_label else None
    if roi_polygon is not None:
        st.success(f"✅ ROI 로드됨 ({len(roi_polygon)}개) — `{source_label}`")
    else:
        st.warning(f"⚠️ '{source_label}' ROI 미설정")
        saved_list = list_saved_rois()
        if saved_list:
            st.caption("저장된 ROI : " + ", ".join(f"`{s}`" for s in saved_list))
            st.caption("→ ROI 설정 페이지에서 같은 이름으로 다시 저장하거나 파일명을 일치시키세요.")

    if st.session_state.running:
        # placeholder로 만들어 while 루프에서 실시간 갱신
        fps_ph   = st.empty()
        frame_ph_count = st.empty()
        infer_ph = st.empty()
        fps_ph.markdown(f"**FPS** &nbsp; {st.session_state.fps_display}")
        frame_ph_count.markdown(f"**프레임** &nbsp; {st.session_state.frame_idx}")
        st.session_state["__fps_ph"]   = fps_ph
        st.session_state["__frame_ph_count"] = frame_ph_count
        st.session_state["__infer_ph"] = infer_ph

    st.markdown("---")

    # 감지 신뢰도는 내부 기본값 사용 (UI 숨김)
    conf_threshold = 0.4

    # 야간 자동 밝기 보정
    enhance_mode = st.radio(
        "야간 밝기 보정",
        ["자동", "강제 ON", "OFF"],
        index=0,
        horizontal=True,
        help="저조도 환경에서 영상을 자동으로 밝게 보정합니다",
    )
    st.session_state.enhance_mode = enhance_mode

# ══════════════════════════════════════════════════════
# 시작/정지 처리
# ══════════════════════════════════════════════════════
if start_btn and selected_source:
    if st.session_state.detector is None:
        progress_ph.info("🔄 YOLOv8 모델 로딩 중... (첫 실행 시 다운로드가 있을 수 있습니다)")
        st.session_state.detector = Detector()
        if not st.session_state.detector.loaded:
            progress_ph.error(f"❌ 모델 로드 실패: {st.session_state.detector.load_error}")
            st.stop()
        # OpenVINO를 쓰려다 실패해 기존 모델로 되돌아간 경우 조용히 넘기지 않고 알림
        if st.session_state.detector.load_warning:
            st.sidebar.warning(f"⚠️ {st.session_state.detector.load_warning}")

    # 비동기 YOLO 워커 생성 (영상 표시와 추론 분리)
    if st.session_state.async_detector is not None:
        st.session_state.async_detector.stop()
    st.session_state.async_detector = AsyncDetectorWorker(st.session_state.detector, 0.4)

    is_rtsp = source_type == "📡 RTSP (자택 CCTV)"
    buf_size = max(int(25 * CLIP_PRE_SEC), 30)

    if is_rtsp:
        valid, err = validate_rtsp_url(selected_source)
        if not valid: progress_ph.error(f"❌ {err}"); st.stop()

        progress_ph.info("📡 RTSP 연결 중...")
        reader = RTSPThreadReader(selected_source)
        ok, err_msg = reader.start()

        if not ok:
            progress_ph.error(f"❌ RTSP 연결 실패: {err_msg}")
            reader.stop(); st.stop()

        st.session_state.rtsp_reader   = reader
        st.session_state.video_source  = None
    else:
        vs = VideoSource(selected_source)
        progress_ph.info("📂 영상 파일 열기 중...")
        opened = vs.open()
        if not opened: progress_ph.error("❌ 영상 파일을 열 수 없습니다."); st.stop()
        st.session_state.video_source = vs
        st.session_state.rtsp_reader  = None
        # 시간 기반 프레임 스킵용: 원본 fps와 재생 시작 시각 기록
        st.session_state.video_fps          = vs.cap.get(cv2.CAP_PROP_FPS) or 30.0
        st.session_state.video_start_time   = time.time()
        st.session_state.video_total_paused = 0.0
        st.session_state.video_pause_start  = 0.0

    progress_ph.success("✅ 시작 준비 완료!")
    st.session_state.update({
        "is_rtsp":        is_rtsp,
        "source_name":    source_label,
        "frame_idx":      0,
        "prev_danger":    False,
        "frame_buffer":   deque(maxlen=buf_size),
        "running":        True,
        "last_good_frame": None,
        "alert_msg":      "",
        "alert_expires":  0.0,
    })
    st.rerun()

if stop_btn:
    stop_all()
    st.rerun()


# ══════════════════════════════════════════════════════
# 영상/상태 플레이스홀더 (위에서 만든 columns 사용)
# ══════════════════════════════════════════════════════
with main_col:
    frame_ph = st.empty()
    info_ph  = st.empty()
    ctrl_box = st.empty()          # 재생/정지 + 시크 슬라이더
    video_progress_ph = st.empty() # 진행률 바 (실시간 갱신)

with status_col:
    status_ph = st.empty()
    alert_ph  = st.empty()
    events_ph = st.empty()
    sound_ph  = st.empty()   # 위험 시 components.html로 audio autoplay 삽입


# ══════════════════════════════════════════════════════
# 대기 화면 (검은색 스크린 박스 적용)
# ══════════════════════════════════════════════════════
if not st.session_state.running:
    # 대기화면: PIL로 이미지 생성 (테마 무관, 외부 접속에서도 동일 표시)
    from PIL import Image as PILImage, ImageDraw as PILDraw, ImageFont as PILFont
    _wi = PILImage.new("RGB", (960, 540), (17, 24, 39))
    _wd = PILDraw.Draw(_wi)
    try:
        _f1 = PILFont.truetype("malgunbd.ttf", 28)
        _f2 = PILFont.truetype("malgun.ttf", 22)
    except:
        _f1 = _f2 = PILFont.load_default()
    _t1, _t2 = "▶ 왼쪽에서 소스를 선택하고", "시작 버튼을 누르세요"
    _b1 = _wd.textbbox((0, 0), _t1, font=_f1)
    _b2 = _wd.textbbox((0, 0), _t2, font=_f2)
    _wd.text(((960 - _b1[2]) // 2, 230), _t1, fill=(156, 163, 175), font=_f1)
    _wd.text(((960 - _b2[2]) // 2, 275), _t2, fill=(96, 165, 250), font=_f2)
    frame_ph.image(_wi, use_container_width=True)
    
    status_ph.markdown("""
    <div class='status-box-safe' style='background: #1e293b; border-color: #475569;'>
        <h2 style='color:#cbd5e1;margin:0'>⏸ 대기 중</h2>
        <p style='color:#94a3b8;margin:4px 0 0'>모니터링을 시작해주세요</p>
    </div>""", unsafe_allow_html=True)
    recent = get_recent_events(5)
    if recent:
        lines = "### 📋 최근 이벤트\n"
        for ev in recent: lines += f"- `{ev['timestamp'][:19]}` **{ev['status']}** `{ev['source']}`\n"
        events_ph.markdown(lines)
    else:
        events_ph.caption("저장된 이벤트 없음")
    st.stop()


# ══════════════════════════════════════════════════════
# 프레임 처리 루프 (실행 중)
# ══════════════════════════════════════════════════════
is_rtsp      = st.session_state.is_rtsp
rtsp_reader  = st.session_state.rtsp_reader
vs           = st.session_state.video_source
detector     = st.session_state.detector

if is_rtsp and (rtsp_reader is None or not rtsp_reader.is_alive):
    stop_all(); st.warning("⚠️ RTSP 스레드가 종료됐습니다."); st.stop()

if not is_rtsp and (vs is None or not vs.is_open()):
    stop_all(); st.warning("⚠️ 영상 소스 연결이 끊어졌습니다."); st.stop()

roi_polygon = load_roi(st.session_state.source_name)

# ══════════════════════════════════════════════════════
# 처리 해상도 축소 (파일 모드) — 메인 루프 부담 줄여 매끄러운 재생 확보
# 디코딩은 원본 크기지만 그 후 draw / YOLO / 화면 전송은 모두 축소된 크기로 처리
# ROI 좌표도 같은 비율로 조정해 위치 어긋남 방지
# ══════════════════════════════════════════════════════
import numpy as np  # 이미 위에서 임포트되어 있지만 명시
PROC_MAX_W = 960     # 1080p / 4K 영상을 이 폭으로 축소해 처리
proc_scale = 1.0
if not is_rtsp and vs is not None and vs.cap is not None:
    orig_w = int(vs.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    if orig_w > PROC_MAX_W:
        proc_scale = PROC_MAX_W / orig_w
        if roi_polygon is not None:
            roi_polygon = (roi_polygon.astype(np.float32) * proc_scale).astype(np.int32)

# ── 영상 재생 컨트롤 (파일 모드에서만 표시) ───────────────
total_video_frames = 0
if not is_rtsp and vs is not None and vs.cap is not None:
    try:
        total_video_frames = int(vs.cap.get(cv2.CAP_PROP_FRAME_COUNT))
    except Exception:
        total_video_frames = 0

    with ctrl_box.container():
        cc1, cc2 = st.columns([1, 5])
        with cc1:
            play_label = "▶ 재생" if st.session_state.paused else "⏸ 일시정지"
            if st.button(play_label, key="play_pause_btn", use_container_width=True, type="primary"):
                if not st.session_state.paused:
                    # 일시정지 시작 시각 기록
                    st.session_state.video_pause_start = time.time()
                else:
                    # 재생 재개: 일시정지로 흘러간 시간 누적
                    st.session_state.video_total_paused += time.time() - st.session_state.video_pause_start
                st.session_state.paused = not st.session_state.paused
                st.rerun()
        with cc2:
            if total_video_frames > 0:
                current_pos = int(vs.cap.get(cv2.CAP_PROP_POS_FRAMES))
                current_pos = max(0, min(current_pos, total_video_frames - 1))
                seek_val = st.slider(
                    "재생 위치",
                    min_value=0,
                    max_value=max(total_video_frames - 1, 1),
                    value=current_pos,
                    key="seek_slider",
                    label_visibility="collapsed",
                )
                if seek_val != current_pos and seek_val != st.session_state.last_seek_val:
                    st.session_state.seek_target = seek_val
                    st.session_state.last_seek_val = seek_val
                    # 시간 기준 재설정: 지금이 seek_val 프레임이라고 가정
                    fps = st.session_state.video_fps or 30.0
                    st.session_state.video_start_time = time.time() - (seek_val / fps)
                    st.session_state.video_total_paused = 0.0
                    st.rerun()

async_worker = st.session_state.async_detector

while st.session_state.running:
    frame_start_time = time.time()  # fps 기반 sleep 계산용
    # 시크 처리 (파일 모드)
    if not is_rtsp and st.session_state.seek_target is not None and vs is not None:
        try:
            vs.cap.set(cv2.CAP_PROP_POS_FRAMES, int(st.session_state.seek_target))
        except Exception:
            pass
        st.session_state.seek_target = None
        st.session_state.frame_buffer.clear()
        reset_parked()

    # 일시정지 (파일 모드만 의미 있음)
    if st.session_state.paused and not is_rtsp:
        if st.session_state.last_good_frame is not None:
            rgb = cv2.cvtColor(st.session_state.last_good_frame, cv2.COLOR_BGR2RGB)
            frame_ph.image(rgb, channels="RGB", use_container_width=True)
        if total_video_frames > 0:
            cur = int(vs.cap.get(cv2.CAP_PROP_POS_FRAMES))
            video_progress_ph.progress(
                min(cur / max(total_video_frames, 1), 1.0),
                text=f"⏸ 일시정지 — {cur}/{total_video_frames} 프레임",
            )
        time.sleep(0.15)
        continue

    if is_rtsp:
        frame = rtsp_reader.get_latest_frame()
        ret   = frame is not None
        if not ret and rtsp_reader.error:
            stop_all(); st.error(f"❌ RTSP 오류: {rtsp_reader.error}"); break
    else:
        ret, frame = vs.read_frame()
        if not ret:
            vs.reset(); continue
        # 처리용 크기로 축소 (디코딩은 원본, 이후 처리는 작게)
        if proc_scale < 1.0 and frame is not None:
            new_w = int(frame.shape[1] * proc_scale)
            new_h = int(frame.shape[0] * proc_scale)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    if not ret or frame is None:
        frame = st.session_state.last_good_frame
        if frame is None:
            time.sleep(0.02); continue
        is_new_frame = False
    else:
        st.session_state.last_good_frame = frame
        is_new_frame = True

    # 야간 밝기 보정 적용 (라디오 모드에 따라)
    mode = st.session_state.get("enhance_mode", "자동")
    if mode == "강제 ON":
        frame, _ = auto_enhance(frame, force=True)
    elif mode == "자동":
        frame, _ = auto_enhance(frame, force=False)
    # "OFF" 면 그대로 통과

    st.session_state.frame_idx += 1
    frame_idx = st.session_state.frame_idx
    update_fps()
    # 사이드바 FPS/프레임 표시 갱신
    if "__fps_ph" in st.session_state:
        st.session_state["__fps_ph"].markdown(f"**FPS** &nbsp; {st.session_state.fps_display}")
        st.session_state["__frame_ph_count"].markdown(f"**프레임** &nbsp; {frame_idx}")
        # 추론 지연 — 이 값이 작을수록 검출 박스가 실제 움직임을 덜 뒤처져 따라갑니다
        if "__infer_ph" in st.session_state and async_worker is not None:
            infer_ms = async_worker.get_infer_ms()
            backend = getattr(st.session_state.detector, "backend", "-")
            st.session_state["__infer_ph"].markdown(
                f"**추론** &nbsp; {infer_ms:.0f} ms &nbsp;<sub>{backend}</sub>",
                unsafe_allow_html=True,
            )

    # 비동기 YOLO 워커에 최신 프레임 전달 → 백그라운드에서 추론
    # 메인 루프는 추론을 기다리지 않고 가장 최근 검출 결과를 사용
    if is_new_frame and async_worker is not None:
        async_worker.submit(frame)
    detections = async_worker.get_detections() if async_worker is not None else []
    st.session_state.last_detections = detections

    danger_result = check_danger(detections, roi_polygon)
    is_danger     = danger_result["is_danger"]

    now = time.time()
    event_triggered = False
    if is_danger and not st.session_state.prev_danger:
        if now - st.session_state.last_event_ts > 15.0:
            event_triggered                = True
            st.session_state.last_event_ts = now
            st.session_state.alert_msg     = "🚨 보안 구역 내 위험 감지!"
            st.session_state.alert_expires = now + 4.0
            # 경고음 재생 (HTML5 audio + autoplay, 매번 새 iframe으로 강제 재생)
            with sound_ph.container():
                components_html(
                    f'<audio autoplay src="data:audio/wav;base64,{ALERT_BEEP_B64}"></audio>',
                    height=0,
                )

    st.session_state.prev_danger = is_danger

    # ── 🚨 프레임 시각화 ───────────────────────
    annotated = frame.copy()
    annotated = draw_detections(annotated, danger_result, roi_polygon)

    if is_danger:
        # 화면 전체를 붉게 덮는 틴트 효과
        overlay = annotated.copy()
        overlay[:] = (0, 0, 255)
        cv2.addWeighted(overlay, 0.25, annotated, 0.75, 0, annotated)
        
        # 가장자리 빨간색 두꺼운 테두리
        cv2.rectangle(annotated, (0, 0), (annotated.shape[1], annotated.shape[0]), (0, 0, 255), 25)
        
        # 화면 상단(Y: 50) 정중앙에 "경고" 아주 굵고 크게(160) 출력
        annotated = draw_text_korean_centered(annotated, "경고", 50, 160, (0, 0, 255))

    # ── 이벤트 저장 ──────────────────────────────────────
    if event_triggered and not st.session_state.post_recording:
        img_name, _ = save_event_image(annotated, st.session_state.source_name)
        st.session_state.pending_img_name = img_name
        st.session_state.pre_frames       = list(st.session_state.frame_buffer)
        st.session_state.post_frames      = []
        st.session_state.post_recording   = True
        st.session_state.post_rec_start   = now

    if st.session_state.post_recording:
        st.session_state.post_frames.append(annotated.copy())
        if now - st.session_state.post_rec_start >= CLIP_POST_SEC:
            all_clip_frames = st.session_state.pre_frames + st.session_state.post_frames
            clip_name, _ = save_event_clip(all_clip_frames, st.session_state.source_name, fps=MAX_CLIP_FPS)
            log_event(st.session_state.source_name, st.session_state.pending_img_name, clip_name)

            # 메모리 즉시 해제
            del all_clip_frames
            st.session_state.post_recording = False
            st.session_state.pre_frames.clear()
            st.session_state.post_frames    = []
            st.session_state.pending_img_name = ""

    st.session_state.frame_buffer.append(annotated.copy())

    # 원격 접속 자동 감지: localhost가 아니면 해상도 축소
    display_frame = annotated
    try:
        host = st.context.headers.get("Host", "localhost")
    except Exception:
        host = "localhost"
    is_remote = "localhost" not in host and "127.0.0.1" not in host
    if is_remote:
        h_orig, w_orig = display_frame.shape[:2]
        max_w = 640
        if w_orig > max_w:
            ratio = max_w / w_orig
            display_frame = cv2.resize(display_frame, (max_w, int(h_orig * ratio)), interpolation=cv2.INTER_AREA)

    rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
    frame_ph.image(rgb, channels="RGB", use_container_width=True)

    # 영상 진행률 갱신 (파일 모드)
    if not is_rtsp and total_video_frames > 0:
        cur = int(vs.cap.get(cv2.CAP_PROP_POS_FRAMES))
        video_progress_ph.progress(
            min(cur / max(total_video_frames, 1), 1.0),
            text=f"▶ {cur}/{total_video_frames} 프레임",
        )

    persons = len(danger_result["all_persons"])
    cars    = len(danger_result["all_cars"])
    info_ph.caption(f"사람 {persons}명 | 자동차 {cars}대 | ROI {'✅' if roi_polygon is not None else '⚠️ 미설정'} | {st.session_state.source_name}")

    # ── 오른쪽 상태창 업데이트 ────────────────────────────
    if is_danger:
        status_ph.markdown("""
        <div class='status-box-danger'>
            <h2 class='danger-title'>🚨 위험 경고</h2>
            <p class='danger-sub'>보행자 감지됨!</p>
        </div>""", unsafe_allow_html=True)
    else:
        status_ph.markdown("""
        <div class='status-box-safe'>
            <h2 class='safe-title'>🟢 정상</h2>
            <p class='safe-sub'>안전 구역</p>
        </div>""", unsafe_allow_html=True)

    if now < st.session_state.alert_expires: alert_ph.error(st.session_state.alert_msg)
    else: alert_ph.empty()

    if event_triggered:
        recent = get_recent_events(5)
        if recent:
            lines = "### 📋 최근 이벤트\n"
            for ev in recent: lines += f"- `{ev['timestamp'][:19]}` **{ev['status']}**\n"
            events_ph.markdown(lines)

    # 재생 속도 조절
    if is_remote:
        time.sleep(0.2)
    elif is_rtsp:
        time.sleep(0.001)
    else:
        # 영상 파일: 원본 fps에 맞춰 sleep → 슬로우모션 방지 + 모든 프레임 표시
        target_dt = 1.0 / (st.session_state.video_fps or 30.0)
        elapsed   = time.time() - frame_start_time
        sleep_t   = target_dt - elapsed
        if sleep_t > 0:
            time.sleep(sleep_t)