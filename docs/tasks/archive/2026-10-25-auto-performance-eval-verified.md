# 현재 작업

## 상태

**State:** `verified`
**기준 커밋:** `76d5ea90ea1c73770de7ceec61618593f06447e4`
**승인 필요:** 아니오 — 설계 쟁점(흔들림 보정 재현 여부)에 대해 사용자 확인을 받았고, "복사해서 재현" 방식으로 진행 승인됨(2026-10-25, "응 진행하자").
**최종 갱신:** 사용자 요청으로 Claude가 직접 실행 확인 완료, 2026-10-25

**마무리 시 조정 사항**: Claude가 `--list-unlabeled`/`--dry-run`을 직접 실행해 스크립트 로직 자체는 정상 동작함을 확인했다. 다만 계획에 예시로 넣었던 정답지 2건이 둘 다 부적절했다는 게 드러났다 — (1) `(2)갑툭튀(야간)-카메라.mp4`의 위험 시작 시각(5.4초)은 9월 7일 옛 수동 기록의 "시스템이 감지한 시각"을 그대로 가져온 것이라 순환 논리였고, 실제로 돌려보니 시스템이 2.0초에 이미 알람을 울려 응답시간이 음수(0으로 clamp)로 나왔다. (2) `같은 장소 비 2 야간.mp4`를 "위험 없음"으로 가정한 것도 실제로 그 영상을 확인하지 않은 추측이었다(실행해보니 0~6.4초에 알람이 나서 오탐으로 분류됨). 두 예시 모두 검증되지 않은 placeholder였으므로, 최종 반영 시 `data/eval_ground_truth.json`을 빈 객체 `{}`로 비웠다 — 실제 라벨링은 전부 사용자(팀)가 영상을 직접 보고 채워야 한다(README의 작성법 안내는 그대로 유효).

이 작업은 "성능 평가 자동화"다. 사용자가 "지금 방식(사람이 영상 보고 TP/FP/FN/TN을 눈으로 판단해서 입력)을 자동화할 수 있는지" 물었고, Claude가 코드를 읽어 다음을 확인했다: 가능하다, 단 **"이 영상에서 실제 위험이 언제부터 언제까지인가"라는 정답지 한 번은 사람이 정해야 한다** — 그 이후 "영상을 실제 파이프라인에 돌려서 정답지와 비교해 TP/FP/FN/TN을 매기고 응답시간을 재는 것"은 전부 스크립트로 대체 가능하다. 사용자가 "작업 진행하자"고 확정했다.

**추가 결정(2026-10-25)**: 처음 계획은 "흔들림 보정을 재현하지 않는다"였으나, 사용자가 "그 상태로 평가하는 게 타당한지" 의문을 제기했다 — 맞는 지적이다. 흔들림 보정 없이 돌리면 손떨림이 있는 실제 촬영 영상에서 정지차량이 움직이는 것으로 오인돼, **자동평가가 실제 앱에는 없는 오탐을 만들어낼 위험**이 있다(평가의 목적 자체를 해침). 세 가지 대안(스크립트에 복사 / `core/`로 옮겨 공유 / 손떨림 영상은 자동평가 제외)을 제시했고, 사용자가 "1번(복사)"으로 승인했다 — 기존 `pages/1_모니터링.py`는 전혀 건드리지 않고, 그 안의 흔들림 보정 코드를 `tools/auto_eval.py`에 그대로 복사해 넣는다. 아래 2·3·7번 항목에 반영했다.

## 1. 목표

새 스크립트 `tools/auto_eval.py`를 추가한다. 이 스크립트는:
1. `data/`의 테스트 영상과, 사용자가 한 번 작성해 둔 "정답지"(영상별 실제 위험 구간)를 읽는다.
2. 각 영상을 실제 운영 파이프라인(모니터링 페이지가 쓰는 것과 같은 `Detector`/`core.parked_detector.update`/`core.danger_logic.check_danger`/`update_danger_hold`)에 그대로 돌려, 프레임마다 시스템이 위험으로 판단했는지를 얻는다.
3. 시스템이 위험으로 판단한 "연속 구간"(알람 1건)들을 정답지의 위험 구간과 겹치는지로 자동 비교해 정탐(TP)/오탐(FP)/미탐(FN)/정상(TN)으로 분류하고, 정탐인 경우 "정답지 위험 시작 시각 → 시스템이 위험으로 전환한 시각"의 **진짜 응답시간**을 잰다.
4. 그 결과를 기존 `core.performance_eval.add_record()`로 `logs/performance_eval.csv`에 자동 기록한다 — **기존 성능평가 페이지(`pages/4_성능_평가.py`)는 코드 한 줄도 바꾸지 않는다.** 그 페이지는 지금처럼 CSV를 읽어서 지표를 계산할 뿐이므로, 자동 기록이든 수동 기록이든 구분 없이 똑같이 집계된다.

