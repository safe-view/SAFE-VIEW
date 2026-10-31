# 현재 작업

## 상태

**State:** `verified`
**기준 커밋:** `544d05ae020a1798021106564fa7cac616f979bd`
**승인 필요:** 아니오 — 리비전 15는 사용자가 리비전 14 실기 확인 후 직접 요청한 2건(자동평가 실패 메시지 문구 변경, "위험 구간 없음" 옆에 기존 안내 문구 복원). 리비전 16은 리비전 15 실기 확인 후 직접 요청 1건("위험 구간 없음" 글자 제거) + Claude 추천 1건(안내 문구를 info 박스로).
**최종 갱신:** Claude, 2026-10-31 — 리비전 16까지 전부 사용자 실기 확인 완료("확인했어 커밋할 링크 만들어줘"), verified로 전환 후 아카이브

**리비전 16 배경**: 사용자가 리비전 15를 확인하고 ① "'위험 구간 없음' 글자는 항상 보일 필요 없으니 안 보이게" 요청 ② "구간 저장 없이 자동 평가를 눌렀는데 에러 없이 성공한 경우가 있었는데 정상이냐"고 질문 — Claude가 정답지 파일을 직접 확인해, 그 영상(`(3)건물 사각지대(야간).mp4`)이 이전에 이미 "위험 없음"으로 저장돼 있었음을 확인하고 설명함(새 버그 아님, 저장 이력이 파일에 남아있던 것) — **코드 변경 불필요**, 질문에 답만 하면 되는 건이라 이번 리비전에 포함 안 함. ③ 안내 문구를 회색 캡션 vs 파란 info 박스 중 추천해달라는 질문 — Claude가 "위험 구간 없음"이 없어지면 이 문구가 유일한 텍스트가 되니 info 박스를 추천, 사용자 동의 전제로 반영.

**리비전 15 배경**: 사용자가 리비전 14("위험 구간 없음" 표시)를 확인하고 두 가지를 요청했다. ① 정답지를 저장하지 않고 "자동 평가 실행"을 누르면 현재 일반 문구("자동 평가 실행에 실패했습니다.")가 뜨는데, 이걸 "자동 평가 실행 실패. 구간 저장을 먼저 해주세요."로 바꿔달라고 요청. ② "위험 구간 없음" 표시는 마음에 들지만, 리비전 14에서 없앤 기존 안내 문구("입력된 위험 구간이 없습니다. 이 상태로 저장하면 정상 영상으로 기록됩니다." — Claude가 리비전 14 이전 코드에서 정확히 확인한 원문, 사용자는 문구를 기억 못 함)를 그 옆에 다시 보여달라고 요청.

**리비전 14 배경**: 사용자가 "시작초/종료초를 입력하지 않은 채 저장하면 '입력된 위험 구간' 목록 자체가 안 보인다"고 보고했다. 실제로는 버그가 아니라 **의도된 분기**였다(구간이 비어 있으면 `#### 입력된 위험 구간` 헤딩 자체를 안 그리고 대신 `st.info(...)` 안내 문구만 보여주던 구조). 사용자는 이 동작 방식 자체를 바꾸고 싶어 한다: ① 구간이 비어 있어도 "입력된 위험 구간" 영역 자체는 항상 보이게 ② 비어 있을 때는 "위험 구간 없음"이라고 표시(기존 긴 안내 문구나 "0초~0초" 같은 값이 아니라) ③ 각 구간 앞에 붙는 "1. " 같은 번호를 뗀다(저장값이 하나뿐이라 번호가 불필요).

**리비전 13 배경**: 사용자가 리비전 12(섹션 순서, 카드 높이 통일)를 스크린샷으로 확인("잘 반영됐는데")하고 두 가지를 더 말했다. ① "정상(TN)이 뭔지" 질문 — Claude가 설명(오탐률(FAR) 계산의 분모로 실제 쓰이는 KISA 표준 분류 중 하나, 지금 0건인 건 TN을 만드는 테스트(위험 없는 영상 평가)를 아직 안 돌려봐서)하고 "지우지 말 것"을 추천했으며, 사용자의 최종 결정을 기다리는 중이라 **이번 리비전에는 포함하지 않는다**. ② "평가 기록 목록은 한 화면에 최대 7행까지 보이고, 그 이상은 마우스 휠/드래그로 스크롤" — 이건 명확한 요청이라 바로 진행한다.

**리비전 12 배경**: 사용자가 리비전 11 결과를 스크린샷으로 보여주며 세 가지를 요청했다. ① "'평가기록 수동 추가' 위치와 '평가 기록 목록'의 위치를 바꿔줘" ② "'위험 발생 구간 입력'을 '성능 자동평가 - 위험 발생 구간 입력'이라고 이름 변경 후 '평가기록 수동 추가' 위치와 바꿔줘" — 두 요청을 **순서대로 적용**하면 최종 섹션 순서는 다음과 같다(Claude가 단계별로 추적):
  - 시작: [종합지표, 수동추가, 기록목록, 위험구간입력]
  - ① 적용(수동추가 ↔ 기록목록 교환): [종합지표, 기록목록, 수동추가, 위험구간입력]
  - ② 적용(위험구간입력 이름 변경 후 수동추가와 교환): [종합지표, 기록목록, **성능 자동평가 - 위험 발생 구간 입력**, 수동추가]
  - **최종 순서: 종합 성능 지표 → 평가 기록 목록 → 성능 자동평가 - 위험 발생 구간 입력 → 평가기록 수동 추가**
③ 스크린샷에서 가로로 배치한 지표 7개의 박스 높이가 제각각이다(일부는 `delta` 줄이 있어 3줄, 없는 것은 2줄이라 카드 높이가 다름) — Claude가 원인을 확인하고 CSS로 높이를 통일하는 안을 제안한다(아래 조사 결과 참고).

**리비전 11 배경**: 사용자가 리비전 10(삭제 버튼 위치/팝업, 지표-건수 통합)을 확인("확인했어")한 뒤, "종합성능 지표 이 상태에서 가로 배치로만 수정해줘" — 즉 리비전 10에서 합친 내용(정탐률/오탐률/미탐률마다 해당 건수가 `delta`로 붙는 것, 정상·총건수 포함, "카테고리별 건수" 블록 없음)은 그대로 두고, **배치만 세로(`st.metric`을 순서대로 나열)에서 가로(한 줄에 나란히)로** 되돌린다.

**리비전 10 배경**: 사용자가 리비전 9를 확인하고 두 가지를 요청했다: ① 삭제 버튼을 목록 우측 상단이 아니라 **체크박스 열(맨 왼쪽) 바로 위**로 옮기고, 삭제 확인창을 인라인이 아니라 **진짜 팝업(모달)**으로 띄울 것(설치된 `streamlit==1.55.0`에는 `st.dialog` 모달 데코레이터가 있어 바로 쓸 수 있음을 Claude가 확인함) ② "📈 종합 성능 지표"(가로 5개 `st.metric`)를 세로 배치로 바꾸고, 옆의 "🧮 카테고리별 건수" 블록은 없애고 그 정보를 지표 쪽에 합칠 것. Claude는 정탐률↔정탐(TP) 건수, 오탐률↔오탐(FP) 건수, 미탐률↔미탐(FN) 건수를 짝짓고, 정밀도·정상(TN)·총 건수·평균 응답시간은 단독 행으로 두는 설계를 제안한다(아래 2번 참고) — 이 매칭 방식이 사용자가 기대한 것과 다르면 구현 후 바로 조정 가능.

**리비전 9 배경**: 리비전 8 실기 중 사용자가 ROI 없는 영상(`10초까지_정면 비 배회 4.mp4`)으로 자동 평가를 돌렸는데, 경고 없이 조용히 미탐만 나온 것을 발견 — 로그가 아니라 화면에 바로 경고가 뜨길 원함. 이 과정에서 Claude가 "평가 기록 목록"의 "응답시간(초)" 칼럼이 계속 비어 보이는 원인을 조사해 `core/performance_eval.py`의 falsy-zero 버그(응답시간이 정확히 0.0초면 빈 문자열로 저장/집계 제외됨)를 발견했고, 삭제하지 말고 고치는 쪽을 추천해 사용자가 동의했다. 추가로 사용자가 "기록 시각 분단위 표시", "체크박스+확인창 기반 삭제", "수동 추가 폼을 토글로 숨기기"를 요청했다.
**리비전 8 이후 Claude 직접 수정(2026-10-31)**: 사용자 요청으로 "🧮 지금 자동 평가 실행" 버튼 라벨에서 "지금"을 빼 "🧮 자동 평가 실행"으로 변경. `python -m py_compile` 재확인 PASS. 라벨 문구만 바꾸는 거라 별도 Codex 라운드 없이 직접 수정함.

**리비전 8 배경**: 사용자가 리비전 7 실기 중 세 가지를 제기했다: ① 새로고침 시 사이드바 스타일이 일시적으로 사라지는 현상(원인 미확정 — `st.navigation` 구조상 이론적으로는 발생하면 안 되는 버그라, 재현 시 콘솔 로그를 받기로 하고 이번 리비전 범위에는 포함하지 않음) ② "구간 추가"와 "저장"이 분리돼 있어 추가만 하고 저장을 안 누르면 반영이 안 되는 게 번거로움 ③ "위험 발생 구간 입력"이 자동으로 "평가 기록"을 만들어주는 줄 알았는데 아니었음 — 원래 반자동화 설계(정답지는 사람이, 채점은 스크립트가)대로 `tools/auto_eval.py`를 버튼으로 트리거하고 싶음. Claude가 계획안을 제시했고 사용자가 위 1~3으로 확정했다.

**리비전 7 이후 Claude 직접 수정(2026-10-31)**: 사용자가 콘솔에서 `The widget with key "ground_truth_start" was created with a default value but also had its value set via the Session State API.` 경고를 보고했다. 원인: `pages/4_성능_평가.py`의 시작초/종료초 `number_input`이 `value=0.0`과 `key=`를 동시에 지정하고 있는데, "⏮/⏭ 이 위치를 시작초로/종료초로" 버튼이 `st.session_state[key] = seek_sec`로 그 키의 값을 직접 설정한 뒤 재실행한다 — 위젯이 다시 그려질 때 `value=0.0`(명시적 기본값)과 세션에 이미 들어있는 값이 충돌해 Streamlit이 경고를 띄운다. 기능 자체는 세션 상태 값이 우선이라 정상 동작했지만 경고 문구가 화면에 남는다. `value=0.0`을 제거해(둘 다 `min_value=0.0`만 남김) 해결 — 최초 렌더 시 `min_value`가 기본값으로 쓰여 동작은 그대로다. `python -m py_compile` 재확인 PASS. 간단한 파라미터 제거라 별도 Codex 라운드 없이 직접 수정함.

**리비전 6 결과(사용자 확인, 2026-10-31)**: "버튼 색상 마음에 들어" — 사이드바 버튼 색상 수정은 확정 완료. 단 "도움말 방식이 아니라 그냥 이름 옆에 설명이 바로 보이게 하는 거였어" — `help=` 툴팁(마우스를 올려야 보이는 "?" 아이콘)은 요청한 것과 다르다는 피드백. 리비전 7로 수정.

**리비전 5 결과(사용자 확인 완료, 2026-10-31)**: "모두 잘 반영됨." 레이아웃 순서, 사이드바 재열기 버튼 모두 실기로 확인됨. 다만 사용자가 추가로 두 가지를 요청: ① 탐색 슬라이더 이름 옆에 사용법 설명 추가 ② 사이드바 펼치고 접는 버튼이 사이드바가 **펼쳐진 상태**일 때(어두운 배경) 안 보임 — 접힌 상태(밝은 페이지 배경)에서는 잘 보임. 두 버튼 모두 색상을 세이프뷰 로고 색(`#4CAF50`, `.streamlit/config.toml`의 `primaryColor`와 동일)으로 통일 요청.

**리비전 6 원인 조사(Claude가 설치된 Streamlit의 실제 프런트엔드 JS 번들을 직접 열어 확인)**: 사이드바를 펼쳤을 때 보이는 접기 버튼(`data-testid="stSidebarCollapseButton"`) 안의 아이콘은 `DynamicIcon` 컴포넌트가 `color: p.colors.fadedText60`(라이트 테마 기준 옅은 회색)를 **아이콘 자신에게 직접 인라인으로** 지정한다. 기존 `app.py`의 CSS 규칙(`[data-testid="stSidebarCollapseButton"] button { color: #CBD5E1 !important; }`)은 `<button>` 엘리먼트의 `color`만 바꿀 뿐, 아이콘 엘리먼트 자신에게 이미 인라인으로 박혀 있는 `color` 값을 상속만으로는 덮어쓰지 못한다(엘리먼트 자신에게 지정된 값이 조상에게서 물려받는 값보다 항상 우선한다) — 그래서 어두운 사이드바 배경에 그 회색 아이콘이 거의 안 보이는 것. 외부 스타일시트의 `!important`는 인라인 스타일도 이길 수 있으므로, **아이콘 엘리먼트 자신(또는 그 자손 전체)을 직접 타깃**하는 선택자로 고치면 해결된다.

**리비전 4 실기 테스트 결과(사용자 확인) 및 원인 규명**: "① 영상 미리보기 화면은 보이는데 재생 버튼을 눌러도 재생 안 됨 ② onSeek→입력란 채우기는 잘 됨 ③ 구간 추가/삭제는 잘 됨." 브라우저 콘솔 로그를 사용자에게 요청해 확인한 결과, `성능_평가/_stcore/host-config`가 404였다 — Streamlit 멀티페이지 앱에서 **루트가 아닌 서브페이지(`pages/` 안)에 커스텀 컴포넌트를 쓸 때 호스트 설정 요청이 현재 페이지 경로를 기준으로 잘못 나가 404가 나는, 이미 보고된 Streamlit 플랫폼 레벨 결함**임을 Claude가 웹 검색으로 확인했다(streamlit-player 자체 버그가 아님). `onSeek`는 react-player 내부 스크러빙 UI만으로도 발생해 동작했지만, 실제 미디어 디코딩/재생은 이 초기화 실패로 막힌 것으로 추정된다. 코드를 더 고쳐서 해결될 문제가 아니라 플랫폼 제약이라고 판단해, Claude가 "① 한 번 더 다른 버전/패키지로 시도 ② 리비전 3(보조 슬라이더) 방식으로 되돌리기" 두 옵션을 제시했고, 사용자가 **"보조 슬라이더로 롤백"**을 선택했다. 이때 사용자가 레이아웃 순서 변경("보조 슬라이더 위치는 시작초로/종료초로 버튼과 영상 화면 사이에 위치")과, 별개로 발견한 **사이드바 재열기 버튼 버그 수정**을 함께 지시해 리비전 5로 묶었다.

**사이드바 버그 원인(Claude가 Streamlit 설치 패키지의 실제 프런트엔드 JS 번들을 직접 열어 확인)**: `app.py`의 전역 CSS가 `header[data-testid="stHeader"] { display: none !important; }`로 Streamlit 기본 헤더를 통째로 숨기고 있다. 그런데 **사이드바를 접었을 때 다시 펼치는 버튼(`data-testid="stExpandSidebarButton"`)이 바로 이 `stHeader` 안에 렌더링된다** — `display:none`은 자손 전체를 완전히 렌더링에서 제외하므로, 헤더를 숨기면 이 재열기 버튼도 같이 사라진다. (문자열 `stExpandSidebarButton`을 실제 설치된 `streamlit` 패키지의 `static/static/js/*.js` 번들에서 직접 grep해 확인함 — 추측이 아님.)

**리비전 3 실기 테스트 결과(사용자 확인)**: "①보조 슬라이더로는 미리보기가 잘 됨 ②시작초/종료초 버튼이 네이티브(영상 안) 진행바에는 반응하지 않음 ③수기 입력은 됨 ④보조 슬라이더를 직접 조작하면 버튼이 의도대로 동작함 — 하지만 이건 원하는 방식이 아니고, 네이티브 진행바 자체가 이 기능을 하길 원함." 즉 보조 슬라이더 기능 자체는 계획대로 정상 동작했으나, 사용자가 원래 원했던 건 "영상 안의 실제 재생바"였다는 게 실기 후 명확해짐 — 설계를 다시 짚어 리비전 4로 반영.

