# pages/4_성능_평가.py — 시스템 정량 성능 평가 페이지
# KISA 지능형 CCTV 성능시험 인증제도 평가 방식 참고

import streamlit as st
import os, sys
import pandas as pd
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.performance_eval import (
    add_record, load_records, delete_record, compute_metrics, CATEGORIES,
)

st.markdown("""
<style>
.eval-heading h1 { color:#0F172A; font-size:2.2rem; font-weight:800; margin-bottom:.2rem; }
.eval-heading p { color:#64748B; font-size:1rem; margin:0 0 1.5rem; }
[data-testid="stForm"] { padding:1.25rem; box-shadow:0 5px 18px rgba(15,23,42,.05); }
[data-testid="stDataFrame"] { border:1px solid #E2E8F0; border-radius:14px; overflow:hidden; }
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

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("정탐률 (Recall)",   f"{metrics['recall']:.1f}%",   help="실제 위험 중 시스템이 감지한 비율 (높을수록 좋음)")
m2.metric("정밀도 (Precision)", f"{metrics['precision']:.1f}%", help="시스템이 감지한 것 중 실제 위험이었던 비율")
m3.metric("오탐률 (FAR)",       f"{metrics['far']:.1f}%",       help="정상 상황을 위험으로 잘못 판단한 비율 (낮을수록 좋음)")
m4.metric("미탐률 (Miss)",      f"{metrics['miss']:.1f}%",      help="실제 위험을 놓친 비율 (낮을수록 좋음)")
m5.metric("평균 응답시간",      f"{metrics['avg_response']:.2f}s" if metrics['rt_samples'] else "—",
          help=f"이벤트 발생 → 알람까지 소요 시간 (샘플 {metrics['rt_samples']}건)")

st.markdown("---")

# ══════════════════════════════════════════════════════
# 좌: 평가 기록 추가 / 우: 카테고리별 카운트
# ══════════════════════════════════════════════════════
form_col, count_col = st.columns([2, 1])

with form_col:
    st.markdown("### ➕ 평가 기록 추가")
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

with count_col:
    st.markdown("### 🧮 카테고리별 건수")
    counts = metrics["counts"]
    total  = metrics["total"]
    for cat, n in counts.items():
        pct = (n / total * 100) if total else 0
        st.markdown(f"**{cat}** &nbsp; {n}건 ({pct:.1f}%)")
    st.markdown(f"---")
    st.markdown(f"**총 측정 건수** &nbsp; {total}건")

st.markdown("---")

# ══════════════════════════════════════════════════════
# 평가 기록 목록 (최신순)
# ══════════════════════════════════════════════════════
st.markdown("### 📋 평가 기록 목록")

if not records:
    st.info("아직 등록된 평가 기록이 없습니다. 위에서 시나리오를 추가해보세요.")
else:
    # 최신순 정렬 + DataFrame 표시
    df_records = list(reversed(records))
    df = pd.DataFrame(df_records)

    # 컬럼 한글화
    df_display = df.rename(columns={
        "timestamp":         "기록 시각",
        "scenario":          "시나리오",
        "source":            "소스",
        "result":            "분류",
        "response_time_sec": "응답시간(초)",
        "notes":             "비고",
    })
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # 개별 삭제
    with st.expander("🗑️ 기록 삭제"):
        del_ts = st.selectbox(
            "삭제할 기록 선택",
            [f"{r['timestamp']} | {r.get('scenario', '')}" for r in df_records],
        )
        if st.button("선택한 기록 삭제", type="secondary"):
            timestamp_to_del = del_ts.split(" | ")[0]
            if delete_record(timestamp_to_del):
                st.success("삭제되었습니다.")
                st.rerun()
            else:
                st.error("삭제에 실패했습니다.")

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