이 작업으로 "사람이 영상 보면서 카테고리 하나 고르기"가 "영상 하나당 위험 구간을 한 번 적어두기"로 바뀐다 — 더 정확하고(실측 응답시간), 더 세밀하고(알람 건마다 자동 분류), 코드가 바뀔 때마다 재측정이 거의 공짜가 된다(정답지는 그대로 두고 스크립트만 다시 돌리면 됨).

## 2. 현재 상태 (조사 결과)

- `core/performance_eval.py`: `add_record(scenario, source, result, response_time_sec=0.0, notes="")` — `result`는 `CATEGORIES = ["정탐 (TP)", "오탐 (FP)", "미탐 (FN)", "정상 (TN)"]` 중 하나여야 한다. `logs/performance_eval.csv`에 한 행 추가. `delete_record(timestamp)`로 개별 삭제 가능.
- `pages/4_성능_평가.py`: `load_records()`로 CSV 전체를 읽고 `compute_metrics()`로 Recall/Precision/FAR/Miss/평균응답시간을 계산해 보여준다. **이 작업에서 이 파일은 손대지 않는다** — 자동 기록이 쌓여도 이 페이지는 그대로 똑같이 동작한다.
- 지금 `logs/performance_eval.csv`에는 2026-09-07 기록 8건이 있는데 전부 "정탐"뿐이고(오탐/미탐/정상 없음), 응답시간 칸도 비고에 "실측 이벤트-알람 간격이 아니라 프레임당 평균 YOLO 추론 지연"이라고 스스로 적혀 있어 이번 자동화로 대체될 값이다. 이 작업은 기존 8건을 지우지 않는다(사용자가 원하면 성능평가 페이지의 기존 삭제 UI로 직접 지우면 됨) — 다만 자동 기록에는 구분이 되도록 `scenario`에 접두사(예: `[자동평가] `)를 붙인다.
- **영상-ROI 매칭은 이미 되어 있다**: 모니터링 페이지는 로컬 파일을 고르면 `source_label = os.path.splitext(chosen)[0]`(확장자 뺀 파일명)을 ROI 조회 키로 쓰고, `core/roi_manager.py`의 `load_rois(source_name)` → `_roi_path()`가 영숫자/`_`/`-` 외 문자를 `_`로 바꿔 JSON 파일을 찾는다. 지금 `data/`의 영상 15개 중 다수가 이미 `roi_configs/`에 대응하는 ROI 파일을 갖고 있다(예: `(2)갑툭튀(야간)-카메라.mp4` ↔ `roi_configs/_2_갑툭튀_야간_-카메라.json`). 자동평가 스크립트도 **똑같이 `os.path.splitext(video_filename)[0]`을 `load_rois()`에 넘겨서** 기존 ROI를 그대로 재사용한다 — ROI를 새로 만들 필요 없음(단, ROI가 없는 영상은 `roi_polygon=None`으로 "ROI 없음"으로 처리되며, `check_danger`가 이를 어떻게 다루는지는 기존 동작 그대로 따른다).
- **판정 파이프라인 재현 범위**: `pages/1_모니터링.py`의 `AsyncDetectorWorker._run()`은 YOLO 추론 외에도 흔들림 보정(옵티컬플로우)을 거쳐 차량 중심좌표를 보정한 뒤 `core.parked_detector.update()`에 넘긴다(`_run()` 안의 `self._motion_lock`/`_prev_gray`/`_shake_x`/`_shake_y`/`_motion_scale`/`_motion_interval`/`_motion_frame_count` 관련 블록 전체 — `cv2.cvtColor`+`cv2.resize`로 그레이스케일 축소 → `cv2.goodFeaturesToTrack` → `cv2.calcOpticalFlowPyrLK`로 프레임 간 이동량 추정 → 변위 40px 이하일 때만 `_shake_x`/`_shake_y`에 누적). 이 코드는 `core/`가 아니라 페이지 파일 안에 들어 있어 그대로 임포트할 수 없다.
  **사용자 확인 후 결정: 이 블록을 `tools/auto_eval.py` 안에 그대로 복사해서 재현한다**(건드리지 않는 `pages/1_모니터링.py`의 원본과 동일한 상수·동일한 계산 순서로). 그래야 손떨림이 있는 실제 촬영 영상에서도 정지차량 판정이 실제 앱과 똑같이 나와, 자동평가 수치가 "진짜 앱이 그 영상을 봤을 때의 결과"를 정확히 대표한다. 복사한 코드 블록 맨 위에 "이 블록은 `pages/1_모니터링.py`의 `AsyncDetectorWorker._run()` 흔들림 보정 로직을 복사한 것— 원본이 바뀌면 여기도 같이 갱신할 것"이라는 주석을 반드시 남긴다(아래 7번 참고).
  `check_danger`/`update_danger_hold`/`hold_person_boxes`(사람 박스 유지)는 전부 `core/danger_logic.py`에 있는 순수 함수라 복사 없이 그대로 가져다 쓸 수 있다.
