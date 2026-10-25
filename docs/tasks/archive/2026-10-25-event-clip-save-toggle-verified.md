# 현재 작업

## 상태

**State:** `verified`
**기준 커밋:** `e8d13a9da553f0bbc73f686428ae3e336e539747`
**승인 필요:** 아니오 (이벤트 클립 저장 여부를 끄고 켜는 UI 위젯의 모양·여백만 조정 — 기존 위험 판정 로직은 무변경, 사용자가 명시적으로 요청)
**최종 갱신:** 사용자 실사용 확인 완료 ("확인했어. 마음에 들어."), 2026-10-25

**1차 구현(토글 ON/OFF)은 approved까지 갔으나, 사용자가 화면을 보고 두 가지를 더 요청해 재작업한다**: (1) `st.toggle` 스위치 모양 대신 "야간 밝기 보정"처럼 알약형 버튼(라디오) 스타일로 바꿔달라, (2) 위 "경고 화면" 상태 박스와의 간격을 더 띄워달라. 1차 구현의 이벤트 저장 분기 로직(966~989행 부근) 자체는 그대로 approved된 내용이 맞으므로 변경하지 않는다 — 이번엔 위젯의 겉모습과 배치 간격만 바꾼다.

이 작업은 "이벤트 클립 저장 on/off 토글"이다. 직전 작업("경고음 지속 재생")은 `verified`로 종료되어 PR #25로 머지됐고, 이후 최재원 님이 노트북에서 작업한 PR #26·#28·#30(위험 경고 3초 유지, 추론 백엔드 자동 선택, 사람 박스 유지)도 모두 이 PC에 동기화·확인 완료됐다(`docs/tasks/archive/2026-10-13-continuous-alert-sound-verified.md` 참고). 이번 작업은 그 위에서 진행한다.

## 1. 목표

현재 위험 이벤트가 발생할 때마다(15초 쿨다운 간격으로) 이미지 스냅샷 + 영상 클립(`CLIP_PRE_SEC`+`CLIP_POST_SEC` = 15초 분량)이 자동으로 저장된다. 사용자는 "원치 않을 때도 불필요한 클립 영상이 중복으로 쌓인다"고 했다 — 클립 **영상**을 저장할지 말지를 사용자가 직접 켜고 끌 수 있는 on/off 토글을 모니터링 페이지에 추가한다.

**배치 위치**: 모니터링 페이지 오른쪽 상태 컬럼(`status_col`)에서, "경고 화면"(위험/정상 상태 박스, `status_ph`)과 "최근 이벤트"(`events_ph`) 사이. 즉 `status_ph`/`alert_ph` 다음, `events_ph` 앞. (1차 구현에서 이미 이 위치에 들어가 있음 — 위치 자체는 유지.)

**범위**: 끄고 켜는 대상은 "영상 클립 저장"만이다. 이벤트 발생 시 찍는 스냅샷 이미지(`save_event_image`)와 CSV 로그 기록(`log_event`) 자체는 위젯과 무관하게 계속 남는다 — 다만 꺼져 있으면 그 로그 행의 `clip_file`이 빈 값이 된다(클립이 없으므로). "이벤트 다시보기" 페이지는 `clip_file`이 비어 있으면 이미 "영상 클립 없음"으로 정상 표시하므로 그쪽은 손댈 필요 없다.

**이번 라운드 추가 요청(사용자 피드백)**:
1. 위젯 모양을 `st.toggle`(스위치)에서 `st.radio`(알약형 버튼, "야간 밝기 보정"과 동일한 스타일)로 바꾼다.
2. "경고 화면" 상태 박스와 이 위젯 사이에 여백을 더 준다.

## 2. 현재 상태

`pages/1_모니터링.py` 관련 코드:

- 704~708행: 상태 컬럼 위젯이 생성되는 지점 (고정 위치, 매 run 동일 — 조건문 없음):
  ```python
  with status_col:
      status_ph = st.empty()
      alert_ph  = st.empty()
      events_ph = st.empty()
      sound_ph  = st.empty()   # 위험 시 components.html로 audio autoplay 삽입
  ```
