# 현재 작업

## 상태

**State:** `verified`
**기준 커밋:** `d5ca3b838fb9417b3f0c81816c7f8565bd5477ef`
**승인 필요:** 아니오 (파일/RTSP 라디오 너비를 아래 버튼들과 맞추는 CSS 조정. 탐지/판정 로직, 구조, 다른 위젯과 무관. 사용자가 명시적으로 요청.)
**최종 갱신:** 사용자가 4차(라디오 폭 통일)까지 실제 화면에서 최종 확인해 verified로 종료, 2026-10-10

이 작업은 "모니터링 재생/일시정지 버튼 배경 투명화"다. 직전 "UI/UX 디자인 통일 — 1단계"는 `verified`로 종료되어 PR #20으로 머지됐다(`docs/tasks/archive/2026-10-10-uiux-design-phase1-verified.md` 참고). 2단계(공유 자원 구조 전환 + 공개 디스플레이 페이지)는 사용자 승인 대기 중이며, 이 작은 수정을 먼저 처리한 뒤 이어간다.

## 1. 목표

`pages/1_모니터링.py`의 로컬 영상 재생 중 영상 아래에 표시되는 "⏸ 일시정지"/"▶ 재생" 토글 버튼(`key="play_pause_btn"`, 약 770행)의 배경색을 현재 파란색(`type="primary"`로 인해 `var(--sv-blue)` 적용)에서 **투명**하게 바꾼다. 글자(아이콘+텍스트)는 그대로 보이게 유지한다.

**중요 — 범위를 이 버튼 하나로 한정**: `app.py`의 `[data-testid="stButton"] > button[kind="primary"]` 규칙은 "▶ 시작" 버튼 등 다른 primary 버튼에도 적용되는 공통 규칙이다. 이 공통 규칙 자체를 바꾸면 다른 버튼들(사용자가 이미 "마음에 든다"고 확인한 버튼 색상)까지 투명해진다. **이 재생/일시정지 버튼만** 선택적으로 타깃해야 한다 — 이 저장소에 이미 쓰인 패턴(`app.py`의 `.sv-source-panel-marker` + `[data-testid="stColumn"]:has(.sv-source-panel-marker)` 방식, "영상 소스 설정" 카드를 특정하기 위해 숨김 마커 요소 + `:has()` 선택자를 쓴 것)을 그대로 재사용해, 이 버튼 바로 앞/뒤에 숨김 마커를 심고 `:has()`로 그 버튼의 컨테이너만 특정해 배경을 `transparent`로 덮어써라.

## 2. 현재 상태

- `pages/1_모니터링.py:770` — `st.button(play_label, key="play_pause_btn", use_container_width=True, type="primary")`.
- `app.py`에 `[data-testid="stButton"] > button[kind="primary"] { background: var(--sv-blue) !important; ... }` 공통 규칙이 있어 모든 `type="primary"` 버튼이 파란 배경을 쓴다.
- 이미 같은 파일에 "특정 위젯 하나만 CSS로 타깃"하는 선례가 있다(`.sv-source-panel-marker` 숨김 마커 + `[data-testid="stElementContainer"]:has(...)`/`[data-testid="stColumn"]:has(...)` 조합).

## 3. 구현 계획

1. `pages/1_모니터링.py`의 재생/일시정지 버튼(770행) 바로 앞 또는 뒤에, 기존 `.sv-source-panel-marker`와 같은 방식으로 숨김 마커를 추가한다(예: `st.markdown('<span class="sv-play-pause-marker"></span>', unsafe_allow_html=True)`, 클래스명은 다른 마커와 겹치지 않게 새로 짓는다).
2. `app.py`의 CSS에 `[data-testid="stElementContainer"]:has(.sv-play-pause-marker)` 또는 해당 버튼을 감싸는 실제 컨테이너(Codex가 렌더링 결과로 정확한 계층 확인)를 대상으로, 그 안의 `button[kind="primary"]`에 한해 `background: transparent !important; border-color: transparent !important;` (또는 테두리는 살짝 남기고 배경만 투명 — 가독성 확인 후 판단)를 적용한다. 글자 색은 기존 primary 버튼 글자색(`#082F49`)이 투명 배경 위에서 눈에 잘 띄는지 확인하고, 안 띄면 적절한 색으로 조정하되 다른 버튼 글자색 규칙은 건드리지 않는다.
3. 마커 요소 자체는 기존 패턴대로 `display: none`으로 화면에 보이지 않게 한다.
4. 다른 `type="primary"` 버튼(▶ 시작, ✅ 확인, ➕ 추가 등)의 배경색은 그대로 파란색으로 유지되는지 확인한다.