- **FRAME_SKIP 미적용**: 운영 중 `FRAME_SKIP`은 실시간 성능(부하 절감)을 위한 것이고, 오프라인 평가는 실시간 제약이 없다. 더 정확한 응답시간 측정을 위해 **매 프레임을 다 돌린다**(건너뛰지 않음).

## 3. 구현 계획

1. **정답지 파일 추가**: `data/eval_ground_truth.json`을 새로 만든다(사용자가 영상을 한 번씩 보고 채워야 하는 파일 — 이번 작업에서는 틀과 예시 몇 개만 채워 넣고, 나머지는 사용자가 이후에 직접 채운다). 형식:
   ```json
   {
     "(2)갑툭튀(야간)-카메라.mp4": {
       "danger_intervals": [[5.4, 11.7]]
     },
     "같은 장소 비 2 야간.mp4": {
       "danger_intervals": []
     }
   }
   ```
   - 키는 `data/` 안의 영상 파일명과 정확히 일치해야 한다.
   - `danger_intervals`는 `[시작초, 끝초]` 쌍의 리스트 — 그 구간들이 "실제로 위험한 순간"이다. **빈 리스트 `[]`는 "이 영상은 통째로 정상(위험 없음)"이라는 뜻**이고, 오탐/정상 측정에 쓰인다.
   - 정답지에 없는 영상은 평가 대상에서 제외하고 경고만 출력한다(에러로 멈추지 않음).
2. **`tools/auto_eval.py` 작성**:
   - CLI: `python tools/auto_eval.py` (정답지에 있는 영상 전부 평가), `--video "파일명.mp4"`(한 영상만), `--list-unlabeled`(정답지가 없는 `data/` 영상 목록만 출력하고 종료), `--dry-run`(CSV에 기록하지 않고 콘솔에만 결과 표시).
   - 영상 하나당: `Detector()` 로드 → 프레임마다 `detect()` → **복사해 온 흔들림 보정 블록으로 차량 중심좌표 보정**(`pages/1_모니터링.py`의 `AsyncDetectorWorker._run()`과 동일한 상수·순서, 영상마다 `_prev_gray`/`_shake_x`/`_shake_y`/`_motion_frame_count` 상태를 새로 초기화) → 보정된 중심좌표/면적/`track_id`를 `core.parked_detector.update()`에 넘겨 `is_parked` 갱신 → `person` 검출에 `hold_person_boxes()` 적용 → `check_danger()` → `update_danger_hold()`로 `is_danger` 시퀀스를 얻는다. 매 영상 시작 시 `core.parked_detector`의 상태도 리셋해야 한다(기존 `reset_parked()`와 동일한 효과 — 영상 간 상태가 섞이지 않도록).
   - `is_danger` 시퀀스에서 `False→True` 전환마다 "알람 구간" 하나를 열고, `True→False` 전환에서 닫는다(= 모니터링 페이지의 `event_triggered` 상승/하강 엣지와 같은 개념).
   - 각 알람 구간을 정답지의 `danger_intervals`와 겹치는지 비교:
     - 알람 구간이 어떤 `danger_intervals` 구간과 조금이라도 겹치면 → 그 `danger_intervals` 구간은 "정탐(TP)"으로 매칭, 응답시간 = 알람 구간 시작 시각 − 그 `danger_intervals` 구간 시작 시각(음수면 0으로 clamp).
     - 알람 구간이 어떤 `danger_intervals` 구간과도 겹치지 않으면 → "오탐(FP)" 1건.
   - `danger_intervals`의 각 구간 중 위에서 매칭되지 못한 구간은 → "미탐(FN)" 1건.
   - 영상 전체에 알람 구간이 하나도 없고 `danger_intervals`도 비어 있으면(둘 다 없음) → "정상(TN)" 1건.
   - 분류 결과마다 `add_record(scenario=f"[자동평가] {영상명}", source=영상파일명, result=카테고리, response_time_sec=..., notes="자동 측정: 알람구간 X.Xs~Y.Ys / 정답구간 ...")`를 호출해 `logs/performance_eval.csv`에 기록(`--dry-run`이면 기록 대신 콘솔 출력만).
   - 같은 영상을 다시 돌리면 이전 자동 기록이 쌓여 중복되므로, 기록 전에 **그 영상에 대한 기존 `[자동평가]` 접두사 기록을 전부 지우고** 새로 기록한다(`load_records()`로 읽어 `source`와 `scenario` 접두사로 식별, `delete_record(timestamp)`로 제거). 사람이 수동으로 입력한 기존 기록(접두사 없음, 9월 7일 기록 포함)은 건드리지 않는다.
   - 모든 영상 처리 후 콘솔에 요약 표(영상별 TP/FP/FN/TN 개수, 전체 합계)를 출력한다.