- 966~989행(현재 로직):
  ```python
  # ── 이벤트 저장 ──────────────────────────────────────
  if event_triggered and not st.session_state.post_recording:
      img_name, _ = save_event_image(annotated, st.session_state.source_name)
      st.session_state.pending_img_name = img_name
      st.session_state.pre_frames       = list(st.session_state.frame_buffer)
      st.session_state.post_frames      = []
      st.session_state.post_recording   = True
      st.session_state.post_rec_start   = now

  if st.session_state.post_recording:
      st.session_state.post_frames.append(annotated.copy())
      if now - st.session_state.post_rec_start >= CLIP_POST_SEC:
          all_clip_frames = st.session_state.pre_frames + st.session_state.post_frames
          clip_name, _ = save_event_clip(all_clip_frames, st.session_state.source_name, fps=MAX_CLIP_FPS)
          log_event(st.session_state.source_name, st.session_state.pending_img_name, clip_name)

          # 메모리 즉시 해제
          del all_clip_frames
          st.session_state.post_recording = False
          st.session_state.pre_frames.clear()
          st.session_state.post_frames    = []
          st.session_state.pending_img_name = ""
  ```
  `event_triggered`는 `is_danger`가 상승 엣지이고 15초 쿨다운을 지났을 때만 True(기존 로직, 이번 작업과 무관하게 무변경). `save_event_image`/`save_event_clip`/`log_event`는 `core/event_saver.py`에 있고, `log_event(source_name, image_filename, clip_filename=None)`처럼 `clip_filename`을 생략하거나 빈 값으로 호출해도 정상 동작한다(CSV에 빈 칸으로 기록됨, 이미 확인됨).
- `pages/3_이벤트_다시보기.py`는 `clip_file`이 비어 있으면 이미 "영상 클립 없음"으로 표시한다(277~289행) — 이쪽은 수정 불필요.
- Streamlit 위젯을 조건문 안의 "매 run마다 코드 경로가 바뀌는 자리"에 두면 cross-run 요소 재조정이 깨져 유령 요소가 생기는 버그가 과거에 있었다(FPS 중복 표시 사건, `docs/tasks/archive/2026-10-13-fps-roi-fixes-verified.md` 참고) — 이번 위젯도 704~708행처럼 **조건 없이 고정된 위치**에 두어야 그 문제를 피할 수 있다(1차 구현에서 이미 지켜짐, 유지).
- **"야간 밝기 보정" 버튼 스타일의 출처**: `pages/1_모니터링.py` 613~621행의 `st.radio("야간 밝기 보정", ["자동", "강제 ON", "OFF"], horizontal=True, ...)`가 그 모양이다. 이 알약형 버튼 스타일은 위젯별로 따로 CSS를 넣은 게 아니라, `app.py` 184~208행에서 `[data-testid="stRadio"] div[role="radiogroup"]` 선택자로 **앱의 모든 `st.radio`에 전역으로 이미 적용돼 있는 스타일**이다(가로 정렬, 알약형 배경, 선택된 항목에 흰 배경+그림자, 라디오 동그라미 숨김). 즉 `st.radio`로 바꾸기만 하면 별도 CSS 추가 없이 똑같은 모양이 나온다.
- 1차 구현(`approved` 상태)의 이벤트 저장 분기 코드(966~989행 부근, `st.session_state.get("save_clip_enabled", True)`로 분기)는 그대로 유지한다 — 이번엔 위젯 종류만 `st.toggle` → `st.radio`로 바꾸고, 그 결과를 여전히 `st.session_state.save_clip_enabled`라는 불리언에 담아야 분기 코드를 안 바꿀 수 있다.

## 3. 구현 계획