## 4. 수용 기준

- [ ] 로컬 영상 재생 중 "⏸ 일시정지"/"▶ 재생" 버튼의 배경이 투명하게 보인다(파란 배경 없음).
- [ ] 같은 버튼의 글자(아이콘+텍스트)는 여전히 잘 보인다(대비 문제 없음).
- [ ] "▶ 시작", "✅ 확인", "➕ 추가" 등 다른 primary 버튼들의 배경색은 기존 파란색 그대로 유지된다(`git diff`로 공통 `button[kind="primary"]` 규칙 자체가 바뀌지 않았는지 확인).
- [ ] `st.button(...)`의 인자(`key`, `use_container_width`, `type` 등)와 호출 위치는 변경되지 않는다 — 추가된 건 마커 요소 하나뿐이다.
- [ ] `core/*.py`, 판정 로직, 다른 위젯 구조는 무변경.

## 5. 예상 변경 파일

- `app.py`
- `pages/1_모니터링.py`
- `docs/tasks/current.md`

## 6. 파일 소유권

| 파일 | 소유자 | 상태 |
|---|---|---|
| `app.py`, `pages/1_모니터링.py` | Codex (구현/테스트) | 착수 가능 |
| `docs/tasks/current.md` | Claude (계획/리뷰) | 계획 작성 완료 |

## 7. 위험 요소 또는 주의사항

- 공통 `button[kind="primary"]` 선택자를 직접 수정하면 다른 버튼들도 같이 투명해진다 — 반드시 마커+`:has()` 패턴으로 이 버튼만 범위를 좁힐 것.
- 배경을 투명하게 하면 버튼 영역의 클릭 가능 범위(히트박스)는 유지되는지(배경이 안 보여도 버튼 자체는 그대로 클릭 가능해야 함) 확인한다 — `background: transparent`는 클릭 영역에 영향을 주지 않지만, 혹시 `display`/`visibility`를 건드리지 않도록 주의.
- 투명 배경 위에서 글자 대비가 떨어지면(예: 밝은 회색 배경 위에 어두운 네이비 글자는 괜찮지만, 영상 카드 같은 어두운 배경 위라면 다를 수 있음) 실제 렌더링에서 확인한다.

## 구현 결과
- 실제 변경 파일: `app.py`, `pages/1_모니터링.py`, `docs/tasks/current.md`
- 계획 대비 변경 요약:
  - 4차 작업으로 `sv-source-panel-marker`가 있는 열 안에서도 접근성 라벨이 `소스`인 파일/RTSP 라디오만 선택해, 그 `stElementContainer`와 `stRadio`에 `width: 100% !important`를 적용했다.
  - 설치된 Streamlit 1.55.0의 `st.radio` 시그니처에서 기본값이 `width="content"`임을 확인해 상위 컨테이너가 콘텐츠 폭으로 축소되는 원인에 대응했다.
  - 기존 `radiogroup`의 `width: 100%`, 항목별 `flex: 1`, 배경·모서리·선택 상태 규칙은 변경하지 않아 두 항목의 1:1 비율과 기존 디자인을 보존했다.
  - `st.radio(...)` 호출과 `pages/1_모니터링.py`의 기존 2·3차 변경은 수정하지 않았다.
