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


def seq_parked_with_gaps(seconds: float) -> list:
    """정지 차량인데 YOLO 가 주기적으로 놓치는 경우.

    실제 영상에서 관찰된 상황입니다 — 야간·가림 때문에 검출이 끊기면 슬롯이
    만료되고 "10초간 정지" 이력이 날아가, 판정이 됐다 풀렸다 합니다.
    추적 ID가 있으면 끊겨도 같은 차로 이어져야 합니다.
    """
    out = []
    for i in range(int(seconds * FPS)):
        # 6초 주기로 6초 동안 검출 안 됨 (SLOT_EXPIRE_SEC 5초를 넘긴다)
        if (i // int(6 * FPS)) % 2 == 1:
            out.append(None)
        else:
            out.append(((100, 200), BASE_AREA))
    return out


def run_two_ids(seq: list) -> dict:
    """같은 자리에 ID만 바뀐 차가 오면 새 슬롯으로 시작하는지 확인."""
    clock = _FakeClock()
    original_time = pd.time
    pd.time = clock
    try:
        pd.reset()
        half = len(seq) // 2
        for center, area in seq[:half]:
            clock.advance()
            pd.update([center], [area], [1])
        before = pd.update([seq[half][0]], [seq[half][1]], [1])
        # 같은 좌표인데 ID만 2로 바뀐다
        after = None
        for center, area in seq[half:half + int(3 * FPS)]:
            clock.advance()
            after = pd.update([center], [area], [2])
        was_parked = bool(before and before[0])
        now_parked = bool(after and after[0])
        return {
            "restarted": was_parked and not now_parked,
            "detail": f"ID 1 일 때 {was_parked} → ID 2 로 바뀐 직후 {now_parked}",
        }
    finally:
        pd.time = original_time


def check_expire_crash() -> tuple:
    """이슈 #15 — SLOT_EXPIRE_SEC 이 이력 보관 기준보다 길 때 죽지 않아야 한다."""
    clock = _FakeClock()
    original_time = pd.time
    original_expire = pd.SLOT_EXPIRE_SEC
    pd.time = clock
    pd.SLOT_EXPIRE_SEC = 20.0
    try:
        pd.reset()
        for _ in range(int(1 * FPS)):        # 차 1대를 잠깐 보여주고
            clock.advance()
            pd.update([(100, 100)], [BASE_AREA])
        for _ in range(int(40 * FPS)):       # 그 차가 사라진 채로 시간만 흐른다
            clock.advance()
            pd.update([(900, 900)], [BASE_AREA])
        return True, "40초 동안 예외 없음"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    finally:
        pd.time = original_time
        pd.SLOT_EXPIRE_SEC = original_expire


# ══════════════════════════════════════════════════════
def run(seq: list, track_id=None) -> dict:
    """시퀀스를 흘려보내고 (최초 판정 시각, 판정 비율, 마지막 상태)를 돌려줍니다.

    seq 의 각 항목이 (center, area) 면 차량 1대가 계속 보이는 경우이고,
    None 이면 그 프레임에서 차량이 검출되지 않은 것으로 다룹니다.
    track_id 를 주면 추적 ID 경로로, 주지 않으면 기존 거리 매칭 경로로 돕니다.
    """
    clock = _FakeClock()
    original_time = pd.time
    pd.time = clock
    try:
        pd.reset()
        first = None
        hits = 0
        last = False
        for item in seq:
            clock.advance()
            if item is None:                      # 검출이 끊긴 프레임
                pd.update([], [], [] if track_id is not None else None)
                last = False
                continue
            center, area = item
            ids = [track_id] if track_id is not None else None
            flags = pd.update([center], [area], ids)
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

    # ── 추적 ID 경로 ────────────────────────────────────────────────
    # F. 검출이 중간중간 끊겨도 같은 ID면 정지 이력이 이어져야 한다.
    #    ID가 없으면(거리 매칭) 슬롯이 만료돼 이력이 날아가고 판정이 깜빡인다.
    gap = seq_parked_with_gaps(120)
    f_id = run(gap, track_id=7)
    f_no = run(gap)
    check("F. 검출이 끊겨도 같은 ID면 이력 유지",
          f_id["first"] is not None and f_id["pct"] > f_no["pct"],
          f"ID 있음 {fmt(f_id)} / ID 없음 {fmt(f_no)}")

    # G. 같은 자리라도 ID가 다르면 다른 차 → 이력이 이어지면 안 된다
    g = run_two_ids(seq_parked(120))
    check("G. 같은 위치라도 ID가 바뀌면 새 차로 취급",
          g["restarted"], g["detail"])

    # H. 이슈 #15 — SLOT_EXPIRE_SEC 을 늘려도 크래시하지 않아야 한다
    check("H. SLOT_EXPIRE_SEC=20 에서 크래시 없음", *check_expire_crash())

    print("\n" + ("전부 PASS" if not _fails else f"FAIL {len(_fails)}건: {_fails}"))
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
