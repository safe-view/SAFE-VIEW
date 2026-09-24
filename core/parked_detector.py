# core/parked_detector.py — 정지 차량 자체 판단 모듈
#
# 동작 원리 (AI 추적 알고리즘 없이 좌표 비교만 사용):
#   1. 매 프레임마다 감지된 차량의 위치를 기록
#   2. 비슷한 위치에 있는 차량은 같은 차량으로 간주 (단순 거리 매칭)
#   3. 1~2개 샘플의 잡음은 무시하고, 3개 연속 이탈로 실제 움직임을 확인
#      박스 크기 변화는 같은 방향으로 3연속이어야 움직임으로 본다 — 다가오거나
#      멀어지는 차는 한 방향으로 꾸준히 변하고, 검출 잡음은 위아래로 진동한다
#      최근 10초간 정지 상태이고, 마지막 확인된 움직임에서 90초가 지나면 정지로 판정
#      움직임을 관찰한 적 없는 차량은 10초 정지만으로 판정
#   4. ByteTrack 같은 무거운 알고리즘 안 씀 → CPU 부하 거의 없음

import time
import math
from statistics import median

# 슬롯은 위치 이력, 마지막 감지/이동 시각, 이동 기준점과 연속 이탈 횟수를 보관
_slots: list[dict] = []

# 설정값
MATCH_DISTANCE_PX  = 80.0    # 두 프레임의 차량을 같은 차로 보는 최대 거리 (px)
STATIONARY_SECONDS = 10.0    # 정지로 판정할 최소 시간 (초)
# 마지막 움직임 이후 정지 판정을 유예할 시간 (초).
# 횡단보도 양보처럼 잠깐 멈춘 차가 주차로 오인돼 위험 판정에서 빠지는 것을 막는 값이다.
# 도입 당시(PR #3) 90초는 "실영상 검증 후 조정" 전제의 잠정값이었고, 실제로 재보니
# 주차한 차가 인식되기까지 100초 넘게 걸렸다.
#
# 이 값은 STATIONARY_SECONDS 보다 커야만 의미가 있다 — 차가 멈춘 시점부터
# "최근 10초간 정지" 조건과 이 유예 조건이 각각 풀리는데, 유예가 10초 이하면
# 정지 조건이 풀리는 시점에 이미 함께 풀려서 아무 역할도 하지 못한다.
# (실측: 유예 5초·9초·10초의 결과가 모두 동일했다.)
# 15초면 정지 10초와 합쳐 25초 — 보통 5~15초인 양보·서행 정차는 계속 걸러내면서
# 실제 주차 차량은 90초일 때보다 훨씬 빨리 인식된다.
RECENT_MOTION_GRACE_SECONDS = 15.0
MOTION_CONFIRM_SAMPLES = 3  # 연속 이탈 확인에 필요한 샘플 수
REFERENCE_SAMPLES = 5  # 기준점의 중앙값에서 최대 2개 잡음을 완화
# 기준 면적 대비 이 비율 이상 변화가 같은 방향으로 3연속이면 움직임으로 본다.
# 실제 영상에서 멈춰 있는 차의 박스 면적 변화를 재보니 중앙값이 4~23% 였다.
# 20%로 두면 이 잡음이 그대로 "움직임"으로 찍혀 유예 타이머가 1초에 한 번꼴로
# 리셋되고, 결국 주차 판정이 영영 나지 않았다. 다가오는 차의 면적 변화는
# 이보다 훨씬 크므로(실측 합성에서 200%) 35%로 올려도 후진 차량은 계속 걸러진다.
AREA_CHANGE_RATIO = 0.35
MOVE_THRESHOLD_PX  = 30.0    # 이 거리 이내로만 움직이면 "정지"로 봄
SLOT_EXPIRE_SEC    = 5.0     # 이 시간 동안 안 보이면 슬롯 삭제 (메모리 정리)