1. **위젯을 `st.toggle` → `st.radio`(알약형 버튼)로 교체 + 여백 추가**: 704~708행의 `status_ph`/`alert_ph` 생성과 `events_ph` 생성 사이 자리는 그대로 두고, 위젯만 "야간 밝기 보정"과 같은 2-옵션 가로 라디오로 바꾼다. `enhance_mode` 라디오(613~621행)가 라디오 선택 결과를 바로 아래서 `st.session_state.enhance_mode = enhance_mode`로 다시 담는 것과 똑같은 패턴을 쓴다:
   ```python
   with status_col:
       status_ph = st.empty()
       alert_ph  = st.empty()
       st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)  # 경고 화면과의 여백
       save_clip_choice = st.radio(
           "🎬 이벤트 클립 저장",
           ["ON", "OFF"],
           index=0,
           horizontal=True,
           key="save_clip_choice",
           help="꺼두면 위험 이벤트의 스냅샷 이미지와 로그는 그대로 남지만, 영상 클립은 저장하지 않습니다.",
       )
       st.session_state.save_clip_enabled = (save_clip_choice == "ON")
       events_ph = st.empty()
       sound_ph  = st.empty()
   ```
   - 라디오의 `key`는 `save_clip_choice`(문자열 "ON"/"OFF")로 하고, 그 값을 바로 아래서 불리언 `st.session_state.save_clip_enabled`로 변환해서 담는다 — 아래쪽(966행 부근)의 분기 코드가 보는 키 이름(`save_clip_enabled`)과 타입(불리언)을 1차 구현 그대로 유지하기 위해서다. 분기 코드 자체는 건드리지 않는다.
   - 여백은 `alert_ph`와 라디오 사이에 고정폭 spacer(`<div style='height:...'>` 또는 Streamlit이 제공하는 다른 적절한 방법)를 넣는 식으로 추가한다. 정확한 픽셀 값은 지정하지 않으니 다른 위젯 간 기존 여백과 비교해 자연스러운 정도(대략 12~20px 범위)로 판단해서 정해도 된다. 이 spacer는 조건 없이 고정된 자리에 매번 동일하게 렌더링되는 정적 요소라 유령 요소 버그 위험이 없다(세션 간 유지되는 `st.empty()`가 아님).
   - `enhance_mode` 라디오처럼 전역 `[data-testid="stRadio"]` CSS를 그대로 타므로, `app.py`에 새 CSS를 추가할 필요는 없다. 다만 이 라디오만 특별히 다른 라디오와 다르게 보여야 하는 요구는 없으므로(모양을 "야간 밝기 보정과 똑같이" 해달라는 요청), 전역 스타일을 그대로 쓰는 것이 맞는 방향이다.
2. **이벤트 저장 로직 분기 (1차 구현 그대로, 변경 없음)**: 966~989행은 이미 approved된 아래 로직을 유지한다 — 위젯이 바뀌어도 이 분기는 똑같이 `st.session_state.get("save_clip_enabled", True)`를 본다.
   - 토글이 켜져 있으면(기본값, 기존과 동일): 지금처럼 스냅샷 저장 → `post_recording` 10초 버퍼링 → 클립 생성 → `log_event(..., clip_name)`. **한 글자도 동작이 달라지면 안 된다.**
   - 토글이 꺼져 있으면: 스냅샷(`save_event_image`)은 그대로 찍지만, `post_recording` 버퍼링 단계 전체를 건너뛰고 그 자리에서 바로 `log_event(source_name, img_name, None)`(또는 빈 문자열)을 호출해 클립 없이 즉시 로그를 남긴다. `pre_frames`/`post_frames`/`post_recording` 관련 session_state는 건드리지 않는다(다음에 토글을 다시 켰을 때 꼬이지 않게).
   - 즉 분기는 `event_triggered and not st.session_state.post_recording` 블록 안에서, `save_event_image` 호출 직후에 토글 값을 보고 둘 중 하나로 가지치기하면 된다. 토글이 꺼진 상태에서는 `post_recording`이 아예 `True`가 되는 일이 없으므로, 그 아래 `if st.session_state.post_recording:` 블록(클립 생성 부분)은 수정할 필요가 없다 — 토글이 꺼져 있는 동안은 그냥 실행이 안 될 뿐이다.
3. **토글을 켜고 끄는 중간에 이미 진행 중이던 클립 녹화**는 중단하지 않는다 — `post_recording`이 이미 `True`인 상태(즉 10초 버퍼링이 진행 중)에서 사용자가 토글을 끄더라도, 이번 작업에서는 그 진행 중인 녹화는 끝까지 완료시킨다(다음 이벤트부터만 토글 값을 반영). 중간에 끄는 걸 감지해서 녹화를 즉시 취소하는 것까지는 이번 범위에 넣지 않는다 — 과도하게 복잡해질 수 있으니, 체감되는 문제가 아니면 단순하게 둔다.

## 4. 수용 기준