**리비전 2 결과(사용자 확인 완료)**: "우와 영상 잘보여. 심지어 모니터링 페이지 영상화면과 달리 영상재생지연이 아예 없어. 그냥 원본 재생 속도랑 똑같아." — 수용 기준의 `[not_run]`이었던 "HEVC 영상 선택 시 실제로 화면에 보인다" 항목이 PASS로 확인됨. (이 발견을 계기로 모니터링 페이지 지연의 구조적 원인도 별도로 분석해 사용자에게 보고함 — 조치는 "연구 일단 보류"로 이번 작업 범위 밖.)

**리비전 2 (2026-10-30)**: 사용자가 실제 화면에서 테스트한 결과 "영상 선택은 되는데 재생바와 선택 버튼 사이에 영상 자체가 안 보인다"고 보고했다. Claude가 ffmpeg로 `data/(1)휴대폰 시나리오-카메라.mp4`를 직접 분석해 원인을 특정했다: 영상이 **HEVC(H.265)** 코덱으로 인코딩돼 있는데(`hevc (Main) (hvc1 / 0x31637668)`), 대부분의 데스크톱 브라우저(Chrome/Firefox)는 HEVC를 `<video>` 태그에서 재생하지 못한다 — 그래서 재생 컨트롤(진행바)은 보이지만 프레임은 전혀 그려지지 않는다. 이 프로젝트는 이미 같은 문제를 `pages/3_이벤트_다시보기.py`의 `get_playable_video()`에서 겪어서 해결해 뒀다(ffmpeg로 H.264로 재인코딩 후 캐싱, `imageio_ffmpeg` 패키지로 ffmpeg 바이너리 확보 — 이미 `requirements.txt`에 있음, 새 의존성 아님). 이번 수정은 그 함수를 공용 모듈로 뽑아 `pages/4_성능_평가.py`의 새 섹션에서도 재사용한다. 아래 1~7번 항목에 반영했다. (사용자가 함께 보고한 "재생바 드래그로 구간 입력" 기능은 설계 검토가 필요해 별도로 사용자에게 옵션을 제시했고, 이 작업 범위에는 포함하지 않는다.)

이 작업은 "위험 발생 구간 입력" 화면 추가다. 현재 `data/eval_ground_truth.json`(자동 성능평가 `tools/auto_eval.py`의 정답지)은 텍스트 편집기로 직접 JSON을 고쳐야 해서 팀원들이 쓰기 번거롭다. 성능평가 페이지에 영상을 선택해 재생하면서 위험 구간(시작~종료 초)을 입력/저장하는 화면을 추가해 이 파일을 편집기 없이 채울 수 있게 한다.

## 1. 목표

`pages/4_성능_평가.py`에 **"🎯 위험 발생 구간 입력"** 섹션을 추가한다:
1. `data/` 폴더의 영상 중 하나를 선택하면 화면에서 재생할 수 있다.
2. 그 영상에 대해 이미 저장된 위험 구간이 있으면 불러와 보여준다.
3. 시작초/종료초를 입력해 구간을 추가하거나, 기존 구간을 삭제할 수 있다.
4. "저장" 시 `data/eval_ground_truth.json`에 그 영상의 `danger_intervals`로 저장된다 — **다른 영상의 기존 데이터는 보존**(병합 저장, 전체 덮어쓰기 금지).
5. 구간이 하나도 없는 상태로 저장하면 "위험 없음(정상 영상)"으로 기록된다(`danger_intervals: []`) — `tools/auto_eval.py`가 이미 이 값을 TN 분류에 사용하므로 동작은 그대로 유지된다.
6. **(리비전 2)** `data/` 영상이 HEVC처럼 브라우저가 못 읽는 코덱이어도, 선택 시 실제로 화면에 영상이 보여야 한다.
7. **(리비전 3, 유지)** 시작초/종료초를 숫자로 직접 타이핑할 수 있다(수기 입력 — 그대로 유지).
8. **(리비전 4, 폐기)** ~~영상 안의 실제 재생 플레이어 진행바 자체로 시작/종료 설정~~ — Streamlit 서브페이지의 커스텀 컴포넌트 플랫폼 결함으로 실제 재생이 안 돼 폐기. 아래 9번으로 되돌림.
9. **(리비전 5)** 리비전 3의 보조 `st.slider` + `st.video` 방식으로 되돌린다. 단 화면 배치 순서를 **"영상 재생 화면 → 보조 탐색 슬라이더 → 시작초로/종료초로 버튼"** 순으로 둔다(기존 리비전 3은 슬라이더가 영상 위에 있었음 — 사용자가 영상과 버튼 사이에 두길 원함).
10. **(리비전 5)** `streamlit-player`, `core.video_playback`의 `media_file_mgr` 사용, 정적 서빙(`static/ground_truth_videos/`, `enableStaticServing`) 관련 추가물을 전부 제거하고 리비전 3 시점 구현으로 복원한다.
11. **(리비전 5, 별개 버그)** 사이드바를 접었을 때 다시 펼치는 버튼이 보이지 않는 전역 UI 버그를 수정한다 — `pages/4`와 무관하게 `app.py`의 전역 CSS 문제이며, 모든 페이지에 영향을 준다.
12. **(리비전 6, 수정됨 — 아래 14번 참고)** ~~탐색 슬라이더 이름 옆에 설명을 `help` 툴팁으로 추가~~ — 사용자가 "마우스를 올려야 보이는 방식이 아니라 항상 바로 보이는 설명"을 원한다고 피드백.
13. **(리비전 6)** 사이드바 펼치기/접기 버튼 아이콘 색상을 둘 다 세이프뷰 로고 색(`#4CAF50`)으로 통일한다 — 특히 사이드바가 펼쳐진 상태(어두운 배경)에서 접기 버튼이 거의 안 보이는 문제를 해결한다. **(사용자 확인 완료: "버튼 색상 마음에 들어")**
14. **(리비전 7)** 탐색 슬라이더의 설명을 `help` 툴팁이 아니라, **라벨 바로 옆에 항상 보이는 텍스트**로 바꾼다.
15. **(리비전 8)** "구간 추가"와 "저장" 두 버튼을 **"구간 저장" 버튼 하나로 통합**한다 — 클릭 한 번으로 (유효한 시작/종료초가 있으면) 구간을 추가하고, 그 즉시 파일에 저장까지 끝낸다.
16. **(리비전 8)** "🧮 지금 자동 평가 실행" 버튼을 추가한다 — 클릭 시 `tools/auto_eval.py --video <선택된 영상>`을 별도 프로세스로 실행해 그 영상의 정답지와 실제 탐지 결과를 비교, TP/FP/FN/TN 기록을 자동 생성한다.
17. **(리비전 8)** 자동 평가 실행이 끝나면 결과 요약과 함께 "📋 평가 기록 목록에 반영됨"을 명확히 안내한다. **(버튼 라벨은 사용자 요청으로 "지금" 제거해 "🧮 자동 평가 실행"으로 수정 완료)**
18. **(리비전 9)** 선택한 영상에 ROI가 없으면, "영상 선택" 바로 아래·영상 화면 위쪽에 "ROI가 없습니다 — ROI 설정 페이지에서 먼저 저장하세요" 경고가 즉시 보인다.
19. **(리비전 9)** 응답시간이 정확히 0초인 자동평가 기록도 "0.00"으로 정상 표시되고, 평균 응답시간 계산에도 포함된다(falsy-zero 버그 수정).
20. **(리비전 9)** "평가 기록 목록"의 "기록 시각"이 초 단위가 아니라 분 단위까지만 표시된다(저장되는 실제 데이터는 그대로, 화면 표시만 변경).
21. **(리비전 9)** 기록 삭제가 체크박스 다중 선택 + 목록 오른쪽 상단의 별도 "삭제" 버튼 + 삭제 확인창(확인/취소) 흐름으로 바뀐다.
22. **(리비전 9)** "➕ 평가 기록 추가" 섹션이 "➕ 평가기록 수동 추가"로 이름이 바뀌고, 토글을 켜야만 입력 폼이 보인다(기본은 숨김). **(사용자 확인 완료)**
23. **(리비전 10)** 삭제 버튼이 체크박스 열(맨 왼쪽) 바로 위로 옮겨지고, 삭제 확인이 인라인이 아니라 진짜 팝업(모달)으로 뜬다. **(사용자 확인 완료)**
24. **(리비전 10, 레이아웃만 리비전 11로 수정)** "📈 종합 성능 지표"가 세로로 배치되고, "🧮 카테고리별 건수" 블록 없이 각 지표 옆에 해당 분류의 건수가 함께 보인다. 지표-건수 통합 내용은 그대로 유지. **(사용자 확인 완료)**
25. **(리비전 11)** 24번의 지표-건수 통합 내용은 그대로 두고, 배치만 세로에서 **가로(한 줄에 나란히)**로 바꾼다. **(사용자 확인 완료)**
26. **(리비전 12)** 페이지 섹션 순서를 "종합 성능 지표 → 평가 기록 목록 → 성능 자동평가 - 위험 발생 구간 입력(이름 변경) → 평가기록 수동 추가"로 바꾼다.
27. **(리비전 12)** 가로로 배치한 지표 7개의 카드 높이를 통일한다(`delta` 유무에 따라 들쭉날쭉하던 것을 CSS로 고정 높이화). **(사용자 확인 완료: "잘 반영됐는데")**
28. **(리비전 13)** "평가 기록 목록" 테이블이 한 화면에 약 7행만 보이는 고정 높이를 갖고, 그 이상은 마우스 휠/드래그로 스크롤해서 본다. **(사용자 확인 완료: "스크롤 잘 적용됐어")**
29. **(리비전 14)** "입력된 위험 구간" 영역은 구간이 비어 있어도 항상 보이고, 비어 있을 때는 "위험 구간 없음"이라고 표시한다. **(사용자 확인 완료, 리비전 15에서 보완)**
30. **(리비전 14)** 구간 목록의 각 줄 앞에 붙던 번호("1. ")를 뗀다. **(사용자 확인 완료)**
31. **(리비전 15)** 정답지를 저장하지 않고 "자동 평가 실행"을 누르면, 실패 메시지가 "자동 평가 실행 실패. 구간 저장을 먼저 해주세요."로 보인다.
32. **(리비전 15)** "위험 구간 없음" 옆/아래에 "입력된 위험 구간이 없습니다. 이 상태로 저장하면 정상 영상으로 기록됩니다." 안내 문구가 다시 보인다. **(사용자 확인 완료, 리비전 16에서 "위험 구간 없음" 문구는 제거)**
33. **(리비전 16)** 구간이 비어 있을 때 보이던 "위험 구간 없음" 한 줄을 없앤다 — 안내 문구만 남긴다.
34. **(리비전 16)** 그 안내 문구를 회색 캡션(`st.caption`)이 아니라 파란 배경 정보 박스(`st.info`)로 보여준다.

## 2. 현재 상태 (조사 결과)