def _distance(p1, p2) -> float:
    """두 점 사이의 거리"""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def _median_center(positions) -> tuple:
    """단일 검출 잡음이 기준점이 되지 않도록 좌표별 중앙값 사용."""
    return tuple(median(p[axis] for _, p in positions) for axis in (0, 1))


def _area_change_direction(reference: float, area: float) -> int:
    """
    기준 면적 대비 유의미한 변화가 있으면 그 방향을 돌려줍니다.

    반환: +1 커짐, -1 작아짐, 0 변화 없음(또는 비교 불가)

    방향까지 보는 이유 — 카메라 쪽으로 다가오거나 멀어지는 차는 박스가 한
    방향으로 꾸준히 커지거나 작아집니다. 반면 가림·조명 때문에 생기는 검출
    박스 떨림은 기준값 위아래로 진동합니다. 크기 변화량만 보면 이 둘을 구분할
    수 없어, 제자리에 선 차가 "움직였다"로 오인됩니다.
    """
    if reference <= 0 or area <= 0:
        return 0
    if abs(area - reference) / reference < AREA_CHANGE_RATIO:
        return 0
    return 1 if area > reference else -1


def update(car_centers: list[tuple], car_areas: list[float]) -> list[bool]:
    """
    현재 프레임의 차량 중심 좌표 리스트를 받아,
    각 차량이 "정지 상태"인지 여부를 같은 순서의 리스트로 반환합니다.

    car_centers: [(cx, cy), (cx, cy), ...]  현재 프레임의 모든 차량 중심점
    car_areas: 중심점과 같은 순서의 바운딩박스 면적 리스트
    반환: [True/False, True/False, ...]      각 차량의 정지 여부
    """
    now = time.time()
    matched_slots = set()
    results = [False] * len(car_centers)

    # 1) 현재 프레임의 각 차량을 가장 가까운 기존 슬롯과 매칭
    for idx, center in enumerate(car_centers):
        best_slot_idx = -1
        best_distance = MATCH_DISTANCE_PX

        for s_idx, slot in enumerate(_slots):
            if s_idx in matched_slots:
                continue   # 이미 다른 차량에 매칭된 슬롯은 건너뜀
            last_pos = slot["positions"][-1][1]
            dist = _distance(last_pos, center)
            if dist < best_distance:
                best_distance = dist
                best_slot_idx = s_idx

        if best_slot_idx >= 0:
            # 기존 슬롯에 매칭 → 위치 추가
            slot = _slots[best_slot_idx]
            slot["positions"].append((now, center))
            area = car_areas[idx]
            slot["areas"].append((now, area))
            if slot["motion_anchor"] is None:
                if len(slot["positions"]) >= REFERENCE_SAMPLES:
                    slot["motion_anchor"] = _median_center(
                        slot["positions"][:REFERENCE_SAMPLES]
                    )
            elif _distance(slot["motion_anchor"], center) >= MOVE_THRESHOLD_PX:
                slot["motion_count"] += 1
                if slot["motion_count"] >= MOTION_CONFIRM_SAMPLES:
                    slot["last_motion_ts"] = now
                    slot["motion_anchor"] = _median_center(
                        slot["positions"][-MOTION_CONFIRM_SAMPLES:]
                    )
                    slot["motion_count"] = 0
            else:
                slot["motion_count"] = 0
            if slot["area_anchor"] is None:
                if len(slot["areas"]) >= REFERENCE_SAMPLES:
                    slot["area_anchor"] = median(a for _, a in slot["areas"][:REFERENCE_SAMPLES])
            else:
                direction = _area_change_direction(slot["area_anchor"], area)
                if direction == 0:
                    slot["area_motion_count"] = 0
                    slot["area_motion_dir"] = 0
                else:
                    # 같은 방향으로 연속해야 실제 이동으로 본다.
                    # 방향이 뒤집히면 떨림이므로 처음부터 다시 센다.
                    if direction != slot["area_motion_dir"]:
                        slot["area_motion_count"] = 0
                        slot["area_motion_dir"] = direction
                    slot["area_motion_count"] += 1
                    if slot["area_motion_count"] >= MOTION_CONFIRM_SAMPLES:
                        slot["last_motion_ts"] = now
                        slot["area_anchor"] = median(
                            a for _, a in slot["areas"][-MOTION_CONFIRM_SAMPLES:]
                        )
                        slot["area_motion_count"] = 0
                        slot["area_motion_dir"] = 0
            slot["last_seen"] = now
            matched_slots.add(best_slot_idx)
            # 정지 여부 판정
            last_motion_ts = slot["last_motion_ts"]
            results[idx] = _is_stationary(slot, now) and (
                last_motion_ts is None
                or now - last_motion_ts >= RECENT_MOTION_GRACE_SECONDS
            )
        else:
            # 새 슬롯 생성
            _slots.append({
                "positions": [(now, center)],
                "areas": [(now, car_areas[idx])],
                "last_seen": now,
                "last_motion_ts": None,
                "motion_anchor": None,
                "motion_count": 0,
                "area_anchor": None,
                "area_motion_count": 0,
                "area_motion_dir": 0,
            })
            # 새 차량은 당연히 정지 아님

    # 2) 오래된 슬롯 정리 (메모리 누수 방지)
    _slots[:] = [s for s in _slots if now - s["last_seen"] <= SLOT_EXPIRE_SEC]

    # 3) 각 슬롯의 위치 이력 중 너무 오래된 것은 잘라냄
    cutoff = now - (STATIONARY_SECONDS * 1.5)
    for slot in _slots:
        slot["positions"] = [(t, p) for t, p in slot["positions"] if t >= cutoff]
        slot["areas"] = [(t, a) for t, a in slot["areas"] if t >= cutoff]

    return results


