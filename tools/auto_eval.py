"""정답 위험 구간과 실제 감지 파이프라인 출력을 비교해 성능을 기록한다."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (  # noqa: E402
    DANGER_HOLD_SEC,
    PERSON_BOX_EDGE_HOLD_SEC,
    PERSON_BOX_HOLD_SEC,
    PERSON_BOX_MIN_HITS,
)
from core import parked_detector  # noqa: E402
from core.danger_logic import check_danger, hold_person_boxes, update_danger_hold  # noqa: E402
from core.detector import Detector  # noqa: E402
from core.performance_eval import add_record, delete_record, load_records  # noqa: E402
from core.roi_manager import load_rois  # noqa: E402


DATA_DIR = PROJECT_ROOT / "data"
GROUND_TRUTH_PATH = DATA_DIR / "eval_ground_truth.json"
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".m4v"}
AUTO_PREFIX = "[자동평가] "

TP = "정탐 (TP)"
FP = "오탐 (FP)"
FN = "미탐 (FN)"
TN = "정상 (TN)"
CATEGORY_ORDER = (TP, FP, FN, TN)


class MotionCompensator:
    """카메라 흔들림 누적 이동량을 계산해 차량 중심을 보정한다."""

    def __init__(self):
        self._prev_gray = None
        self._shake_x = 0.0
        self._shake_y = 0.0
        self._motion_scale = 0.125
        self._motion_interval = 3
        self._motion_frame_count = 0

    def correct_car_centers(self, frame, car_centers):
        # pages/1_모니터링.py AsyncDetectorWorker._run()의 흔들림 보정 로직을
        # 복사한 블록이다. 원본이 바뀌면 이 계산과 상수도 반드시 같이 갱신할 것.
        estimate_motion = (
            self._prev_gray is None
            or self._motion_frame_count % self._motion_interval == 0
        )
        self._motion_frame_count += 1
        if estimate_motion:
            current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            current_gray = cv2.resize(
                current_gray,
                None,
                fx=self._motion_scale,
                fy=self._motion_scale,
                interpolation=cv2.INTER_AREA,
            )
        if (estimate_motion and self._prev_gray is not None
                and self._prev_gray.shape == current_gray.shape):
            prev_points = cv2.goodFeaturesToTrack(
                self._prev_gray,
                maxCorners=30,
                qualityLevel=0.01,
                minDistance=5,
                blockSize=7,
            )
            if prev_points is not None:
                current_points, status, _ = cv2.calcOpticalFlowPyrLK(
                    self._prev_gray, current_gray, prev_points, None
                )
                if current_points is not None and status is not None:
                    tracked = status.reshape(-1) == 1
                    if np.any(tracked):
                        displacement = (
                            current_points[tracked] - prev_points[tracked]
                        ).reshape(-1, 2)
                        dx, dy = np.median(displacement, axis=0)
                        dx = float(dx) / self._motion_scale
                        dy = float(dy) / self._motion_scale
                        if math.hypot(dx, dy) <= 40.0:
                            self._shake_x += dx
                            self._shake_y += dy
        if estimate_motion:
            self._prev_gray = current_gray
        shake_x = self._shake_x
        shake_y = self._shake_y

        return [(x - shake_x, y - shake_y) for x, y in car_centers]


def parse_args():
    parser = argparse.ArgumentParser(description="영상 위험 감지 성능 자동 평가")
    parser.add_argument("--video", help="data 폴더 안에서 평가할 영상 파일명")
    parser.add_argument(
        "--list-unlabeled",
        action="store_true",
        help="정답지가 없는 영상 목록만 출력",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="CSV를 변경하지 않고 결과만 출력",
    )
    return parser.parse_args()


def load_ground_truth():
    try:
        with GROUND_TRUTH_PATH.open("r", encoding="utf-8") as file:
            raw = json.load(file)
    except FileNotFoundError as exc:
        raise ValueError(f"정답지 파일이 없습니다: {GROUND_TRUTH_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"정답지 JSON 형식이 잘못됐습니다: {exc}") from exc

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


def video_files():
    return sorted(
        path.name
        for path in DATA_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def list_unlabeled(ground_truth):
    unlabeled = [name for name in video_files() if name not in ground_truth]
    if unlabeled:
        print("정답지가 없는 영상:")
        for name in unlabeled:
            print(f"- {name}")
    else:
        print("모든 영상에 정답지가 있습니다.")


def select_videos(ground_truth, requested_video):
    available = set(video_files())
    if requested_video:
        if requested_video not in ground_truth:
            raise ValueError(f"정답지에 없는 영상입니다: {requested_video}")
        if requested_video not in available:
            raise ValueError(f"data 폴더에 없는 영상입니다: {requested_video}")
        return [requested_video]

    selected = []
    for name in ground_truth:
        if name in available:
            selected.append(name)
        else:
            print(f"[경고] 정답지 영상이 data 폴더에 없어 제외합니다: {name}")
    for name in sorted(available - set(ground_truth)):
        print(f"[경고] 정답지가 없어 평가에서 제외합니다: {name}")
    return selected


def apply_parked_flags(detections, frame, motion):
    cars = [d for d in detections if d["class_name"] == "car"]
    car_centers = [d["center"] for d in cars]
    car_areas = [
        (d["bbox"][2] - d["bbox"][0]) * (d["bbox"][3] - d["bbox"][1])
        for d in cars
    ]
    car_ids = [d.get("track_id") for d in cars]
    corrected_centers = motion.correct_car_centers(frame, car_centers)
    parked_flags = parked_detector.update(corrected_centers, car_areas, car_ids)
    for car, is_parked in zip(cars, parked_flags):
        car["is_parked"] = is_parked


def detect_alarm_intervals(video_path, detector, roi_polygon):
    capture = cv2.VideoCapture(os.fspath(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"영상을 열 수 없습니다: {video_path.name}")

    fps = float(capture.get(cv2.CAP_PROP_FPS))
    if not math.isfinite(fps) or fps <= 0:
        print(f"[경고] FPS를 읽지 못해 30 FPS로 처리합니다: {video_path.name}")
        fps = 30.0

    detector.reset_tracker()
    parked_detector.reset()
    motion = MotionCompensator()
    person_hold = []
    danger_last_seen_ts = None
    alarm_start = None
    alarm_intervals = []
    frame_index = 0
    original_time_module = parked_detector.time
    video_clock = SimpleNamespace(time=lambda: 0.0)
    parked_detector.time = video_clock

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            now = frame_index / fps
            frame_index += 1
            detections = detector.detect(frame)

            # parked_detector의 초 단위 상태도 빠른 벽시계가 아닌 영상 시간으로 계산한다.
            video_clock.time = lambda video_time=now: video_time
            apply_parked_flags(detections, frame, motion)

            persons_now = [d for d in detections if d["class_name"] == "person"]
            held_persons, person_hold = hold_person_boxes(
                person_hold,
                persons_now,
                now,
                frame.shape[1],
                frame.shape[0],
                PERSON_BOX_HOLD_SEC,
                PERSON_BOX_EDGE_HOLD_SEC,
                PERSON_BOX_MIN_HITS,
                new_result=True,
            )
            detections = [d for d in detections if d["class_name"] != "person"] + held_persons
            danger_result = check_danger(detections, roi_polygon)
            is_danger, danger_last_seen_ts = update_danger_hold(
                danger_result["is_danger"],
                danger_last_seen_ts,
                now,
                DANGER_HOLD_SEC,
            )

            if is_danger and alarm_start is None:
                alarm_start = now
            elif not is_danger and alarm_start is not None:
                alarm_intervals.append((alarm_start, now))
                alarm_start = None
    finally:
        parked_detector.time = original_time_module
        parked_detector.reset()
        detector.reset_tracker()
        capture.release()

    if alarm_start is not None:
        alarm_intervals.append((alarm_start, frame_index / fps))
    return alarm_intervals


def classify_intervals(alarm_intervals, danger_intervals):
    results = []
    matched_truth = set()

    for alarm_start, alarm_end in alarm_intervals:
        overlaps = [
            index
            for index, (truth_start, truth_end) in enumerate(danger_intervals)
            if alarm_start <= truth_end and alarm_end >= truth_start
        ]
        if overlaps:
            matched_truth.update(overlaps)
            truth_index = overlaps[0]
            truth_start, truth_end = danger_intervals[truth_index]
            results.append({
                "result": TP,
                "response_time": max(0.0, alarm_start - truth_start),
                "notes": (
                    f"자동 측정: 알람구간 {alarm_start:.1f}s~{alarm_end:.1f}s / "
                    f"정답구간 {truth_start:.1f}s~{truth_end:.1f}s"
                ),
            })
        else:
            results.append({
                "result": FP,
                "response_time": 0.0,
                "notes": f"자동 측정: 알람구간 {alarm_start:.1f}s~{alarm_end:.1f}s / 정답구간 없음",
            })

    for index, (truth_start, truth_end) in enumerate(danger_intervals):
        if index not in matched_truth:
            results.append({
                "result": FN,
                "response_time": 0.0,
                "notes": f"자동 측정: 알람구간 없음 / 정답구간 {truth_start:.1f}s~{truth_end:.1f}s",
            })

    if not alarm_intervals and not danger_intervals:
        results.append({
            "result": TN,
            "response_time": 0.0,
            "notes": "자동 측정: 알람구간 없음 / 정답구간 없음",
        })
    return results


def remove_previous_auto_records(video_name):
    records = load_records()
    timestamps = {
        record.get("timestamp", "")
        for record in records
        if record.get("source") == video_name
        and record.get("scenario", "").startswith(AUTO_PREFIX)
    }
    collisions = [
        record for record in records
        if record.get("timestamp", "") in timestamps
        and not (
            record.get("source") == video_name
            and record.get("scenario", "").startswith(AUTO_PREFIX)
        )
    ]
    if collisions:
        raise RuntimeError(
            "기존 자동평가 기록의 타임스탬프를 다른 기록도 사용 중이라 "
            "안전하게 교체할 수 없습니다. 성능 평가 페이지에서 해당 자동 기록을 삭제해 주세요."
        )
    for timestamp in sorted(timestamps):
        if timestamp and not delete_record(timestamp):
            raise RuntimeError(f"기존 자동평가 기록을 삭제하지 못했습니다: {timestamp}")
    return len(timestamps)


def save_results(video_name, results):
    removed = remove_previous_auto_records(video_name)
    if removed:
        print(f"  기존 자동평가 기록 삭제: {removed}개 타임스탬프")
    scenario = f"{AUTO_PREFIX}{video_name}"
    for result in results:
        if not add_record(
            scenario=scenario,
            source=video_name,
            result=result["result"],
            response_time_sec=result["response_time"],
            notes=result["notes"],
        ):
            raise RuntimeError(f"평가 기록 저장 실패: {video_name} / {result['result']}")


def print_video_results(video_name, results, dry_run):
    suffix = " (dry-run)" if dry_run else ""
    print(f"\n[{video_name}]{suffix}")
    for result in results:
        response = (
            f", 응답시간 {result['response_time']:.2f}s"
            if result["result"] == TP else ""
        )
        print(f"- {result['result']}{response}: {result['notes']}")


def print_summary(summaries):
    print("\n요약")
    print(f"{'영상':<36} {'TP':>4} {'FP':>4} {'FN':>4} {'TN':>4}")
    print("-" * 56)
    total = Counter()
    for video_name, counts in summaries:
        total.update(counts)
        print(
            f"{video_name:<36} {counts[TP]:>4} {counts[FP]:>4} "
            f"{counts[FN]:>4} {counts[TN]:>4}"
        )
    print("-" * 56)
    print(f"{'전체':<36} {total[TP]:>4} {total[FP]:>4} {total[FN]:>4} {total[TN]:>4}")


def main():
    args = parse_args()
    try:
        ground_truth = load_ground_truth()
        if args.list_unlabeled:
            list_unlabeled(ground_truth)
            return 0

        selected = select_videos(ground_truth, args.video)
        if not selected:
            print("평가할 영상이 없습니다.")
            return 0

        detector = Detector()
        if not detector.loaded:
            raise RuntimeError(f"탐지 모델을 불러오지 못했습니다: {detector.load_error}")

        summaries = []
        for video_name in selected:
            source_label = os.path.splitext(video_name)[0]
            roi_polygon = load_rois(source_label)
            if roi_polygon is None:
                print(
                    f"[경고] ROI가 없습니다: {video_name} — ROI 설정 페이지에서 먼저 저장하세요."
                )
            alarms = detect_alarm_intervals(DATA_DIR / video_name, detector, roi_polygon)
            results = classify_intervals(alarms, ground_truth[video_name])
            print_video_results(video_name, results, args.dry_run)
            if not args.dry_run:
                save_results(video_name, results)
            summaries.append((video_name, Counter(item["result"] for item in results)))

        print_summary(summaries)
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"[오류] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