- `tools/auto_eval.py`(`docs/tasks/archive/2026-10-25-auto-performance-eval-verified.md`에서 구현)가 이미 `load_ground_truth()`(검증: 각 구간은 `[시작초, 끝초]`, `0 <= 시작 < 끝`), `video_files()`(`data/` 안의 영상 확장자 목록), `GROUND_TRUTH_PATH`, `DATA_DIR`, `VIDEO_EXTENSIONS`를 자체 모듈 안에 정의해 두고 있다. 이 함수들은 순수 파이썬(json/pathlib)만 쓴다.
- 문제: `tools/auto_eval.py`는 최상단에서 `cv2`, `numpy`, `core.detector.Detector`(YOLO 모델 로딩 경로 포함)를 임포트한다. 이 페이지가 `tools.auto_eval`을 통째로 import하면 성능평가 페이지를 열 때마다 무거운 영상·추론 라이브러리가 로딩돼 페이지가 느려진다 — 사용자가 전에 지적한 "체크 화면 추가가 성능 저하로 이어지지 않을지" 우려가 실제로 발생할 수 있는 지점이다.
- `pages/4_성능_평가.py`는 현재 `core.performance_eval`만 가볍게 import하고 있어 빠르게 뜬다(기존 동작 유지가 중요).
- `data/eval_ground_truth.json`은 `.gitignore`에서 `data/*` 제외 + `!data/eval_ground_truth.json` 예외로 추적되는 공유 파일이다(팀 전체가 공유). 현재 내용은 `{}`.
- `st.video(path)`는 로컬 파일 경로를 받아 재생할 수 있다(스트림릿 표준 기능, 별도 패키지 불필요) — **단, 브라우저가 디코딩 못 하는 코덱이면 컨트롤만 보이고 프레임은 안 그려진다.**
- **(리비전 2) `data/` 영상 코덱 확인**: ffmpeg로 `data/(1)휴대폰 시나리오-카메라.mp4`를 직접 분석한 결과 `Video: hevc (Main) (hvc1 / 0x31637668)` — HEVC(H.265)다. 휴대폰 촬영 영상이라 다른 `data/` 영상들도 HEVC일 가능성이 높다. Chrome/Firefox 등 주요 데스크톱 브라우저는 HEVC를 `<video>`에서 재생하지 못하는 경우가 많아, 지금 섹션에서 "진행바는 보이는데 영상이 안 보이는" 증상이 발생한다.
- **이미 같은 문제를 해결해 둔 코드가 있다**: `pages/3_이벤트_다시보기.py`의 `get_playable_video(clip_path)`(127~140줄) — 변환 결과가 캐시 디렉터리(`saved_events/_converted/`)에 있으면 그대로 쓰고, 없으면 `imageio_ffmpeg.get_ffmpeg_exe()`로 확보한 ffmpeg 바이너리로 `-c:v libx264 -preset fast -crf 23 -movflags +faststart -an`(오디오 제거) 옵션으로 재인코딩해 캐시한다. `imageio-ffmpeg>=0.4.0`은 이미 `requirements.txt`에 있어 새 의존성이 필요 없다.
- **(리비전 4) `st.video`는 네이티브 진행바 위치를 Python으로 돌려주지 않는다**: 브라우저 쪽 재생 위치는 단방향(Python→브라우저)으로만 전달되고, 사용자가 그 진행바를 조작한 결과는 Python이 읽을 방법이 없다(리비전 3에서 보조 `st.slider`로 돌아간 이유). 이걸 읽으려면 양방향 통신이 가능한 컴포넌트가 필요하다.
- **(리비전 4) `streamlit-player`(PyPI) 조사 결과**: `okld/streamlit-player` 패키지의 `st_player(url, events=[...], controls=True, key=...)`는 react-player를 감싼 컴포넌트로, `events`에 `"onSeek"`을 넣으면 사용자가 진행바를 조작할 때마다 `_PlayerEvent(name="onSeek", data=<이동한 초>)`를 반환한다 — 이게 바로 네이티브 진행바의 실제 조작 결과다. (GitHub 소스로 직접 확인: 지원 이벤트는 `onStart/onPlay/onProgress/onDuration/onPause/onBuffer/onBufferEnd/onSeek/onEnded/onError`.)
- **(리비전 4) 로컬 파일 재생의 제약**: `st_player`는 `url`(문자열)을 받는 구조라, `st.video`처럼 바이트를 직접 넘길 수 없다. 로컬 파일을 재생하려면 스트림릿의 **정적 파일 서빙**(`enableStaticServing`)을 켜고, `<앱 루트>/static/` 폴더 밑에 파일을 두면 `app/static/<파일명>`으로 접근 가능하다(Streamlit 공식 문서 확인). 현재 `.streamlit/config.toml`에는 `[server] headless = true`만 있고 `enableStaticServing`은 없음(기본값 false) — 이번에 추가해야 한다. 설치된 `streamlit==1.55.0`에서 지원되는 기능이다.
- **(리비전 4) 영향받지 않는 부분**: 이벤트 다시보기(`pages/3`)는 여전히 `st.video(bytes)`를 쓰고 그대로 둔다 — 정적 서빙/`st_player`는 "위험 발생 구간 입력" 섹션에만 적용한다.
- **(리비전 9) ROI 조회 함수**: `core/roi_manager.py`의 `load_rois(source_label)`을 `pages/1_모니터링.py`가 이미 쓰고 있다 — 영상 파일명에서 확장자를 뺀 문자열(`os.path.splitext(name)[0]`)을 넘기면 ROI가 없을 때 `None`을 반환한다. 실제로 확인한 결과 `data/` 영상 15개 중 13개는 이미 ROI가 설정돼 있고, `10초까지_정면 비 배회 4.mp4`·`3초부터_정면 비 갑툭튀.mp4` 2개만 없다.
- **(리비전 9) 응답시간 falsy-zero 버그**: `core/performance_eval.py`의 `add_record()`가 `f"{response_time_sec:.2f}" if response_time_sec else ""`로 CSV에 쓰는데, 파이썬에서 `0.0`은 거짓으로 평가되므로 **응답시간이 정확히 0초인 기록은 빈 문자열로 저장**된다. `compute_metrics()`도 `rt_values.append(rt) if rt > 0`이라 0초 기록을 평균 계산에서 아예 제외한다. 올바른 조건은 "값이 있는지"(`response_time_sec is not None`)여야지 "참인지"가 아니다.
- **(리비전 9) 기존 삭제 확인창 패턴**: `pages/3_이벤트_다시보기.py`(239~254줄)에 이미 "삭제하시겠습니까?" 확인/취소 2단계 패턴이 구현돼 있다(`st.session_state[confirm_key]`로 확인 모드 전환). 새로 디자인하지 말고 이 패턴을 재사용한다.
- **(리비전 9) `st.data_editor`로 체크박스 컬럼**: 데이터프레임에 `"선택"` 불리언 컬럼을 추가하고 `st.data_editor(..., disabled=[다른 모든 컬럼])`로 그 컬럼만 편집 가능하게 하면, 사용자가 여러 행을 체크할 수 있다. 반환되는 편집된 데이터프레임에서 `"선택"`이 `True`인 행의 `id`를 모아 삭제 대상으로 쓴다.
- **(리비전 10) `st.dialog` 확인**: 설치된 `streamlit==1.55.0`에 `st.dialog(title, *, width="small", dismissible=True, ...)` 데코레이터가 실제로 존재함을 `hasattr(st, "dialog")`로 직접 확인했다. `@st.dialog("제목")`을 붙인 함수를 호출하면 그 함수 본문이 모달 팝업 안에 렌더링된다 — 진짜 팝업창을 원하는 요청에 정확히 맞는 공식 기능이고, 새 의존성이 필요 없다.
- **(리비전 10) 현재 "📈 종합 성능 지표"/"🧮 카테고리별 건수" 구조**: 지표 5개(`st.columns(5)`에 `st.metric`)가 상단에 먼저 가로로 나열되고, 그보다 아래 "➕ 평가기록 수동 추가"와 같은 줄(`st.columns([2, 1])`)의 오른쪽 칸에 "🧮 카테고리별 건수"(TP/FP/FN/TN 건수+비율, 총 건수)가 별도로 있다. 리비전 10은 이 둘을 하나의 세로 블록으로 합친다 — "➕ 평가기록 수동 추가"는 오른쪽 칸이 없어지므로 전체 폭으로 바뀐다.
- **(리비전 12) 현재 페이지 섹션 순서(코드 상 정의 순서)**: `📈 종합 성능 지표` → `➕ 평가기록 수동 추가` → `📋 평가 기록 목록`(체크박스 삭제+팝업 포함) → `🎯 위험 발생 구간 입력`(영상재생·슬라이더·구간저장·자동평가 실행 버튼 포함). 네 섹션 모두 서로 데이터 의존성이 없다(`records`/`metrics`는 상단에서 한 번 계산돼 종합 지표·기록 목록에서만 쓰이고, 위험 구간 입력/수동 추가는 각자 독립적인 session_state 키를 쓴다) — **섹션 전체 블록을 통째로 순서만 옮기면 되고, 블록 내부 로직은 손댈 필요가 없다.**
- **(리비전 12) 지표 카드 높이 불균일 원인**: `st.metric`에 `delta`를 준 것(정탐률/오탐률/미탐률)은 라벨+값+delta 3줄이 되고, `delta`가 없는 것(정밀도/정상(TN)/평균 응답시간/총 측정 건수)은 2줄이라 카드 높이가 짧다. 설치된 Streamlit의 실제 프런트엔드 번들에서 `data-testid="stMetric"`가 각 지표 카드를 감싸는 최상위 엘리먼트임을 확인했다 — `[data-testid="stMetric"] { min-height: ...px; }`로 모든 카드 높이를 통일하면 내용과 무관하게 깔끔하게 맞출 수 있다(새 의존성/구조 변경 불필요, CSS 한 줄).
- **(리비전 13) `st.data_editor`의 `height` 파라미터**: `st.dataframe`/`st.data_editor`는 둘 다 `height`(픽셀) 인자를 받아 그 높이를 넘는 내용은 내부 스크롤 영역으로 자동 처리한다(별도 JS/CSS 없이 표준 기능, 마우스 휠/드래그 스크롤 동작은 Streamlit이 기본 제공). 행 높이는 보통 헤더 약 38px + 데이터 행 약 35px/행이다 — 7행을 보여주려면 대략 `38 + 7*35 ≈ 283px`, 여유를 조금 둬 `height=280~300` 범위를 제안한다. 정확한 픽셀값은 실제 화면에서 몇 행이 보이는지 사용자가 확인한 뒤 미세 조정하면 된다(헤드리스 브라우저로 직접 셀 수 없어 계산값으로 제안).
- **(리비전 14) 현재 "입력된 위험 구간" 표시 코드**: `pages/4_성능_평가.py` 220번째 줄 부근 — `intervals`가 비어 있지 않을 때만 `"#### 입력된 위험 구간"` 헤딩과 목록(번호 "{index+1}. " 포함)을 그리고, 비어 있으면 그 헤딩 자체를 안 그리고 `st.info("입력된 위험 구간이 없습니다. ...")`로 완전히 다른 블록을 보여준다 — 버그가 아니라 의도된 분기였지만, 사용자가 원하는 방식과 다르다.

## 3. 구현 계획

1. **새 모듈 `core/ground_truth.py` 추가** — 순수 파이썬(json/pathlib)만 사용, `cv2`/`numpy`/`torch` 등 무거운 의존성 없음:
   - `DATA_DIR`, `GROUND_TRUTH_PATH`, `VIDEO_EXTENSIONS` 상수
   - `video_files() -> list[str]`
   - `load_ground_truth() -> dict[str, list[tuple[float, float]]]` — `tools/auto_eval.py`의 기존 `load_ground_truth()` 검증 로직(각 구간 `[시작, 끝]`, `0 <= 시작 < 끝`, JSON 형식 오류 처리)을 그대로 옮긴다.
   - `save_intervals(video_name: str, intervals: list[tuple[float, float]]) -> None` — 기존 JSON을 읽어 다른 영상의 항목은 그대로 두고, `video_name` 항목만 `{"danger_intervals": [[s, e], ...]}`로 교체해 다시 쓴다(병합 저장). 파일이 없으면 빈 `{}`에서 시작.
2. **`tools/auto_eval.py` 수정** — 자체 정의했던 `load_ground_truth()`, `video_files()`, `GROUND_TRUTH_PATH`, `DATA_DIR`, `VIDEO_EXTENSIONS`를 삭제하고 `core/ground_truth.py`에서 import해 사용한다. **이 파일의 나머지 로직(알람 구간 감지·분류·CSV 기록)은 전혀 바꾸지 않는다.** 이렇게 해야 성능평가 페이지와 자동평가 스크립트가 같은 검증 규칙을 공유해 형식이 어긋날 위험이 없다.
3. **`pages/4_성능_평가.py`에 섹션 추가** — "📋 평가 기록 목록" 섹션과 "ℹ️ 평가 방법 안내" expander 사이에, 항상 렌더링되는 최상위 블록으로 추가한다(조건부로 사라지는 위치에 두지 않음 — 과거 스트림릿 "ghost element" 문제 회피):
   - `from core.ground_truth import DATA_DIR, video_files, load_ground_truth, save_intervals` 추가(가벼운 import만, `tools.auto_eval` 전체는 import하지 않음).
   - 영상 선택 `st.selectbox` → 선택된 영상 `st.video()`로 재생.
   - 영상이 바뀌면(`st.session_state`에 저장된 "마지막으로 로드한 영상"과 다르면) 그 영상의 기존 구간을 `load_ground_truth()`에서 불러와 `st.session_state`에 편집 중 목록으로 적재.
   - 구간 목록 표시 + 개별 삭제 버튼.
   - 시작초/종료초 `st.number_input` 2개 + "추가" 버튼(종료 <= 시작이면 에러 표시, 저장하지 않음).
   - "저장" 버튼 → `save_intervals(선택된 영상, 편집 중 목록)` 호출 후 성공 메시지.
   - `data/` 폴더가 비었을 때(영상이 없을 때)는 안내 메시지만 표시.
4. **(리비전 2) 공용 변환 모듈 `core/video_playback.py` 신규 추가** — `pages/3_이벤트_다시보기.py`의 `get_playable_video()`를 그대로 옮긴다(로직 변경 없음, 함수 시그니처에 `cache_dir`과 `timeout_sec`을 매개변수로 추가해 호출부마다 다른 캐시 위치/타임아웃을 쓸 수 있게 한다 — 기존 호출부는 기존 값(`saved_events/_converted/`, 30초)을 그대로 넘겨 동작 무변경):
   ```python
   def get_playable_video(clip_path: str, cache_dir: str, timeout_sec: float = 30.0) -> str | None:
       ...  # pages/3의 기존 구현과 동일
   ```
5. **(리비전 2) `pages/3_이벤트_다시보기.py` 수정** — 자체 정의했던 `get_playable_video()`를 지우고 `core/video_playback.py`에서 import해 `CONVERTED_DIR`과 기존 타임아웃(30초)을 그대로 넘겨 호출한다. **동작 변화 없음(순수 리팩터링).**
6. **(리비전 2) `pages/4_성능_평가.py`의 "위험 발생 구간 입력" 섹션 수정** — `st.video(str(DATA_DIR / selected_video))` 직접 호출을 제거하고, `get_playable_video(str(DATA_DIR / selected_video), cache_dir="data/_converted", timeout_sec=120.0)`로 변환된 경로를 얻어 `with open(playable, "rb") as f: st.video(f.read())` 방식으로 재생한다(바이트로 넘기는 건 `pages/3`과 동일한 패턴). 변환 중에는 `st.spinner`로 로딩 표시. 변환 실패 시 에러 메시지 표시(크래시하지 않음). `data/_converted/`는 `data/*` gitignore 규칙에 이미 포함돼 추적되지 않는다(.gitignore 수정 불필요). **(실제 반영: `cache_dir=str(DATA_DIR / "_converted")`로 절대경로화됨 — Claude가 리뷰 중 직접 수정.)**
7. **(리비전 3) `core/video_playback.py`에 `get_video_duration_seconds(path: str) -> float | None` 추가** — 새 heavy 의존성 없이 기존 `imageio_ffmpeg.get_ffmpeg_exe()`로 ffmpeg를 실행해 `-i` 출력(stderr)에서 `Duration: HH:MM:SS.ss`를 정규식으로 파싱해 초 단위로 변환한다. 파싱 실패/영상 열기 실패 시 `None`을 반환한다(예외를 던지지 않음 — 호출부가 기본값으로 대체).
8. **(리비전 3) `pages/4_성능_평가.py`의 "위험 발생 구간 입력" 섹션에 탐색 UI 추가**:
   - 변환된(`playable`) 파일의 길이를 `get_video_duration_seconds(playable)`로 구한다. `None`이면 기본값(예: 300.0초)으로 대체하고 `st.caption`으로 "영상 길이를 확인할 수 없어 기본 범위를 사용합니다"라고 안내한다(크래시 없음).
   - `seek_sec = st.slider("🔎 위치 탐색(초)", min_value=0.0, max_value=duration, value=..., step=0.1, key="ground_truth_seek")`를 영상 선택 직후 추가.
   - 기존 `st.video(bytes)` 호출에 `start_time=seek_sec`를 추가해, 슬라이더를 움직이면(릴리즈 시 1회 rerun) 그 위치로 미리보기가 이동한다. 오디오는 이미 `-an`으로 제거돼 있어 자동재생 정책과 무관하다.
   - 슬라이더 옆에 버튼 2개: "⏮ 이 위치를 시작초로", "⏭ 이 위치를 종료초로". 클릭 시 `st.session_state["ground_truth_start"] = seek_sec`(또는 `"ground_truth_end"`)로 **기존 `number_input` 위젯의 session_state 값**을 먼저 설정하고 `st.rerun()`한다 — 그러면 다음 렌더에서 그 `number_input`이 이 값으로 표시된다(위젯 재생성 전에 session_state를 쓰는 기존 검증된 패턴, 구간 추가/삭제에서 쓴 것과 동일).
   - **기존 `number_input`(시작초/종료초) 수기 입력은 그대로 남겨 둔다** — 슬라이더는 값을 채워주는 보조 수단일 뿐, 미세 조정은 여전히 직접 타이핑으로 가능해야 한다.
   - 영상이 바뀌면(선택 영상이 달라지면) 슬라이더 위치를 0으로 초기화한다(이전 영상의 탐색 위치가 새 영상에 남아있으면 혼란스러움).
9. **(리비전 4) 의존성 추가** — `pip install streamlit-player`로 설치 후, 실제 설치된 버전을 `requirements.txt`에 `streamlit-player==<설치된 버전>` 형태로 고정 기록한다(추측 버전 쓰지 말 것).
10. **(리비전 4) 정적 파일 서빙 활성화** — `.streamlit/config.toml`의 `[server]` 섹션에 `enableStaticServing = true`를 추가한다(기존 `headless = true`는 유지). 프로젝트 루트(= `app.py`가 있는 위치, `ROOT`)에 `static/ground_truth_videos/` 폴더를 두고, 이 폴더를 `.gitignore`에 추가한다(변환 캐시이므로 `data/_converted/`, `saved_events/_converted/`와 동일하게 추적 제외).
11. **(리비전 4) `pages/4_성능_평가.py`의 "위험 발생 구간 입력" 섹션 재구성** — 리비전 3에서 추가한 보조 `st.slider("🔎 위치 탐색(초)")`와 `st.video(bytes, start_time=...)` 호출을 제거하고 다음으로 교체한다:
    - `get_playable_video(str(DATA_DIR / selected_video), cache_dir=os.path.join(ROOT, "static", "ground_truth_videos"), timeout_sec=120.0)`로 변환본을 **`static/` 아래**에 생성한다(`ROOT`는 파일 상단에 이미 정의된 프로젝트 루트 변수 — 기존 `data/_converted/` 캐시와는 별개. 정적 서빙 경로에 있어야 `st_player`가 URL로 접근 가능하기 때문).
    - 변환된 파일명으로 정적 URL을 구성한다(Streamlit 공식 규칙: `static/` 밑 파일은 `app/static/<파일명>`으로 접근 가능 — 실제 설치된 `streamlit==1.55.0`에서 정확한 경로 규칙을 코드로 재확인할 것, 추측 금지).
    - `from streamlit_player import st_player`로 플레이어를 띄우고 `events=["onSeek"]`를 지정한다. 반환값 `event`의 `event.name == "onSeek"`이면 `event.data`(이동한 초)를 `st.session_state.ground_truth_last_seek`에 저장한다.
    - "⏮ 이 위치를 시작초로" / "⏭ 이 위치를 종료초로" 버튼은 이제 `st.session_state.ground_truth_last_seek`(네이티브 진행바 조작 결과)를 읽어 `ground_truth_start`/`ground_truth_end`에 쓰고 `st.rerun()`한다 — 로직은 동일하되 값의 출처만 "보조 슬라이더" → "네이티브 진행바 onSeek"로 바뀐다.
    - 변환 실패 시(기존과 동일하게) 에러 메시지를 표시하고 크래시하지 않는다.
    - 영상이 바뀌면 `ground_truth_last_seek`를 초기화한다.
