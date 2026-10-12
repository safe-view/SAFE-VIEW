"""추론 백엔드를 바꿔도 기존 동작이 보존되는지 검증합니다.

OpenVINO 백엔드는 "같은 결과를 더 빨리" 내는 것이 목적이므로, 속도(벤치마크)와
별개로 아래 네 가지가 유지돼야 합니다.

    A1 — openvino 가 없거나 모델을 안 내보낸 환경에서 기존대로 동작하는가
    A4 — 위험 판정 6개 사례가 기존과 같은 답을 내는가
    R1 — ROI 가 여러 개일 때(도로 양쪽 보행 구역) 판정·구역 인덱스가 맞는가
    R2 — 여러 구역 저장·불러오기와 구형식 ROI 파일 호환
    A5 — 워밍업 덕분에 첫 프레임에서 멈추지 않는가
    A8 — detect() 반환 딕셔너리 형식이 그대로인가
         (`track_id` 는 추적 도입 때 추가된 키로, 추적이 꺼져 있으면 None)

    python tools/verify_detector.py

종료 코드 0 이면 전부 통과입니다.
"""

import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import config
from core.danger_logic import check_danger
from core.detector import Detector

DETECT_KEYS = {"class_id", "class_name", "confidence", "bbox", "center",
               "bottom_center", "track_id"}
_fails: list[str] = []


