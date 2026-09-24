"""정지차량 판정(`core/parked_detector.py`)의 회귀 테스트.

실제 영상 없이, 합성 입력과 가상 시계로 결정론적으로 돌립니다. 임계값이나
판정 로직을 건드렸을 때 무엇이 좋아지고 무엇이 깨지는지 바로 보이게 하는 것이
목적입니다.

    python tools/verify_parked.py

종료 코드 0 이면 전부 통과입니다.

왜 가상 시계인가 — 이 모듈은 `time.time()`(벽시계)으로 정지 시간을 잽니다.
실제로 초를 기다리며 테스트하면 몇 분이 걸리고, PC 속도에 따라 결과가
달라집니다. 시계를 프레임당 1/FPS 씩 흐르는 가짜로 바꾸면 빠르고 재현됩니다.
"""

import os
import sys

# Windows 콘솔 기본 인코딩(cp949)에는 일부 문자가 없어 출력이 깨집니다.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.parked_detector as pd

FPS = 30.0
_fails: list[str] = []


class _FakeClock:
    """프레임마다 1/FPS 씩 흐르는 가상 시계."""

    def __init__(self):
        self.now = 1_000_000.0

    def time(self):
        return self.now

    def advance(self):
        self.now += 1.0 / FPS


# ══════════════════════════════════════════════════════
# 합성 입력 — 차량 1대의 (중심점, 박스 면적) 시퀀스
# ══════════════════════════════════════════════════════
BASE_AREA = 5000.0


def seq_parked(seconds: float) -> list:
    """완전 정지. 중심점·면적 모두 고정."""
    return [((100, 200), BASE_AREA) for _ in range(int(seconds * FPS))]


def seq_move_then_park(move_sec: float, total_sec: float) -> list:
    """앞쪽 move_sec 초만 이동한 뒤 남은 시간 정지 (주차하는 차)."""
    out = []
    for i in range(int(total_sec * FPS)):
        t = i / FPS
        x = 100 + int(min(t, move_sec) * 60)
        out.append(((x, 200), BASE_AREA))
    return out


# 실측 픽스처 — `data/시나리오1.mp4` 에서 중심점이 28px 안에만 머문(= 사실상
# 주차돼 있는) 차량의 프레임별 박스 면적입니다. 기준값 대비 변화는 중앙값 7.6%,
# 최대 28% 로, 차는 가만히 있는데도 검출 박스가 이만큼 흔들립니다.
# 떨림 패턴을 지어내면 실제와 다른 것을 테스트하게 되므로 측정값을 그대로 씁니다.
MEASURED_PARKED_AREAS = [
    50856, 50856, 49280, 50080, 50402, 49612, 49612, 49138, 47736, 48032,
    48944, 48944, 47978, 48931, 49855, 49810, 49810, 53912, 51100, 49470,
    44640, 44928, 39754, 40040, 38056, 36270, 36270, 40180, 43337, 38304,
    37570, 37281, 43659, 42920, 44696, 45144, 44847, 43800, 44384, 44384,
    44243, 44536, 57113, 47642, 43452, 44676, 44676, 44676, 42196, 43428,
    46035, 46035, 43400, 43090, 43400, 43803, 43803, 43332, 42861, 42704,
    44160, 44160, 45792, 45563, 44436, 43631, 43792, 44436, 45760, 45563,
    45760, 45760, 45920, 46110, 46136, 45687, 45687, 45978, 45820, 46136,
    46587, 46587, 45951, 45792, 46240, 46240, 46240, 46240, 46240, 46080,
    46207, 46207, 46240, 46400, 46587, 46587, 46587, 47040, 47334, 46880,
]


def seq_parked_with_real_jitter(seconds: float) -> list:
    """실제로 주차돼 있던 차량의 검출 박스 면적 흔들림을 그대로 재생합니다.

    중심점은 고정해 면적 신호만 검증합니다. 차는 움직이지 않았으므로
    정지차량으로 잡혀야 합니다.
    """
    n = int(seconds * FPS)
    return [((100, 200), float(MEASURED_PARKED_AREAS[i % len(MEASURED_PARKED_AREAS)]))
            for i in range(n)]


