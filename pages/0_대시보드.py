# pages/0_대시보드.py — 대시보드 (홈 화면)

import streamlit as st
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import EVENTS_DIR, ROI_DIR, DATA_DIR

st.title("🚨 도로변 사각지대 보행자 위험 감지 및 시청각 경고 시스템")
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ### 프로젝트 개요

    생활도로·골목·주차장·도로변 주차 구간에서 **주차 차량 및 구조물**로 인해 시야가 제한되는 환경에서
    CCTV 또는 저장 영상으로 **사람과 차량을 실시간 인식**하고,
    사용자가 지정한 **ROI(관심구역) 내 위험 상황**을 감지하여
    화면 및 청각 경고와 이벤트 클립 영상을 저장하는 프로토타입입니다.

    ---
    ### 사용 방법

    1. **👈 왼쪽 사이드바**에서 페이지를 선택하세요.
    2. **🗺️ ROI 설정** 페이지에서 관심구역을 먼저 설정하세요.
    3. **🎥 모니터링** 페이지에서 영상을 선택하고 감지를 시작하세요.

    ---
    ### 위험 판단 규칙

    | 조건 | 상태 |
    |------|------|
    | 아무것도 없음 | 🟢 정상 |
    | 사람만 있음 | 🟢 정상 |
    | 자동차만 있음 | 🟢 정상 |
    | 사람 + 자동차, 사람이 ROI 밖에 위치 | 🟢 정상 |
    | **사람 + 자동차, 사람이 ROI 안에 위치** | 🔴 **위험** |
    """)

with col2:
    st.markdown("### 시스템 상태")

    roi_count = len([f for f in os.listdir(ROI_DIR) if f.endswith(".json")]) if os.path.exists(ROI_DIR) else 0
    with st.container(border=True):
        st.caption("🗺️ 저장된 ROI")
        st.markdown(f"### {roi_count}개")

    event_count = len([f for f in os.listdir(EVENTS_DIR) if f.endswith(".jpg")]) if os.path.exists(EVENTS_DIR) else 0
    with st.container(border=True):
        st.caption("🖼️ 저장된 이벤트 이미지")
        st.markdown(f"### {event_count}개")

    data_count = len([f for f in os.listdir(DATA_DIR) if f.endswith((".mp4", ".avi", ".mov"))]) if os.path.exists(DATA_DIR) else 0
    with st.container(border=True):
        st.caption("🎬 샘플 영상 파일")
        st.markdown(f"### {data_count}개")

    st.markdown("---")
    st.markdown("""
    **기술 스택**
    - 🐍 Python + Streamlit
    - 👁️ YOLOv8 (Ultralytics)
    - 📹 OpenCV
    """)

st.markdown("---")
st.info("💡 **시작 전 확인:** 테스트용 영상 파일(.mp4)은 미리 `data/` 폴더에 넣어주세요. YOLOv8 모델은 처음 실행할 때 자동으로 다운로드됩니다.")
