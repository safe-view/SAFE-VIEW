# pages/4_성능_평가.py — 시스템 정량 성능 평가 페이지
# KISA 지능형 CCTV 성능시험 인증제도 평가 방식 참고

import streamlit as st
import os, sys
import subprocess
import pandas as pd
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.performance_eval import (
    add_record, load_records, delete_record, compute_metrics, CATEGORIES,
)
from core.ground_truth import DATA_DIR, load_ground_truth, save_intervals, video_files
from core.roi_manager import load_rois
from core.video_playback import get_playable_video, get_video_duration_seconds

st.markdown("""
<style>
.eval-heading h1 { color:#0F172A; font-size:2.2rem; font-weight:800; margin-bottom:.2rem; }
.eval-heading p { color:#64748B; font-size:1rem; margin:0 0 1.5rem; }
[data-testid="stForm"] { padding:1.25rem; box-shadow:0 5px 18px rgba(15,23,42,.05); }
[data-testid="stDataFrame"] { border:1px solid #E2E8F0; border-radius:14px; overflow:hidden; }
[data-testid="stMetric"] { min-height:135px; }
[data-testid="stTextInput"] input, [data-baseweb="select"] > div,
[data-testid="stNumberInput"] input, [data-testid="stTextArea"] textarea {
    border-color:#CBD5E1 !important; border-radius:10px !important;
}
</style>
<div class="eval-heading">
    <h1>📊 시스템 성능 평가</h1>
    <p>KISA 지능형 CCTV 성능시험 인증제도 평가 방식을 참고한 정량 성능 기록입니다.</p>
</div>
""", unsafe_allow_html=True)

# session_state 초기화
if "eval_added_msg" not in st.session_state:
    st.session_state.eval_added_msg = ""

# ══════════════════════════════════════════════════════
# 상단: 핵심 지표
# ══════════════════════════════════════════════════════
records = load_records()
metrics = compute_metrics(records)

st.markdown("### 📈 종합 성능 지표")

counts = metrics["counts"]
total = metrics["total"]


def _pct(count):
    return f"{(count / total * 100):.1f}%" if total else "0.0%"


metric_cols = st.columns(7)

metric_cols[0].metric(
    "정탐률 (Recall)",
    f"{metrics['recall']:.1f}%",
    delta=f"정탐(TP) {counts['정탐 (TP)']}건 ({_pct(counts['정탐 (TP)'])})",
    delta_color="off",
    help="실제 위험 중 시스템이 감지한 비율 (높을수록 좋음)",
)
metric_cols[1].metric(
    "정밀도 (Precision)",
    f"{metrics['precision']:.1f}%",
    help="시스템이 감지한 것 중 실제 위험이었던 비율",
)
metric_cols[2].metric(
    "오탐률 (FAR)",
    f"{metrics['far']:.1f}%",
    delta=f"오탐(FP) {counts['오탐 (FP)']}건 ({_pct(counts['오탐 (FP)'])})",
    delta_color="off",
    help="정상 상황을 위험으로 잘못 판단한 비율 (낮을수록 좋음)",
)
metric_cols[3].metric(
    "미탐률 (Miss)",
    f"{metrics['miss']:.1f}%",
    delta=f"미탐(FN) {counts['미탐 (FN)']}건 ({_pct(counts['미탐 (FN)'])})",
    delta_color="off",
    help="실제 위험을 놓친 비율 (낮을수록 좋음)",
)
metric_cols[4].metric("정상 (TN)", f"{counts['정상 (TN)']}건 ({_pct(counts['정상 (TN)'])})")
metric_cols[5].metric(
    "평균 응답시간",
    f"{metrics['avg_response']:.2f}s" if metrics["rt_samples"] else "—",
    help=f"이벤트 발생 → 알람까지 소요 시간 (샘플 {metrics['rt_samples']}건)",
)
metric_cols[6].metric("총 측정 건수", f"{total}건")

st.markdown("---")

# ══════════════════════════════════════════════════════
# 평가 기록 목록 (최신순)
# ══════════════════════════════════════════════════════
st.markdown("### 📋 평가 기록 목록")


@st.dialog("삭제 확인")
def _confirm_delete_dialog(pending_ids):
    st.warning(f"선택한 {len(pending_ids)}건을 삭제하시겠습니까?")
    confirm_col, cancel_col = st.columns(2)
    if confirm_col.button(
        "삭제", key="eval_delete_confirm", type="primary", use_container_width=True
    ):
        failed_ids = [record_id for record_id in pending_ids if not delete_record(record_id)]
        st.session_state.eval_delete_pending = []
        if failed_ids:
            st.error(f"{len(failed_ids)}건을 삭제하지 못했습니다.")
        else:
            st.success(f"{len(pending_ids)}건이 삭제되었습니다.")
        st.rerun()
    if cancel_col.button("취소", key="eval_delete_cancel", use_container_width=True):
        st.session_state.eval_delete_pending = []
        st.rerun()

if not records:
    st.info("아직 등록된 평가 기록이 없습니다. 위에서 시나리오를 추가해보세요.")
