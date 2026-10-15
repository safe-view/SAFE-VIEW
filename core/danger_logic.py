# core/danger_logic.py — 위험 상태 판단 로직
# 단순한 규칙 기반: person + car 동시 존재 & person이 ROI 내부 → 위험

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.roi_manager import normalize_rois, roi_indices_containing


def update_danger_hold(raw_danger: bool, last_seen_ts, now: float, hold_sec: float):
    """
    프레임 단위 판정이 끊겨도 경고가 깜빡이지 않도록,
    마지막 위험 감지 시점부터 hold_sec 동안 위험 상태를 유지합니다.

    Args:
        raw_danger:   이번 프레임의 check_danger 결과
        last_seen_ts: 마지막 위험 감지 시각 (한 번도 없으면 None)
        now:          현재 시각
        hold_sec:     유지 시간(초)

    Returns:
        (held_danger, last_seen_ts)
    """
    if raw_danger:
        last_seen_ts = now
    held = last_seen_ts is not None and (now - last_seen_ts) < hold_sec
    return held, last_seen_ts


def _box_iou(a, b) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def _same_person(a, b) -> bool:
    """
    추적 ID 없이 위치로 같은 사람인지 봅니다.
    a 박스 중심이 b 박스(상하좌우 25%씩 확장) 안에 있거나, 두 박스 IoU가 0.2를 넘으면 같은 사람.
    """
    cx = (a[0] + a[2]) / 2
    cy = (a[1] + a[3]) / 2
    mw = (b[2] - b[0]) * 0.25
    mh = (b[3] - b[1]) * 0.25
    inside = b[0] - mw <= cx <= b[2] + mw and b[1] - mh <= cy <= b[3] + mh
    return inside or _box_iou(a, b) > 0.2


def hold_person_boxes(held: list, persons: list, now: float, frame_w: int, frame_h: int,
                      hold_sec: float, edge_hold_sec: float, min_hits: int,
                      new_result: bool = True, edge_px: int = 10):
    """
    사람 감지가 잠깐 끊겨도 마지막 박스를 짧게 유지한 사람 목록을 만듭니다.
    모니터링 화면은 이 목록을 check_danger 에 넘기므로, 유지된 사람도 위험 판정에 포함됩니다.

    Args:
        held:          직전 상태 [{"person": dict, "last_seen": float, "hits": int}]
        persons:       이번 프레임의 실제 검출 사람 목록
        now:           현재 시각
        frame_w/h:     프레임 크기 (가장자리 판정용)
        hold_sec:      화면 안쪽에서 끊겼을 때 유지 시간(초). 0 이하면 유지 안 함
        edge_hold_sec: 마지막 박스가 가장자리에 닿아 있을 때 유지 시간(초)
        min_hits:      이 횟수 이상 이어서 검출된 사람만 유지 (1프레임 오검출 제외)
        new_result:    새 추론 결과면 True. 같은 결과를 반복해서 받는 프레임은 False
                       (False면 검출 횟수를 올리지 않음)

    Returns:
        (persons, new_held) — persons: 실제 검출 + 유지 중인 사람
    """
    if hold_sec <= 0:
        return list(persons), []

    display = list(persons)
    new_held = []
    for p in persons:
        prev_hits = [h["hits"] for h in held if _same_person(p["bbox"], h["person"]["bbox"])]
        if new_result:
            hits = 1 + max(prev_hits, default=0)
        else:
            hits = max(prev_hits, default=1)
        new_held.append({"person": p, "last_seen": now, "hits": hits})

    # 최근에 본 항목부터 — 같은 사람의 유지 박스가 여러 개 남지 않게
    for h in sorted(held, key=lambda h: -h["last_seen"]):
        box = h["person"]["bbox"]
        if any(_same_person(d["bbox"], box) for d in display):
            continue
        if h["hits"] < min_hits:
            continue
        at_edge = (box[0] <= edge_px or box[1] <= edge_px
                   or box[2] >= frame_w - edge_px or box[3] >= frame_h - edge_px)
        limit = edge_hold_sec if at_edge else hold_sec
        if now - h["last_seen"] <= limit:
            display.append(h["person"])
            new_held.append(h)

    return display, new_held


