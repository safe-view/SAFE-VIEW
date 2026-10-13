# 현재 작업

## 상태

**State:** `verified`
**기준 커밋:** `6c140e3036860afeecf7eb3c13f6e58f15d9f982`
**승인 필요:** 아니오 (경고음 재생 방식만 바꾸는 것 — `is_danger` 판정 로직(`core/danger_logic.py`) 자체는 무변경. 사용자가 명시적으로 요청.)
**최종 갱신:** 사용자 실사용 확인 완료 ("내가 원하는대로 잘 작동해"), 2026-10-13

이 작업은 "위험 상태 지속 중 경고음 계속 재생"이다. 직전 "모니터링 FPS 중복 표시 재수정 + ROI 저장 확인 메시지 위치 이동"은 `verified`로 종료되어 PR #24로 머지됐다(`docs/tasks/archive/2026-10-13-fps-roi-fixes-verified.md` 참고).

## 1. 목표

현재 `pages/1_모니터링.py`의 경고음은 위험 상태로 **전환되는 순간에만** 약 2초짜리 삑삑 클립(2비프×3묶음=6회)을 한 번 재생하고 끝난다 — 위험이 계속 이어져도 추가로 울리지 않고, 15초 쿨다운(`last_event_ts`)까지 걸려 있다. 이걸 **"화면이 위험 상태인 동안에는 경고음이 끊기지 않고 계속 울린다"**로 바꾼다. 위험 상태가 끝나면(`is_danger`가 `False`로 돌아가면) 경고음도 멈춘다.

**핵심 제약**: `event_triggered`/`last_event_ts`(15초 쿨다운)는 소리뿐 아니라 **이벤트 클립 저장**(926행)과 **최근 이벤트 목록 갱신**(996행)에도 같이 쓰이고 있다. 이 작업은 소리 재생 로직만 분리해서 바꾸고, 이벤트 클립 저장 빈도(15초 쿨다운 포함)는 **절대 건드리지 않는다** — 그대로면 위험이 10분 지속돼도 클립은 여전히 15초에 한 번 꼴로만 저장돼야 한다. `core/danger_logic.py`(`is_danger` 판정 자체)도 무변경.

## 2. 현재 상태

`pages/1_모니터링.py` 관련 코드:

- 1~46행: `_make_beep_b64()`로 880Hz 비프음 wav를 코드에서 직접 생성해 base64로 임베드(`ALERT_BEEP_B64`). 기본값: 비프 2개가 한 묶음, 묶음 3개, 묶음당 비프 간격 0.1초, 묶음 사이 간격 0.35초, 비프 길이 0.18초 → 전체 클립 길이 약 2.08초.
- 694행: `sound_ph = st.empty()` — 경고음 재생용 placeholder.
- 889~903행(현재 로직):
  ```python
  event_triggered = False
  if is_danger and not st.session_state.prev_danger:
      if now - st.session_state.last_event_ts > 15.0:
          event_triggered                = True
          st.session_state.last_event_ts = now
          st.session_state.alert_msg     = "🚨 보안 구역 내 위험 감지!"
          st.session_state.alert_expires = now + 4.0
          with sound_ph.container():
              components_html(
                  f'<audio autoplay src="data:audio/wav;base64,{ALERT_BEEP_B64}"></audio>',
                  height=0,
              )
  st.session_state.prev_danger = is_danger
  ```
  `is_danger and not prev_danger` = 위험 상태로 막 전환된 "그 프레임"에서만 True. `event_triggered`는 926행(이벤트 클립 저장 트리거)과 996행(최근 이벤트 목록 갱신 트리거)에서도 쓰인다.
- `<audio autoplay src=...>`는 Streamlit이 markdown 내 `<script>`를 막아서 `components.v1.html()`로 새 iframe을 매번 만들어 강제 재생하는 방식이다(기존에 이미 검증된 패턴).

## 3. 구현 계획

1. **소리 트리거를 이벤트/쿨다운 로직과 분리**: `event_triggered`/`last_event_ts` 15초 쿨다운 블록은 지금 그대로 둔다(이벤트 클립 저장용으로만 계속 쓰임). 경고음은 `is_danger`와 `st.session_state.prev_danger`만 보고 별도로 판단한다:
   - `is_danger`가 `False`→`True`로 바뀌는 프레임(상승 엣지)에 `ALERT_BEEP_B64`를 **`loop` 속성을 추가해서** 재생 시작: `<audio autoplay loop src="data:audio/wav;base64,{ALERT_BEEP_B64}"></audio>`. 약 2초짜리 클립이 `loop`로 끊김 없이 반복되므로 "위험 상태 내내 계속 울림"이 된다.
   - `is_danger`가 `True`로 유지되는 동안(이미 같은 iframe이 재생 중인 프레임들)에는 **다시 삽입하지 않는다** — 매 프레임 새 iframe을 만들면 재생이 뚝뚝 끊기며 재시작된다. `prev_danger`가 이미 `True`였던 프레임에는 건드리지 않는다.
   - `is_danger`가 `True`→`False`로 바뀌는 프레임(하강 엣지)에 `sound_ph.empty()`로 iframe을 제거해 재생을 멈춘다.