12. **(리비전 4) `core/video_playback.py`의 `get_video_duration_seconds()` 정리** — 리비전 3에서 보조 슬라이더의 `max_value` 계산에만 쓰였는데, 이번에 그 슬라이더 자체가 없어진다. 다른 호출부가 없다면(`rg`로 확인) 죽은 코드이므로 **제거**한다. 다른 곳에서 쓰기로 한다면 그 이유를 구현 결과에 남길 것.
13. **(리비전 4, 폐기)** ~~검증 방법 지침~~ — 실기 테스트 결과 재생 자체가 안 돼 리비전 4 설계 전체를 폐기한다. 아래 14~17번이 리비전 5(되돌리기) 계획이다.

### 리비전 5 — streamlit-player 폐기, 리비전 3 방식 복원 + 레이아웃 변경 + 사이드바 버그 수정

14. **`pages/4_성능_평가.py`의 "위험 발생 구간 입력" 섹션을 리비전 3 시점 구현으로 되돌린다**:
    - `from streamlit import runtime`, `from streamlit_player import st_player`, `runtime.get_instance().media_file_mgr.add(...)` 호출을 전부 제거한다.
    - `get_playable_video()` 호출의 `cache_dir`을 다시 `str(DATA_DIR / "_converted")`로 되돌린다(리비전 4에서 `static/ground_truth_videos`로 옮겼던 것을 원복).
    - `get_video_duration_seconds(playable)`로 영상 길이를 구하고(`None`이면 300.0 기본값 + 안내 캡션), **배치 순서를 다음으로 한다**:
      1. `with open(playable, "rb") as f: st.video(f.read())` — 영상 재생 화면
      2. `seek_sec = st.slider("🔎 위치 탐색(초)", 0.0, duration, step=0.1, key="ground_truth_seek")` — 보조 탐색 슬라이더 (영상 "아래")
      3. "⏮ 이 위치를 시작초로" / "⏭ 이 위치를 종료초로" 버튼 (슬라이더 "아래") — 클릭 시 `st.session_state.ground_truth_start`/`ground_truth_end`에 `seek_sec`을 쓰고 `st.rerun()`
    - **주의**: 슬라이더가 움직인 값을 영상 미리보기에 반영하려면(리비전 3처럼) `st.video(..., start_time=seek_sec)`을 쓰되, 슬라이더를 영상보다 먼저 렌더링해 그 값을 읽은 뒤 영상에 적용해야 한다 — 단, 사용자는 "영상 화면 → 슬라이더 → 버튼" **화면상 배치 순서**를 원한 것이므로, 코드 실행 순서(슬라이더 값을 먼저 계산)와 **화면 렌더링 순서**(영상을 먼저 그린 뒤 슬라이더를 그 아래 배치)를 구분해서 구현할 것. (예: `seek_sec` 계산을 먼저 하되 `st.video`를 그보다 위에 배치한 `st.container`/순서로 그릴 수도 있고, 간단히는 "이전 run의 slider 값으로 비디오를 그리고, 그 아래 슬라이더를 배치"해도 사용자 경험상 큰 차이가 없다 — 어떤 방식이든 **최종 화면 순서가 영상→슬라이더→버튼**이면 된다.)
    - 영상이 바뀌면 `ground_truth_seek`(슬라이더 세션 상태)를 0.0으로 초기화.
15. **`requirements.txt`에서 `streamlit-player==0.1.5` 제거.**
16. **`.streamlit/config.toml`에서 `enableStaticServing = true` 제거**(리비전 4에서 추가한 것 — 리비전 5에선 정적 서빙이 더 이상 필요 없음). `.gitignore`의 `static/ground_truth_videos/` 줄도 제거하고, 실제로 생성된 `static/ground_truth_videos/` 디렉터리도 정리(더는 쓰지 않음 — `data/_converted/`로 캐시가 다시 모인다).
17. **사이드바 재열기 버튼 버그 수정 (`app.py`)**: Claude가 설치된 `streamlit` 패키지의 프런트엔드 JS 번들(`venv/Lib/site-packages/streamlit/static/static/js/*.js`)을 직접 열어 확인한 사실 — 사이드바를 접으면 다시 펼치는 버튼은 `data-testid="stExpandSidebarButton"`으로 렌더링되고, 이 버튼은 `header[data-testid="stHeader"]` **안에** 있다. 현재 `app.py`의 전역 CSS가 `header[data-testid="stHeader"] { display: none !important; }`로 헤더 전체를 지워서 이 버튼도 함께 사라진다. 다음으로 교체한다:
    ```css
    header[data-testid="stHeader"] {
        display: block !important;
        position: fixed !important;
        top: 0; left: 0; right: 0;
        background: transparent !important;
        box-shadow: none !important;
        z-index: 999999;
        visibility: hidden;
    }
    header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"] {
        visibility: visible !important;
    }
    ```
    - `visibility: hidden`은 자손이 `visibility: visible`로 다시 보이게 할 수 있다(`display:none`과 다른 점 — 이 차이를 이용한다).
    - 기존에 `#MainMenu`, `footer`를 숨기던 규칙은 그대로 둔다(이 수정과 무관).
    - **검증 시 주의**: 사이드바가 펼쳐진 상태에서는 이 버튼이 애초에 안 보여야 하므로(접었을 때만 나타나는 버튼), "항상 화면에 떠 있는 투명 바 때문에 다른 요소 클릭이 막히지 않는지"를 코드 리뷰로 확인할 것 — `visibility:hidden`인 요소는 클릭도 통과시키므로(히트테스트 제외) 문제 없을 것으로 예상되나, 혹시 모를 레이아웃 겹침 여부도 함께 점검.

### 리비전 6 — 슬라이더 사용법 설명 + 사이드바 버튼 색상 통일

18. **`pages/4_성능_평가.py`의 탐색 슬라이더에 `help` 파라미터 추가**:
    ```python
    seek_sec = st.slider(
        "🔎 위치 탐색(초)",
        min_value=0.0,
        max_value=float(duration),
        step=0.1,
        key="ground_truth_seek",
        help="시작초/종료초를 입력할 위치를 드래그 하거나 클릭하세요.",
    )
    ```
    - 스트림릿 위젯의 `help`는 라벨 옆에 "?" 아이콘으로 표시되고 마우스를 올리면 설명이 뜬다 — "이름 옆에 설명"이라는 요청에 맞는 표준 방식. 새 `st.caption`을 추가하는 방식은 쓰지 않는다(화면이 번잡해지지 않도록).
19. **`app.py`의 사이드바 접기/펼치기 버튼 아이콘 색상 수정** — 기존 규칙을 아이콘 엘리먼트까지 직접 타깃하도록 바꾼다:
    ```css
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarCollapseButton"] button * {
        color: #4CAF50 !important;
    }
    header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"] {
        visibility: visible !important;
        color: #4CAF50 !important;
    }
    header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"] * {
        color: #4CAF50 !important;
    }
    ```
    - 기존 `[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button { color: #CBD5E1 !important; }` 규칙은 **삭제하거나 위 `#4CAF50` 규칙으로 교체**한다(두 규칙이 동시에 있으면 CSS 명시도 다툼으로 혼란스러워질 수 있음 — 하나만 남긴다).
    - `#4CAF50`은 `.streamlit/config.toml`의 `primaryColor`(세이프뷰 로고 초록색)와 동일한 값이다 — 추측하지 말고 그 파일의 값을 그대로 가져다 쓸 것.
    - **아이콘 자신에게 인라인으로 박힌 `color`를 덮으려면 버튼의 모든 자손(`*`)까지 명시적으로 타깃해야 한다** — 조사 결과에 적어둔 이유 그대로. 버튼 엘리먼트에만 `color`를 주는 것만으로는 해결되지 않았던 걸 재현하지 말 것.

### 리비전 7 — 슬라이더 설명을 "항상 보이는 텍스트"로 변경

**사용자 피드백**: "도움말 방식이 아니라 그냥 이름 옆에 설명이 바로 보이게 하는 거였어." `help=` 파라미터는 라벨 옆에 작은 "?" 아이콘만 두고, 마우스를 올려야 설명이 보이는 **호버 방식**이다 — 사용자는 마우스 조작 없이 **항상 바로 보이는 텍스트**를 원한다.

20. **`pages/4_성능_평가.py`의 탐색 슬라이더 — `help` 파라미터를 제거하고, 라벨 문자열 자체에 설명을 포함시킨다**:
    ```python
    seek_sec = st.slider(
        "🔎 위치 탐색(초) — 시작초/종료초를 입력할 위치를 드래그 하거나 클릭하세요",
        min_value=0.0,
        max_value=float(duration),
        step=0.1,
        key="ground_truth_seek",
    )
    ```
    - Streamlit 위젯은 라벨을 별도 꾸밈 요소 없이 "이름 + 설명을 한 줄의 라벨 문자열"로 합치는 것이 가장 단순하고 확실하게 "항상 보이는" 방식이다 — 새로운 컴포넌트나 커스텀 HTML을 만들지 않는다.
    - `help=` 파라미터는 제거한다(남겨두면 "?" 아이콘이 중복으로 남아 혼란을 줄 수 있음).

**(참고, 이미 반영됨)** 리비전 7 사용자 실기 중 발견된 "The widget with key 'ground_truth_start' was created with a default value but also had its value set via the Session State API" 경고는 Claude가 직접 `number_input`의 `value=0.0`을 제거해 해결했다(위 상태 섹션 기록 참고) — 리비전 8 범위에 다시 포함할 필요 없음.

### 리비전 8 — 저장 버튼 통합 + 자동 평가 실행 버튼

21. **`pages/4_성능_평가.py` — "구간 추가"와 "저장" 버튼을 "구간 저장" 버튼 하나로 통합**:
    ```python
    if st.button("💾 구간 저장", type="primary", use_container_width=True):
        if end_sec > start_sec:
            intervals.append((float(start_sec), float(end_sec)))
            st.session_state.ground_truth_intervals = intervals
        try:
            save_intervals(selected_video, intervals)
            st.success(f"'{selected_video}'의 위험 발생 구간을 저장했습니다.")
            st.rerun()
        except (OSError, ValueError) as exc:
            st.error(f"저장에 실패했습니다: {exc}")
    ```
    - **판단 기준**: 시작초/종료초가 untouched 기본값(둘 다 0.0)이면 "추가할 새 구간 없음"으로 보고 **현재 목록을 그대로 저장만** 한다(삭제만 하고 저장하려는 경우, 또는 "위험 없음"으로 빈 목록을 저장하려는 경우에 해당). `end_sec > start_sec`이면 유효한 새 구간으로 보고 추가 후 저장한다. `end_sec`이 설정됐는데 `start_sec`보다 작거나 같은 "명백히 잘못 입력된" 경우에만 에러를 보여줄지는 구현 중 가장 혼란이 적은 쪽으로 판단하되, **최소 요구사항은 "버튼 하나로 추가+저장이 모두 끝난다"**는 것이다.
    - 기존 두 버튼("구간 추가", "저장")과 그 두 개의 `st.columns` 레이아웃은 제거하고, 버튼 하나를 전체 너비로 배치한다.
    - 삭제 버튼(`delete_ground_truth_{index}`)의 동작은 그대로 둔다(목록에서만 제거, 파일 반영은 여전히 "구간 저장" 클릭 시 — 삭제 후 저장하려면 이 통합 버튼을 누르면 된다).
22. **`pages/4_성능_평가.py` — "🧮 지금 자동 평가 실행" 버튼 추가** (구간 저장 버튼 아래, 같은 섹션 안):
    ```python
    import subprocess
    import sys
    ...
    if st.button("🧮 지금 자동 평가 실행", use_container_width=True):
        with st.spinner(f"'{selected_video}' 평가 중 — 영상 길이에 따라 다소 걸릴 수 있습니다..."):
            result = subprocess.run(
                [sys.executable, os.path.join(ROOT, "tools", "auto_eval.py"),
                 "--video", selected_video],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=ROOT,
            )
        if result.returncode == 0:
            st.success("자동 평가가 완료됐습니다. 아래 '📋 평가 기록 목록'에 반영됐습니다.")
            with st.expander("실행 로그 보기"):
                st.code(result.stdout or "(출력 없음)")
        else:
            st.error("자동 평가 실행에 실패했습니다.")
            with st.expander("오류 로그 보기"):
                st.code(result.stderr or "(오류 메시지 없음)")
    ```
    - `tools/auto_eval.py`를 **import하지 않고 `subprocess`로 별도 프로세스 실행** — 페이지 자체는 여전히 `cv2`/`torch`를 로딩하지 않는다(기존 성능 원칙 유지).
    - `sys.executable`로 현재 venv의 파이썬 인터프리터를 명시적으로 써서, 다른 파이썬이 잡히는 일이 없게 한다.
    - `--video <선택된 영상>`으로 **선택된 영상 하나만** 평가한다(전체 영상을 매번 다 돌리지 않음).
    - 그 영상에 대한 정답지가 비어 있거나(`eval_ground_truth.json`에 아직 저장 안 한 상태) 없으면, `tools/auto_eval.py`는 기존 동작대로 "정답지가 없어 제외" 경고만 찍고 조용히 끝난다 — 페이지에서 "먼저 '구간 저장'을 눌러 정답지를 저장하세요"처럼 더 친절한 사전 안내 문구를 버튼 위에 `st.caption`으로 덧붙인다.
    - 실행 결과(성공/실패)와 표준출력/표준에러를 `st.expander`로 보여줘 팀원이 무슨 일이 있었는지 바로 확인할 수 있게 한다.
23. **"📋 평가 기록 목록에 반영됨" 안내 문구**는 21·22번에 이미 포함돼 있다 — 자동 평가 성공 메시지에 반드시 그 문구가 들어가야 한다(사용자가 명시적으로 요청한 문구).

### 리비전 9 — ROI 경고, 응답시간 버그, 시각 표시, 삭제 UX, 수동 추가 토글

24. **`pages/4_성능_평가.py` — ROI 없음 경고**: `from core.roi_manager import load_rois` 추가. `selected_video = st.selectbox(...)` 바로 다음 줄에:
    ```python
    if load_rois(os.path.splitext(selected_video)[0]) is None:
        st.warning("⚠️ ROI가 없습니다 — ROI 설정 페이지에서 먼저 저장하세요.")
    ```
    영상 재생(`st.video`) 스피너/블록보다 **먼저** 보이도록 이 위치에 둔다.
25. **`core/performance_eval.py` — 응답시간 falsy-zero 버그 수정**:
    - `add_record()`의 `response_time_sec` 기본값을 `0.0`에서 `None`으로 바꾸고, CSV 작성 조건을 `if response_time_sec else ""`에서 **`if response_time_sec is not None else ""`**로 바꾼다. (0.0은 "값 없음"이 아니라 "측정된 응답시간이 0초"라는 뜻이어야 한다.)
    - `compute_metrics()`의 응답시간 집계 조건도 `if rt > 0`에서 **값이 존재하는지**로 바꾼다(빈 문자열/`None`이 아니면 포함, 0.0도 포함):
      ```python
      raw = r.get("response_time_sec")
      if raw not in (None, ""):
          try:
              rt_values.append(float(raw))
          except ValueError:
              pass
      ```
26. **`tools/auto_eval.py`의 `save_results()` — 자동 기록은 TP에만 실제 응답시간을 쓴다**: 오탐/미탐/정상(FP/FN/TN)은 애초에 "알람까지 걸린 시간"이라는 개념 자체가 성립하지 않는다(콘솔 출력 `print_video_results`도 이미 TP일 때만 응답시간을 보여주고 있다 — 같은 원칙을 CSV 기록에도 맞춘다). `save_results()`에서 `add_record()` 호출 시:
    ```python
    for result in results:
        response_time = result["response_time"] if result["result"] == TP else None
        if not add_record(..., response_time_sec=response_time, ...):
    ```
    이렇게 하면 TP는 0초여도 "0.00"으로 정확히 기록되고, FP/FN/TN은 (의미 없는 값이므로) 계속 빈칸으로 남는다 — 수동 추가 폼에서 사용자가 직접 입력한 값은 어떤 분류든 그대로 존중한다(25번 수정만으로 충분, `add_record` 자체는 손대지 않음).