else:
    # 최신순 정렬 + DataFrame 표시
    df_records = list(reversed(records))
    df = pd.DataFrame(df_records).set_index("id")
    df["timestamp"] = df["timestamp"].str[:16]
    df.insert(0, "선택", False)

    # 컬럼 한글화
    df_display = df.rename(columns={
        "timestamp":         "기록 시각",
        "scenario":          "시나리오",
        "source":            "소스",
        "result":            "분류",
        "response_time_sec": "응답시간(초)",
        "notes":             "비고",
    })
    delete_col, _ = st.columns([1, 5])
    delete_button = delete_col.empty()
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=290,
        disabled=[column for column in df_display.columns if column != "선택"],
        key="eval_records_editor",
    )
    selected_ids = edited_df.index[edited_df["선택"]].tolist()

    if delete_button.button("🗑️ 삭제", use_container_width=True):
        if selected_ids:
            st.session_state.eval_delete_pending = selected_ids
        else:
            st.warning("삭제할 기록을 선택하세요.")

    pending_ids = st.session_state.get("eval_delete_pending", [])
    if pending_ids:
        _confirm_delete_dialog(pending_ids)

st.markdown("---")

# ══════════════════════════════════════════════════════
# 성능 자동평가 - 위험 발생 구간 입력
# ══════════════════════════════════════════════════════
st.markdown("### 🎯 성능 자동평가 - 위험 발생 구간 입력")

videos = video_files()
if not videos:
    st.info("data 폴더에 재생할 영상이 없습니다.")