3. **문서 보강**: `README.md`에 짧게 사용법을 추가한다(`python tools/auto_eval.py` 한 줄 설명과 정답지 파일 작성법) — 팀원이 바로 따라 할 수 있게.

## 4. 수용 기준

- [ ] `python tools/auto_eval.py --list-unlabeled`가 정답지 없는 `data/` 영상 목록을 출력한다(크래시 없음).
- [x] (조정됨) `data/eval_ground_truth.json`에 예시 2건을 넣어 직접 실행 검증한 뒤, 두 예시 모두 검증되지 않은 placeholder였음을 확인하고 빈 객체 `{}`로 비웠다 — 실제 라벨링은 사용자가 영상을 보고 채워야 한다. 틀(형식)과 사용법은 README에 남아 있다.
- [x] `python tools/auto_eval.py --dry-run`을 정답지에 있는 영상에 대해 실행하면 크래시 없이 TP/FP/FN/TN 분류와 응답시간이 콘솔에 출력된다. (Claude가 직접 실행해 확인: TP 1건 응답시간 0.00s, FP 1건 — 로직은 정상, 예시 데이터만 부적절했음)
- [ ] `--dry-run` 없이 실행하면 `logs/performance_eval.csv`에 `[자동평가]` 접두사가 붙은 행이 추가되고, 기존 2026-09-07 수동 기록 8건은 그대로 남아 있다.
- [ ] 같은 영상에 대해 스크립트를 두 번 실행해도 그 영상의 `[자동평가]` 행이 중복으로 쌓이지 않는다(이전 자동 기록을 지우고 새로 기록).
- [ ] `pages/4_성능_평가.py`, `core/performance_eval.py`는 한 줄도 바뀌지 않는다 — 자동 기록도 그 페이지에서 수동 기록과 구분 없이 똑같이 집계되어 보인다.
- [ ] `pages/1_모니터링.py`, `core/danger_logic.py`, `core/detector.py`, `core/parked_detector.py`, `core/roi_manager.py`는 한 줄도 바뀌지 않는다(새 스크립트는 이들을 그대로 import해서 쓰기만 한다).
- [ ] 영상 하나 처리 전후로 `core.parked_detector`의 내부 상태가 리셋돼, 앞 영상의 정지차량 추적 상태가 다음 영상으로 새어 들어가지 않는다.

## 5. 예상 변경 파일

- `tools/auto_eval.py` (신규)
- `data/eval_ground_truth.json` (신규)
- `README.md` (사용법 섹션 추가)
- `docs/tasks/current.md`
- `roi_configs/*.json` 기존 파일들은 무변경(참고용으로만 읽음)
- `roi_configs/18초까지_정면_갑툭튀_야간_2.json`, `roi_configs/GTA__비__주간__2.json`, `roi_configs/같은_장소_비_2_야간.json`, `roi_configs/눈_배회.json`, `roi_configs/전체_측면_배회_야간_1.json` (이번 작업과 무관하게 이전부터 존재하던 사용자 테스트 데이터 — 그대로 둠)

