# 세이프뷰(SAFEVIEW)
2026년 캡스톤 디자인
AI 기반 사각지대 위험 감지 시스템

도로변 주차 차량으로 인해 시야가 안 보이는 골목이나 노상공영주차장에서, CCTV 영상으로 사람 및 차량을 인식하고 경고로직 ROI 안에 둘 다 있을 때 경고를 띄우는 시스템이다.


## 기능

- CCTV 실시간 영상(RTSP) 로딩 또는 로컬 영상 파일 입력
- YOLOv8로 사람과 차량 인식
- ROI(관심 구역)를 마우스로 직접 그려서 저장
- 사람+차량+ROI 동시 존재 → 위험 판정
- 위험 시 화면 빨간 테두리, 경고음, 이벤트 저장 (전 5초 + 후 10초 클립)
- 이벤트 다시보기 페이지 (캘린더 형태로 날짜 선택)
- CCTV 여러 대를 프리셋으로 등록해두고 토글로 전환
- Cloudflare Tunnel로 외부 공유 가능


## 사용 기술

Python 3.13, Streamlit, YOLOv8 (Ultralytics), OpenCV, Pillow, NumPy, pandas, imageio-ffmpeg, streamlit-image-coordinates.

외부 공유는 cloudflared 사용. 모델은 yolov8n.pt (가벼운 nano 버전, 자동 다운로드됨).


## 폴더 구조

```
blind_spot_safety/
  app.py             # 진입점
  config.py          # 설정값
  requirements.txt
  core/
    detector.py      # YOLOv8 인식
    roi_manager.py   # ROI 저장/불러오기
    video_source.py  # RTSP/파일 입력
    danger_logic.py  # 위험 판단
    event_saver.py   # 이미지/클립/로그 저장
    rtsp_presets.py  # 다중 CCTV 프리셋
  pages/
    0_대시보드.py
    1_모니터링.py
    2_ROI_설정.py
    3_이벤트_다시보기.py
```

`data/`, `saved_events/`, `roi_configs/`, `logs/` 폴더는 실행 시 자동 생성된다.


## 실행 방법

```
git clone https://github.com/Mingoon77/SAFE-VIEW.git
cd SAFE-VIEW
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

자동으로 http://localhost:8501 이 열린다.

### 추론 속도 높이기 (선택)

모니터링 화면은 최신 프레임 1장만 남기고 추론하므로, **추론 1회에 걸리는 시간**이 곧 검출 박스가 실제 움직임보다 얼마나 뒤처지는지를 결정한다. 이 시간을 줄이려고 OpenVINO 런타임 경로를 넣어 뒀다.

기본값은 기존과 같은 PyTorch(`INFER_BACKEND = "pytorch"`)다. **측정해 보고 켜야 한다.**

```
python tools/export_openvino.py     # yolov8n_openvino_model/ 생성 (한 번만)
python tools/bench_detector.py      # 백엔드별 추론 지연 비교
python tools/verify_detector.py     # 결과·위험 판정이 그대로인지 검증
```

Intel Core Ultra 5 125H / Windows 11 에서 측정한 결과는 다음과 같다.

| 구성 | 추론 지연 | PyTorch 대비 |
|---|---|---|
| PyTorch (기본값) | 약 60 ms | 기준 |
| OpenVINO CPU | 95~124 ms | **느려짐** |
| OpenVINO GPU | 약 25 ms | **2.5배 빠름** (첫 로드 40~80초) |

CPU에서 느린 이유는 ultralytics가 Windows에서 OpenVINO CPU 정밀도를 FP32로 고정하기 때문이다. 쓸 만한 구성은 Intel 내장 그래픽(GPU)뿐이고, 대신 앱을 켤 때마다 커널 컴파일로 40~80초가 걸린다. 상시 감시용이면 켤 만하고, 자주 껐다 켜는 개발·시연 중에는 기본값이 낫다.

켜려면 `config.py`에서 `INFER_BACKEND = "openvino"`, `OPENVINO_DEVICE = "GPU"` 로 바꾼다. `openvino`가 없거나 모델을 내보내지 않았으면 자동으로 `yolov8n.pt`로 되돌아가므로 이 단계를 건너뛰어도 된다. 생성된 모델 폴더는 커밋하지 않는다.

위 수치는 PC 한 대 기준이므로, 자기 PC에서 `tools/bench_detector.py`로 직접 재보고 판단하면 된다.

CCTV를 쓰려면 rtsp_presets.json 파일을 만들어서 RTSP 주소를 등록하면 된다. 형식은 다음과 같다.

```json
[
  { "name": "주차장 입구", "url": "rtsp://아이디:비밀번호@IP:554/Streaming/Channels/102" }
]
```


## 위험 판단 규칙

| 감지 조건 | 위치 | 결과 |
|----------|------|------|
| 사람 + 차량 둘 다 | ROI 안 | 위험 |
| 사람 + 차량 둘 다 | ROI 밖 | 정상 |
| 사람만 | 무관 | 정상 |
| 차량만 | 무관 | 정상 |


## 개발에 AI를 사용한 부분

이번 프로젝트는 Claude(Anthropic의 AI 코딩 어시스턴트)와 GPT(CODEX)를 적극적으로 활용해서 진행하였따.

AI 활용 업무:
- 초기 코드 및 구조 생성 (Streamlit 페이지 구성, OpenCV/YOLOv8 연동 코드 등)
- 오류 메시지 분석 및 해결 방법 제안
- UI 디자인 코드 (CSS, 레이아웃)
- Git push, 폴더 정리 같은 반복 작업 자동화

우리가 직접 진행한 업무:
- 요구사항 정의 (어떤 기능이 필요한지, 어떤 화면이 되어야 하는지)
- 시스템 동작 흐름 설계 (입력 → 처리 → 출력 구조)
- 자택 CCTV(RTSP) 연동 및 실제 환경 테스트
- ROI 설정 방식, 위험 판정 기준 같은 핵심 로직 결정
- 코드의 동작 검증 및 수정
- 팀원 및 교수님 피드백 반영

사용한 라이브러리(Streamlit, YOLOv8, OpenCV 등)의 구조나 동작 원리는 작업하면서 같이 학습했다. 단순히 코드를 복붙하는 게 아니라, 왜 이렇게 동작하는지 이해하면서 진행했다.


## 라이센스

학술 목적으로 만든 캡스톤 졸업작품이라 사용한 오픈소스의 라이센스는 모두 준수했다. 자세한 분석은 별도 "오픈소스 활용 보고서"에 정리했다.

주요 라이센스:
- Ultralytics YOLOv8: AGPL-3.0 (소스 공개 의무)
- Streamlit, OpenCV, OpenVINO, Cloudflare Tunnel: Apache 2.0
- NumPy, pandas: BSD-3-Clause
- Pillow: HPND
- streamlit-image-coordinates: MIT
- imageio-ffmpeg: BSD-2-Clause (번들 FFmpeg는 LGPL-2.1+)

상업 용도로 쓰려면 YOLOv8 라이센스 때문에 모델 교체나 별도 라이센스 구매가 필요하다.
