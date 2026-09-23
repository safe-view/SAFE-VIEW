# core/detector.py — YOLOv8 객체 인식 모듈
# YOLOv8 모델을 불러오고, 프레임에서 person / car 를 탐지합니다.
#
# 추론 백엔드는 config.INFER_BACKEND로 고릅니다. OpenVINO로 내보낸 모델이
# 있으면 그것을 쓰고, 없으면 기존 yolov8n.pt로 그대로 동작합니다.
# 어느 쪽이든 detect()가 돌려주는 딕셔너리 형식은 동일합니다.

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    YOLO_MODEL, CONFIDENCE_THRESHOLD, CLASS_IDS, TARGET_CLASS_IDS,
    INFER_BACKEND, OPENVINO_MODEL_DIR, OPENVINO_DEVICE, INFER_IMGSZ,
)


def openvino_available() -> bool:
    """openvino 패키지가 설치돼 있고 내보낸 모델 폴더가 준비됐는지 확인합니다."""
    if not os.path.isdir(OPENVINO_MODEL_DIR):
        return False
    try:
        import openvino  # noqa: F401
    except Exception:
        return False
    return True


class Detector:
    """
    YOLOv8 기반 객체 탐지기.
    처음 생성 시 모델을 로드합니다(시간이 걸릴 수 있습니다).

    속성:
        loaded         — 모델 로드 성공 여부
        backend        — 실제로 쓰이는 백엔드 ('openvino' 또는 'pytorch')
        device         — 추론 디바이스 표기 (OpenVINO일 때만 의미 있음)
        last_infer_ms  — 가장 최근 detect() 1회에 걸린 추론 시간(ms)
        load_warning   — OpenVINO 로드에 실패해 폴백했을 때의 사유 (없으면 None)
    """

    def __init__(self, model_name: str = YOLO_MODEL, backend: str = INFER_BACKEND,
                 device: str = OPENVINO_DEVICE):
        self.loaded = False
        self.backend = "pytorch"
        self._ov_device = device.upper()   # OpenVINO 로 갔을 때 쓸 디바이스
        self.device = "CPU"                # 실제로 추론이 도는 곳 (화면 표시용)
        self.last_infer_ms = 0.0
        self.load_warning = None
        self.load_error = None

        # ultralytics 임포트는 여기서 해서 로딩 오류를 한 곳에서 처리
        try:
            from ultralytics import YOLO
        except Exception as e:
            self.load_error = str(e)
            print(f"[Detector] ultralytics 임포트 실패: {e}")
            return

        if backend not in ("auto", "openvino", "pytorch"):
            # config 오타로 조용히 느린 경로를 타는 일이 없도록 알립니다.
            print(f"[Detector] 알 수 없는 INFER_BACKEND='{backend}' → 'auto'로 처리합니다.")
            backend = "auto"

        # ── 1) OpenVINO 백엔드 시도 ────────────────────────
        # 'auto'는 준비된 경우에만, 'openvino'는 명시적으로 요청된 경우 시도합니다.
        want_openvino = backend == "openvino" or (backend == "auto" and openvino_available())
        if want_openvino:
            try:
                if not os.path.isdir(OPENVINO_MODEL_DIR):
                    raise FileNotFoundError(
                        f"내보낸 모델 폴더가 없습니다: {OPENVINO_MODEL_DIR} "
                        f"(python tools/export_openvino.py 로 생성하세요)"
                    )
                # 내보낸 디렉터리는 task를 명시해야 ultralytics가 추론기를 고를 수 있습니다.
                self.model = YOLO(OPENVINO_MODEL_DIR, task="detect")
                self.backend = "openvino"
                self.device = self._ov_device
                self.loaded = True
            except Exception as e:
                # OpenVINO 실패가 곧 "탐지 0건"이 되면 안 되므로 .pt로 폴백합니다.
                self.load_warning = f"OpenVINO 로드 실패 → PyTorch 폴백: {e}"
                print(f"[Detector] {self.load_warning}")

        # ── 2) 기존 PyTorch(.pt) 백엔드 ────────────────────
        if not self.loaded:
            try:
                self.model = YOLO(model_name)
                self.backend = "pytorch"
                self.loaded = True
            except Exception as e:
                self.load_error = str(e)
                print(f"[Detector] 모델 로드 실패: {e}")
                return

        self._warmup()

    # 워밍업에 쓰는 더미 프레임 크기 (세로, 가로)
    # OpenVINO 모델은 dynamic 으로 내보내므로 입력 형태마다 한 번씩 최적화가 일어납니다.
    # CCTV에서 흔한 16:9 와 4:3 만 미리 돌립니다 — 형태를 하나 늘릴 때마다 시작이
    # 느려지고, 특히 GPU 에서는 형태당 수십 초씩 붙습니다.
    _WARMUP_SHAPES = ((720, 1280), (960, 1280))

    def _warmup(self):
        """
        더미 프레임으로 추론을 미리 돌려 둡니다.

        OpenVINO는 첫 추론에서 모델 컴파일이 일어나 수 초가 걸릴 수 있습니다.
        그 지연이 실제 첫 위험 상황과 겹치지 않도록 로드 시점에 미리 흡수합니다.
        """
        try:
            import numpy as np
            for h, w in self._WARMUP_SHAPES:
                dummy = np.zeros((h, w, 3), dtype=np.uint8)
                self._infer(dummy, CONFIDENCE_THRESHOLD)
        except Exception as e:
            print(f"[Detector] 워밍업 건너뜀: {e}")

    def _infer(self, frame, conf: float):
        """
        추론 1회. 클래스·신뢰도 필터를 NMS 단계로 내려보내 후처리할 박스 수를 줄입니다.
        (파이썬 쪽 필터는 detect()에 안전망으로 그대로 남아 있습니다.)
        """
        kwargs = {}
        if self.backend == "openvino":
            # 디바이스를 명시하지 않으면 ultralytics 가 "AUTO"를 쓰는데,
            # 측정 결과 AUTO 가 CPU 직접 지정보다 느렸습니다(config 주석 참고).
            kwargs["device"] = f"intel:{self.device.lower()}"
        return self.model(
            frame,
            verbose=False,
            imgsz=INFER_IMGSZ,
            conf=conf,
            classes=TARGET_CLASS_IDS,
            **kwargs,
        )[0]

    def detect(self, frame, conf: float = CONFIDENCE_THRESHOLD) -> list[dict]:
        """
        프레임에서 객체를 탐지하고 결과 리스트를 반환합니다.

        반환 형식 (각 항목):
        {
            'class_id':      int,        # COCO 클래스 ID
            'class_name':    str,        # 'person' 또는 'car' 등
            'confidence':    float,      # 신뢰도 0~1
            'bbox':          (x1,y1,x2,y2),
            'center':        (cx, cy),   # 박스 중심점
            'bottom_center': (cx, y2),   # 박스 하단 중심점 (발 위치)
        }
        """
        if not self.loaded:
            return []

        try:
            started = time.perf_counter()
            results = self._infer(frame, conf)
            self.last_infer_ms = (time.perf_counter() - started) * 1000.0
        except Exception as e:
            print(f"[Detector] 추론 오류: {e}")
            return []

        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in TARGET_CLASS_IDS:
                continue
            confidence = float(box.conf[0])
            if confidence < conf:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            # 오토바이(motorcycle)는 car 클래스로 통합 매핑
            # → 위험 판단, 정지차량 판정, 시각화 모두 car와 동일하게 처리됨
            class_name = CLASS_IDS.get(cls_id, "unknown")
            if class_name == "motorcycle":
                class_name = "car"

            detections.append({
                "class_id":      cls_id,
                "class_name":    class_name,
                "confidence":    round(confidence, 2),
                "bbox":          (x1, y1, x2, y2),
                "center":        (cx, cy),
                "bottom_center": (cx, y2),   # 발 위치로 ROI 판단에 사용
            })

        return detections