def check(label: str, ok: bool, detail: str = ""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        _fails.append(label)


def sample_frame():
    """ultralytics 에 동봉된 샘플 이미지 (사람·차량이 찍혀 있음). 다운로드 없음."""
    import cv2
    from ultralytics.utils import ASSETS
    for name in ("bus.jpg", "zidane.jpg"):
        path = os.path.join(str(ASSETS), name)
        if os.path.isfile(path):
            img = cv2.imread(path)
            if img is not None:
                return img
    raise SystemExit("샘플 이미지를 찾지 못했습니다. ultralytics 설치를 확인하세요.")


def fake_det(name: str, cx: int, cy: int, parked: bool = False) -> dict:
    """위험 판정 사례용 가짜 탐지 결과 (발 위치는 bottom_center)."""
    return {"class_id": 0 if name == "person" else 2, "class_name": name,
            "confidence": 0.9, "bbox": (cx - 20, cy - 40, cx + 20, cy),
            "center": (cx, cy - 20), "bottom_center": (cx, cy), "is_parked": parked}


def verify_warmup(frame) -> list[dict]:
    print("\n[A5] 첫 프레임 지연 (워밍업 효과)")
    started = time.perf_counter()
    det = Detector()
    load_s = time.perf_counter() - started
    if not det.loaded:
        check("모델 로드", False, det.load_error or "")
        return []

    started = time.perf_counter()
    detections = det.detect(frame)
    first_ms = (time.perf_counter() - started) * 1000
    det.detect(frame)
    steady_ms = det.last_infer_ms

    print(f"       백엔드={det.backend} device={det.device} 로드+워밍업 {load_s:.1f}s")
    # 첫 추론이 이후 추론과 같은 자릿수면 워밍업이 컴파일 비용을 흡수한 것입니다.
    check("첫 detect 가 정상 추론 시간 범위", first_ms < steady_ms * 3 + 50,
          f"첫 {first_ms:.1f} ms / 이후 {steady_ms:.1f} ms")
    return detections


def verify_format(detections: list[dict]):
    print("\n[A8] detect() 반환 형식")
    if not detections:
        check("탐지 결과가 있어야 형식 검증 가능", False)
        return
    check("키 집합 일치", all(set(d) == DETECT_KEYS for d in detections),
          f"{len(detections)}건")
    check("값 타입·파생값 규칙 일치", all(
        isinstance(d["class_id"], int) and isinstance(d["class_name"], str)
        and isinstance(d["confidence"], float)
        and len(d["bbox"]) == 4 and all(isinstance(v, int) for v in d["bbox"])
        and d["center"] == ((d["bbox"][0] + d["bbox"][2]) // 2,
                            (d["bbox"][1] + d["bbox"][3]) // 2)
        and d["bottom_center"] == (d["center"][0], d["bbox"][3])
        for d in detections))
    check("confidence 소수 2자리 반올림",
          all(round(d["confidence"], 2) == d["confidence"] for d in detections))
    check("클래스가 TARGET_CLASS_IDS 안에만 있음",
          all(d["class_id"] in config.TARGET_CLASS_IDS for d in detections))
    check("motorcycle → car 통합 유지",
          all(d["class_name"] != "motorcycle" for d in detections))


def verify_danger():
    print("\n[A4] 위험 판정 6개 사례")
    roi = np.array([(100, 100), (500, 100), (500, 500), (100, 500)], dtype=np.int32)
    cases = [
        ("정상 (아무것도 없음)",   [],                                                    False),
        ("사람만 (ROI 안)",        [fake_det("person", 300, 300)],                        False),
        ("차량만 (ROI 안)",        [fake_det("car", 300, 300)],                           False),
        ("ROI 밖 사람+차량",       [fake_det("person", 800, 800), fake_det("car", 820, 800)], False),
        ("ROI 안 사람+차량",       [fake_det("person", 300, 300), fake_det("car", 320, 300)], True),
        ("ROI 안 사람+정지차량",   [fake_det("person", 300, 300),
                                    fake_det("car", 320, 300, parked=True)],              False),
    ]
    for label, detections, expected in cases:
        got = check_danger(detections, roi)["is_danger"]
        check(label, got == expected, f"기대 {expected} / 실제 {got}")


def verify_multi_roi():
    print("\n[R1] 여러 ROI 위험 판정 (도로 양쪽 보행 구역)")
    roi_a = np.array([(100, 100), (300, 100), (300, 500), (100, 500)], dtype=np.int32)
    roi_b = np.array([(700, 100), (900, 100), (900, 500), (700, 500)], dtype=np.int32)
    rois = [roi_a, roi_b]
    car = fake_det("car", 500, 300)
    cases = [
        ("ROI A 안 사람+차량",       [fake_det("person", 200, 300), car],          True,  [0]),
        ("ROI B 안 사람+차량",       [fake_det("person", 800, 300), car],          True,  [1]),
        ("양쪽 ROI 사람+차량",       [fake_det("person", 200, 300),
                                      fake_det("person", 800, 300), car],          True,  [0, 1]),
        ("두 ROI 사이 도로 사람+차량", [fake_det("person", 500, 300), car],          False, []),
        ("ROI A 안 사람+정지차량",   [fake_det("person", 200, 300),
                                      fake_det("car", 500, 300, parked=True)],     False, []),
        ("빈 ROI 리스트",            [fake_det("person", 200, 300), car],          False, None),
    ]
    for label, detections, expected, expected_idx in cases:
        result = check_danger(detections, [] if expected_idx is None else rois)
        got, got_idx = result["is_danger"], result["danger_roi_indices"]
        ok = got == expected and got_idx == (expected_idx or [])
        check(label, ok, f"기대 {expected}{expected_idx or []} / 실제 {got}{got_idx}")


def verify_roi_storage():
    print("\n[R2] ROI 저장·불러오기 (여러 구역 + 구형식 호환)")
    import json
    import tempfile
    from core import roi_manager

    tri_a = [[10, 10], [100, 10], [50, 90]]
    tri_b = [[200, 10], [300, 10], [250, 90]]
    original_dir = roi_manager.ROI_DIR
    with tempfile.TemporaryDirectory() as tmp:
        roi_manager.ROI_DIR = tmp   # roi_configs/ 에 테스트 파일을 남기지 않음
        try:
            path = roi_manager.save_roi("multi", [tri_a, tri_b])
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            loaded = roi_manager.load_rois("multi")
            check("2개 구역 저장 → 2개 복원",
                  loaded is not None and [p.tolist() for p in loaded] == [tri_a, tri_b])
            check("JSON 에 polygons(2개)와 points(첫 구역) 함께 기록",
                  data.get("polygons") == [tri_a, tri_b] and data.get("points") == tri_a)
            check("load_roi 는 첫 구역 (N,2) 배열 반환",
                  roi_manager.load_roi("multi").tolist() == tri_a)

            with open(os.path.join(tmp, "legacy.json"), "w", encoding="utf-8") as f:
                json.dump({"source": "legacy", "points": tri_a}, f)
            legacy = roi_manager.load_rois("legacy")
            check("구형식(points만) → 1개 구역으로 로드",
                  legacy is not None and len(legacy) == 1 and legacy[0].tolist() == tri_a)

            roi_manager.save_roi("single", tri_b)
            single = roi_manager.load_rois("single")
            check("단일 다각형 save_roi 호출 → 1개 구역 저장",
                  single is not None and len(single) == 1 and single[0].tolist() == tri_b)
        finally:
            roi_manager.ROI_DIR = original_dir


def verify_fallback(frame):
    print("\n[A1] OpenVINO 미준비 환경 폴백")
    ov_dir = config.OPENVINO_MODEL_DIR
    if not os.path.isdir(ov_dir):
        print("       내보낸 모델이 없어 이미 폴백 상태입니다 — 그대로 검증합니다.")
        hidden = None
    else:
        hidden = ov_dir + "_hidden"
        shutil.move(ov_dir, hidden)
    try:
        auto = Detector(backend="auto")
        check("모델 로드 성공", auto.loaded)
        check("pytorch 로 폴백", auto.backend == "pytorch", f"backend={auto.backend}")
        check("auto 에서는 경고 없이 조용히 폴백", auto.load_warning is None)
        detections = auto.detect(frame)
        check("탐지가 정상 동작", len(detections) > 0, f"{len(detections)}건")
        check("반환 형식 동일", all(set(d) == DETECT_KEYS for d in detections))

        forced = Detector(backend="openvino")
        check("backend='openvino' 강제 시에도 폴백하고 경고를 남김",
              forced.loaded and forced.backend == "pytorch"
              and bool(forced.load_warning))
    finally:
        if hidden:
            shutil.move(hidden, ov_dir)


def main() -> int:
    frame = sample_frame()
    detections = verify_warmup(frame)
    verify_format(detections)
    verify_danger()
    verify_multi_roi()
    verify_roi_storage()
    verify_fallback(frame)

    print("\n" + ("전부 PASS" if not _fails else f"FAIL {len(_fails)}건: {_fails}"))
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