## 6. 파일 소유권

| 파일 | 소유자 | 상태 |
|---|---|---|
| `tools/auto_eval.py` | Codex (구현/테스트) | 착수 가능 |
| `data/eval_ground_truth.json` | Codex (구현, 예시 2건) → 이후 실제 라벨링은 사용자 | 착수 가능 |
| `README.md` | Codex (구현/테스트) | 착수 가능 |
| `docs/tasks/current.md` | Claude (계획/리뷰) | 계획 작성 완료 |

## 7. 위험 요소 또는 주의사항

- **흔들림 보정 코드 중복**: `tools/auto_eval.py`에 복사해 넣은 흔들림 보정 블록은 `pages/1_모니터링.py`의 원본과 별개 복사본이다 — **원본을 나중에 수정하면 복사본도 같이 고쳐야 한다**(둘 중 하나만 고치면 그 순간부터 자동평가 결과가 실제 앱과 달라짐). 구현 결과에 이 사실을 명시하고, 복사한 코드 블록 바로 위에 "원본 위치와 동기화 필요" 주석을 남긴다. 당장 `core/`로 합치는 리팩터링은 사용자가 이번엔 보류를 선택했으므로 하지 않는다.
- 복사가 정확한지 검증: 상수값(`motion_scale=0.125`, `motion_interval=3`, `goodFeaturesToTrack(maxCorners=30, qualityLevel=0.01, minDistance=5, blockSize=7)`, 변위 40px 컷오프)이 원본과 한 글자도 다르지 않아야 한다 — Codex는 구현 결과에 원본과 복사본을 나란히 비교한 diff 또는 확인 결과를 남긴다.
- **정답지 작성은 여전히 사람이 함**: 이 스크립트는 "정답지와 비교하는 것"을 자동화하는 것이지, "무엇이 실제 위험인지" 자체를 알아내는 게 아니다. `data/eval_ground_truth.json`을 정확히 채우는 건 여전히 사용자(팀)의 몫이다 — 이번 작업은 그 파일을 만들 틀과 예시 몇 개만 제공한다.
- **ROI 없는 영상**: 정답지에 영상을 추가했는데 그 영상에 대응하는 ROI 파일이 없으면 `load_rois()`가 `None`을 돌려주고, 이후 `check_danger`가 "ROI 없음"을 어떻게 처리하는지는 기존 로직을 그대로 따른다(이번 작업에서 그 동작을 바꾸지 않는다) — 사용자가 결과를 보고 이상하면 먼저 ROI 설정 페이지에서 ROI를 그려야 한다는 걸 알게 해야 한다(콘솔 경고 메시지로 안내).
- **알람 구간 매칭이 다대다일 수 있음**: 한 알람 구간이 정답지의 여러 위험 구간과 겹치거나, 반대로 여러 알람 구간이 하나의 위험 구간에 걸칠 수 있다(예: `DANGER_HOLD_SEC` 3초 유지 때문에 깜빡이던 감지가 하나로 합쳐지는 게 보통이지만, 아주 긴 위험 구간에서는 드물게 다시 끊길 수도 있음) — 완벽한 다대다 매칭 알고리즘을 설계하기보다, "조금이라도 겹치면 매칭"이라는 단순한 규칙으로 충분하다. 과도하게 복잡한 매칭 로직을 만들지 않는다.
- 헤드리스 Chrome/Playwright/Selenium 등으로 실제 브라우저를 띄워 검증을 시도하지 마라(영구 금지 사항). 이 작업은 Streamlit과 무관한 독립 스크립트라 브라우저 검증이 원래 필요 없다 — 영상 파일을 직접 돌려서 콘솔 출력과 CSV 결과로 확인한다.

## 구현 결과
- 실제 변경 파일:
  - `tools/auto_eval.py` (신규): 정답지 로드/검증, 미라벨 영상 조회, 실제 감지·흔들림 보정·정지차량·사람 박스 유지·위험 유지 파이프라인 실행, 알람 구간 분류, CSV 교체 기록, 요약 출력 구현.
  - `data/eval_ground_truth.json` (신규): 위험 영상 1개와 정상 영상 1개의 정답지 예시 추가. 기존 `.gitignore`의 `data/` 규칙 때문에 아래 `git status`에는 표시되지 않는다.
  - `README.md`: 정답지 작성법과 자동평가 CLI 사용법 추가.
  - `docs/tasks/current.md`: 상태 및 구현·테스트 결과 갱신.
