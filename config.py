# config.py — 전역 설정값 모음
# 여기서 모델명, 폴더 경로, 감지 임계값 등을 한곳에서 관리합니다.

import os

# ── 모델 설정 ──────────────────────────────────────────
YOLO_MODEL = "yolov8n.pt"          # 가장 가벼운 YOLOv8 nano 모델 (자동 다운로드)
CONFIDENCE_THRESHOLD = 0.4         # 객체 인식 최소 신뢰도 (0~1)

# COCO 데이터셋 클래스 ID (YOLOv8 기본값)
CLASS_IDS = {
    0: "person",
    2: "car",
    3: "motorcycle",
    7: "truck",
}
# 이번 프로토타입에서 실제로 감지할 클래스 (오토바이는 car 클래스로 통합 처리)
TARGET_CLASS_IDS = [0, 2, 3]       # person, car, motorcycle

# ── 폴더 경로 ──────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DATA_DIR        = os.path.join(BASE_DIR, "data")
EVENTS_DIR      = os.path.join(BASE_DIR, "saved_events")
ROI_DIR         = os.path.join(BASE_DIR, "roi_configs")
LOGS_DIR        = os.path.join(BASE_DIR, "logs")
LOG_FILE        = os.path.join(LOGS_DIR, "events_log.csv")

# ── 추론 백엔드 설정 ───────────────────────────────────
# 탐지 정확도가 아니라 "프레임당 추론 지연"을 줄이기 위한 설정입니다.
# 모니터링 화면은 최신 프레임 1장만 남기고 추론하므로, 추론이 빠를수록
# 검출 박스가 실제 움직임을 덜 뒤처져 따라가고 위험 판정도 더 빨리 나옵니다.
#
# 기본값이 "pytorch" 인 이유 — 측정 결과입니다(Intel Core Ultra 5 125H, Windows 11).
#   PyTorch CPU        60 ms   ← 기준
#   OpenVINO CPU   95~110 ms   느려짐. ultralytics 가 Windows 에서 OpenVINO CPU
#                              정밀도를 FP32 로 고정해(nn/backends/openvino.py)
#                              FP16 내보내기의 이점이 사라집니다.
#   OpenVINO GPU       25 ms   2.5배 빠름. 단 첫 로드에 커널 컴파일로 40~80초.
# 즉 CPU에서는 OpenVINO 가 이득이 아니므로 켜지 않는 것이 기본입니다.
# 자기 PC에서는 `python tools/bench_detector.py` 로 직접 재본 뒤 바꾸세요.
#
# "pytorch"  : 기존 동작 (기본값)
# "openvino" : OpenVINO 사용. 실패하면 .pt 로 폴백하고 경고를 남깁니다.
# "auto"     : 내보낸 모델이 있고 openvino 가 설치돼 있으면 OpenVINO, 아니면 .pt
INFER_BACKEND      = "pytorch"
OPENVINO_MODEL_DIR = os.path.join(BASE_DIR, "yolov8n_openvino_model")
# OpenVINO 를 쓸 때의 디바이스. 반드시 명시합니다 — ultralytics 기본값 "AUTO" 는
# 측정에서 직접 지정보다 느렸습니다.
#   "GPU" : Intel 내장 그래픽. 위 측정에서 유일하게 이득이 난 구성입니다.
#   "CPU" : 이 프로젝트 측정에서는 PyTorch 보다 느렸습니다.
#   "NPU" : 지원 안 됨 — dynamic shape 모델을 읽지 못합니다.
OPENVINO_DEVICE    = "GPU"
INFER_IMGSZ        = 640           # 추론 입력 해상도 — 내보내기 imgsz와 반드시 일치해야 함

# ── 차량 추적 설정 ─────────────────────────────────────
# ByteTrack 으로 차량마다 ID를 붙입니다. 정지차량 판정은 "이 차가 10초간
# 안 움직였나"를 봐야 하는데, ID가 없으면 검출이 한 번 끊길 때마다 그 이력이
# 사라져 판정이 깜빡입니다.
#
# 측정(시나리오1 351프레임): 추론 지연 45.9ms → 47.1ms (+2.6%) 로 비용이 거의
# 없고, 상위 ID는 351프레임 내내 끊기지 않았습니다. OpenVINO 백엔드에서도
# 동작합니다. BoT-SORT 는 +55% 인데 ID 품질 차이가 없어 쓰지 않습니다.
#
# False 로 두면 추적 없이 기존 거리 기반 매칭으로 동작합니다.
USE_TRACKER        = True
TRACKER_CONFIG     = "bytetrack.yaml"   # ultralytics 에 동봉된 설정

# ── 영상 처리 설정 ─────────────────────────────────────
FRAME_SKIP      = 2       # N 프레임마다 1번 YOLO 실행 (부하 감소)
CLIP_PRE_SEC    = 5       # 이벤트 발생 전 몇 초 저장
CLIP_POST_SEC   = 10      # 이벤트 발생 후 몇 초 저장
MAX_CLIP_FPS    = 10      # 저장 클립 FPS

# ── ROI 박스 색상 (BGR) ────────────────────────────────
COLOR_ROI        = (0, 255, 255)   # 노란색 (ROI 테두리)
COLOR_NORMAL     = (0, 200, 0)     # 초록색 (정상 바운딩 박스)
COLOR_DANGER     = (0, 0, 220)     # 빨간색 (위험 바운딩 박스)
COLOR_WARNING_BG = (0, 0, 180)     # 경고 오버레이 색상

# ── 미리 정의된 예시 소스 (드롭다운에서 선택 가능) ─────
PRESET_SOURCES = {
    "샘플 영상 (data 폴더에서 선택)": "__file__",
    "자택 CCTV (RTSP 직접 입력)":    "__rtsp__",
}