def seq_reversing(seconds: float = 30.0) -> list:
    """후진 차량. 중심점은 사실상 고정인데 면적이 한 방향으로 꾸준히 커짐.

    PR #10이 잡으려 한 케이스입니다. 카메라 쪽으로 다가오거나 멀어지는 차는
    화면상 중심점이 거의 안 움직이고 박스 크기만 변합니다. 실제로 움직이는
    중이므로 정지차량으로 잡히면 안 됩니다.

    면적이 30초에 걸쳐 3배가 되는 속도로 둡니다 — 이보다 훨씬 느리면 (예:
    10초 동안 면적 변화가 20% 미만) 애초에 거의 멈춘 차라 정지로 봐도 무방합니다.
    """
    out = []
    n = int(seconds * FPS)
    for i in range(n):
        grow = 1.0 + 2.0 * (i / n)              # 면적이 3배까지 단조 증가
        out.append(((100, 200), BASE_AREA * grow))
    return out


def seq_moving(seconds: float) -> list:
    """일반 이동 차량. 중심점이 계속 이동."""
    return [((100 + int(i / FPS * 60), 200), BASE_AREA)
            for i in range(int(seconds * FPS))]


# ══════════════════════════════════════════════════════
def run(seq: list) -> dict:
    """시퀀스를 흘려보내고 (최초 판정 시각, 판정 비율, 마지막 상태)를 돌려줍니다."""
    clock = _FakeClock()
    original_time = pd.time
    pd.time = clock
    try:
        pd.reset()
        first = None
        hits = 0
        last = False
        for center, area in seq:
            clock.advance()
            flags = pd.update([center], [area])
            last = bool(flags and flags[0])
            if last:
                hits += 1
                if first is None:
                    first = clock.now - 1_000_000.0
        return {"first": first, "pct": hits / len(seq) * 100, "last": last}
    finally:
        pd.time = original_time


def check(label: str, ok: bool, detail: str = ""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        _fails.append(label)


def fmt(r: dict) -> str:
    first = "판정 없음" if r["first"] is None else f"{r['first']:.1f}초"
    return f"최초 {first}, 유지 {r['pct']:.0f}%"


def main() -> int:
    print(f"설정값  STATIONARY={pd.STATIONARY_SECONDS}s  "
          f"GRACE={pd.RECENT_MOTION_GRACE_SECONDS}s  "
          f"AREA_RATIO={pd.AREA_CHANGE_RATIO}  "
          f"MOVE_PX={pd.MOVE_THRESHOLD_PX}\n")

    # A. 완전 정지 → 기준 시간쯤 판정되고 계속 유지
    a = run(seq_parked(120))
    check("A. 완전 정지 120초 → 정지차량으로 판정",
          a["first"] is not None and a["first"] < pd.STATIONARY_SECONDS + 5
          and a["pct"] > 80, fmt(a))

    # B. 주차하는 차 → 유예 시간 뒤에는 판정돼야 함
    b = run(seq_move_then_park(5, 120))
    limit = 5 + pd.STATIONARY_SECONDS + pd.RECENT_MOTION_GRACE_SECONDS + 5
    check("B. 5초 이동 후 정지 → 유예 뒤 판정",
          b["first"] is not None and b["first"] <= limit,
          f"{fmt(b)} (허용 {limit:.0f}초 이내)")

    # C. 박스 떨림만 있는 정지 차량 → 판정돼야 함 (이슈 #13 본체)
    c = run(seq_parked_with_real_jitter(120))
    check("C. 정지 + 실측 박스 떨림(중앙값 7.6%, 최대 28%) → 정지차량으로 판정",
          c["first"] is not None and c["pct"] > 50, fmt(c))

    # D. 후진 차량 → 판정되면 안 됨 (PR #10 이 지킨 동작)
    d = run(seq_reversing(30))
    check("D. 후진 차량(면적 단조 증가) → 정지차량으로 판정 안 됨",
          d["first"] is None, fmt(d))

    # E. 일반 이동 차량 → 판정되면 안 됨
    e = run(seq_moving(120))
    check("E. 이동 차량(중심점 이동) → 정지차량으로 판정 안 됨",
          e["first"] is None, fmt(e))

    print("\n" + ("전부 PASS" if not _fails else f"FAIL {len(_fails)}건: {_fails}"))
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
