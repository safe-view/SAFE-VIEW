"""영상별 정답 위험 구간을 불러오고 저장한다."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
GROUND_TRUTH_PATH = DATA_DIR / "eval_ground_truth.json"
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".m4v"}


def _load_raw_ground_truth():
    try:
        with GROUND_TRUTH_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as exc:
        raise ValueError(f"정답지 파일이 없습니다: {GROUND_TRUTH_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"정답지 JSON 형식이 잘못됐습니다: {exc}") from exc


def load_ground_truth() -> dict[str, list[tuple[float, float]]]:
    raw = _load_raw_ground_truth()
    if not isinstance(raw, dict):
        raise ValueError("정답지 최상위 값은 영상 파일명을 키로 하는 객체여야 합니다.")

    ground_truth = {}
    for video_name, entry in raw.items():
        if not isinstance(video_name, str) or not isinstance(entry, dict):
            raise ValueError("각 정답지 항목은 영상 파일명과 객체여야 합니다.")
        intervals = entry.get("danger_intervals")
        if not isinstance(intervals, list):
            raise ValueError(f"{video_name}: danger_intervals는 리스트여야 합니다.")
        normalized = []
        for interval in intervals:
            if (not isinstance(interval, list) or len(interval) != 2
                    or isinstance(interval[0], bool) or isinstance(interval[1], bool)
                    or not isinstance(interval[0], (int, float))
                    or not isinstance(interval[1], (int, float))):
                raise ValueError(f"{video_name}: 각 구간은 [시작초, 끝초]여야 합니다.")
            start, end = map(float, interval)
            if start < 0 or end <= start:
                raise ValueError(f"{video_name}: 구간은 0 <= 시작초 < 끝초여야 합니다.")
            normalized.append((start, end))
        ground_truth[video_name] = normalized
    return ground_truth


def video_files() -> list[str]:
    return sorted(
        path.name
        for path in DATA_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def save_intervals(
    video_name: str,
    intervals: list[tuple[float, float]],
) -> None:
    try:
        raw = _load_raw_ground_truth()
    except ValueError as exc:
        if GROUND_TRUTH_PATH.exists():
            raise
        raw = {}

    if not isinstance(raw, dict):
        raise ValueError("정답지 최상위 값은 영상 파일명을 키로 하는 객체여야 합니다.")

    normalized = []
    for interval in intervals:
        if (not isinstance(interval, (list, tuple)) or len(interval) != 2
                or isinstance(interval[0], bool) or isinstance(interval[1], bool)
                or not isinstance(interval[0], (int, float))
                or not isinstance(interval[1], (int, float))):
            raise ValueError("각 구간은 [시작초, 끝초]여야 합니다.")
        start, end = map(float, interval)
        if start < 0 or end <= start:
            raise ValueError("구간은 0 <= 시작초 < 끝초여야 합니다.")
        normalized.append([start, end])

    raw[video_name] = {"danger_intervals": normalized}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with GROUND_TRUTH_PATH.open("w", encoding="utf-8") as file:
        json.dump(raw, file, ensure_ascii=False, indent=2)
        file.write("\n")