2. **깜빡임(hysteresis) 고려**: `is_danger`는 프레임 단위 판정이라 검출이 순간적으로 흔들리면 한두 프레임만 `False`가 됐다가 바로 `True`로 돌아올 수 있다. 이 경우 지금 방식대로면 소리가 꺼졌다 켜졌다 뚝뚝 끊기는 느낌을 줄 수 있다. 실제로 이게 체감될 정도인지 확인하고, 거슬리면 "최근 N프레임 중 하나라도 위험이면 계속 위험으로 간주" 같은 짧은 유예를 소리 트리거에만 추가하는 것을 고려하라(강제하지 않음 — 먼저 단순한 방식으로 구현하고 실제로 문제가 보이면 추가). 이 유예는 이벤트 클립 저장 쿨다운(15초)과는 별개의, 훨씬 짧은(예: 1초 이내) 것이어야 한다.
3. `_make_beep_b64()`의 기본 파라미터(음높이·묶음 구성 등)는 바꾸지 않는다 — 반복 재생 방식만 바꾸는 것이지 소리 자체를 바꾸는 게 아니다.

## 4. 수용 기준

- [ ] 위험 상태가 10초 이상 지속되는 테스트 영상에서, 경고음이 중간에 끊기지 않고 계속 들린다(기존처럼 한 번 짧게 울리고 끝나지 않는다).
- [ ] 위험 상태가 끝나면(사람이 ROI를 벗어나는 등) 경고음이 멈춘다 — 위험이 아닌데 계속 울리지 않는다.
- [ ] 이벤트 클립 저장 빈도는 그대로다 — 위험이 10초 이상 지속돼도 클립이 반복 저장되지 않고 기존처럼 15초 쿨다운이 유지된다(`event_triggered`/`last_event_ts` 로직 무변경 확인).
- [ ] "최근 이벤트" 목록 갱신 빈도도 그대로다(996행 `event_triggered` 조건 무변경).
- [ ] `core/danger_logic.py`(`is_danger` 판정 로직)는 단 한 줄도 바뀌지 않는다.
- [ ] 비프음 자체의 음높이·패턴(`_make_beep_b64` 기본값)은 바뀌지 않는다 — 반복 재생 방식만 바뀐다.
- [ ] 다른 위젯·페이지 라우팅·`core/*.py`는 무변경.

## 5. 예상 변경 파일

- `pages/1_모니터링.py`
- `docs/tasks/current.md`
- `roi_configs/GTA__비__주간__2.json` (이번 작업과 무관하게 이전부터 존재하던 사용자 테스트 데이터 — 그대로 둠)
- `roi_configs/같은_장소_비_2_야간.json` (위와 동일 사유)
- `roi_configs/전체_측면_배회_야간_1.json` (위와 동일 사유 — 사용자가 앱에서 직접 저장한 ROI 테스트 데이터)

## 6. 파일 소유권

| 파일 | 소유자 | 상태 |
|---|---|---|
| `pages/1_모니터링.py` | Codex (구현/테스트) | 착수 가능 |
| `docs/tasks/current.md` | Claude (계획/리뷰) | 계획 작성 완료 |

## 7. 위험 요소 또는 주의사항

- `event_triggered`/`last_event_ts` 쿨다운을 실수로 소리 로직과 같이 바꾸지 않도록 주의 — 이벤트 클립이 위험 지속 중 반복 저장되면 디스크 용량·이벤트 목록 스팸 문제가 생긴다.
- `<audio autoplay loop>`가 실제 브라우저에서 끊김 없이 반복되는지는 이 샌드박스에서 직접 확인하기 어렵다(헤드리스 브라우저 사용 금지 — 반복 시도하지 말 것). 코드 논리로 확인 가능한 것까지만 확인하고, 최종 청취 확인은 사용자가 한다고 명시하라.
- `is_danger` 깜빡임으로 소리가 뚝뚝 끊기면 사용자 경험이 나쁘다 — 2번 항목의 짧은 유예를 필요시에만 가볍게 추가하되 과도하게 복잡한 상태 머신을 만들지 마라.
- 매 프레임 `is_danger` 체크 자체는 가볍지만, `sound_ph.empty()`/새 iframe 삽입이 불필요하게 자주 일어나지 않도록(= 정말 엣지에서만 호출되도록) 조건을 정확히 짜라.

## 구현 결과
- 실제 변경 파일:
  - `pages/1_모니터링.py`
  - `docs/tasks/current.md`