- 계획 이탈 사항: 실제 브라우저의 계산된 픽셀 너비 확인은 기존 Windows 샌드박스의 Chrome/Edge Mojo·Crashpad 자식 프로세스 차단 때문에 미실행했다. 대신 설치 버전의 함수 시그니처와 프런트엔드 DOM 속성(`data-testid="stRadio"`, `role="radiogroup"`, `aria-label`)을 확인해 선택자를 작성했다.
- 종료 시점 git 상태 (`git status --porcelain`):
  ```text
   M app.py
   M docs/tasks/current.md
   M "pages/1_\353\252\250\353\213\210\355\204\260\353\247\201.py"
  ```

## 테스트 결과
- 실행 명령/검증:
  - Python `ast.parse`로 `app.py`, `pages/1_모니터링.py` 구문 검사: PASS
  - `inspect.signature(st.radio)` 확인: PASS — Streamlit 1.55.0에서 기본 폭이 `width="content"`임을 확인
  - 설치된 Streamlit 1.55.0 프런트엔드 번들 확인: PASS — 라디오가 `data-testid="stRadio"`와 `role="radiogroup"`, `aria-label`을 렌더링함을 확인
  - `rg` 정적 불변식 검사: PASS — `aria-label="소스"`로 한정한 너비 선택자 2개, 파일/RTSP `st.radio(...)` 호출 1개, 공통 primary 버튼 규칙 유지
  - `python -m streamlit run app.py --server.headless true --server.port 8523 --browser.gatherUsageStats false` 기동 후 `/_stcore/health`: PASS (`200 ok`)
  - `git diff --check`: PASS (오류 없음, Git의 LF→CRLF 안내만 출력)
  - `git diff -- app.py pages/1_모니터링.py`: 4차 변경이 `app.py`의 파일/RTSP 라디오 전용 CSS뿐이고 `pages/1_모니터링.py`에는 새 변경이 없음을 확인: PASS
- 4차 작업 수용 기준 체크리스트:
  - [ ] 미실행 — 실제 화면에서 "📁 파일"/"📡 RTSP" 라디오 외곽 폭이 아래 `use_container_width=True` 버튼과 픽셀 단위로 같은지 육안 확인. 브라우저 자식 프로세스 차단으로 확인 불가.
  - [x] PASS — 파일/RTSP 라디오의 `stElementContainer`와 `stRadio` 모두 전체 폭을 사용하도록 CSS를 적용했다.
  - [x] PASS — 선택자를 `sv-source-panel-marker` 열 및 `aria-label="소스"`로 한정해 같은 열의 "야간 밝기 보정" 라디오와 다른 페이지 라디오에 영향을 주지 않는다.
  - [x] PASS — 두 세그먼트의 기존 `flex: 1` 규칙을 유지해 1:1 비율을 보존했다.
  - [x] PASS — 라디오 배경, 둥근 모서리, 선택 상태 등 기존 스타일 규칙을 변경하지 않았다.
  - [x] PASS — `st.radio(...)`의 인자·옵션·위치는 변경하지 않았다.
  - [x] PASS — `core/*.py`, 탐지·판정 로직은 변경하지 않았다.
- 미실행 항목과 사유: 실제 라디오/버튼 픽셀 너비 비교는 브라우저 프로세스 차단으로 미실행했다. 서버 기동/health, 구문, 설치 버전 기본 폭, DOM 속성, CSS 범위와 호출 불변식은 검증했다.

## 리뷰 및 남은 위험