def check_danger(detections: list, roi_polygon) -> dict:
    """
    탐지 결과와 ROI를 받아 위험 상태 여부를 판단합니다.
    roi_polygon: 다각형 하나(numpy array (N,2)) 또는 다각형 리스트 — 사람이
                 어느 ROI 에라도 들어가면 ROI 내부로 판단합니다.

    반환 dict:
    {
        "is_danger":         bool,   # 위험 상태 여부
        "has_person":        bool,
        "has_car":           bool,
        "dangerous_persons": list,   # ROI 내부에 있는 person 탐지 목록
        "danger_roi_indices": list,  # 위험 인물이 들어 있는 ROI 인덱스
        "all_persons":       list,
        "all_cars":          list,
    }
    """
    persons = [d for d in detections if d["class_name"] == "person"]
    cars    = [d for d in detections if d["class_name"] == "car"]

    # 정지 차량은 위험 판단에서 제외 (이동 가능성이 있는 차량만 위험 요소로 간주)
    active_cars = [c for c in cars if not c.get("is_parked", False)]

    result = {
        "is_danger":         False,
        "has_person":        len(persons) > 0,
        "has_car":           len(active_cars) > 0,
        "dangerous_persons": [],
        "danger_roi_indices": [],
        "all_persons":       persons,
        "all_cars":          cars,   # 시각화는 정지 차량 포함 (노란 박스로 표시)
    }

    # 위험 판단 조건:
    # 1) person 존재
    # 2) 이동 가능 차량(active_cars) 존재
    # 3) person의 발 위치(bottom_center)가 ROI 중 하나라도의 내부
    if not persons or not active_cars:
        return result

    polygons = normalize_rois(roi_polygon)
    if not polygons:
        # ROI 미설정 시 위험 판단 불가 → 정상 처리
        return result

    dangerous = []
    danger_indices = set()
    for person in persons:
        # 발 위치(bottom_center)로 ROI 판단
        indices = roi_indices_containing(person["bottom_center"], polygons)
        if indices:
            dangerous.append(person)
            danger_indices.update(indices)

    if dangerous:
        result["is_danger"] = True
        result["dangerous_persons"] = dangerous
        result["danger_roi_indices"] = sorted(danger_indices)

    return result


def draw_detections(frame, danger_result: dict, roi_polygon=None):
    """
    프레임 위에 바운딩 박스, 레이블, ROI를 그립니다.
    위험 상태이면 빨간색, 정상이면 초록색 박스.
    """
    import cv2
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import COLOR_NORMAL, COLOR_DANGER
    from core.roi_manager import draw_roi_on_frame

    is_danger = danger_result["is_danger"]

    # ROI 그리기
    frame = draw_roi_on_frame(frame, roi_polygon, danger=is_danger,
                              danger_indices=danger_result.get("danger_roi_indices"))

    # 위험한 person ID 집합 (비교용)
    dangerous_ids = {id(p) for p in danger_result["dangerous_persons"]}

    YELLOW = (0, 255, 255)  # BGR: 정지 차량용 노란색

    # 사람 박스 그리기
    for person in danger_result["all_persons"]:
        x1, y1, x2, y2 = person["bbox"]
        color = COLOR_DANGER if is_danger else COLOR_NORMAL
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = "person"
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x1, y1 - lh - 6), (x1 + lw, y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    # 차량 박스 그리기 (정지 여부에 따라 색상 + 라벨 위치 분기)
    frame_h, frame_w = frame.shape[:2]
    for car in danger_result["all_cars"]:
        x1, y1, x2, y2 = car["bbox"]
        is_parked = car.get("is_parked", False)

        if is_parked:
            color    = YELLOW
            text_clr = (0, 0, 0)
            label_name = "pk.car"
        elif is_danger:
            color    = COLOR_DANGER
            text_clr = (255, 255, 255)
            label_name = "car"
        else:
            color    = COLOR_NORMAL
            text_clr = (255, 255, 255)
            label_name = "car"

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = label_name
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)

        if is_parked:
            # 정지 차량 라벨은 박스 아래쪽에 배치 (왼쪽 기본, 잘리면 오른쪽)
            label_x = x1
            label_y = y2 + lh + 6
            # 화면 아래로 잘리면 박스 위로 폴백
            if label_y + 4 > frame_h:
                label_y = y1 - 4
                bg_top = y1 - lh - 6
                bg_bot = y1
            else:
                bg_top = y2 + 2
                bg_bot = y2 + lh + 8
            # 오른쪽으로 넘치면 오른쪽 정렬로 보정
            if label_x + lw > frame_w:
                label_x = max(0, x2 - lw)
            cv2.rectangle(frame, (label_x, bg_top), (label_x + lw, bg_bot), color, -1)
            cv2.putText(frame, label, (label_x, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_clr, 1, cv2.LINE_AA)
        else:
            # 일반 차량 라벨은 기존대로 박스 위쪽
            cv2.rectangle(frame, (x1, y1 - lh - 6), (x1 + lw, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_clr, 1, cv2.LINE_AA)

    # 위험 상태: 빨간 테두리 오버레이
    if is_danger:
        h, w = frame.shape[:2]
        thickness = 8
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), COLOR_DANGER, thickness)

    return frame