27. **`pages/4_성능_평가.py` — 기록 시각 분 단위 표시**: `df_display`를 만들 때 `timestamp` 문자열(`"YYYY-MM-DD HH:MM:SS"`)을 분 단위로 자른다(`[:16]`). 저장되는 실제 CSV 값은 그대로 두고 **화면 표시용 DataFrame에서만** 자른다.
28. **`pages/4_성능_평가.py` — 체크박스 다중 선택 + 확인창 삭제**로 기존 `st.expander`+`selectbox`+버튼 삭제 UI를 교체한다:
    - 레코드 `id`를 일반 컬럼이 아니라 **DataFrame의 index**로 둔다(`pd.DataFrame(df_records).set_index("id")`) — 그래야 `hide_index=True`로 화면엔 안 보이면서도, `st.data_editor`가 돌려주는 결과의 인덱스로 원래 `id`를 안정적으로 추적할 수 있다(정렬/편집 후에도 행-ID 매핑이 깨지지 않도록).
    - `"선택"`이라는 불리언 컬럼을 맨 앞에 추가하고, `st.data_editor(df_display, hide_index=True, disabled=["선택" 이외 모든 컬럼])`로 그 컬럼만 체크 가능하게 한다.
    - 목록 영역 위쪽에 `st.columns([5, 1])`로 오른쪽 칸에 "🗑️ 삭제" 버튼을 둔다(목록 오른쪽 상단에 있는 것처럼 보이도록).
    - "삭제" 클릭 → 체크된 행이 없으면 경고만 표시 → 있으면 `st.session_state`에 삭제 대기 id 목록을 저장하고 확인 질문("선택한 N건을 삭제하시겠습니까?") + "삭제"/"취소" 버튼 2개를 보여준다(패턴은 `pages/3_이벤트_다시보기.py`의 기존 확인창 그대로 재사용).
    - "삭제" 확인을 누르면 대기 중인 id들을 각각 `delete_record()`로 지우고 성공 메시지, "취소"를 누르면 그냥 대기 상태만 비운다.
29. **`pages/4_성능_평가.py` — "➕ 평가 기록 추가" → "➕ 평가기록 수동 추가" 이름 변경 + 토글로 폼 숨김**:
    ```python
    st.markdown("### ➕ 평가기록 수동 추가")
    show_manual_form = st.toggle("입력창 열기", key="eval_manual_form_toggle")
    if show_manual_form:
        with st.form("eval_form", clear_on_submit=True):
            ...(기존 폼 내용 그대로)...
    ```
    기본값은 꺼짐(`st.toggle`은 별도 `value=` 안 주면 기본 `False`) — 페이지 진입 시 폼이 바로 안 보인다.

### 리비전 10 — 삭제 버튼 위치/팝업화, 종합 지표 세로 통합

30. **삭제 버튼을 체크박스 열 위로 이동**: 현재 `_, delete_col = st.columns([5, 1])`(오른쪽 끝)를 `delete_col, _ = st.columns([1, 5])`(왼쪽 끝 — `"선택"` 체크박스 컬럼이 테이블의 첫 번째/왼쪽 컬럼이므로, 그 위에 오도록)로 바꾼다. `delete_col.empty()`로 자리를 먼저 잡고 `st.data_editor` 렌더링 후 버튼 내용을 채우는 기존 패턴은 그대로 유지한다.
31. **삭제 확인을 `st.dialog` 모달 팝업으로 교체**:
    ```python
    @st.dialog("삭제 확인")
    def _confirm_delete_dialog(pending_ids):
        st.warning(f"선택한 {len(pending_ids)}건을 삭제하시겠습니까?")
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button("삭제", type="primary", use_container_width=True, key="eval_delete_confirm"):
            failed_ids = [rid for rid in pending_ids if not delete_record(rid)]
            st.session_state.eval_delete_pending = []
            if failed_ids:
                st.error(f"{len(failed_ids)}건을 삭제하지 못했습니다.")
            else:
                st.success(f"{len(pending_ids)}건이 삭제되었습니다.")
            st.rerun()
        if cancel_col.button("취소", use_container_width=True, key="eval_delete_cancel"):
            st.session_state.eval_delete_pending = []
            st.rerun()

    ...
    pending_ids = st.session_state.get("eval_delete_pending", [])
    if pending_ids:
        _confirm_delete_dialog(pending_ids)
    ```
    기존 "선택 없이 삭제 클릭 → 경고" 분기(`st.warning("삭제할 기록을 선택하세요.")`)는 그대로 인라인으로 둔다(선택 자체가 없으니 모달을 띄울 필요가 없음) — **모달은 "확인/취소"가 필요한 단계에만** 쓴다.
32. **"📈 종합 성능 지표"를 세로로 재배치하고 "🧮 카테고리별 건수"를 통합**:
    ```python
    st.markdown("### 📈 종합 성능 지표")
    counts = metrics["counts"]
    total = metrics["total"]

    def _pct(n):
        return f"{(n / total * 100):.1f}%" if total else "0.0%"

    st.metric("정탐률 (Recall)", f"{metrics['recall']:.1f}%",
              delta=f"정탐(TP) {counts['정탐 (TP)']}건 ({_pct(counts['정탐 (TP)'])})", delta_color="off",
              help="실제 위험 중 시스템이 감지한 비율 (높을수록 좋음)")
    st.metric("정밀도 (Precision)", f"{metrics['precision']:.1f}%",
              help="시스템이 감지한 것 중 실제 위험이었던 비율")
    st.metric("오탐률 (FAR)", f"{metrics['far']:.1f}%",
              delta=f"오탐(FP) {counts['오탐 (FP)']}건 ({_pct(counts['오탐 (FP)'])})", delta_color="off",
              help="정상 상황을 위험으로 잘못 판단한 비율 (낮을수록 좋음)")
    st.metric("미탐률 (Miss)", f"{metrics['miss']:.1f}%",
              delta=f"미탐(FN) {counts['미탐 (FN)']}건 ({_pct(counts['미탐 (FN)'])})", delta_color="off",
              help="실제 위험을 놓친 비율 (낮을수록 좋음)")
    st.metric("정상 (TN)", f"{counts['정상 (TN)']}건 ({_pct(counts['정상 (TN)'])})")
    st.metric("평균 응답시간", f"{metrics['avg_response']:.2f}s" if metrics['rt_samples'] else "—",
              help=f"이벤트 발생 → 알람까지 소요 시간 (샘플 {metrics['rt_samples']}건)")
    st.metric("총 측정 건수", f"{total}건")
    ```
    - 5개를 나열하던 `st.columns(5)`는 제거하고, `st.metric`을 세로로 하나씩 호출한다(열 없이 순서대로 — 자연히 세로 배치가 된다).
    - **지표-건수 매칭 기준**: 정탐률↔정탐(TP), 오탐률↔오탐(FP), 미탐률↔미탐(FN)은 `delta`로 건수를 함께 보여준다(1:1로 대응되는 분류). 정밀도는 TP/FP 둘 다에 걸쳐 있어 특정 건수 하나와 묶지 않고 단독으로 둔다. 정상(TN)과 총 건수는 대응하는 비율 지표가 없으므로 건수만 표시한다. **이 매칭 방식이 사용자가 기대한 것과 다르면 쉽게 조정 가능하니, 실기 확인 후 알려줄 것.**
    - 기존 "🧮 카테고리별 건수" 블록(94~102번째 줄 부근)은 통째로 삭제한다.
    - `form_col, count_col = st.columns([2, 1])`도 더 이상 오른쪽 칸이 필요 없으므로 제거하고, "➕ 평가기록 수동 추가" 블록을 전체 폭으로 바꾼다(`with form_col:` 대신 바로 최상위 블록으로).

### 리비전 11 — 종합 성능 지표, 가로 배치로 되돌리기(내용은 그대로)

33. **`pages/4_성능_평가.py` — 리비전 10의 지표 7개(`st.metric` 7회 호출)를 `st.columns(7)`로 감싸 한 줄에 나란히 배치한다.** 각 `st.metric` 호출 인자(`delta`, `delta_color="off"`, `help` 포함)는 **하나도 바꾸지 않는다** — 오직 "순서대로 세로 나열" → "7칸 컬럼에 하나씩" 배치만 바꾼다:
    ```python
    cols = st.columns(7)
    cols[0].metric("정탐률 (Recall)", ..., delta=..., delta_color="off", help=...)
    cols[1].metric("정밀도 (Precision)", ..., help=...)
    cols[2].metric("오탐률 (FAR)", ..., delta=..., delta_color="off", help=...)
    cols[3].metric("미탐률 (Miss)", ..., delta=..., delta_color="off", help=...)
    cols[4].metric("정상 (TN)", ...)
    cols[5].metric("평균 응답시간", ..., help=...)
    cols[6].metric("총 측정 건수", ...)
    ```
    (정확한 인자 값은 리비전 10에서 이미 구현된 그대로 가져다 쓴다 — 위 코드는 배치 구조만 보여주는 뼈대.)
    - 7칸이 좁아 `delta` 텍스트(예: "정탐(TP) 12건 (60.0%)")가 줄바꿈되거나 잘릴 수 있다 — Streamlit이 자동으로 줄바꿈 처리하므로 별도 CSS를 추가하지 않아도 되지만, 실제 화면에서 너무 뭉개지면 사용자가 보고 조정 요청할 수 있다.

### 리비전 12 — 섹션 순서 재배치 + 지표 카드 높이 통일

34. **`pages/4_성능_평가.py` — 섹션 순서를 "종합 성능 지표 → 평가 기록 목록 → 성능 자동평가 - 위험 발생 구간 입력 → 평가기록 수동 추가"로 재배치**:
    - 네 섹션(각각 `st.markdown("---")`로 구분된 블록)을 **블록 단위로 통째로 옮긴다** — 블록 내부의 코드(위젯, 조건문, `session_state` 키 이름 등)는 한 글자도 바꾸지 않는다. 섹션 사이 의존성이 없음을 조사 결과에서 확인했으므로 순서만 바꿔도 안전하다.
    - `🎯 위험 발생 구간 입력` 섹션의 `st.markdown("### 🎯 위험 발생 구간 입력")`을 `st.markdown("### 🎯 성능 자동평가 - 위험 발생 구간 입력")`로 제목만 바꾼다(그 안의 "🧮 자동 평가 실행" 버튼 등 하위 요소 문구는 그대로).
    - 최종 파일 안 블록 순서: ① 📈 종합 성능 지표 ② 📋 평가 기록 목록(체크박스+삭제 팝업) ③ 🎯 성능 자동평가 - 위험 발생 구간 입력(제목 변경) ④ ➕ 평가기록 수동 추가.
35. **`pages/4_성능_평가.py` 상단 CSS — 지표 카드 높이 통일**:
    ```css
    [data-testid="stMetric"] {
        min-height: 135px;
    }
    ```
    기존 `st.markdown("""<style>...</style>""", unsafe_allow_html=True)` 블록(파일 상단, `.eval-heading` 등이 있는 곳)에 이 규칙을 추가한다. 135px는 `delta`가 있는 3줄짜리 카드가 자연스럽게 들어갈 정도의 제안값이다 — 실제 화면에서 너무 크거나 작으면 사용자가 보고 조정 요청할 수 있다.

### 리비전 13 — 평가 기록 목록 고정 높이(약 7행) + 스크롤

36. **`pages/4_성능_평가.py`의 "📋 평가 기록 목록" — `st.data_editor` 호출에 `height=` 인자를 추가**:
    ```python
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=290,
        disabled=[column for column in df_display.columns if column != "선택"],
        key="eval_records_editor",
    )
    ```
    - `height=290`은 조사 결과에 적어둔 계산(헤더 약 38px + 7행 × 약 35px)에 따른 제안값 — 다른 매개변수(`disabled`, `key`, `use_container_width`, `hide_index`)는 그대로 둔다.
    - 기록이 7건 이하일 때는 빈 공간이 남고, 8건 이상일 때부터 내부 스크롤이 생기는 게 정상 동작이다(Streamlit 표준 동작, 추가 코드 불필요).

### 리비전 14 — "입력된 위험 구간" 항상 표시 + 빈 상태 문구 + 번호 제거

37. **`pages/4_성능_평가.py`의 "입력된 위험 구간" 표시 로직을 다음으로 교체**:
    ```python
    intervals = st.session_state.get("ground_truth_intervals", [])
    st.markdown("#### 입력된 위험 구간")
    if intervals:
        for index, (start, end) in enumerate(intervals):
            interval_col, delete_col = st.columns([5, 1])
            interval_col.write(f"{start:g}초 ~ {end:g}초")
            if delete_col.button("삭제", key=f"delete_ground_truth_{index}"):
                intervals.pop(index)
                st.session_state.ground_truth_intervals = intervals
                st.rerun()
    else:
        st.write("위험 구간 없음")
    ```
    - `"#### 입력된 위험 구간"` 헤딩을 `if intervals:` 바깥으로 빼서 **항상 그려지게** 한다.
    - 비어 있을 때는 기존의 긴 `st.info(...)` 안내 문구 대신 **"위험 구간 없음"** 한 줄만 보여준다.
    - 목록 줄의 `f"{index + 1}. {start:g}초 ~ {end:g}초"`에서 번호 부분(`{index + 1}. `)을 떼고 `f"{start:g}초 ~ {end:g}초"`만 남긴다 — `index`는 삭제 버튼의 `key`를 만드는 데는 계속 쓰이므로 `enumerate`는 그대로 유지한다(화면에 보이는 문자열에서만 번호를 뺀다).
    - 삭제 버튼 동작, `session_state` 갱신, `st.rerun()` 흐름은 전혀 바꾸지 않는다.

### 리비전 15 — 자동평가 실패 메시지 변경 + 빈 구간 안내 문구 복원

38. **`pages/4_성능_평가.py` — 자동 평가 실패 메시지 문구 변경**:
    ```python
    st.error("자동 평가 실행 실패. 구간 저장을 먼저 해주세요.")
    ```
    기존 `st.error("자동 평가 실행에 실패했습니다.")`를 위 문구로 교체한다. 이 분기는 `subprocess`의 종료 코드가 0이 아닐 때 전부 타는 공통 실패 분기다 — "정답지 미저장"이 가장 흔한 실패 원인이라 이 문구로 바꾸는 것이고, 다른 원인(예: 영상 파일 손상)으로 실패해도 같은 문구가 뜬다는 점은 감수한다(상세 원인은 바로 아래 "오류 로그 보기"에서 여전히 확인 가능하므로 사용자에게 확인됨).
39. **`pages/4_성능_평가.py` — "위험 구간 없음"일 때 안내 문구 추가 복원**:
    ```python
    else:
        st.write("위험 구간 없음")
        st.caption("입력된 위험 구간이 없습니다. 이 상태로 저장하면 정상 영상으로 기록됩니다.")
    ```
    리비전 14 이전 코드에 있던 원문 그대로를 `st.caption`으로 "위험 구간 없음" 바로 아래에 추가한다(완전히 되돌리는 게 아니라 "위험 구간 없음" 한 줄은 유지하고, 그 보조 설명을 다시 붙이는 것).

### 리비전 16 — "위험 구간 없음" 제거 + 안내 문구를 info 박스로

40. **`pages/4_성능_평가.py`의 빈 구간 분기를 다음으로 교체**:
    ```python
    else:
        st.info("입력된 위험 구간이 없습니다. 이 상태로 저장하면 정상 영상으로 기록됩니다.")
    ```
    - `st.write("위험 구간 없음")` 줄을 삭제한다.
    - `st.caption(...)`을 `st.info(...)`로 바꾼다(문구 내용은 그대로, 표시 스타일만 회색 캡션 → 파란 배경 정보 박스).
    - `"#### 입력된 위험 구간"` 헤딩은 계속 항상 보이게 유지한다(리비전 14에서 정한 것 — 이번 요청은 그 아래 내용만 바꾸는 것).

## 4. 수용 기준

