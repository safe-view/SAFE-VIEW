"""추론 백엔드를 바꿔도 기존 동작이 보존되는지 검증합니다.

OpenVINO 백엔드는 "같은 결과를 더 빨리" 내는 것이 목적이므로, 속도(벤치마크)와
별개로 아래 네 가지가 유지돼야 합니다.

    A1 — openvino 가 없거나 모델을 안 내보낸 환경에서 기존대로 동작하는가
    A4 — 위험 판정 6개 사례가 기존과 같은 답을 내는가
    R1 — ROI 가 여러 개일 때(도로 양쪽 보행 구역) 판정·구역 인덱스가 맞는가
    R2 — 여러 구역 저장·불러오기와 구형식 ROI 파일 호환
    H1 — 마지막 감지 후 3초 경고 유지, 깜빡이는 감지가 이벤트 1건으로 묶이는가
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
from core.danger_logic import check_danger, update_danger_hold, hold_person_boxes
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


def verify_danger_hold():
    print("\n[H1] 위험 경고 유지 (마지막 감지 후 3초)")
    hold = 3.0

    def run(seq):
        """seq: [(now, raw)] → [held]"""
        last, out = None, []
        for now, raw in seq:
            held, last = update_danger_hold(raw, last, now, hold)
            out.append(held)
        return out

    def rising_edges(states):
        prev, n = False, 0
        for s in states:
            n += s and not prev
            prev = s
        return n

    check("감지 이력 없음 → 유지 안 함", run([(0.0, False)]) == [False])
    check("감지 직후 → 위험", run([(0.0, True)]) == [True])
    check("감지 후 2.9초 → 유지", run([(0.0, True), (2.9, False)])[-1] is True)
    check("감지 후 3.1초 → 해제", run([(0.0, True), (3.1, False)])[-1] is False)
    refreshed = run([(0.0, True), (2.0, True), (4.9, False), (5.1, False)])
    check("재감지 시 타이머 갱신 (4.9초 유지 / 5.1초 해제)",
          refreshed[2:] == [True, False], f"실제 {refreshed}")

    flicker = [True, False, True, False, False, True, False, False, False]
    seq = [(i * 0.5, raw) for i, raw in enumerate(flicker)]
    states = run(seq)
    check("깜빡이는 감지 → 경고 계속 유지", all(states), f"실제 {states}")
    check("깜빡이는 감지 → 이벤트(상승 에지) 1회", rising_edges(states) == 1)

    # 마지막 True(2.5초) 기준 3초가 지나면 해제되고, 다음 감지는 새 이벤트
    states = run(seq + [(5.6, False), (6.0, True)])
    check("유지 해제 후 재감지 → 새 이벤트",
          states[-2:] == [False, True] and rising_edges(states) == 2, f"실제 {states}")


def verify_person_box_hold():
    print("\n[H2] 사람 박스 유지 (안쪽 0.7초 / 가장자리 0.3초 / 2회 이상 검출)")
    W, H = 960, 540
    params = dict(frame_w=W, frame_h=H, hold_sec=0.7, edge_hold_sec=0.3, min_hits=2)

    def person(x1, y1, x2, y2):
        return {"class_name": "person", "bbox": (x1, y1, x2, y2),
                "bottom_center": ((x1 + x2) // 2, y2)}

    def run(seq, **over):
        """seq: [(now, [person...], new_result)] → [표시 박스 목록]"""
        held, out = [], []
        for now, persons, new_result in seq:
            shown, held = hold_person_boxes(held, persons, now, new_result=new_result,
                                            **{**params, **over})
            out.append([p["bbox"] for p in shown])
        return out

    inner = person(400, 200, 440, 290)
    edge = person(500, 460, 540, 540)          # 아래 가장자리에 발이 걸친 사람
    seen_twice = [(0.0, [inner], True), (0.04, [inner], True)]

    check("2회 검출 후 끊김 0.1초 → 마지막 박스 표시",
          run(seen_twice + [(0.14, [], True)])[-1] == [inner["bbox"]])
    out = run(seen_twice + [(0.64, [], True), (0.84, [], True)])
    check("끊김 0.6초 표시 / 0.8초 사라짐", out[-2] == [inner["bbox"]] and out[-1] == [],
          f"실제 {out[-2:]}")
    out = run([(0.0, [edge], True), (0.04, [edge], True), (0.24, [], True), (0.44, [], True)])
    check("가장자리 끊김 0.2초 표시 / 0.4초 사라짐", out[-2] == [edge["bbox"]] and out[-1] == [],
          f"실제 {out[-2:]}")
    check("1회만 검출(오검출) → 끊기면 바로 사라짐",
          run([(0.0, [inner], True), (0.04, [], True)])[-1] == [])
    out = run([(0.0, [inner], True), (0.02, [inner], False), (0.03, [inner], False),
               (0.05, [], True)])
    check("같은 결과 반복(new_result=False) → 검출 횟수 안 늘어남", out[-1] == [],
          f"실제 {out[-1]}")
    moved = person(404, 202, 444, 292)
    out = run(seen_twice + [(0.1, [], True), (0.14, [moved], True)])
    check("재검출 → 유지 박스 버리고 현재 박스 하나만", out[-1] == [moved["bbox"]],
          f"실제 {out[-1]}")
    other = person(100, 200, 140, 290)
    out = run([(0.0, [inner, other], True), (0.04, [inner, other], True), (0.1, [other], True)])
    check("2명 중 1명만 끊김 → 끊긴 사람만 유지",
          sorted(out[-1]) == sorted([other["bbox"], inner["bbox"]]), f"실제 {out[-1]}")
    out = run(seen_twice + [(0.1, [], True)], hold_sec=0)
    check("hold_sec=0 → 현재 검출만 (기존 동작)", out[-1] == [], f"실제 {out[-1]}")

    # 유지된 사람도 위험 판정에 들어간다 (모니터링 화면과 같은 연결 방식)
    roi = np.array([[380, 180], [460, 180], [460, 310], [380, 310]], dtype=np.int32)
    car = fake_det("car", 700, 300)

    def danger_at(seq):
        held, result = [], None
        for now, persons, new_result in seq:
            kept, held = hold_person_boxes(held, persons, now, new_result=new_result, **params)
            result = check_danger(kept + [car], roi)
        return result["is_danger"]

    check("ROI 안 사람이 0.3초 끊김 + 차량 → 위험",
          danger_at(seen_twice + [(0.34, [], True)]) is True)
    check("ROI 안 사람이 0.8초 끊김 + 차량 → 위험 아님 (유지 만료)",
          danger_at(seen_twice + [(0.84, [], True)]) is False)
    check("1회 오검출 사람이 끊김 + 차량 → 위험 아님",
          danger_at([(0.0, [inner], True), (0.04, [], True)]) is False)


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
    verify_danger_hold()
    verify_person_box_hold()
    verify_roi_storage()
    verify_fallback(frame)

    print("\n" + ("전부 PASS" if not _fails else f"FAIL {len(_fails)}건: {_fails}"))
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
