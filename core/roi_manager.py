# core/roi_manager.py — ROI(관심구역) 저장·불러오기·판단 모듈
# ROI는 다각형 좌표 리스트로 관리하며, 소스명 기준으로 JSON 파일에 저장됩니다.
# 한 소스에 다각형을 여러 개 둘 수 있습니다 (예: 도로 양쪽 보행 구역).

import os
import json
import numpy as np
import cv2
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ROI_DIR, COLOR_ROI


def _roi_path(source_name: str) -> str:
    """소스명에 대응하는 ROI JSON 파일 경로를 반환합니다."""
    # 파일명에 사용할 수 없는 문자 제거
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in source_name)
    return os.path.join(ROI_DIR, f"{safe_name}.json")


def delete_roi(source_name: str) -> bool:
    """저장된 ROI 파일을 삭제합니다."""
    path = _roi_path(source_name)
    if os.path.exists(path):
        try:
            os.remove(path)
            return True
        except Exception as e:
            print(f"[ROI] 삭제 실패: {e}")
    return False


def normalize_rois(roi) -> list:
    """
    ROI 입력을 다각형 배열 리스트로 맞춥니다.
    None → [], 단일 (N,2) 배열/좌표 리스트 → [다각형], 다각형 리스트 → 그대로.
    꼭짓점이 3개 미만인 다각형은 제외합니다.
    """
    if roi is None:
        return []
    if isinstance(roi, np.ndarray):
        polygons = [roi] if roi.ndim == 2 else list(roi)
    else:
        roi = list(roi)
        if not roi:
            return []
        # 첫 원소가 숫자쌍 [x, y] 이면 단일 다각형
        first = roi[0]
        if len(first) == 2 and np.isscalar(first[0]):
            polygons = [roi]
        else:
            polygons = roi
    result = []
    for poly in polygons:
        arr = np.asarray(poly, dtype=np.int32).reshape(-1, 2)
        if len(arr) >= 3:
            result.append(arr)
    return result


def save_roi(source_name: str, polygons: list) -> str:
    """
    ROI 다각형들을 JSON 파일로 저장합니다.
    polygons: [[[x1,y1], [x2,y2], ...], ...] 형태의 다각형 리스트
              (기존처럼 [[x1,y1], ...] 단일 다각형을 넘겨도 됩니다)
    반환: 저장된 파일 경로
    """
    os.makedirs(ROI_DIR, exist_ok=True)
    path = _roi_path(source_name)
    polys = [[[int(p[0]), int(p[1])] for p in poly] for poly in normalize_rois(polygons)]
    data = {
        "source": source_name,
        "polygons": polys,
        # 구버전 코드 호환: 첫 번째 다각형을 기존 키로도 기록
        "points": polys[0] if polys else [],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def load_rois(source_name: str):
    """
    JSON 파일에서 ROI 다각형들을 불러옵니다.
    "polygons" 가 없는 구형식 파일은 "points" 를 다각형 1개로 읽습니다.
    반환: list[numpy array (N,2)] or None (파일이 없거나 유효한 다각형이 없으면)
    """
    path = _roi_path(source_name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("polygons"):
            polygons = normalize_rois(data["polygons"])
        else:
            polygons = normalize_rois(data.get("points"))
        return polygons or None
    except Exception as e:
        print(f"[ROI] 불러오기 실패: {e}")
        return None


def load_roi(source_name: str):
    """
    JSON 파일에서 첫 번째 ROI 다각형을 불러옵니다 (하위 호환용).
    반환: numpy array (N,2) or None (파일 없으면)
    """
    polygons = load_rois(source_name)
    return polygons[0] if polygons else None


def list_saved_rois() -> list[str]:
    """저장된 ROI 파일 목록(소스명)을 반환합니다."""
    if not os.path.exists(ROI_DIR):
        return []
    names = []
    for fname in os.listdir(ROI_DIR):
        if fname.endswith(".json"):
            path = os.path.join(ROI_DIR, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                names.append(data.get("source", fname.replace(".json", "")))
            except Exception:
                names.append(fname.replace(".json", ""))
    return names


def roi_indices_containing(point: tuple, roi) -> list[int]:
    """주어진 점(x, y)을 포함하는 ROI 다각형의 인덱스 목록을 반환합니다."""
    indices = []
    for i, polygon in enumerate(normalize_rois(roi)):
        # pointPolygonTest: 양수=내부, 0=경계, 음수=외부
        result = cv2.pointPolygonTest(
            polygon.reshape((-1, 1, 2)).astype(np.int32),
            (float(point[0]), float(point[1])),
            False,
        )
        if result >= 0:
            indices.append(i)
    return indices


def is_point_in_roi(point: tuple, roi_polygon) -> bool:
    """
    주어진 점(x, y)이 ROI 다각형 중 하나라도의 내부에 있는지 판단합니다.
    roi_polygon: numpy array (N,2), 다각형 리스트 or None
    """
    return bool(roi_indices_containing(point, roi_polygon))


def draw_roi_on_frame(frame, roi_polygon, danger: bool = False, danger_indices=None):
    """
    프레임 위에 ROI를 반투명 다각형으로 그립니다.
    danger_indices 가 주어지면 해당 다각형만 빨간색, 아니면 danger=True 일 때 전부 빨간색.
    그 외에는 노란색.
    """
    polygons = normalize_rois(roi_polygon)
    if not polygons:
        return frame

    danger_set = set(danger_indices) if danger_indices is not None else None
    for i, polygon in enumerate(polygons):
        is_red = (i in danger_set) if danger_set is not None else danger
        pts = polygon.reshape((-1, 1, 2)).astype(np.int32)
        color = (0, 0, 200) if is_red else COLOR_ROI

        # 반투명 채우기
        overlay = frame.copy()
        cv2.fillPoly(overlay, [pts], color)
        cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)

        # 테두리
        cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)

        # 꼭짓점 표시
        for pt in polygon:
            cv2.circle(frame, (int(pt[0]), int(pt[1])), 5, color, -1)

        # 구역이 여러 개면 구역 번호 표시
        if len(polygons) > 1:
            x0, y0 = int(polygon[0][0]), int(polygon[0][1])
            cv2.putText(frame, f"ROI{i + 1}", (x0 + 8, y0 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

    return frame


def parse_roi_text(text: str):
    """
    텍스트 형식 "x1,y1; x2,y2; x3,y3 ..." 을 numpy array 로 변환합니다.
    실패하면 None 을 반환합니다.
    """
    try:
        points = []
        # 세미콜론 또는 줄바꿈으로 분리
        for token in text.replace("\n", ";").split(";"):
            token = token.strip()
            if not token:
                continue
            parts = token.split(",")
            if len(parts) != 2:
                return None
            x, y = int(parts[0].strip()), int(parts[1].strip())
            points.append([x, y])
        if len(points) < 3:
            return None
        return np.array(points, dtype=np.int32)
    except Exception:
        return None
