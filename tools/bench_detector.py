"""백엔드별 YOLO 추론 지연을 측정하고 두 백엔드의 검출 결과를 비교합니다.

모니터링 화면(`pages/1_모니터링.py`)의 AsyncDetectorWorker 는 최신 프레임 1장만
남기고 나머지를 버리며 추론합니다. 즉 "추론 1회에 걸리는 시간"이 곧 검출 박스가
실제 움직임보다 얼마나 뒤처지는지, 위험 판정이 얼마나 늦게 나오는지를 결정합니다.
이 스크립트는 그 한 가지 숫자를 백엔드별로 잽니다.

    python tools/bench_detector.py                        # 두 백엔드 비교
    python tools/bench_detector.py --backend pytorch      # baseline 만
    python tools/bench_detector.py --video data/sample.mp4 --frames 300

영상을 주지 않으면 data/ 에서 첫 번째 영상을 찾고, 그래도 없으면 ultralytics 에
동봉된 샘플 이미지를 조금씩 움직여 프레임을 만듭니다. 어느 쪽을 썼는지는 결과
맨 위에 표시되며, 실제 현장 영상으로 다시 재보는 게 가장 정확합니다.
"""

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from config import (
    DATA_DIR, CONFIDENCE_THRESHOLD, INFER_IMGSZ,
    OPENVINO_MODEL_DIR, OPENVINO_DEVICE, YOLO_MODEL,
)
from core.detector import Detector

VIDEO_EXTS = (".mp4", ".avi", ".mov", ".mkv")
WARMUP_FRAMES = 10


# ══════════════════════════════════════════════════════
# 프레임 준비
# ══════════════════════════════════════════════════════
def find_sample_video() -> str | None:
    if not os.path.isdir(DATA_DIR):
        return None
    for name in sorted(os.listdir(DATA_DIR)):
        if name.lower().endswith(VIDEO_EXTS):
            return os.path.join(DATA_DIR, name)
    return None