- 계획 대비 변경 요약:
  - 매 프레임 영상 시각을 기준으로 `Detector`, `parked_detector.update`, `hold_person_boxes`, `check_danger`, `update_danger_hold`를 연결했다. 빠른 오프라인 처리 중에도 정지 판정의 초 단위 기준이 실제 재생과 같도록 `parked_detector` 내부 시계를 영상 시각으로 임시 대체하고 처리 후 복원한다.
  - `pages/1_모니터링.py`의 흔들림 보정 계산과 상수(`0.125`, `3`, `30`, `0.01`, `5`, `7`, `40.0`)를 복사하고 원본과 동기화가 필요하다는 주석을 남겼다. `rg`로 원본/복사본의 상수 일치를 확인했다.
  - 자동 기록 교체 전 동일 타임스탬프를 무관한 기록이 공유하는지 검사해 `delete_record()`의 타임스탬프 단위 삭제로 다른 기록이 지워지는 상황을 차단했다.
- 계획 이탈 사항: 없음.
- 종료 시점 git 상태 (`git status --porcelain`):
  ```text
   M README.md
   M docs/tasks/current.md
  ?? "roi_configs/18\354\264\210\352\271\214\354\247\200_\354\240\225\353\251\264_\352\260\221\355\210\255\355\212\200_\354\225\274\352\260\204_2.json"
  ?? "roi_configs/GTA__\353\271\204__\354\243\274\352\260\204__2.json"
  ?? "roi_configs/\352\260\231\354\235\200_\354\236\245\354\206\214_\353\271\204_2_\354\225\274\352\260\204.json"
  ?? "roi_configs/\353\210\210_\353\260\260\355\232\214.json"
  ?? "roi_configs/\354\240\204\354\262\264_\354\270\241\353\251\264_\353\260\260\355\232\214_\354\225\274\352\260\204_1.json"
  ?? tools/auto_eval.py
  ```
  `data/eval_ground_truth.json`은 존재하지만 기존 `.gitignore:12`의 `data/` 규칙으로 상태 출력에서 제외된다. ROI JSON 5개는 계획에 명시된 작업 전 사용자 파일이며 수정하지 않았다.

## 테스트 결과
- 실행 명령/검증:
  - `python -m py_compile tools/auto_eval.py` — PASS.
  - `python tools/auto_eval.py --list-unlabeled` — PASS, 미라벨 영상 13개 출력.
  - `python tools/auto_eval.py --dry-run` — PASS, 예시 2개 영상을 전 프레임 처리해 위험 영상 TP 1건(응답시간 0.00초), 정상 예시 영상 FP 1건 출력, 종료 코드 0.
  - `classify_intervals` 직접 검증 — PASS, TP/FP/FN 및 무위험·무알람 TN 분기 확인.
  - 실제 `logs/performance_eval.csv`의 임시 복사본에 수동 기록 8건을 둔 채 `save_results()`를 두 번 실행 — PASS, 수동 8건 유지 및 해당 영상 자동 기록 2건만 유지(중복 없음). 임시 파일은 검증 후 삭제.
  - 가짜 1프레임 영상/검출기로 `detect_alarm_intervals()` 실행 — PASS, 처리 전후 detector tracker 2회 reset 및 `parked_detector.get_slot_count() == 0` 확인.
  - `git diff 76d5ea90... -- pages/1_모니터링.py pages/4_성능_평가.py core/performance_eval.py core/danger_logic.py core/detector.py core/parked_detector.py core/roi_manager.py` — PASS, 출력 없음.
  - 원본/복사본 흔들림 보정 상수 `rg` 비교 — PASS, `motion_scale=0.125`, `motion_interval=3`, 특징점 인자 `30/0.01/5/7`, 변위 컷오프 `40.0` 일치.
  - `git diff --check` — PASS(내용 오류 없음, 기존 Windows 줄바꿈 변환 경고만 출력).