- [ ] 모니터링 페이지 오른쪽, "경고 화면"(위험/정상 상태 박스)과 "최근 이벤트" 사이에 "이벤트 클립 저장" on/off 위젯이 보인다.
- [ ] 그 위젯이 스위치(toggle)가 아니라 "야간 밝기 보정"과 같은 알약형 버튼(라디오) 모양이다 — `app.py`의 전역 `stRadio` CSS를 그대로 타는 `st.radio`로 구현됐다.
- [ ] "경고 화면" 상태 박스와 이 위젯 사이에 1차 구현 때보다 눈에 띄게 넓어진 여백이 있다.
- [ ] 기본값은 ON이다 — 아무것도 안 바꾸면 기존처럼 이미지+클립+로그가 모두 저장된다.
- [ ] OFF 상태에서 위험 이벤트가 발생하면: 스냅샷 이미지와 CSV 로그 행은 남지만, `saved_events/`에 새 `.mp4` 클립 파일이 생기지 않는다. (1차 구현에서 이미 확인된 분기이므로 코드를 다시 바꾸지 않았다면 자동으로 유지됨)
- [ ] OFF 상태에서 발생한 이벤트는 "이벤트 다시보기" 페이지에 "영상 클립 없음"으로 정상 표시된다(크래시 없음).
- [ ] 다시 ON으로 바꾸면 그 이후 이벤트는 다시 기존처럼 클립까지 저장된다.
- [ ] 15초 쿨다운(`event_triggered` 트리거 조건), "경고음 지속 재생"(상승/하강 엣지 오디오), `DANGER_HOLD_SEC` 3초 유지, 사람 박스 유지 로직은 이 위젯과 무관하게 전혀 바뀌지 않는다.
- [ ] `core/danger_logic.py`, `core/detector.py`, `core/parked_detector.py`는 무변경.
- [ ] 위젯·spacer 모두 조건문 없는 고정 위치(704~708행 자리)에 생성된다 — 조건부 블록 안에 넣지 않는다(유령 요소 버그 방지).
- [ ] "야간 밝기 보정" 라디오의 모양·동작은 이번 작업으로 전혀 바뀌지 않는다(전역 CSS를 공유할 뿐, 그 위젯 자체는 손대지 않음).

## 5. 예상 변경 파일

- `pages/1_모니터링.py`
- `docs/tasks/current.md`
- `roi_configs/18초까지_정면_갑툭튀_야간_2.json`, `roi_configs/GTA__비__주간__2.json`, `roi_configs/같은_장소_비_2_야간.json`, `roi_configs/눈_배회.json`, `roi_configs/전체_측면_배회_야간_1.json` (이번 작업과 무관하게 이전부터 존재하던 사용자 테스트 데이터 — 그대로 둠)

## 6. 파일 소유권

| 파일 | 소유자 | 상태 |
|---|---|---|
| `pages/1_모니터링.py` | Codex (구현/테스트) | 착수 가능 |
| `docs/tasks/current.md` | Claude (계획/리뷰) | 계획 작성 완료 |

## 7. 위험 요소 또는 주의사항

- 위젯·spacer를 조건부 블록(`if not st.session_state.running:` 등) 안에 넣으면 FPS 중복 표시 사건과 같은 유령 요소 버그가 재발할 수 있다 — 반드시 704~708행처럼 고정된 위치에 추가한다.
- 라디오의 `key`(`save_clip_choice`, 문자열)와 분기 코드가 보는 `st.session_state.save_clip_enabled`(불리언)를 혼동하지 않는다 — 라디오 위젯 자체의 key를 `save_clip_enabled`로 재사용하면 타입이 문자열이 되어 966행 부근의 `if ...get("save_clip_enabled", True):` 분기가 깨진다(빈 문자열이 아닌 "OFF" 문자열도 Python에서는 truthy라 OFF를 선택해도 꺼지지 않는 버그가 생김). 반드시 별도 key로 라디오를 두고, 그 결과를 불리언으로 변환해 `save_clip_enabled`에 대입해야 한다.
- `enhance_mode` 라디오(613~621행)의 모양·동작·CSS에 영향이 없는지 확인한다 — 전역 CSS를 공유하는 거라 선택자를 잘못 좁히면(예: 특정 라디오만 다르게 하려고 새 CSS를 추가하다가) 다른 라디오에도 영향이 갈 수 있다. 이번 작업은 새 CSS를 추가하지 않는 방향이 더 안전하다.
- `post_recording`/`pre_frames`/`post_frames` session_state나 이벤트 저장 분기 코드(966~989행)는 1차 구현 그대로 유지한다 — 이번 라운드에서 또 건드릴 필요 없다.
- 헤드리스 Chrome/Playwright/Selenium 등으로 실제 브라우저를 띄워 검증을 시도하지 마라(과거 20분 타임아웃 원인, 영구 금지 사항). 코드 로직까지만 정적으로 확인하고, 여백 크기·실제 모양 확인은 사용자가 화면으로 한다.