- [ ] 성능평가 페이지에 "🎯 위험 발생 구간 입력" 섹션이 보이고, `data/` 영상 목록이 선택 가능하다.
- [ ] 영상을 선택하면 화면에서 재생된다.
- [ ] 이미 `eval_ground_truth.json`에 구간이 있는 영상을 선택하면 그 구간들이 불러와져 표시된다.
- [ ] 구간을 추가/삭제할 수 있고, 종료초가 시작초보다 작거나 같으면 에러가 뜨고 추가되지 않는다.
- [ ] "저장"을 누르면 `data/eval_ground_truth.json`에 해당 영상의 `danger_intervals`가 저장된다.
- [ ] 한 영상을 저장해도 **다른 영상의 기존 항목이 지워지지 않는다**(병합 저장 확인).
- [ ] 구간 없이(빈 목록으로) 저장하면 `danger_intervals: []`로 저장되고, `tools/auto_eval.py --dry-run`으로 그 영상을 돌리면 TN(또는 FP, 알람이 있다면)으로 정상 분류된다.
- [ ] `tools/auto_eval.py --list-unlabeled`, `tools/auto_eval.py --dry-run`을 기존 라벨된 영상에 대해 실행한 결과가 이번 리팩터링 전후로 동일하다(회귀 없음 확인).
- [ ] 성능평가 페이지 로딩 시 `cv2`/`numpy`/`core.detector`(YOLO 모델 로딩 경로)가 import되지 않는다 — `core/ground_truth.py`는 순수 파이썬만 사용한다(페이지 속도 저하 방지, `grep`으로 import 확인).
- [ ] 기존 "📈 종합 성능 지표", "➕ 평가 기록 추가", "📋 평가 기록 목록", "삭제" 기능은 동작이 전혀 바뀌지 않는다.
- [ ] **(리비전 2)** HEVC로 인코딩된 `data/` 영상(예: `(1)휴대폰 시나리오-카메라.mp4`)을 선택하면 변환을 거쳐 실제로 화면에 영상이 보인다(진행바만 뜨는 현상 재발 없음).
- [ ] **(리비전 2)** `pages/3_이벤트_다시보기.py`의 이벤트 클립 재생(🎬 클립 재생 탭)이 리팩터링 전후로 동일하게 동작한다(회귀 없음) — `get_playable_video` 호출부가 `CONVERTED_DIR`과 30초 타임아웃을 그대로 넘기는지 코드로 확인.
- [ ] **(리비전 2)** 변환 실패(ffmpeg 오류 등) 시 페이지가 크래시하지 않고 에러 메시지만 표시된다.
- [x] **(리비전 2, 사용자 확인 완료)** HEVC 영상을 선택하면 실제로 화면에 영상이 보인다 — 사용자 실기 테스트: "우와 영상 잘보여".
- [x] **(리비전 3, 사용자 확인 — 기능은 정상 동작했으나 리비전 4에서 UI 대체됨)** 보조 슬라이더로 미리보기, 버튼으로 입력란 채우기, 수기 입력 공존, 길이 조회 실패 시 대체, 영상 전환 시 초기화, 기존 저장 로직 무변경 — 전부 실기 확인됨. 단 사용자가 "네이티브 진행바 자체"를 원해 아래 리비전 4로 UI를 대체한다(보조 슬라이더/`st.video` 제거).
- [x] **(리비전 4, 폐기 — 실기 테스트로 플랫폼 결함 확인됨, 아래 리비전 5로 대체)** 영상 플레이어 재생/탐색, onSeek 전달, static 서빙 — 사용자 실기 확인 결과 재생 자체가 안 됨(Streamlit 서브페이지 커스텀 컴포넌트 플랫폼 결함). 리비전 5에서 전부 되돌림.
- [ ] **(리비전 5)** 화면에 "영상 재생 화면 → 보조 탐색 슬라이더 → 시작초로/종료초로 버튼" 순서로 배치된다.
- [ ] **(리비전 5)** 보조 슬라이더를 움직이면(놓으면) 영상이 그 위치로 미리보기(탐색)된다(리비전 3과 동일 동작, 배치 순서만 다름).
- [ ] **(리비전 5)** "⏮ 이 위치를 시작초로"/"⏭ 이 위치를 종료초로" 버튼을 누르면 슬라이더의 현재 값이 입력란에 채워진다.
- [x] **(리비전 5, 사용자 확인 완료)** 기존 수기 입력(number_input)은 그대로 동작한다.
- [x] **(리비전 5, 사용자 확인 완료)** `streamlit-player`, `media_file_mgr`, `static/ground_truth_videos/`, `enableStaticServing` 관련 코드/설정이 전부 제거됐다(`rg`로 확인, Claude가 직접 재확인함).
- [x] **(리비전 5, 사용자 확인 완료)** `requirements.txt`에 `streamlit-player`가 더 이상 없다.
- [x] **(리비전 5, 사용자 확인 완료)** 변환 캐시가 다시 `data/_converted/`에 생성된다.
- [x] **(리비전 5, 사용자 확인 완료)** 영상을 바꾸면 슬라이더 위치가 0으로 초기화된다.
- [x] **(리비전 5, 사용자 확인 완료)** 변환 실패 시 크래시 없이 에러 메시지만 표시된다.
- [x] **(리비전 5, 사용자 확인 완료)** 기존 저장/삭제/병합 저장 동작은 변경 없음.
- [x] **(리비전 5, 사용자 확인 완료)** `pages/3_이벤트_다시보기.py`의 기존 `st.video(bytes)` 재생은 변경 없음.
- [x] **(리비전 5, 사이드바 버그, 사용자 확인 완료)** 사이드바를 접었다가, 다시 펼치는 버튼(`stExpandSidebarButton`)이 보이고 클릭하면 사이드바가 다시 열린다 — "모두 잘 반영됨".
- [x] **(리비전 5, 사이드바 버그, 사용자 확인 완료)** 사이드바가 펼쳐진 상태의 기존 레이아웃/스타일(로고, 네비게이션 링크 디자인 등)은 그대로 유지된다(회귀 없음).
- [x] **(리비전 6, 수정됨 — 리비전 7 참고)** ~~탐색 슬라이더 라벨 옆에 "?" 도움말 아이콘, 호버 시 문구 표시~~ — 사용자가 호버 방식이 아닌 항상 보이는 텍스트를 원해 리비전 7로 교체.
- [x] **(리비전 6, 사용자 확인 완료: "버튼 색상 마음에 들어")** 사이드바가 **펼쳐진 상태**에서 접기 버튼 아이콘이 `#4CAF50`(로고 초록색)로 선명하게 보인다(어두운 배경에 묻히지 않음).
- [x] **(리비전 6, 사용자 확인 완료)** 사이드바가 **접힌 상태**에서 재열기 버튼 아이콘도 동일하게 `#4CAF50`로 보인다.
- [x] **(리비전 6, 사용자 확인 완료)** 색상 규칙이 중복/충돌 없이 하나로 정리됐다(기존 `#CBD5E1` 규칙이 남아 있지 않음).
- [ ] **(리비전 7)** 탐색 슬라이더의 라벨을 보면 마우스 조작 없이 바로 "시작초/종료초를 입력할 위치를 드래그 하거나 클릭하세요" 설명이 함께 보인다.
- [x] **(리비전 7, 사용자 확인 완료)** `help=` 파라미터("?" 호버 아이콘)가 더 이상 없다(중복 표시 방지).
- [x] **(리비전 7, 사용자 확인 완료: "설명 잘 보이고 기능들도 정상")** 슬라이더의 나머지 동작(탐색/버튼 채우기/영상 전환 시 초기화)은 변경 없음.
- [ ] **(리비전 8)** "구간 추가"/"저장" 두 버튼이 "구간 저장" 버튼 하나로 합쳐져 있다.
- [ ] **(리비전 8)** 유효한 시작/종료초(종료 > 시작)가 입력된 상태에서 "구간 저장"을 누르면, 그 구간이 목록에 추가되고 즉시 파일에 저장된다(별도로 "저장"을 또 누를 필요 없음).
- [ ] **(리비전 8)** 시작/종료초가 기본값(둘 다 0)인 채로 "구간 저장"을 누르면, 에러 없이 현재 목록(삭제 반영 포함)이 그대로 저장된다.
- [x] **(리비전 8, 사용자 확인 완료: "기능들 모두 정상")** "🧮 자동 평가 실행" 버튼이 보인다(라벨은 이후 "지금" 제거 요청으로 추가 수정됨).
- [x] **(리비전 8, 사용자 확인 완료)** 그 버튼을 누르면 `tools/auto_eval.py --video <선택된 영상>`이 별도 프로세스(subprocess)로 실행되고, 페이지 자체는 `cv2`/`numpy`/`torch`를 import하지 않는다.
- [x] **(리비전 8, 사용자 확인 완료)** 실행 성공 시 "📋 평가 기록 목록에 반영됨"이라는 문구가 포함된 성공 메시지가 뜬다.
- [x] **(리비전 8, 사용자 확인 완료)** 실행 실패 시 크래시 없이 에러 메시지와 로그가 표시된다.
- [x] **(리비전 8, 사용자 확인 완료)** 정답지가 비어 있는 영상에 대해 실행해도 페이지가 죽지 않는다.
- [x] **(리비전 8, 사용자 확인 완료)** 기존 구간 삭제, 영상 선택/재생, 보조 슬라이더 탐색 동작은 변경 없음.
- [x] **(리비전 9, 사용자 확인 완료)** ROI가 없는 영상을 선택하면, 영상 선택과 영상 재생 사이에 "ROI가 없습니다 — ROI 설정 페이지에서 먼저 저장하세요" 경고가 바로 보인다.
- [x] **(리비전 9, 사용자 확인 완료)** ROI가 있는 영상을 선택하면 그 경고가 보이지 않는다(오탐지 없음).
- [x] **(리비전 9, 사용자 확인 완료)** 응답시간이 정확히 0초인 자동평가 TP 기록이 "0.00"으로 표시된다(더 이상 빈칸 아님).
- [x] **(리비전 9, 사용자 확인 완료)** 그 0초 기록이 "평균 응답시간" 계산에 포함된다.
- [x] **(리비전 9, 사용자 확인 완료)** 자동평가 FP/FN/TN 기록의 응답시간 칸은 기존처럼 비어 있다(응답시간 개념이 없는 분류이므로 — 회귀 아님, 의도된 동작).
- [x] **(리비전 9, 사용자 확인 완료)** "평가 기록 목록"의 "기록 시각" 컬럼이 "YYYY-MM-DD HH:MM" 형식(분 단위)으로 보인다.
- [x] **(리비전 9, 사용자 확인 완료)** 저장된 CSV 원본의 타임스탬프는 초 단위 그대로 유지된다(화면 표시만 변경, 데이터는 무변경).
- [x] **(리비전 9, 사용자 확인 완료)** 평가 기록 목록에 체크박스 컬럼이 있고, 여러 행을 동시에 선택할 수 있다.
- [x] **(리비전 9, 사용자 확인 완료)** 목록 영역 상단 오른쪽에 별도의 "삭제" 버튼이 있다.
- [x] **(리비전 9, 사용자 확인 완료)** 아무것도 선택하지 않고 "삭제"를 누르면 에러 없이 안내만 뜨고 아무것도 지워지지 않는다.
- [x] **(리비전 9, 사용자 확인 완료)** 하나 이상 선택 후 "삭제"를 누르면 확인 질문과 "삭제"/"취소" 버튼이 뜬다 — "취소"를 누르면 아무것도 지워지지 않는다.
- [x] **(리비전 9, 사용자 확인 완료)** 확인 단계에서 "삭제"를 누르면 선택한 행들이 모두 지워지고, 선택하지 않은 다른 행은 그대로 남는다.
- [x] **(리비전 9, 사용자 확인 완료)** "➕ 평가 기록 추가" 제목이 "➕ 평가기록 수동 추가"로 바뀌어 있다.
- [x] **(리비전 9, 사용자 확인 완료)** 페이지에 처음 들어왔을 때 수동 추가 입력 폼이 보이지 않고, 토글을 켜야 폼이 나타난다.
- [x] **(리비전 9, 사용자 확인 완료)** 토글을 켜고 기존처럼 시나리오명/영상소스/분류/응답시간/비고를 입력해 "기록 추가"를 누르면 정상적으로 기록이 추가된다(기존 수동 추가 기능 자체는 변경 없음).
- [x] **(리비전 9, 사용자 확인 완료)** 위험 발생 구간 입력 섹션(영상 재생/슬라이더/구간 저장/자동 평가 버튼)은 이번 리비전에서 변경되지 않는다(회귀 없음).
- [x] **(리비전 10, 사용자 확인 완료)** 삭제 버튼이 체크박스 열(테이블 맨 왼쪽) 위쪽에 보인다(기존처럼 오른쪽이 아님).
- [x] **(리비전 10, 사용자 확인 완료)** 하나 이상 선택 후 "삭제"를 누르면 **진짜 모달 팝업**(화면 중앙에 떠서 배경이 흐려지거나 어두워지는 형태)으로 확인 질문이 뜬다 — 기존처럼 목록 아래에 인라인으로 뜨지 않는다.
- [x] **(리비전 10, 사용자 확인 완료)** 팝업에서 "삭제"를 누르면 선택한 행이 지워지고 팝업이 닫힌다. "취소"를 누르면 아무것도 안 지워지고 팝업이 닫힌다.
- [x] **(리비전 10, 사용자 확인 완료)** 아무것도 선택하지 않고 "삭제"를 누르면 (모달 없이) 안내 문구만 뜬다 — 기존 동작 유지.
- [x] **(리비전 10, 사용자 확인 완료)** "📈 종합 성능 지표"가 가로 5칸이 아니라 세로로 하나씩 나열된다.
- [x] **(리비전 10, 사용자 확인 완료)** 정탐률/오탐률/미탐률 지표에 각각 대응하는 분류(정탐/오탐/미탐)의 건수가 함께 보인다.
- [x] **(리비전 10, 사용자 확인 완료)** 정상(TN) 건수와 총 측정 건수도 어떤 형태로든 화면에 보인다(사라지지 않음).
- [x] **(리비전 10, 사용자 확인 완료)** 별도의 "🧮 카테고리별 건수" 블록은 더 이상 없다.
- [x] **(리비전 10, 사용자 확인 완료)** "➕ 평가기록 수동 추가" 섹션은 계속 정상 동작한다(토글, 폼 제출 등 — 리비전 9 기능 회귀 없음).
- [x] **(리비전 10, 사용자 확인 완료)** 평가 기록 목록(체크박스 선택 포함)과 위험 발생 구간 입력 섹션은 이번 리비전에서 로직이 바뀌지 않는다(레이아웃/표시 방식 변경 외 회귀 없음).
- [x] **(리비전 11, 사용자 확인 완료)** "📈 종합 성능 지표" 7개가 세로 나열이 아니라 한 줄에 나란히(가로) 보인다.
- [x] **(리비전 11, 사용자 확인 완료)** 정탐률/오탐률/미탐률에 딸린 건수(`delta`)가 가로 배치에서도 그대로 보인다(내용 손실 없음).
- [x] **(리비전 11, 사용자 확인 완료)** 정상(TN)·총 측정 건수·정밀도·평균 응답시간도 계속 보인다.
- [x] **(리비전 11, 사용자 확인 완료)** "🧮 카테고리별 건수" 블록이 다시 생기지 않는다(리비전 10에서 없앤 것 유지).
- [x] **(리비전 11, 사용자 확인 완료)** 평가 기록 목록, 위험 발생 구간 입력 섹션 등 다른 부분은 변경되지 않는다.
- [x] **(리비전 12, 사용자 확인 완료)** 페이지 맨 위부터 순서대로 "📈 종합 성능 지표" → "📋 평가 기록 목록" → "🎯 성능 자동평가 - 위험 발생 구간 입력" → "➕ 평가기록 수동 추가"가 보인다.
- [x] **(리비전 12, 사용자 확인 완료)** "위험 발생 구간 입력" 섹션의 제목이 정확히 "🎯 성능 자동평가 - 위험 발생 구간 입력"으로 바뀌어 있다.
- [x] **(리비전 12, 사용자 확인 완료)** 순서가 바뀌어도 각 섹션의 기능(지표 표시, 기록 목록 체크박스/삭제 팝업, 영상재생/슬라이더/구간저장/자동평가 실행, 수동 추가 토글/폼)은 전부 그대로 동작한다(회귀 없음).
- [x] **(리비전 12, 사용자 확인 완료)** 가로로 나열된 지표 7개의 카드 높이가 전부 같다(delta 유무와 무관하게).
- [x] **(리비전 12, 사용자 확인 완료)** 지표 카드 안의 내용(라벨/값/delta/도움말 아이콘)은 리비전 11과 동일하다 — 높이만 통일되고 내용은 변경되지 않는다.
- [x] **(리비전 13, 사용자 확인 완료)** "평가 기록 목록" 테이블에 고정 높이가 적용돼, 전체 화면을 다 차지하지 않고 일정 높이 안에서만 보인다.
- [x] **(리비전 13, 사용자 확인 완료)** 기록이 7건보다 많을 때, 테이블 내부에서 마우스 휠/드래그로 스크롤해서 나머지 기록을 볼 수 있다.
- [x] **(리비전 13, 사용자 확인 완료)** 기록이 7건 이하일 때는 스크롤 없이 정상적으로 전부 보인다(크래시나 빈 공간 과다 등 이상 없음).
- [x] **(리비전 13, 사용자 확인 완료)** 체크박스 선택, 삭제 버튼, 삭제 확인 팝업 등 기존 기능은 높이 제한과 무관하게 그대로 동작한다.
- [x] **(리비전 13, 사용자 확인 완료)** 다른 섹션(종합 지표, 성능 자동평가 섹션, 수동 추가)은 이번 리비전에서 변경되지 않는다.
- [x] **(리비전 14, 사용자 확인 완료)** 구간을 하나도 추가하지 않고 "구간 저장"을 눌러도, "입력된 위험 구간" 영역 자체는 화면에 보인다(사라지지 않음).
- [x] **(리비전 14, 사용자 확인 완료)** 구간이 비어 있을 때 그 영역에 "위험 구간 없음"이라는 문구가 보인다(기존의 긴 안내 문구나 "0초~0초" 같은 값이 아님).
- [x] **(리비전 14, 사용자 확인 완료)** 구간이 하나 이상 있을 때는 각 줄이 "N초 ~ M초" 형식으로 보이고, 앞에 "1." 같은 번호가 없다.
- [x] **(리비전 14, 사용자 확인 완료)** 구간별 "삭제" 버튼은 번호가 빠져도 정상적으로 그 줄만 삭제한다(동작 회귀 없음).
- [x] **(리비전 14, 사용자 확인 완료)** 영상 재생, 슬라이더, 구간 저장, 자동 평가 실행 등 다른 기능은 변경되지 않는다.
- [x] **(리비전 15, 사용자 확인 완료)** 정답지를 저장하지 않은 영상에서 "자동 평가 실행"을 누르면, 에러 메시지가 정확히 "자동 평가 실행 실패. 구간 저장을 먼저 해주세요."로 보인다.
- [x] **(리비전 15, 사용자 확인 완료)** "오류 로그 보기" 확장 영역의 실제 에러 내용은 그대로 유지된다(상세 원인 확인 경로는 안 없어짐).
- [x] **(리비전 15, 사용자 확인 완료 — "위험 구간 없음" 문구는 리비전 16에서 다시 제거)** 구간이 비어 있을 때 "위험 구간 없음"과 함께 안내 문구가 둘 다 보인다.
- [x] **(리비전 15, 사용자 확인 완료)** 구간이 하나 이상 있을 때는 그 안내 문구가 보이지 않는다(빈 상태에서만 표시).
- [x] **(리비전 15, 사용자 확인 완료)** 자동 평가 성공 메시지("📋 평가 기록 목록에 반영됨" 포함)는 변경되지 않는다.
- [ ] **(리비전 16)** 구간이 비어 있을 때 "위험 구간 없음"이라는 한 줄 텍스트는 더 이상 보이지 않는다.
- [ ] **(리비전 16)** 구간이 비어 있을 때 안내 문구가 회색 캡션이 아니라 파란 배경 정보 박스(`st.info` 스타일)로 보인다.
- [ ] **(리비전 16)** 안내 문구의 내용 자체는 바뀌지 않는다("입력된 위험 구간이 없습니다. 이 상태로 저장하면 정상 영상으로 기록됩니다.").
- [ ] **(리비전 16)** 구간이 하나 이상 있을 때는 정상적으로 그 목록이 보인다(빈 상태 분기와 무관하게 회귀 없음).
- [ ] **(리비전 16)** "#### 입력된 위험 구간" 헤딩은 구간 유무와 무관하게 계속 보인다.