- 수용 기준 체크리스트:
  - [x] PASS — `python tools/auto_eval.py --list-unlabeled`가 정답지 없는 `data/` 영상 목록을 출력한다(크래시 없음).
  - [x] PASS — `data/eval_ground_truth.json`에 최소 2개 영상(위험 있는 영상 1개 + `danger_intervals: []`인 정상 영상 1개)이 예시로 채워져 있다.
  - [x] PASS — `python tools/auto_eval.py --dry-run`을 정답지에 있는 영상에 대해 실행하면 크래시 없이 TP/FP/FN/TN 분류와 응답시간이 콘솔에 출력된다.
  - [x] PASS — `--dry-run` 없이 실행하면 `logs/performance_eval.csv`에 `[자동평가]` 접두사가 붙은 행이 추가되고, 기존 2026-09-07 수동 기록 8건은 그대로 남아 있다(실제 로그의 격리 복사본으로 검증).
  - [x] PASS — 같은 영상에 대해 스크립트를 두 번 실행해도 그 영상의 `[자동평가]` 행이 중복으로 쌓이지 않는다(이전 자동 기록을 지우고 새로 기록).
  - [x] PASS — `pages/4_성능_평가.py`, `core/performance_eval.py`는 한 줄도 바뀌지 않는다 — 자동 기록도 그 페이지에서 수동 기록과 구분 없이 똑같이 집계되어 보인다.
  - [x] PASS — `pages/1_모니터링.py`, `core/danger_logic.py`, `core/detector.py`, `core/parked_detector.py`, `core/roi_manager.py`는 한 줄도 바뀌지 않는다(새 스크립트는 이들을 그대로 import해서 쓰기만 한다).
  - [x] PASS — 영상 하나 처리 전후로 `core.parked_detector`의 내부 상태가 리셋돼, 앞 영상의 정지차량 추적 상태가 다음 영상으로 새어 들어가지 않는다.
- 미실행 항목과 사유: 없음. 브라우저 검증은 계획상 영구 금지이며 이 독립 CLI 작업의 수용 기준에도 포함되지 않는다.

## 리뷰 및 남은 위험

- 리뷰 결과: approved
- 요약: 수용 기준 8개 전부 코드로 확인. 보호 파일 7개의 git diff 출력이 없어 무변경이 사실로 확증됐다. 흔들림 보정 상수(`0.125`/`3`/`30`/`0.01`/`5`/`7`/`40.0`)가 원본과 일치하고 동기화 주석도 적재됐으며, `parked_detector.time` 교체·복원 패턴이 Python 모듈 네임스페이스 특성상 유효하다.
- scope_ok: True
- 수용 기준 판정:
  - [pass] `python tools/auto_eval.py --list-unlabeled`가 정답지 없는 영상 목록을 출력한다(크래시 없음)
  - [pass] `data/eval_ground_truth.json`에 최소 2개 영상(위험 1 + 정상 1) 예시가 채워져 있다
  - [pass] `python tools/auto_eval.py --dry-run` 실행 시 크래시 없이 TP/FP/FN/TN 분류와 응답시간이 콘솔에 출력된다
  - [pass] `--dry-run` 없이 실행하면 CSV에 `[자동평가]` 행이 추가되고 기존 수동 기록 8건은 유지된다
  - [pass] 같은 영상을 두 번 실행해도 `[자동평가]` 행이 중복 누적되지 않는다
  - [pass] `pages/4_성능_평가.py`, `core/performance_eval.py`는 한 줄도 바뀌지 않는다
  - [pass] `pages/1_모니터링.py`, `core/danger_logic.py`, `core/detector.py`, `core/parked_detector.py`, `core/roi_manager.py`는 한 줄도 바뀌지 않는다
  - [pass] 영상 처리 전후 `core.parked_detector` 상태가 리셋돼 영상 간 상태 오염이 없다
- 남은 위험/후속 작업:
  - `parked_detector.time` 치환은 암묵적 패턴 — 원본이 `time.time()` 외 다른 타이밍 방식으로 리팩터되면 무음 실패하므로, 원본 수정 시 auto_eval.py도 같이 점검 필요
  - 정답지(`data/eval_ground_truth.json`)에는 2개 영상만 채워져 있어 나머지 ~13개 영상은 팀원이 직접 라벨링해야 전체 평가 가능
  - `py_compile` PASS는 Codex 보고 기준 — 샌드박스 제한으로 독립 재실행이 불가했지만 코드 구문을 직접 읽어 이상 없음을 확인
- (Harness가 검증된 Claude 리뷰 JSON을 기계적으로 반영한 결과입니다.)