def load_frames(video_path: str | None, count: int) -> tuple[list, str]:
    """측정용 프레임을 모읍니다. (프레임 리스트, 출처 설명) 을 돌려줍니다."""
    if video_path:
        import cv2
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise SystemExit(f"영상을 열 수 없습니다: {video_path}")
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join(chr((fourcc >> (8 * i)) & 0xFF) for i in range(4)).strip()

        frames = []
        while len(frames) < count:
            ok, frame = cap.read()
            if not ok:
                if not frames:
                    raise SystemExit(f"프레임을 한 장도 읽지 못했습니다: {video_path}")
                # 영상이 짧으면 처음부터 다시 읽어 프레임 수를 채웁니다.
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = cap.read()
                if not ok:
                    break
            frames.append(frame)
        cap.release()
        desc = (f"{os.path.basename(video_path)} — {w}x{h}, "
                f"{fps:.1f}fps, codec={codec or '?'}")
        return frames, desc

    # 영상이 없을 때: ultralytics 에 동봉된 샘플 이미지(사람·차량이 찍혀 있음)를
    # 조금씩 이동·확대해 프레임을 만듭니다. 난수 프레임과 달리 실제 검출이 나오므로
    # 두 백엔드의 검출 결과 비교(정확도 동등성)가 의미를 갖습니다. 다운로드는 없습니다.
    sample = load_bundled_sample()
    if sample is not None:
        h, w = sample.shape[:2]
        pad = 24
        frames = []
        for i in range(count):
            # 프레임마다 crop 위치를 조금씩 옮겨 "움직이는 장면"을 흉내냅니다.
            dx = int(pad * (i % 16) / 15)
            dy = int(pad * ((i // 4) % 16) / 15)
            frames.append(sample[dy:h - pad + dy, dx:w - pad + dx].copy())
        return frames, (f"ultralytics 동봉 샘플 이미지 {w}x{h} 를 이동시킨 합성 시퀀스 "
                        f"(data/ 에 영상 없음 — 실제 현장 영상으로 재측정 권장)")

    # 샘플 이미지마저 없으면 재현 가능한 난수 프레임 (추론 비용은 재지만
    # 검출이 거의 없어 정확도 비교는 의미가 없습니다)
    rng = np.random.default_rng(0)
    frames = [rng.integers(0, 256, (720, 1280, 3), dtype=np.uint8) for _ in range(count)]
    return frames, "합성 난수 프레임 1280x720 (검출이 거의 없어 정확도 비교는 무의미)"


def load_bundled_sample():
    """ultralytics 패키지에 들어 있는 샘플 이미지를 읽습니다 (네트워크 접근 없음)."""
    try:
        import cv2
        from ultralytics.utils import ASSETS
        for name in ("bus.jpg", "zidane.jpg"):
            path = os.path.join(str(ASSETS), name)
            if os.path.isfile(path):
                img = cv2.imread(path)
                if img is not None:
                    return img
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════
# 측정
#
# 백엔드마다 별도 프로세스에서 잽니다. 한 프로세스에서 PyTorch를 먼저 돌리면
# torch 스레드풀이 살아남아 뒤이어 도는 OpenVINO와 CPU를 두고 경쟁하고, 그
# 결과 OpenVINO 지연이 실제보다 2배 넘게 부풀려집니다(측정 초기에 실제로 겪은
# 현상입니다). 부모가 자식 프로세스를 띄우고 JSON으로 결과만 받아옵니다.
# ══════════════════════════════════════════════════════
JSON_MARKER = "___BENCH_JSON___"


def run_backend(backend: str, frames: list, conf: float,
                device: str = OPENVINO_DEVICE) -> dict | None:
    """한 백엔드를 이 프로세스에서 측정합니다 (자식 프로세스에서 호출됩니다)."""
    print(f"\n[{backend}] 모델 로드 중...")
    det = Detector(backend=backend, device=device)
    if not det.loaded:
        print(f"[{backend}] 로드 실패: {det.load_error}")
        return None
    if det.backend != backend:
        print(f"[{backend}] 요청한 백엔드로 로드되지 않았습니다 (실제: {det.backend})")
        if det.load_warning:
            print(f"          {det.load_warning}")
        return None

    latencies = []
    per_frame = []
    for i, frame in enumerate(frames):
        dets = det.detect(frame, conf=conf)
        if i >= WARMUP_FRAMES:          # 워밍업 구간은 통계에서 제외
            latencies.append(det.last_infer_ms)
        per_frame.append(dets)

    latencies.sort()
    mean = statistics.fmean(latencies)
    return {
        "backend":   det.backend,
        "mean":      mean,
        "p50":       latencies[len(latencies) // 2],
        "p95":       latencies[int(len(latencies) * 0.95)],
        "max":       latencies[-1],
        "fps":       1000.0 / mean if mean else 0.0,
        "samples":   len(latencies),
        "per_frame": per_frame,
    }


def run_backend_isolated(backend: str, args, quiet: bool = False) -> dict | None:
    """자식 프로세스를 띄워 한 백엔드를 측정하고 결과를 돌려받습니다."""
    cmd = [sys.executable, os.path.abspath(__file__),
           "--_worker", backend,
           "--frames", str(args.frames),
           "--conf", str(args.conf),
           "--device", args.device]
    if args.video:
        cmd += ["--video", args.video]

    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    payload = None
    for line in proc.stdout.splitlines():
        if line.startswith(JSON_MARKER):
            payload = json.loads(line[len(JSON_MARKER):])
        elif line.strip() and not quiet:
            print(line)
    if payload is None:
        print(f"[{backend}] 측정 실패 (종료 코드 {proc.returncode})")
        if proc.stderr.strip():
            print("  " + proc.stderr.strip().splitlines()[-1])
    return payload


# ══════════════════════════════════════════════════════
# 두 백엔드 결과 비교
# ══════════════════════════════════════════════════════
def iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter == 0:
        return 0.0
    union = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / union if union else 0.0


def compare(a_frames: list, b_frames: list) -> dict:
    """프레임별 검출 개수 일치율, 매칭 박스 평균 IoU, confidence 평균 절대 차이."""
    same_count = 0
    ious = []
    conf_diffs = []

    for a_dets, b_dets in zip(a_frames, b_frames):
        if len(a_dets) == len(b_dets):
            same_count += 1
        # 같은 클래스끼리 IoU 가 가장 큰 상대를 짝지어 비교합니다.
        remaining = list(b_dets)
        for a in a_dets:
            best, best_iou = None, 0.0
            for b in remaining:
                if b["class_id"] != a["class_id"]:
                    continue
                v = iou(a["bbox"], b["bbox"])
                if v > best_iou:
                    best, best_iou = b, v
            if best is not None and best_iou > 0:
                remaining.remove(best)
                ious.append(best_iou)
                conf_diffs.append(abs(a["confidence"] - best["confidence"]))

    total = len(a_frames)
    return {
        "count_match_pct": (same_count / total * 100) if total else 0.0,
        "mean_iou":        statistics.fmean(ious) if ious else 0.0,
        "mean_conf_diff":  statistics.fmean(conf_diffs) if conf_diffs else 0.0,
        "matched":         len(ious),
    }


# ══════════════════════════════════════════════════════
def print_env(frame_desc: str):
    def ver(mod):
        try:
            return __import__(mod).__version__
        except Exception:
            return "미설치"

    cpu = platform.processor() or "?"
    print("═" * 64)
    print("실행 환경")
    print("═" * 64)
    print(f"  CPU         : {cpu}")
    print(f"  OS          : {platform.system()} {platform.release()}")
    print(f"  Python      : {platform.python_version()}")
    print(f"  ultralytics : {ver('ultralytics')}")
    print(f"  torch       : {ver('torch')}")
    print(f"  openvino    : {ver('openvino')}")
    print(f"  모델        : {YOLO_MODEL} / imgsz={INFER_IMGSZ}")
    print(f"  OV 모델폴더 : {OPENVINO_MODEL_DIR}"
          f" ({'있음' if os.path.isdir(OPENVINO_MODEL_DIR) else '없음'})")
    print(f"  OV 디바이스 : {OPENVINO_DEVICE}")
    print(f"  프레임      : {frame_desc}")


def print_result(backend: str, rounds: list[dict]):
    """여러 회차의 측정을 요약합니다. 회차별 편차가 크면 그 사실도 같이 보여줍니다."""
    means = sorted(r["mean"] for r in rounds)
    med = statistics.median(means)
    print(f"\n[{backend}] 추론 지연 — {len(rounds)}회차 × {rounds[0]['samples']}프레임")
    print(f"  회차 평균의 중앙값 {med:7.2f} ms   "
          f"(최소 {means[0]:.2f} / 최대 {means[-1]:.2f})")
    print(f"  p50 중앙값 {statistics.median([r['p50'] for r in rounds]):7.2f} ms   "
          f"p95 중앙값 {statistics.median([r['p95'] for r in rounds]):7.2f} ms")
    print(f"  환산 추론 FPS: {1000.0 / med:.1f}")
    return med


def main() -> int:
    parser = argparse.ArgumentParser(description="YOLO 추론 지연 벤치마크")
    parser.add_argument("--backend", choices=["pytorch", "openvino", "both"],
                        default="both")
    parser.add_argument("--frames", type=int, default=60,
                        help=f"회차당 프레임 수 (앞 {WARMUP_FRAMES}장은 워밍업)")
    parser.add_argument("--repeat", type=int, default=5,
                        help="회차 수. 두 백엔드를 번갈아 재서 발열·부하 드리프트를 상쇄합니다")
    parser.add_argument("--video", default=None, help="측정에 쓸 영상 경로")
    parser.add_argument("--conf", type=float, default=CONFIDENCE_THRESHOLD)
    parser.add_argument("--device", default=OPENVINO_DEVICE,
                        help="OpenVINO 추론 디바이스 (CPU / GPU / NPU)")
    parser.add_argument("--_worker", default=None,
                        help=argparse.SUPPRESS)   # 내부용: 자식 프로세스 측정 모드
    args = parser.parse_args()

    if args.frames <= WARMUP_FRAMES:
        raise SystemExit(f"--frames 는 {WARMUP_FRAMES} 보다 커야 합니다.")

    video = args.video or find_sample_video()

    # ── 자식 프로세스: 한 백엔드만 측정하고 JSON 한 줄로 결과를 돌려줍니다 ──
    if args._worker:
        frames, _ = load_frames(video, args.frames)
        r = run_backend(args._worker, frames, args.conf, args.device)
        if r is None:
            return 1
        print(JSON_MARKER + json.dumps(r))
        return 0

    # ── 부모 프로세스 ──
    # 프레임 자체는 결정론적으로 만들어지므로 자식들이 같은 입력을 봅니다.
    _, frame_desc = load_frames(video, min(args.frames, WARMUP_FRAMES + 1))
    print_env(frame_desc)

    targets = ["pytorch", "openvino"] if args.backend == "both" else [args.backend]

    # 노트북은 발열·백그라운드 부하로 수십 초 사이에도 성능이 크게 드리프트합니다.
    # 한 백엔드를 길게 재고 다른 백엔드를 길게 재면 그 드리프트가 그대로 비교값에
    # 섞이므로, 짧은 측정을 번갈아 반복하고 회차별 비율의 중앙값을 봅니다.
    rounds: dict[str, list] = {b: [] for b in targets}
    for i in range(args.repeat):
        print(f"\r측정 중... {i + 1}/{args.repeat} 회차", end="", flush=True)
        for backend in targets:
            r = run_backend_isolated(backend, args, quiet=True)
            if r:
                rounds[backend].append(r)
    print("\r" + " " * 40 + "\r", end="")

    results = {b: rs for b, rs in rounds.items() if rs}
    medians = {b: print_result(b, rs) for b, rs in results.items()}

    if "pytorch" in results and "openvino" in results:
        pt, ov = results["pytorch"], results["openvino"]
        print("\n" + "═" * 64)
        print("비교")
        print("═" * 64)
        # 같은 회차끼리 짝지어 비율을 내면 드리프트가 분자·분모에서 함께 상쇄됩니다.
        ratios = sorted(p["mean"] / o["mean"] for p, o in zip(pt, ov))
        print(f"  회차별 배속 : "
              + ", ".join(f"{x:.2f}" for x in ratios))
        print(f"  배속 중앙값 : {statistics.median(ratios):.2f}배 "
              f"(1보다 크면 OpenVINO 가 빠름)")
        print(f"  평균 지연   : {medians['pytorch']:.2f} ms → {medians['openvino']:.2f} ms")

        c = compare(pt[-1]["per_frame"], ov[-1]["per_frame"])
        print(f"\n  검출 결과 동등성 (매칭된 박스 {c['matched']}개)")
        print(f"    프레임별 검출 개수 일치율 : {c['count_match_pct']:.1f} %")
        print(f"    매칭 박스 평균 IoU        : {c['mean_iou']:.4f}")
        print(f"    confidence 평균 절대 차이 : {c['mean_conf_diff']:.4f}")

    if not results:
        print("\n측정된 백엔드가 없습니다.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