def _is_stationary(slot: dict, now: float) -> bool:
    """슬롯의 위치와 면적 이력을 보고 정지 여부 판단"""
    positions = slot["positions"]
    if len(positions) < 2:
        return False

    # STATIONARY_SECONDS 이전 시점의 위치 찾기
    cutoff = now - STATIONARY_SECONDS
    old_pos = None
    old_index = 0
    for index, (ts, pos) in enumerate(positions):
        if ts <= cutoff:
            old_pos = pos
            old_index = index
        else:
            break

    if old_pos is None:
        return False   # 아직 그만큼 데이터가 없음

    # 구간 경계의 단일 잡음도 기준점을 왜곡하지 않도록 중앙값 사용
    start = max(0, old_index - REFERENCE_SAMPLES + 1)
    reference = _median_center(positions[start:start + REFERENCE_SAMPLES])
    consecutive = 0
    for _, pos in positions[old_index + 1:]:
        if _distance(reference, pos) >= MOVE_THRESHOLD_PX:
            consecutive += 1
            if consecutive >= MOTION_CONFIRM_SAMPLES:
                return False
        else:
            consecutive = 0
    areas = slot["areas"]
    area_reference = median(a for _, a in areas[start:start + REFERENCE_SAMPLES])
    consecutive = 0
    last_direction = 0
    for _, area in areas[old_index + 1:]:
        # 위 update() 와 같은 기준: 같은 방향으로 연속해야 실제 이동으로 본다.
        # 방향이 뒤집히는 것은 검출 박스 떨림이므로 다시 센다.
        direction = _area_change_direction(area_reference, area)
        if direction == 0:
            consecutive = 0
            last_direction = 0
            continue
        if direction != last_direction:
            consecutive = 0
            last_direction = direction
        consecutive += 1
        if consecutive >= MOTION_CONFIRM_SAMPLES:
            return False
    return True


def reset() -> None:
    """모니터링 시작/정지 시 모든 상태 초기화"""
    _slots.clear()


def get_slot_count() -> int:
    """현재 추적 중인 차량 슬롯 수 (디버그용)"""
    return len(_slots)