## 5. 예상 변경 파일

- `core/ground_truth.py` (신규)
- `tools/auto_eval.py` (정답지 로드 함수를 `core/ground_truth.py`로 이전 — 나머지 로직 무변경)
- `pages/4_성능_평가.py` (새 섹션 추가)
- `docs/tasks/current.md`
- `roi_configs/18초까지_정면_갑툭튀_야간_2.json`, `roi_configs/GTA__비__주간__2.json`, `roi_configs/같은_장소_비_2_야간.json`, `roi_configs/눈_배회.json`, `roi_configs/전체_측면_배회_야간_1.json` (이번 작업과 무관하게 이전부터 존재하던 사용자 테스트 데이터 — 그대로 둠, 무변경)
- `core/video_playback.py` (신규, 리비전 2 — 리비전 4에서 `get_video_duration_seconds` 제거 가능)
- `pages/3_이벤트_다시보기.py` (리비전 2 — `get_playable_video` 추출만, 동작 무변경)
- `requirements.txt` (리비전 4에서 추가한 `streamlit-player` — 리비전 5에서 제거)
- `.streamlit/config.toml` (리비전 4에서 추가한 `enableStaticServing` — 리비전 5에서 제거)
- `.gitignore` (리비전 4에서 추가한 `static/ground_truth_videos/` — 리비전 5에서 제거)
- `app.py` (리비전 5 — 사이드바 재열기 버튼 CSS 수정)
- `data/eval_ground_truth.json` (이번 작업과 무관 — 사용자가 실제로 영상 2개를 라벨링해 저장한 데이터. 계속 바뀔 수 있음 — Codex가 건드리지 않는다)
- `core/performance_eval.py` (리비전 9 — 응답시간 falsy-zero 버그 수정)

## 6. 파일 소유권

| 파일 | 소유자 | 상태 |
|---|---|---|
| `core/ground_truth.py` | Codex (구현/테스트) | 착수 가능 |
| `tools/auto_eval.py` | Codex (구현/테스트, 리팩터링만) | 착수 가능 |
| `pages/4_성능_평가.py` | Codex (구현/테스트, 리비전 5에서 리비전 3 방식으로 복원+재배치) | 착수 가능 |
| `core/video_playback.py` | Codex (구현/테스트, 리비전 2·3 유지) | 착수 가능 |
| `pages/3_이벤트_다시보기.py` | Codex (구현/테스트, 리비전 2 — 추출만) | 착수 가능 |
| `requirements.txt` | Codex (리비전 5 — streamlit-player 제거) | 착수 가능 |
| `.streamlit/config.toml` | Codex (리비전 5 — enableStaticServing 제거) | 착수 가능 |
| `.gitignore` | Codex (리비전 5 — static 줄 제거) | 착수 가능 |
| `app.py` | Codex (리비전 5 — 사이드바 CSS 수정) | 착수 가능 |
| `core/performance_eval.py` | Codex (리비전 9 — 응답시간 버그 수정) | 착수 가능 |
| `docs/tasks/current.md` | Claude (계획/리뷰) | 계획 작성 완료 |

## 7. 위험 요소 또는 주의사항