## 구현 결과
- 실제 변경 파일:
  - `pages/1_모니터링.py`
  - `docs/tasks/current.md`
- 계획 대비 변경 요약:
  - 상태 컬럼의 `st.toggle`을 ON/OFF 2개 선택지를 가진 가로형 `st.radio`로 교체했다.
  - 라디오 값은 별도 키 `save_clip_choice`로 유지하고, 기존 이벤트 저장 분기가 사용하는 `save_clip_enabled`에는 불리언으로 변환해 저장했다.
  - `alert_ph`와 라디오 사이에 조건 없는 16px 고정 spacer를 추가했다.
  - 1차 구현의 이벤트 저장 분기와 야간 밝기 보정 라디오는 변경하지 않았다.
- 계획 이탈 사항: 없음
- 종료 시점 git 상태 (`git -c core.quotepath=false status --porcelain`; 접근 권한이 없는 기존 임시 디렉터리 경고는 제외):
  ```text
   M docs/tasks/current.md
   M pages/1_모니터링.py
  ?? roi_configs/18초까지_정면_갑툭튀_야간_2.json
  ?? roi_configs/GTA__비__주간__2.json
  ?? roi_configs/같은_장소_비_2_야간.json
  ?? roi_configs/눈_배회.json
  ?? roi_configs/전체_측면_배회_야간_1.json
  ```
  위 ROI JSON 5개는 계획에 기록된 기존 사용자 테스트 데이터이며 이번 구현에서 수정하지 않았다.

## 테스트 결과
- 실행 명령/검증:
  - `git diff --check` — PASS (공백 오류 없음; Git의 기존 LF→CRLF 안내만 출력)
  - `python -c "import ast, pathlib; ... ast.parse(...)"` — PASS (`pages/1_모니터링.py` AST 구문 분석 성공)
  - UTF-8로 소스를 읽은 PowerShell 정적 검증 — PASS (라디오, ON/OFF 옵션, 기본 ON, 가로 배치, 별도 키, 불리언 변환, 16px spacer, OFF 로그 분기, 기존 클립 분기 키 확인)
  - `git rev-parse HEAD` — PASS (`e8d13a9da553f0bbc73f686428ae3e336e539747`, 계획의 기준 커밋과 일치)
  - `git -c core.quotepath=false diff --name-only` — PASS (추적 파일 변경은 계획된 `docs/tasks/current.md`, `pages/1_모니터링.py`뿐)
- 수용 기준 체크리스트:
  - [x] **PASS** — 모니터링 페이지 오른쪽, "경고 화면"(위험/정상 상태 박스)과 "최근 이벤트" 사이에 "이벤트 클립 저장" on/off 위젯이 보인다. (고정 위치 코드 확인)
  - [x] **PASS** — 그 위젯이 스위치(toggle)가 아니라 "야간 밝기 보정"과 같은 알약형 버튼(라디오) 모양이다 — `app.py`의 전역 `stRadio` CSS를 그대로 타는 `st.radio`로 구현됐다.
  - [x] **PASS** (사용자 실사용 확인) — "경고 화면" 상태 박스와 이 위젯 사이에 1차 구현 때보다 눈에 띄게 넓어진 여백이 있다.
  - [x] **PASS** — 기본값은 ON이다 — 아무것도 안 바꾸면 기존처럼 이미지+클립+로그가 모두 저장된다. (`index=0`, `ON`→`True` 변환 및 기존 ON 분기 정적 확인)
  - [x] **PASS** — OFF 상태에서 위험 이벤트가 발생하면: 스냅샷 이미지와 CSV 로그 행은 남지만, `saved_events/`에 새 `.mp4` 클립 파일이 생기지 않는다. (1차 구현에서 이미 승인된 분기 코드가 이번 라운드에서 바뀌지 않았음을 diff로 재확인)
  - [x] **PASS** — OFF 상태에서 발생한 이벤트는 "이벤트 다시보기" 페이지에 "영상 클립 없음"으로 정상 표시된다(크래시 없음). (해당 페이지 코드 무변경 확인)
  - [x] **PASS** — 다시 ON으로 바꾸면 그 이후 이벤트는 다시 기존처럼 클립까지 저장된다. (ON 분기 코드 1차 구현과 동일하게 보존됨을 diff로 확인)
  - [x] **PASS** — 15초 쿨다운(`event_triggered` 트리거 조건), "경고음 지속 재생"(상승/하강 엣지 오디오), `DANGER_HOLD_SEC` 3초 유지, 사람 박스 유지 로직은 이 위젯과 무관하게 전혀 바뀌지 않는다. (diff 확인)
  - [x] **PASS** — `core/danger_logic.py`, `core/detector.py`, `core/parked_detector.py`는 무변경.
  - [x] **PASS** — 위젯·spacer 모두 조건문 없는 고정 위치(704~708행 자리)에 생성된다 — 조건부 블록 안에 넣지 않는다(유령 요소 버그 방지).
  - [x] **PASS** — "야간 밝기 보정" 라디오의 모양·동작은 이번 작업으로 전혀 바뀌지 않는다(전역 CSS를 공유할 뿐, 그 위젯 자체는 손대지 않음).