- 리뷰 결과: approved
- 요약: 4차 작업(파일/RTSP 라디오 너비 CSS 통일)은 예상 파일 범위 내 변경이며 CSS 로직이 정확하다 — sv-source-panel-marker 열과 aria-label='소스'로 이중 범위 한정 후 stElementContainer·stRadio에 width: 100% !important 적용, 기존 radiogroup flex·스타일 규칙 및 공통 primary 버튼 규칙은 무변경. 실제 브라우저 픽셀 너비 비교는 환경 제약으로 미실행이며 앱 실행 후 사용자 육안 확인이 남아있다.
- scope_ok: True
- 수용 기준 판정:
  - [not_run] 실제 화면에서 파일/RTSP 라디오 폭이 아래 버튼과 동일한지 육안 확인
  - [pass] sv-source-panel-marker 열 + aria-label='소스' 라디오만 width: 100% !important 적용 (stElementContainer + stRadio 양쪽 선택자)
  - [pass] sv-source-panel-marker + aria-label='소스'로 이중 범위 한정 — 야간 밝기 보정 라디오 및 다른 페이지 미영향
  - [pass] radiogroup flex: 1 비율 및 기존 배경·모서리·선택 상태 스타일 무변경
  - [pass] st.radio(...) 인자·옵션·위치 불변, 마커 미추가(4차 범위 내)
  - [pass] 공통 button[kind='primary'] 파란 배경 규칙 무변경
  - [pass] core/*.py, 판정 로직, FPS 계산 로직 무변경
- 남은 위험/후속 작업:
  - 실제 앱에서 '📁 파일'/'📡 RTSP' 라디오 폭이 아래 '▶ 시작'/'⏹ 정지' 버튼과 동일한지 /프로토타입 스킬로 앱 실행 후 육안 확인 필요
- (Harness가 검증된 Claude 리뷰 JSON을 기계적으로 반영한 결과입니다.)

### 추가 작업 — FPS 중복 표시 제거 (2026-10-10, Claude)

1차(재생/일시정지 버튼 투명화)는 사용자가 확인했다. 이어서 새 요청이 들어왔다: "서브 사이드바(영상 소스 설정 패널) 맨 아래 '시스템 상태' 아래에 표시되는 FPS가 두 번 출력되니 하나는 없애달라."

**정적 코드 확인 결과(원인 미확정)**: `pages/1_모니터링.py`를 전체 검색(`FPS`/`fps_display`/`fps_ph` 대소문자 무관)한 결과, 실제로 "FPS" 라벨을 그리는 코드는 아래 한 곳뿐이다:

```python
fps_ph = st.empty()
fps_ph.markdown(f"**FPS** &nbsp; {st.session_state.fps_display}")
st.session_state["__fps_ph"] = fps_ph
```

그리고 `while st.session_state.running:` 루프 안에서 같은 placeholder를 갱신하는 코드가 한 번 더 있다:

```python
if "__fps_ph" in st.session_state:
    st.session_state["__fps_ph"].markdown(f"**FPS** &nbsp; {st.session_state.fps_display}")
```

이건 **같은 placeholder를 값만 바꿔 갱신**하는 정상적인 패턴이라 정적으로는 중복의 원인이 보이지 않는다. 즉 코드만 읽어서는 왜 두 번 보이는지 특정하지 못했다 — 아래 중 하나일 가능성이 있다(강제하지 않음, Codex가 실제 앱을 실행해 직접 재현·확인할 것):

- Streamlit 재실행(rerun) 타이밍 문제: 일시정지/재생 버튼 클릭이나 다른 위젯 상호작용으로 전체 스크립트가 재실행될 때, `settings_col` 블록이 다시 실행되며 새 `fps_ph`(`st.empty()`)를 또 만드는데, 그 순간 이전 `while` 루프에서 쓰던 구 `fps_ph` 참조가 아직 화면에 남아있어 일시적으로 두 개가 보이는 경우.
- `st.empty()`로 만든 placeholder의 위젯 키/위치가 매 rerun마다 새로 생성되면서 이전 요소가 완전히 치워지지 않는 Streamlit 자체의 동작 특성.
- 혹은 실제로는 다른 곳(예: 최근 리팩터링 중 남은 코드, 혹은 이 파일이 아닌 다른 곳)에 정적 검색으로 못 찾은 FPS 표시가 더 있을 가능성(재확인 필요).

**지시**: 반드시 실제로 `streamlit run app.py`를 띄워 로컬 영상을 재생하면서 "시스템 상태" 아래 FPS가 정말 두 줄/두 번 보이는지 직접 재현하라. 재현되면 정확한 원인을 찾아 **하나만 남도록** 고쳐라(어느 쪽을 남길지는 중요하지 않다 — 둘 다 같은 값을 보여주므로, 더 안정적으로 갱신되는 쪽을 남겨라). AppTest 같은 정적 렌더 트리 검사로는 이번 버그가 안 잡힐 가능성이 높다는 걸 감안하고, 실제 런타임에서 확인한 근거를 테스트 결과에 구체적으로 남겨라.

**범위**: FPS 표시 로직만 다듬는 것이며, `fps_display` 계산 로직(`update_fps()`)이나 다른 위젯·`core/*.py`는 변경하지 않는다.

### 3차 작업 — 지시 정정: 버튼이 아니라 프레임 카운터 텍스트였음 (2026-10-10, Claude)

사용자가 1차 지시를 정정했다: "일시정지 버튼의 배경색을 없애달란 게 아니라, 일시정지 버튼 아래에 뜨는 숫자/숫자 프레임 글자의 배경색을 없애달라는 것"이었다. FPS 중복은 2차 수정 후에도 여전히 재현된다(원인 미해결) — 이건 사용자에게 먼저 "강력 새로고침(Ctrl+Shift+R) 후에도 재현되는지" 확인을 요청해둔 상태라 **이번 라운드에는 포함하지 않는다.**

**1. 재생/일시정지 버튼 배경 투명화를 되돌린다**

1차에서 `app.py`에 추가한 아래 규칙 때문에 버튼 배경이 투명해졌는데, 이건 사용자가 원한 게 아니었다 — 제거해서 원래(공통 `button[kind="primary"]` 규칙에 따른 파란 배경)로 되돌려라:

```css
[data-testid="stColumn"]:has(.sv-play-pause-marker) [data-testid="stButton"] > button[kind="primary"] {
    background: transparent !important;
    border-color: transparent !important;
}
```

이 규칙과 `pages/1_모니터링.py`에 추가했던 `sv-play-pause-marker` 마커(`st.markdown('<span class="sv-play-pause-marker" ...>', ...)`도 더 이상 필요 없으면 같이 제거하되, 3번 항목(프레임 카운터)에 같은 마커 패턴을 재사용할 거라면 마커 자체는 남기고 CSS 타깃만 바꿔도 된다 — Codex가 판단.

**2. 프레임 카운터 텍스트("2/102 프레임")의 배경을 투명하게**

재생/일시정지 버튼 바로 아래에 `st.progress(fraction, text=f"▶ {cur}/{total_video_frames} 프레임")` 형태로 표시되는 진행률 바(`video_progress_ph`, `pages/1_모니터링.py` 약 825행 일시정지 중 / 약 961행 재생 중, 두 호출 다 같은 `video_progress_ph` placeholder를 공유)가 있다. 이 위젯은 Streamlit 기본 `st.progress`이며, 라벨 텍스트("▶ 2/102 프레임" 등) 부분에 Streamlit 기본 배경(또는 우리가 이미 깔아둔 공통 스타일)이 남아있어 사용자가 이를 "배경이 있다"고 느낀다. 이 텍스트 라벨의 배경을 투명하게 만들어라.

- Streamlit의 `st.progress(text=...)` 실제 DOM 구조(라벨을 감싸는 `data-testid`)를 실제 렌더링으로 먼저 확인하라(지금까지 여러 번 그랬듯 추측하지 말 것 — 아마 `[data-testid="stProgress"]` 하위에 라벨 텍스트 요소가 있을 것이다).
- 이 영상 진행률 바는 모니터링 페이지에서만 쓰이므로, 다른 페이지의 `st.progress`(있다면)에 영향을 주지 않도록 범위를 좁혀라(예: 기존 `.sv-play-pause-marker` 같은 숨김 마커를 이 진행률 바 근처에 추가해 `:has()`로 범위를 좁히는 패턴을 재사용).
- 진행 바 자체(채워지는 막대 부분)의 색상은 바꾸지 않는다 — 라벨 텍스트의 배경만 투명하게.

**범위**: 1번은 되돌리기, 2번은 CSS 추가다. `st.progress`/`st.button` 호출의 인자·위치·동작은 바뀌지 않는다. `core/*.py`, 판정 로직, FPS 계산 로직은 무변경.

### 4차 작업 — 파일/RTSP 라디오 너비를 버튼들과 통일 (2026-10-10, Claude)

3차(버튼 되돌리기 + 프레임 카운터 투명화)는 사용자가 확인했다. FPS 중복은 사용자가 **강력 새로고침(Ctrl+Shift+R) 후 1개만 보임을 확인** — 실제 코드 버그가 아니라 브라우저 탭이 이전 세션 상태를 들고 있던 문제였다. FPS 관련 추가 수정은 필요 없다.

**새 요청**: "영상 소스 설정" 패널(서브 사이드바) 안의 "📁 파일"/"📡 RTSP" 라디오(세그먼트 버튼)가, 그 아래 "▶ 시작"/"⏹ 정지" 같은 `use_container_width=True` 버튼들보다 폭이 좁아 보인다. 라디오 폭을 버튼들과 같은 폭으로 맞춰라.

**원인 추정**: `app.py`의 `[data-testid="stRadio"] div[role="radiogroup"] { width: 100%; ... }`는 라디오그룹 **내부** 요소에 `width: 100%`를 주고 있지만, 이는 그 부모인 `[data-testid="stRadio"]` 자체(또는 그걸 감싸는 `[data-testid="stElementContainer"]`)의 실제 폭을 기준으로 한 100%일 뿐이다. 만약 `[data-testid="stRadio"]` 자체가 Streamlit 기본값상 컬럼 전체 폭을 안 쓰고 내용물 크기만큼만 차지하는 상태(예: `display: inline-block`이거나 `width`가 명시돼 있지 않아 자동)라면, 안쪽 `radiogroup`의 100%는 그 좁은 부모 기준이라 버튼들(컬럼 전체 폭)보다 좁게 보인다.

**수정 방향**: 추측만으로 고치지 말고, 실제 렌더링에서 `[data-testid="stRadio"]`(및 필요하면 그 상위 `[data-testid="stElementContainer"]`)의 실제 폭이 버튼을 감싸는 `[data-testid="stElementContainer"]`(`use_container_width=True` 버튼)의 폭과 다른지 확인하라. 다르다면 `[data-testid="stRadio"]`(또는 적절한 상위 요소)에 `width: 100%`(필요하면 `display: block`도 같이)를 추가해 버튼들과 같은 폭이 되도록 맞춰라. 라디오 트랙 내부의 세그먼트 비율(2개 항목이 균등하게 1:1로 나뉘는 것)과 다른 스타일(배경, 둥근 모서리, 선택 상태 등)은 그대로 유지한다.

**범위**: 라디오 폭 CSS만 조정하며 `st.radio(...)` 호출의 인자·옵션·위치는 변경하지 않는다. `core/*.py`, 판정 로직은 무변경.

### 최종 종결 — 사용자 최종 확인 (2026-10-10, Claude)

4차(파일/RTSP 라디오 폭 통일)까지 사용자가 실제 화면에서 확인했다. 이 작업 전체는 4라운드로 진행됐다: 1차 재생/일시정지 버튼 투명화(사용자 지시 오해) → 2차 FPS 중복 조사(코드 수정 시도, 추후 사용자가 강력 새로고침으로 재검증해 실제로는 브라우저 세션 캐시 문제였음을 확인 — 코드 버그 아님) → 3차 1차 지시 정정(버튼 투명화 되돌림) + 프레임 카운터 텍스트 배경 투명화 → 4차 파일/RTSP 라디오 폭을 버튼들과 통일.

`core/*.py`, 판정 로직, 위젯 종류·인자, 페이지 라우팅은 전 라운드에서 무변경.

**State를 `verified`로 확정하고 이 작업을 종료한다.**