- **`tools/auto_eval.py` 회귀 위험**: 이미 `verified`로 끝난 작업의 파일을 다시 건드린다. 정답지 로드 함수를 옮기기만 하고 알람 감지·분류·CSV 기록 로직은 손대지 않아야 한다. 구현 후 기존 수용 기준(`--list-unlabeled`, `--dry-run` 정상 동작, 동일 영상 재실행 시 중복 기록 없음)을 다시 확인할 것.
- **무거운 라이브러리 import 금지**: `core/ground_truth.py`는 `cv2`/`numpy`/`torch`/`core.detector`를 절대 import하지 않는다. 성능평가 페이지가 이 섹션 때문에 느려지면 안 된다(사용자가 명시적으로 우려했던 부분).
- **병합 저장 필수**: "저장" 시 JSON 전체를 덮어쓰지 말고, 반드시 기존 파일을 읽어 다른 영상 항목을 보존한 뒤 대상 영상 항목만 교체해서 써야 한다 — 팀이 공유하는 파일이라 실수로 다른 사람이 입력한 정답지를 날리면 안 된다.
- **위젯 위치 안정성**: 새 섹션은 항상 렌더링되는 최상위 블록에 둔다(조건부로 나타나거나 사라지는 블록 끝에 두지 않음) — 과거 스트림릿에서 "구조적으로 불안정한 위치의 위젯이 cross-run 재조정 실패를 일으킨" 사례가 있었다.
- **영상 재생 성능**: `st.video()`로 큰 영상을 재생하면 로딩이 느릴 수 있으나, 이는 모니터링 페이지의 실시간 추론 성능과는 무관한 별도 페이지이므로 허용되는 트레이드오프다(사용자 승인 불필요, 이미 목표에 반영됨).
- 헤드리스 브라우저(Chrome/Playwright/Selenium)로 실제 재생·클릭 검증을 시도하지 말 것(영구 금지 사항) — 코드 읽기, `st.session_state` 흐름 분석, `python -m py_compile`, `tools/auto_eval.py` CLI 재실행으로 검증한다.
- **(리비전 2) `pages/3_이벤트_다시보기.py` 회귀 위험**: 이미 동작 중인 이벤트 재생 기능의 함수를 옮기는 것이므로, 동작이 1바이트도 달라지면 안 된다. `CONVERTED_DIR`/타임아웃 값을 그대로 넘기는지, import 외에 호출부 로직을 바꾸지 않았는지 `git diff`로 확인할 것.
- **(리비전 2) 변환 캐시 용량**: `data/_converted/`에 변환본이 쌓인다. `saved_events/_converted/`처럼 `data/*` gitignore 규칙에 이미 포함되므로 git에는 안 올라가지만, 로컬 디스크 용량은 쓴다 — 이번 작업 범위에서 자동 정리 기능을 추가하지 않는다(필요하면 사용자가 직접 폴더를 비우면 됨).
- **(리비전 2) 변환 시간**: `data/`의 라벨링용 영상은 이벤트 클립보다 길 수 있어 타임아웃을 120초로 늘렸다. 그래도 아주 긴 영상은 시간이 걸릴 수 있으므로 변환 중 `st.spinner`로 로딩 중임을 알린다.
- **(리비전 3) 슬라이더 과다 rerun 우려 없음**: 스트림릿 슬라이더는 드래그 중이 아니라 "놓았을 때" 1회만 서버에 값을 전송한다 — 과도한 재실행 걱정 없음.
- **(리비전 3) duration 파싱 실패 대비**: ffmpeg 출력 형식이 예상과 다르거나 영상이 손상된 경우 정규식이 매치하지 않을 수 있다 — 반드시 `None`을 반환하고 기본값으로 대체하도록 구현할 것(예외로 페이지가 죽으면 안 됨).
- **(리비전 3) 위젯 session_state 갱신 패턴 재사용**: 버튼 클릭 → `st.session_state[key] = 값` → `st.rerun()` 패턴은 이미 이 섹션의 구간 추가/삭제에서 쓰고 있는 검증된 패턴이다. 새 트릭을 만들지 말고 그대로 재사용할 것.
- 헤드리스 브라우저 검증 금지는 리비전 3에도 동일하게 적용된다 — 실제 슬라이더 드래그/버튼 클릭 확인은 사용자가 직접 한다.
- **(리비전 4) 새 의존성**: `streamlit-player`를 처음 추가하는 것이므로, `pip install` 후 실제 설치된 버전으로 `requirements.txt`를 갱신할 것(추측 버전 금지). 가상환경이 깨지지 않는지 `python -m py_compile` 및 기존 페이지 임포트 확인.
- **(리비전 4) 정적 서빙 URL 규칙은 추측하지 말고 코드로 확인**: Streamlit 버전별로 정적 서빙 URL 프리픽스가 다를 수 있다. 설치된 `streamlit==1.55.0` 기준으로 실제 파일을 `static/ground_truth_videos/`에 두고, 그 URL로 직접 HTTP 요청(`requests.get` 등, 서버가 켜진 상태에서)을 보내 200이 오는지 확인한 뒤 코드에 반영할 것 — 이건 브라우저 자동화가 아니라 단순 HTTP 호출이라 금지 규칙에 해당하지 않는다.
- **(리비전 4) `static/` 디렉터리 git 추적**: `static/ground_truth_videos/`는 변환 캐시이므로 `.gitignore`에 추가해 추적 제외한다. `static/` 전체를 통째로 제외하면 안 되는 특별한 이유가 생기지 않는 한, `static/ground_truth_videos/`만 명시적으로 제외한다(향후 다른 정적 자원을 `static/`에 둘 가능성을 막지 않기 위해).
- **(리비전 4) 이벤트 다시보기(`pages/3`) 영향 없음 확인**: 이 리비전은 `pages/4`에만 영향을 준다 — `pages/3`이 여전히 `st.video(bytes)`를 쓰고 정적 서빙과 무관하게 동작하는지 `git diff`로 확인할 것.
- **(리비전 4) `st_player`의 `url` 파라미터에 로컬 파일 경로를 그대로 넣지 말 것** — 반드시 정적 서빙 URL(예: `app/static/ground_truth_videos/<파일명>`, 또는 리더 슬래시 포함 형태 중 실제로 동작을 확인한 쪽)을 넣어야 한다.
- 헤드리스 브라우저 금지는 리비전 4에도 동일 — "네이티브 진행바를 드래그해서 실제로 onSeek가 동작하는지"는 사용자 실기 확인이 필요하다.
- **(리비전 5) 되돌리기 완전성 확인**: `streamlit-player`/`media_file_mgr` 관련 코드를 "일부만" 지우고 흔적이 남으면(예: 안 쓰는 import, 죽은 `static/` 참조) 나중에 혼란을 준다. `rg -i "streamlit_player|streamlit-player|media_file_mgr|enableStaticServing|ground_truth_videos"`로 전체 저장소를 검색해 전부 제거됐는지 확인할 것.
- **(리비전 5) 레이아웃 순서 재현**: "화면상 보이는 순서"가 영상→슬라이더→버튼이면 되는 것이지, 반드시 코드 작성 순서가 그래야 하는 건 아니다(슬라이더 값을 영상의 `start_time`에 쓰려면 슬라이더를 먼저 "읽어야" 하는 경우가 있을 수 있음) — 혼동하지 말 것. 최종 목표는 "사용자가 화면에서 보는 순서"다.
- **(리비전 5) 사이드바 CSS 수정 범위**: `header[data-testid="stHeader"]`를 다시 `display:block`으로 되돌리면서 `visibility:hidden`으로 숨기는 전략이 기존에 그 헤더를 숨겨서 얻었던 다른 효과(예: 레이아웃 상단 여백)에 영향을 주지 않는지 확인할 것 — `position:fixed`로 문서 흐름에서 분리했으므로 `.block-container`의 `padding-top` 등 기존 값은 그대로 둬도 될 것으로 예상되나, 실제 화면에서 상단 여백이 이상해지면 보고할 것.
- 헤드리스 브라우저 금지는 리비전 5에도 동일 — 사이드바 버튼이 실제로 클릭되는지, 슬라이더가 실제로 영상을 탐색하는지는 사용자 실기 확인이 필요하다.
- **(리비전 6) 인라인 스타일 우선순위 함정 재발 방지**: 이번 버그의 원인이 "조상 엘리먼트에만 `color`를 줘서 자손의 인라인 `color`를 못 이긴 것"이었다. 같은 실수를 반복하지 않도록, 아이콘 색을 바꿀 때는 항상 `버튼 *` 형태로 자손까지 명시적으로 타깃할 것 — 이 패턴은 앞으로 Streamlit 내부 아이콘(Material 아이콘 등) 색상을 바꿀 때마다 재사용할 수 있다.
- **(리비전 6) 중복 규칙 정리**: 기존 `#CBD5E1` 규칙을 지우지 않고 새 `#4CAF50` 규칙만 추가하면, CSS 명시도(specificity)가 같을 경우 "나중에 선언된 규칙이 이긴다"는 규칙에 의존하게 되어 나중에 순서가 바뀌면 또 깨질 수 있다 — 반드시 기존 규칙을 지우거나 교체할 것.
- **(리비전 6) `help` 파라미터는 기존 수용 기준에 영향 없음**: 슬라이더에 `help`를 추가하는 것은 `key`/`value`/`min_value`/`max_value`/`step` 등 기존 동작에 영향을 주지 않는 추가 파라미터다 — 다른 로직을 함께 건드리지 말 것.
- 헤드리스 브라우저 금지는 리비전 6에도 동일 — 실제 색상이 어떻게 보이는지, 도움말 아이콘이 잘 뜨는지는 사용자 실기 확인이 필요하다(단 CSS 선택자가 코드상 올바른지는 Claude가 리뷰에서 확인).
- **(리비전 8) subprocess가 heavy-import 원칙을 어기지 않는지 확인 필수**: `subprocess.run([sys.executable, "tools/auto_eval.py", ...])`는 **새 프로세스**를 띄우는 것이라, 그 프로세스 안에서 `cv2`/`torch`가 로딩되는 것과 `pages/4_성능_평가.py` 자체(= 현재 떠 있는 Streamlit 프로세스)가 그것들을 import하는 것은 다르다. `tools/auto_eval.py`를 **`import`로 가져오지 말고 반드시 `subprocess`로만** 실행할 것 — import하면 기존에 지킨 "페이지는 가볍게" 원칙이 깨진다.
- **(리비전 8) 긴 실행 시간 동안 페이지가 멈춘 것처럼 보일 수 있음**: `subprocess.run()`은 완료까지 기다리는 블로킹 호출이라, 영상이 길면 스트림릿 UI가 그동안 멈춘 것처럼 보인다 — `st.spinner`로 "실행 중" 상태를 반드시 표시해 사용자가 멈췄다고 오해하지 않게 한다. 타임아웃은 걸지 않는다(채점은 끝까지 돌아야 의미가 있음 — 단, 비정상적으로 오래 걸리면 `Ctrl+C`로 서버 자체를 재시작해야 할 수 있다는 점을 알아둘 것).
- **(리비전 8) 버튼 통합 시 "삭제만 하고 아무것도 안 바꾼 채 저장" 케이스를 깨뜨리지 말 것**: 시작/종료초가 기본값(0, 0)이어도 에러 없이 현재 목록을 그대로 저장할 수 있어야 한다 — 이 케이스를 빠뜨리면 구간 삭제 후 저장이 안 되는 회귀가 생긴다.
- **(리비전 8) `cwd` 지정**: `subprocess.run(..., cwd=ROOT)`로 작업 디렉터리를 프로젝트 루트로 고정해야 `tools/auto_eval.py` 내부의 상대 경로(정답지, `data/` 등)가 꼬이지 않는다.
- 헤드리스 브라우저 금지는 리비전 8에도 동일 — 버튼을 실제로 눌러서 자동 평가가 돌아가는지는 사용자 실기 확인이 필요하다. 다만 `python -m py_compile`과 `subprocess` 호출 인자가 코드상 올바른지는 Claude가 리뷰에서 확인한다.
- **(리비전 9) `data_editor`의 id-매핑은 반드시 pandas index로**: 체크박스 선택 결과를 enumerate로 위치 기반 매핑하면, 정렬/필터링 등으로 행 순서가 바뀔 때 엉뚱한 기록이 삭제될 위험이 있다. 반드시 `id`를 DataFrame의 실제 index로 설정(`set_index("id")`)하고 `hide_index=True`로 화면에서만 숨긴 뒤, 반환된 edited DataFrame의 `.index`로 선택된 id를 추적할 것.
- **(리비전 9) 응답시간 수정의 의도된 비대칭**: FP/FN/TN 자동 기록은 수정 후에도 계속 빈칸으로 남는 게 **올바른 동작**이다(응답시간이라는 개념 자체가 그 분류에는 없음) — "모든 기록에 숫자가 채워져야 버그가 고쳐진 것"이라고 오해해 FP/FN/TN에도 억지로 값을 채우지 말 것.
- **(리비전 9) `add_record` 기본값 변경의 파급 범위 확인**: `response_time_sec` 기본값을 `0.0`→`None`으로 바꾸면 이 함수를 호출하는 다른 모든 곳(수동 추가 폼, `tools/auto_eval.py`)이 영향을 받을 수 있다 — `rg "add_record("`로 전체 호출부를 찾아 각각 의도한 값을 명시적으로 넘기고 있는지 확인할 것.
- **(리비전 9) 삭제 확인 세션 상태 키 충돌 주의**: 기존 "위험 발생 구간 입력" 섹션과 "평가 기록" 섹션이 같은 페이지 안에 있으므로, 삭제 대기 상태를 담는 `session_state` 키 이름이 다른 기능의 키(`ground_truth_*`)와 겹치지 않게 한다(예: `eval_delete_pending`처럼 구분되는 접두사 사용).
- **(리비전 9) 토글 상태는 리런 때마다 유지**: `st.toggle`에 `key=`를 지정해 두면 페이지 리런에도 사용자가 연 상태를 유지한다 — 다른 조작(구간 저장, 자동 평가 실행 등) 때문에 리런될 때마다 폼이 저절로 닫히면 안 된다.
- 헤드리스 브라우저 금지는 리비전 9에도 동일 — 체크박스 클릭, 삭제 확인창, 토글 등 실제 화면 동작은 사용자 실기 확인이 필요하다. 로직·조건문이 코드상 올바른지는 Claude가 리뷰에서 확인한다.
- **(리비전 10) `st.dialog` 함수는 모듈 최상위(또는 호출 전)에 정의**: 데코레이터가 붙은 함수는 파일 안 어디에 둬도 동작하지만, 호출 시점(아래쪽 "삭제" 버튼 로직)보다 먼저 정의돼 있어야 한다 — 함수 정의를 호출부 바로 위나 파일 상단 쪽에 둘 것.
- **(리비전 10) 모달 안에서의 `st.rerun()`**: `st.dialog` 문서에 따르면 다이얼로그 안에서 상태를 바꾸고 닫으려면 보통 `st.rerun()`을 호출해야 한다(자동으로 안 닫히는 경우가 있음) — "삭제"/"취소" 클릭 후 반드시 `st.rerun()`을 호출해 모달이 닫히고 목록이 갱신되게 할 것.
- **(리비전 10) `st.metric`의 `delta_color="off"` 필수**: `delta`에 건수를 텍스트로 넣을 때 `delta_color`를 지정하지 않으면 양수/음수로 해석해 초록/빨강 화살표가 붙어 오해를 준다 — 반드시 `delta_color="off"`로 중립 표시할 것.
- **(리비전 10) `count_col` 제거 영향 범위 한정**: `form_col, count_col = st.columns([2, 1])` 구조를 없애는 건 "📈 종합 성능 지표"/"🧮 카테고리별 건수" 영역에만 해당한다 — 그 아래 "📋 평가 기록 목록"이나 "🎯 위험 발생 구간 입력" 섹션의 레이아웃은 건드리지 않는다.
- 헤드리스 브라우저 금지는 리비전 10에도 동일 — 실제 팝업이 뜨는지, 지표가 세로로 잘 보이는지는 사용자 실기 확인이 필요하다. `st.dialog` 데코레이터 사용법과 조건문이 코드상 올바른지는 Claude가 리뷰에서 확인한다.
- **(리비전 12) 블록 이동 중 코드 누락/중복 금지**: 섹션을 옮길 때 `st.markdown("---")` 구분선이나 블록 경계를 잘못 잘라 일부 코드가 중복되거나 누락되지 않도록 주의할 것 — 이동 후 `python -m py_compile`과 각 섹션 헤딩(`###`)이 정확히 4개, 한 번씩만 존재하는지 `rg`로 확인한다.
- **(리비전 12) `records`/`metrics` 변수 정의 위치 유지**: `records = load_records()`, `metrics = compute_metrics(records)`는 "📈 종합 성능 지표"와 "📋 평가 기록 목록" 둘 다에서 쓰인다 — 두 섹션이 종합 지표 바로 다음에 기록 목록이 오도록 순서가 유지되므로 이 계산을 파일 최상단(지표 섹션 시작 전)에 그대로 둔다.
- **(리비전 12) 제목 문자열은 정확히 일치시킬 것**: "🎯 성능 자동평가 - 위험 발생 구간 입력"에서 이모지·공백·하이픈까지 요청된 그대로 쓸 것(임의로 "–"나 "—" 같은 다른 대시 문자로 바꾸지 말 것).
- **(리비전 12) `min-height` 값은 제안값**: 135px는 Claude의 제안이지 확정값이 아니다 — 실제 화면에서 너무 여유롭거나 부족하면 사용자 피드백에 따라 쉽게 조정 가능하다는 점을 구현 결과에 남길 것.
- 헤드리스 브라우저 금지는 리비전 12에도 동일 — 실제 섹션 순서와 카드 높이가 화면에서 어떻게 보이는지는 사용자 실기 확인이 필요하다. 코드상 블록 순서와 CSS 규칙이 올바른지는 Claude가 리뷰에서 확인한다.
- **(리비전 13) "정상(TN) 제거" 요청은 이번 범위 밖**: 사용자가 TN에 대해 질문했고 Claude가 "지우지 말 것"을 추천했지만, 최종 결정은 아직 사용자가 내리지 않았다 — 이번 리비전에서 TN 관련 코드를 임의로 바꾸지 않는다(질문받지 않은 변경을 먼저 하지 말 것).
- **(리비전 13) `height=` 값은 제안값**: 290px는 Claude가 계산으로 제안한 값이지 확정값이 아니다 — 실제로 7행보다 많거나 적게 보이면 사용자 피드백에 따라 조정 가능하다는 점을 구현 결과에 남길 것.
- 헤드리스 브라우저 금지는 리비전 13에도 동일 — 실제로 몇 행이 보이고 스크롤이 매끄러운지는 사용자 실기 확인이 필요하다. `height=` 인자가 코드상 올바르게 들어갔는지는 Claude가 리뷰에서 확인한다.
- **(리비전 14) "정상(TN) 제거"는 여전히 범위 밖**: 이번 리비전도 TN 관련 코드를 건드리지 않는다 — 사용자 결정이 따로 올 때까지 대기.
- **(리비전 16) "구간 저장 없이 자동 평가 성공" 질문은 코드 변경 대상이 아님**: 사용자가 물었던 질문(저장 버튼 없이 자동 평가가 성공한 이유)은 Claude가 기존 정답지 파일(`(3)건물 사각지대(야간).mp4`가 이미 저장돼 있었음)을 확인해 설명으로 해결했다 — 이 리비전에서 관련 코드를 바꾸지 않는다.
- **(리비전 16) info 박스 채택 근거**: `st.info`는 Claude의 추천이고, "위험 구간 없음"이 없어지면 이 문구가 유일한 텍스트가 되므로 더 눈에 띄는 스타일이 적절하다는 이유였다 — 구현 결과에 이 근거를 남길 것.
- 헤드리스 브라우저 금지는 리비전 16에도 동일 — 실제 화면에서 색상/스타일이 어떻게 보이는지는 사용자 실기 확인이 필요하다. 코드 로직이 올바른지는 Claude가 리뷰에서 확인한다.

## 구현 결과
- 실제 변경 파일: `pages/4_성능_평가.py`, `docs/tasks/current.md`
- 계획 대비 변경 요약: 리비전 16 계획대로 빈 구간 분기에서 `st.write("위험 구간 없음")`을 제거하고, 기존 안내 문구를 `st.caption(...)`에서 `st.info(...)`로 변경했다. 문구가 빈 상태의 유일한 설명이므로 더 눈에 띄는 정보 박스를 사용한다는 계획 근거를 그대로 반영했으며, `"#### 입력된 위험 구간"` 헤딩과 구간 목록/삭제/저장/자동평가 로직은 변경하지 않았다.
- 계획 이탈 사항: 없음
- 종료 시점 git 상태 (`git -c core.quotepath=false status --porcelain`; 아래에는 이번 리비전 이전부터 존재하며 계획에 명시된 누적 변경 및 사용자 테스트 데이터도 포함됨):
  ```text
   M .gitignore
   M app.py
   M core/performance_eval.py
   M data/eval_ground_truth.json
   M docs/tasks/current.md
   M pages/3_이벤트_다시보기.py
   M pages/4_성능_평가.py
   M requirements.txt
   M tools/auto_eval.py
  ?? core/ground_truth.py
  ?? core/video_playback.py
  ?? roi_configs/18초까지_정면_갑툭튀_야간_2.json
  ?? roi_configs/GTA__비__주간__2.json
  ?? roi_configs/같은_장소_비_2_야간.json
  ?? roi_configs/눈_배회.json
  ?? roi_configs/전체_측면_배회_야간_1.json
  ```

## 테스트 결과
- 실행 명령/검증:
  - `python -m py_compile "pages/4_성능_평가.py"` — PASS (Python 구문 검사)
  - `rg -n "입력된 위험 구간|위험 구간 없음|st\.info" "pages/4_성능_평가.py"` — PASS (`#### 입력된 위험 구간` 헤딩과 새 `st.info(...)` 확인, 제거 대상 한 줄 텍스트 없음)
  - `git diff --check -- "pages/4_성능_평가.py" docs/tasks/current.md` — PASS (공백 오류 없음; 기존 LF→CRLF 경고만 출력)
- 수용 기준 체크리스트 (리비전 16):
  - [x] PASS — 구간이 비어 있을 때 `"위험 구간 없음"`이라는 한 줄 텍스트는 더 이상 렌더링하지 않는다.
  - [ ] 미실행 — 구간이 비어 있을 때 안내 문구가 파란 배경 정보 박스로 실제 보이는지는 헤드리스 브라우저 검증 금지에 따라 사용자 실기 확인이 필요하다. 코드상 `st.info(...)` 적용은 PASS다.
  - [x] PASS — 안내 문구는 `"입력된 위험 구간이 없습니다. 이 상태로 저장하면 정상 영상으로 기록됩니다."`로 내용 변경 없이 유지했다.
  - [x] PASS — 구간이 하나 이상일 때의 목록 렌더링 분기는 수정하지 않아 기존 목록 표시 흐름을 유지한다.
  - [x] PASS — `"#### 입력된 위험 구간"` 헤딩은 `if intervals:` 바깥에 그대로 있어 구간 유무와 무관하게 렌더링된다.
- 미실행 항목과 사유: `st.info`의 실제 색상/화면 표시 1건은 계획의 헤드리스 브라우저 검증 금지에 따라 미실행했다. 사용자 실기 확인이 필요하다. 리비전 1~15 수용 기준은 이미 기록된 사용자 확인 결과를 유지했으며, 이번 최소 UI 변경에서 재실행하지 않았다.

## 리뷰 및 남은 위험

- 리뷰 결과: approved
- 요약: 리비전 16의 핵심 변경(line 233~234: `st.write("위험 구간 없음")` 제거 + `st.caption` → `st.info` 교체)이 코드상 올바르게 반영됐다. 계획 이탈 없음, 기존 로직 보존, 수용 기준 5 PASS / 1 not_run(사유 명시). UI 파란 박스 실표시는 사용자 실기 확인이 남아 있다.
- scope_ok: True
- 수용 기준 판정:
  - [pass] 구간이 비어 있을 때 '위험 구간 없음' 텍스트를 렌더링하지 않는다 (수용 기준 33)
  - [pass] 안내 문구를 st.info 파란 배경 박스로 표시한다 — 코드상 적용 확인 (수용 기준 34)
  - [not_run] st.info 실제 파란 박스 표시 — 브라우저 실기 확인 필요 (수용 기준 34, UI)
  - [pass] '#### 입력된 위험 구간' 헤딩이 구간 유무와 무관하게 항상 렌더링된다
  - [pass] 구간이 하나 이상일 때 기존 목록 렌더링 분기가 보존된다
  - [pass] 리비전 15 에러 메시지: '자동 평가 실행 실패. 구간 저장을 먼저 해주세요.'
- 남은 위험/후속 작업:
  - st.info() 파란 배경 박스 실제 표시 여부 — 브라우저에서 사용자 실기 확인 필요
  - 리비전 1~16 누적 변경(app.py, core/*, pages/*, tools/*)이 아직 미커밋 상태 — /깃업데이트 또는 PR로 반영 권장
- (Harness가 검증된 Claude 리뷰 JSON을 기계적으로 반영한 결과입니다.)