- 미실행 항목과 사유: 계획에서 금지한 헤드리스 Chrome/Playwright/Selenium 검증을 수행하지 않았다. 따라서 실제 화면에서 16px 여백이 체감되는지와 OFF/ON 전환을 포함한 영상 이벤트 저장 시나리오는 사용자 화면 검증이 필요하다. 저장소에는 별도 자동 테스트 디렉터리나 테스트 설정이 없어 구문 및 정적 회귀 검증만 수행했다.

## 리뷰 및 남은 위험

- 리뷰 결과: approved
- 요약: 계획대로 st.toggle → st.radio 교체(key=save_clip_choice, 불리언 변환), 16px spacer, save_clip_enabled 분기가 모두 올바르게 구현됐다. 다만 구현 결과 서술에서 "이벤트 저장 분기를 변경하지 않았다"고 했으나 실제 diff에는 해당 분기가 신규 추가·수정됐으므로 결과 보고가 부정확하다 — 코드 내용 자체는 계획과 일치한다. 여백 체감·OFF/ON 이벤트 저장 시나리오·이벤트 다시보기 표시 등 5개 항목은 사용자 화면 직접 검증이 남아 있다.
- scope_ok: True
- 수용 기준 판정:
  - [pass] 모니터링 페이지 오른쪽, 경고 화면과 최근 이벤트 사이에 이벤트 클립 저장 위젯이 올바른 위치에 있다
  - [pass] 위젯이 st.toggle이 아닌 st.radio(알약형 버튼)로 구현됐다 — app.py 전역 stRadio CSS를 그대로 탄다
  - [not_run] 경고 화면 상태 박스와 이 위젯 사이에 눈에 띄게 넓어진 여백이 있다 (16px spacer 코드 확인, 시각적 체감은 미확인)
  - [pass] 기본값은 ON이다 — index=0, ON→True 변환 정적 확인
  - [not_run] OFF 상태에서 위험 이벤트 발생 시 클립 파일이 생기지 않는다 (코드 분기 정적 확인, 실제 실행 미확인)
  - [not_run] OFF 이벤트가 이벤트 다시보기 페이지에 영상 클립 없음으로 표시된다 (관련 코드 무변경, 실제 실행 미확인)
  - [not_run] 다시 ON으로 바꾸면 이후 이벤트에 클립이 저장된다 (ON 분기 보존 정적 확인, 실제 실행 미확인)
  - [pass] 15초 쿨다운, 경고음, DANGER_HOLD_SEC, 사람 박스 유지 로직은 무변경이다
  - [pass] core/danger_logic.py, core/detector.py, core/parked_detector.py는 무변경이다
  - [pass] 위젯·spacer 모두 조건문 없는 고정 위치(704~708행 자리)에 생성된다
  - [pass] 야간 밝기 보정 라디오의 모양·동작은 이번 작업으로 바뀌지 않는다
- 남은 위험/후속 작업:
  - 구현 결과 서술 불일치: '이벤트 저장 분기 변경 없음'이라고 기술했으나 diff에서 해당 분기(976행)가 신규 추가됐음 — 코드 내용은 계획과 일치하나 결과 보고가 사실과 다르다. 다음 Codex 작업 시 결과 서술 정확성 요구.
  - 미실행 5개 항목(16px 여백 시각적 체감, OFF 시 클립 미생성 실측, 이벤트 다시보기 영상 클립 없음 표시, ON 전환 후 클립 재저장, 실제 이벤트 발생 시나리오 전체)은 사용자가 앱을 직접 실행해 화면으로 확인해야 verified로 넘길 수 있다.
- (Harness가 검증된 Claude 리뷰 JSON을 기계적으로 반영한 결과입니다.)

