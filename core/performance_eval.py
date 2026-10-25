# core/performance_eval.py — 시스템 성능 정량 평가 로그
#
# KISA 지능형 CCTV 성능시험 인증제도의 평가 방식을 참고:
#   - 정탐(True Positive):  실제 위험 O / 시스템 감지 O
#   - 오탐(False Positive): 실제 위험 X / 시스템 감지 O
#   - 미탐(False Negative): 실제 위험 O / 시스템 감지 X
#   - 정상(True Negative):  실제 위험 X / 시스템 감지 X

import os
import csv
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOGS_DIR

EVAL_LOG = os.path.join(LOGS_DIR, "performance_eval.csv")

# 평가 결과 카테고리
CATEGORIES = ["정탐 (TP)", "오탐 (FP)", "미탐 (FN)", "정상 (TN)"]
FIELDNAMES = [
    "id", "timestamp", "scenario", "source",
    "result", "response_time_sec", "notes",
]


def _new_record_id() -> str:
    return uuid.uuid4().hex[:12]


def _write_records(records: list[dict]) -> None:
    with open(EVAL_LOG, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)


def _ensure_file():
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(EVAL_LOG):
        with open(EVAL_LOG, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(FIELDNAMES)


def add_record(scenario: str, source: str, result: str,
               response_time_sec: float = 0.0, notes: str = "") -> bool:
    """평가 기록 한 건 추가"""
    if result not in CATEGORIES:
        return False
    _ensure_file()
    try:
        with open(EVAL_LOG, "a", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow([
                _new_record_id(),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                scenario, source, result,
                f"{response_time_sec:.2f}" if response_time_sec else "",
                notes,
            ])
        return True
    except Exception as e:
        print(f"[PerformanceEval] 기록 실패: {e}")
        return False


def load_records() -> list[dict]:
    """전체 평가 기록 로드"""
    if not os.path.exists(EVAL_LOG):
        return []
    try:
        with open(EVAL_LOG, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            records = list(reader)
            has_id_column = reader.fieldnames is not None and "id" in reader.fieldnames

        if records and not has_id_column:
            records = [{"id": _new_record_id(), **record} for record in records]
            _write_records(records)
        return records
    except Exception:
        return []


def delete_record(record_id: str) -> bool:
    """특정 ID의 평가 기록 삭제"""
    records = load_records()
    if not records:
        return False
    filtered = [r for r in records if r.get("id") != record_id]
    if len(filtered) == len(records):
        return False
    try:
        _write_records(filtered)
        return True
    except Exception:
        return False


def compute_metrics(records: list[dict]) -> dict:
    """
    정탐률·오탐률·미탐률 계산.

    정탐률(Recall)    = TP / (TP + FN)
    정밀도(Precision) = TP / (TP + FP)
    오탐률(FAR)       = FP / (FP + TN)
    미탐률(Miss)      = FN / (TP + FN)
    """
    counts = {"정탐 (TP)": 0, "오탐 (FP)": 0, "미탐 (FN)": 0, "정상 (TN)": 0}
    rt_values = []

    for r in records:
        result = r.get("result", "")
        if result in counts:
            counts[result] += 1
        try:
            rt = float(r.get("response_time_sec") or 0)
            if rt > 0:
                rt_values.append(rt)
        except ValueError:
            pass

    tp = counts["정탐 (TP)"]
    fp = counts["오탐 (FP)"]
    fn = counts["미탐 (FN)"]
    tn = counts["정상 (TN)"]
    total = tp + fp + fn + tn

    def pct(num, denom):
        return (num / denom * 100) if denom else 0.0

    return {
        "counts":       counts,
        "total":        total,
        "recall":       pct(tp, tp + fn),       # 정탐률
        "precision":    pct(tp, tp + fp),       # 정밀도
        "far":          pct(fp, fp + tn),       # 오탐률
        "miss":         pct(fn, tp + fn),       # 미탐률
        "avg_response": (sum(rt_values) / len(rt_values)) if rt_values else 0.0,
        "rt_samples":   len(rt_values),
    }