- 계획 대비 변경 요약: 위험 상태 상승 엣지에서 `autoplay loop` 오디오 iframe을 한 번 삽입하고, 하강 엣지에서 `sound_ph.empty()`로 제거하도록 경고음 로직을 이벤트 저장 로직과 분리했다. `event_triggered`/`last_event_ts` 15초 쿨다운과 그 소비 지점은 변경하지 않았다.
- 계획 이탈 사항: 없음
- 종료 시점 git 상태 (`git -c core.quotepath=false status --porcelain --untracked-files=all`):
  ```text
   M docs/tasks/current.md
   M pages/1_모니터링.py
  ?? roi_configs/GTA__비__주간__2.json
  ?? roi_configs/같은_장소_비_2_야간.json
  ?? roi_configs/전체_측면_배회_야간_1.json
  ```
  위 ROI JSON 3개는 계획에 기록된 기존 사용자 테스트 데이터로 수정하지 않았다.

## 테스트 결과
- 실행 명령/검증:
  - UTF-8로 파일을 읽는 Python 정적 검사: `ast.parse` 구문 분석, `autoplay loop` 오디오 1개, 기존 비반복 오디오 0개, 하강 엣지의 `sound_ph.empty()`, 15초 쿨다운 조건 1개를 assertion으로 확인 — PASS
  - `git diff --check` — PASS (오류 없음, 기존 줄바꿈 변환 경고만 출력)
  - `git diff -- pages/1_모니터링.py core/danger_logic.py` 및 변경 파일 목록 확인 — PASS (`core/danger_logic.py` 무변경, 계획된 코드 변경만 존재)
- 수용 기준 체크리스트:
  - [x] **PASS** (사용자 실사용 확인) — 위험 상태가 10초 이상 지속되는 테스트 영상에서, 경고음이 중간에 끊기지 않고 계속 들린다(기존처럼 한 번 짧게 울리고 끝나지 않는다).
  - [x] **PASS** (사용자 실사용 확인) — 위험 상태가 끝나면(사람이 ROI를 벗어나는 등) 경고음이 멈춘다 — 위험이 아닌데 계속 울리지 않는다.
  - [x] **PASS** — 이벤트 클립 저장 빈도는 그대로다 — 위험이 10초 이상 지속돼도 클립이 반복 저장되지 않고 기존처럼 15초 쿨다운이 유지된다(`event_triggered`/`last_event_ts` 로직 무변경 확인).
  - [x] **PASS** — "최근 이벤트" 목록 갱신 빈도도 그대로다(996행 `event_triggered` 조건 무변경).
  - [x] **PASS** — `core/danger_logic.py`(`is_danger` 판정 로직)는 단 한 줄도 바뀌지 않는다.
  - [x] **PASS** — 비프음 자체의 음높이·패턴(`_make_beep_b64` 기본값)은 바뀌지 않는다 — 반복 재생 방식만 바뀐다.
  - [x] **PASS** — 다른 위젯·페이지 라우팅·`core/*.py`는 무변경.
- 미실행 항목과 사유: 실제 브라우저에서 10초 이상 위험 영상을 재생해 청취해야 하는 첫 두 항목은 샌드박스에서 확인할 수 없고, 계획에서 헤드리스 브라우저 사용을 금지했으므로 미실행했다. 사용자의 실제 화면·청취 확인이 필요하다.

## 리뷰 및 남은 위험

- 리뷰 결과: approved
- 요약: 소리 트리거를 이벤트/쿨다운 로직에서 완전히 분리해 상승 엣지에서 `autoplay loop` iframe을 삽입하고 하강 엣지에서 `sound_ph.empty()`로 제거하는 계획이 코드에 정확히 반영됐다. `event_triggered`/`last_event_ts` 15초 쿨다운 블록은 무변경이며 범위 밖 파일 수정도 없다. 실제 브라우저 청취 확인(수용 기준 1·2) 은 사용자가 직접 수행해야 한다.
- scope_ok: True
- 수용 기준 판정:
  - [not_run] 위험 상태 10초 이상 지속 → 경고음이 끊기지 않고 계속 들린다
  - [not_run] 위험 상태 종료 → 경고음이 멈춘다
  - [pass] 이벤트 클립 저장 빈도 무변경 (15초 쿨다운 유지)
  - [pass] 최근 이벤트 목록 갱신 빈도 무변경 (996행 event_triggered 조건)
  - [pass] core/danger_logic.py 무변경
  - [pass] _make_beep_b64 기본값 무변경 (반복 재생 방식만 변경)
  - [pass] 다른 위젯·페이지 라우팅·core/*.py 무변경
- 남은 위험/후속 작업:
  - 수용 기준 1·2(실제 브라우저 청취)는 미실행 — 10초 이상 위험이 지속되는 영상을 재생해 경고음이 계속 울리는지, 위험 종료 시 멈추는지 사용자가 직접 청취 확인 필요
  - is_danger 깜빡임(한두 프레임 False→True 반복) 시 소리가 끊겼다 켜지는 현상 발생 가능 — hysteresis 미적용(계획상 단순 방식 우선), 체감되면 짧은 유예(1초 이내)를 소리 트리거에만 추가하는 후속 작업 필요
- (Harness가 검증된 Claude 리뷰 JSON을 기계적으로 반영한 결과입니다.)