else:
    selected_video = st.selectbox("영상 선택", videos, key="ground_truth_video")

    if load_rois(os.path.splitext(selected_video)[0]) is None:
        st.warning("⚠️ ROI가 없습니다 — ROI 설정 페이지에서 먼저 저장하세요.")

    if st.session_state.get("ground_truth_loaded_video") != selected_video:
        try:
            saved_intervals = load_ground_truth().get(selected_video, [])
        except ValueError as exc:
            st.error(str(exc))
            saved_intervals = []
        st.session_state.ground_truth_intervals = list(saved_intervals)
        st.session_state.ground_truth_loaded_video = selected_video
        st.session_state.ground_truth_seek = 0.0

    with st.spinner("미디어 로딩 중..."):
        playable = get_playable_video(
            str(DATA_DIR / selected_video),
            cache_dir=str(DATA_DIR / "_converted"),
            timeout_sec=120.0,
        )
    if playable:
        duration = get_video_duration_seconds(playable)
        if duration is None or duration <= 0:
            duration = 300.0
            st.caption("영상 길이를 확인할 수 없어 기본 범위를 사용합니다.")

        seek_sec = min(
            float(st.session_state.get("ground_truth_seek", 0.0)),
            duration,
        )
        with open(playable, "rb") as video_file:
            st.video(video_file.read(), start_time=seek_sec)
        seek_sec = st.slider(
            "🔎 위치 탐색(초) — 시작초/종료초를 입력할 위치를 드래그 하거나 클릭하세요",
            min_value=0.0,
            max_value=float(duration),
            step=0.1,
            key="ground_truth_seek",
        )

        start_seek_col, end_seek_col = st.columns(2)
        if start_seek_col.button("⏮ 이 위치를 시작초로", use_container_width=True):
            st.session_state.ground_truth_start = seek_sec
            st.rerun()
        if end_seek_col.button("⏭ 이 위치를 종료초로", use_container_width=True):
            st.session_state.ground_truth_end = seek_sec
            st.rerun()
    else:
        st.error("스트리밍 변환에 실패했습니다. 영상 파일을 확인하세요.")

    intervals = st.session_state.get("ground_truth_intervals", [])
    st.markdown("#### 입력된 위험 구간")
    if intervals:
        for index, (start, end) in enumerate(intervals):
            interval_col, delete_col = st.columns([5, 1])
            interval_col.write(f"{start:g}초 ~ {end:g}초")
            if delete_col.button("삭제", key=f"delete_ground_truth_{index}"):
                intervals.pop(index)
                st.session_state.ground_truth_intervals = intervals
                st.rerun()
    else:
        st.info("입력된 위험 구간이 없습니다. 이 상태로 저장하면 정상 영상으로 기록됩니다.")

    start_col, end_col = st.columns(2)
    start_sec = start_col.number_input(
        "시작초", min_value=0.0, step=0.1, key="ground_truth_start"
    )
    end_sec = end_col.number_input(
        "종료초", min_value=0.0, step=0.1, key="ground_truth_end"
    )

    if saved_message := st.session_state.pop("ground_truth_saved_message", ""):
        st.success(saved_message)

    if st.button("💾 구간 저장", type="primary", use_container_width=True):
        intervals_to_save = list(intervals)
        if start_sec == 0.0 and end_sec == 0.0:
            pass
        elif end_sec <= start_sec:
            st.error("종료초는 시작초보다 커야 합니다.")
            intervals_to_save = None
        else:
            intervals_to_save.append((float(start_sec), float(end_sec)))

        if intervals_to_save is not None:
            try:
                save_intervals(selected_video, intervals_to_save)
                st.session_state.ground_truth_intervals = intervals_to_save
                st.session_state.ground_truth_saved_message = (
                    f"'{selected_video}'의 위험 발생 구간을 저장했습니다."
                )
                st.rerun()
            except (OSError, ValueError) as exc:
                st.error(f"저장에 실패했습니다: {exc}")

    st.caption("자동 평가 전에 먼저 '구간 저장'을 눌러 정답지를 저장하세요.")

    if eval_result := st.session_state.pop("ground_truth_eval_result", None):
        if eval_result["returncode"] == 0:
            st.success("자동 평가가 완료됐습니다. 📋 평가 기록 목록에 반영됨")
            log_title = "실행 로그 보기"
        else:
            st.error("자동 평가 실행 실패. 구간 저장을 먼저 해주세요.")
            log_title = "오류 로그 보기"
        with st.expander(log_title):
            output_parts = []
            if eval_result["stdout"]:
                output_parts.append(eval_result["stdout"])
            if eval_result["stderr"]:
                output_parts.append(eval_result["stderr"])
            st.code("\n".join(output_parts) or "(출력 없음)")

    if st.button("🧮 자동 평가 실행", use_container_width=True):
        with st.spinner(
            f"'{selected_video}' 평가 중 — 영상 길이에 따라 다소 걸릴 수 있습니다..."
        ):
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        os.path.join(ROOT, "tools", "auto_eval.py"),
                        "--video",
                        selected_video,
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=ROOT,
                )
                eval_result = {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            except OSError as exc:
                eval_result = {
                    "returncode": -1,
                    "stdout": "",
                    "stderr": str(exc),
                }
        st.session_state.ground_truth_eval_result = eval_result
        st.rerun()

st.markdown("---")

# ══════════════════════════════════════════════════════
# 평가 기록 수동 추가
# ══════════════════════════════════════════════════════
st.markdown("### ➕ 평가기록 수동 추가")
show_manual_form = st.toggle("입력창 열기", key="eval_manual_form_toggle")
if show_manual_form:
    with st.form("eval_form", clear_on_submit=True):
        scenario  = st.text_input("시나리오명", placeholder="예: 골목 보행자 등장, 주차장 차량 접근")
        source    = st.text_input("영상 소스",   placeholder="예: 카메라03, sample.mp4")
        c1, c2    = st.columns(2)
        result    = c1.selectbox("결과 분류", CATEGORIES,
                                 help="정탐: 위험 O 감지 O / 오탐: 위험 X 감지 O / 미탐: 위험 O 감지 X / 정상: 위험 X 감지 X")
        resp_time = c2.number_input("응답시간 (초)", min_value=0.0, max_value=60.0, value=0.0, step=0.1,
                                     help="이벤트 발생부터 알람까지 걸린 시간")
        notes     = st.text_area("비고", placeholder="환경 조건, 특이사항 등", height=80)

        submitted = st.form_submit_button("기록 추가", type="primary", use_container_width=True)
        if submitted:
            if not scenario.strip():
                st.error("시나리오명을 입력하세요.")
            else:
                if add_record(scenario, source, result, resp_time, notes):
                    st.session_state.eval_added_msg = f"✅ '{scenario}' 기록이 추가되었습니다."
                    st.rerun()
                else:
                    st.error("기록 추가에 실패했습니다.")

if st.session_state.eval_added_msg:
    st.success(st.session_state.eval_added_msg)
    st.session_state.eval_added_msg = ""

st.markdown("---")

# ══════════════════════════════════════════════════════
# 평가 방법 안내
# ══════════════════════════════════════════════════════
with st.expander("ℹ️ 평가 방법 안내 (KISA 인증 기준 참고)"):
    st.markdown("""
##### 분류 기준

| 분류 | 실제 위험 | 시스템 감지 | 설명 |
|------|----------|------------|------|
| 정탐 (TP) | O | O | 위험을 정확히 잡아낸 경우 |
| 오탐 (FP) | X | O | 정상 상황을 위험으로 잘못 알람한 경우 |
| 미탐 (FN) | O | X | 위험 상황을 놓친 경우 |
| 정상 (TN) | X | X | 정상 상황을 정상으로 정확히 판단한 경우 |

##### 지표 계산식

- 정탐률 (Recall)    = TP / (TP + FN) × 100
- 정밀도 (Precision) = TP / (TP + FP) × 100
- 오탐률 (FAR)       = FP / (FP + TN) × 100
- 미탐률 (Miss)      = FN / (TP + FN) × 100

##### 평가 절차

1. 테스트 영상 또는 실제 환경에서 다양한 시나리오를 실행합니다.
2. 각 시나리오에 대해 실제 위험 여부(O/X)와 시스템 감지 여부(O/X)를 확인합니다.
3. 그 결과를 위 폼에 입력하여 카테고리(TP/FP/FN/TN)로 기록합니다.
4. 응답시간은 이벤트 발생 시점부터 알람이 울리기까지의 시간을 측정합니다.
5. 누적된 기록을 바탕으로 시스템 성능 지표가 자동 계산됩니다.
""")
