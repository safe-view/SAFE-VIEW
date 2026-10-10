# 현재 작업

## 상태

**State:** `verified`
**기준 커밋:** `e3c175707e41148959c5f6a9bfd4582a6b6ce9ef`
**승인 필요:** 아니오 (순수 시각적 변경 — 탐지/판정 로직, 페이지 라우팅 구조, 세션 아키텍처는 전혀 건드리지 않음. 사용자가 목업을 직접 보고 "이 목업대로 디자인 작업 진행하자"로 명시적으로 승인함.)
**최종 갱신:** 사용자가 8차(로고-문구 간격) 수정까지 실제 화면에서 최종 확인해 verified로 종료, 2026-10-10

이 작업은 "UI/UX 디자인 통일 — 1단계(비주얼)"이다. 발표/데모 완성도를 높이기 위해, 지금 페이지마다 스타일이 다르고(대시보드·ROI설정·성능평가는 기본 Streamlit 룩, 모니터링·다시보기만 커스텀 브랜드 컬러) 대시보드 홈에는 "세이프뷰" 브랜딩조차 안 보이는 문제를 해결한다.

**승인된 목업**: https://claude.ai/artifact/5ZtF8GgJC9TR9mxSGLiv7x
- `Main.dc.html` — 모니터링(관리자) 화면: 다크 네이비 사이드바 + 영상 모니터 카드 + 실시간 현황/이벤트/시스템 정보 패널
- `AdminShell.dc.html` — 대시보드 홈: 같은 사이드바 + "세이프뷰" 브랜딩 히어로 + 통계 카드 + 시작하기 스텝 가이드
- `PublicDisplay.dc.html` — 공개 경고 디스플레이 컨셉: 영상 위에 배경 없이 큰 외곽선 텍스트로 경고 문구 표시(이번 1단계는 이 스타일만 기존 모니터링 페이지의 영상 오버레이에 반영하고, "공개 디스플레이 전용 페이지"는 2단계에서 만든다 — 아래 제외 범위 참고)

이번 작업 전, "흔들림 보정 작업"은 GPU 보유 팀원 PC 실측으로 로컬 영상 FPS 저하가 김영민 PC 고유의 저사양 CPU 문제였음이 확정되어 `verified`로 종료했다(`docs/tasks/archive/2026-10-10-shake-compensation-verified.md` 참고). ByteTrack 재검토는 배포 목표 사양이 먼저 확정된 뒤 별도로 판단하기로 보류했다.

## 1. 목표

5개 페이지(대시보드·모니터링·ROI 설정·다시보기·성능 평가)의 색상·폰트·카드 스타일을 통일하고, 대시보드 홈에 "세이프뷰" 브랜딩을 전면에 노출한다. 모니터링 페이지의 영상 위 경고 문구(`draw_text_korean_centered` 호출)는 목업의 "배경 없는 큰 외곽선 텍스트" 스타일로 교체한다.

**핵심 제약 — 위젯·구조 100% 보존(가장 중요):** 이번 작업은 "더 예쁘게"만 하는 것이고 기능과 구조는 작업 전과 완전히 동일해야 한다. 특히 아래는 지금 쓰이는 위젯 종류·배치·동작 순서를 **그대로** 유지하고 색상/폰트/여백/카드 테두리 같은 시각 스타일만 입힌다:
- 영상 소스 선택: `st.radio("소스", ["📁 파일", "📡 RTSP"], horizontal=True, ...)` — 라디오를 토글/탭/드롭다운 등 다른 위젯으로 바꾸지 않는다 (`pages/1_모니터링.py:427`, `pages/2_ROI_설정.py:94`).
- 로컬 영상 파일 선택: `st.selectbox("영상 파일 선택", ...)` + `st.expander("🗑️ 저장된 영상 삭제")` — 그대로 유지 (`pages/1_모니터링.py:452,459`, `pages/2_ROI_설정.py:119,124`).
- RTSP 프리셋: `st.selectbox`로 저장된 카메라 선택 + `st.expander("➕ 카메라 등록 / 삭제")` 안에 `st.text_input`/삭제용 `st.selectbox` — 그대로 유지 (`pages/1_모니터링.py:498,516,520,530`).
- ROI 저장 목록: `st.selectbox("ROI 선택", ["— 선택 —"] + saved)` — 그대로 유지 (`pages/2_ROI_설정.py:228`).
- 그 외 모든 위젯(시작/정지 버튼, 보정 모드 라디오 등)의 종류·위치·순서도 동일하게 유지한다. "이 라디오를 셀렉트박스로", "이 리스트를 카드 그리드로" 같은 구조 변경은 **금지**. 시각적으로 예뻐 보이도록 CSS로 꾸미는 것(둥근 모서리, 색상, 카드 배경, 아이콘 등)은 허용되지만, Streamlit 위젯 자체의 타입·파라미터·배치 순서를 바꾸는 것은 허용되지 않는다.

**이번 단계에서 하지 않는 것(명시적 제외, 2단계로 분리):**
- 공개 디스플레이 전용 페이지 신설 (별도 기기/모니터에 송출하려면 `st.cache_resource`로 영상 캡처·추론·판정 파이프라인을 세션별이 아닌 앱 전체 공유 자원으로 바꿔야 함 — 이건 아키텍처 변경이라 별도 계획으로 진행)
- 페이지 라우팅 메커니즘 교체 (`pages/` 디렉토리 자동 감지 → `st.navigation`/`st.Page`로 바꾸는 것) — 사이드바 외양은 **CSS만으로** 조정하고 라우팅 방식 자체는 그대로 둔다
- 탐지/판정 로직(`core/detector.py`, `core/parked_detector.py`, `core/danger_logic.py`), ROI 저장/계산 로직, 이벤트 저장 로직, 성능 평가 계산 로직 — 전부 무변경
- ByteTrack/`USE_TRACKER`, OpenVINO, `FRAME_SKIP` — 무관, 건드리지 않음

## 2. 현재 상태

- `app.py`, `pages/1_모니터링.py`, `pages/3_이벤트_다시보기.py`에는 커스텀 `<style>` 블록(브랜드 컬러 `#0F172A` 등)이 있지만, `pages/0_대시보드.py`, `pages/2_ROI_설정.py`, `pages/4_성능_평가.py`는 기본 Streamlit 스타일 그대로다.
- `pages/0_대시보드.py`는 제목이 "🚨 도로변 사각지대 보행자 위험 감지 및 시청각 경고 시스템"으로, "세이프뷰"/SafeView 브랜드명이 전혀 안 보인다. 하단엔 "테스트용 영상 파일(.mp4)은 미리 data/ 폴더에 넣어주세요" 같은 개발자용 셋업 안내가 그대로 노출된다.
- `pages/1_모니터링.py`의 `draw_text_korean_centered(annotated, "경고", 50, 160, (0, 0, 255))` (약 923행)가 위험 감지 시 영상 프레임 위에 "경고" 글자를 빨간색+검은 외곽선으로, 배경 없이, 화면 상단 쪽에 크게 그린다. 이 메커니즘 자체는 이미 목업이 요구하는 "배경 없는 큰 글씨" 방식과 같고, 문구·위치·크기만 다듬으면 된다.
- Streamlit 버전은 1.55.0 — 사이드바는 `pages/` 폴더를 자동 감지해 생성되는 기본 내비게이션이며, 다크 톤·활성 페이지 강조는 `[data-testid="stSidebarNav"]` 등을 타깃으로 한 CSS로 조정 가능하다(라우팅 구조 자체를 바꾸지 않고도 가능).

## 3. 구현 계획

1. **`app.py`**: 전역 `<style>`에 사이드바(`[data-testid="stSidebarNav"]` 및 관련 컨테이너) 다크 네이비(`#0B1220`) 배경, 링크 텍스트 색상, 활성 페이지 강조 스타일을 추가한다. Google Fonts "Noto Sans KR" 로드, 전역 `font-family` 적용. 색상 토큰은 기존 코드에서 이미 쓰는 값을 그대로 재사용한다(네이비 `#0F172A`/`#0B1220`, 슬레이트 `#64748B`/`#94A3B8`, 포인트 블루 `#38BDF8`, 위험 레드 `#DC2626`/`#EF4444`, 안전 그린 `#4ADE80`/`#10B981`, 배경 `#F1F5F9`/`#F8FAFC`).
2. **`pages/0_대시보드.py`**: 목업 `AdminShell.dc.html` 참고해 재작성 — 상단에 "세이프뷰" 브랜드 히어로(짧은 태그라인으로 교체, 지금의 긴 기술적 제목 문장은 부제로 축소), 통계는 지금처럼 `os.listdir` 등으로 계산한 **실제 값**을 카드 스타일로 표시(목업의 예시 숫자 5/42/8을 그대로 박아넣지 않는다), "사용 방법"을 스텝 카드로 교체. "mp4 파일 넣어주세요" 안내는 삭제하거나 작은 캡션으로 축소.
3. **`pages/2_ROI_설정.py`, `pages/4_성능_평가.py`**: 제목/구분선 등에 동일 색상·타이포 적용, 주요 섹션을 카드(`st.container(border=True)` 또는 동등한 CSS)로 감싸 통일감을 준다. ROI 그리기 흐름, 성능 평가 입력/계산 로직은 손대지 않는다.
4. **`pages/1_모니터링.py`**:
   - 상태 패널(`status-box-danger`/`status-box-safe`)과 레이아웃을 목업 `Main.dc.html`의 톤(카드 배경, 둥근 모서리, 색상)에 맞게 다듬는다. 소스 선택·시작/정지 등 기존 컨트롤의 동작은 변경하지 않는다.
   - `draw_text_korean_centered(annotated, "경고", 50, 160, (0, 0, 255))` 호출을 목업 스타일에 맞춰 조정한다(예: 문구를 좀 더 구체적으로, 위치를 화면 상단~중단 사이로). 이 함수가 호출되는 **조건**(언제 위험으로 판단해 문구를 그리는지)은 `danger_logic`의 판정 결과를 그대로 따르며 변경하지 않는다 — 그리는 문구·폰트 크기·위치만 조정한다.
5. **`pages/3_이벤트_다시보기.py`**: 이미 브랜드 컬러를 쓰고 있어 큰 변경은 필요 없다. 다른 페이지와 색상 토큰이 어긋나는 부분만(있다면) 맞춘다.
6. 사이드바 커스터마이징은 `data-testid` 등 Streamlit 내부 DOM 구조에 의존하므로, 적용한 선택자를 코드 주석으로 남겨 향후 Streamlit 업그레이드 시 깨지면 바로 찾을 수 있게 한다.

## 4. 수용 기준

- [ ] 5개 페이지(대시보드/모니터링/ROI 설정/다시보기/성능 평가) 모두에서 동일한 색상 팔레트·폰트가 적용된 것이 육안으로 확인된다.
- [ ] 사이드바가 모든 페이지에서 일관된 다크 톤으로 보이고, 현재 열려 있는 페이지가 강조 표시된다.
- [ ] 대시보드 홈 최초 화면에 "세이프뷰"/SafeView 브랜딩이 보이고, "data/ 폴더에 mp4 넣어주세요" 같은 개발자용 안내가 전면에 노출되지 않는다.
- [ ] 대시보드의 통계 수치(저장된 ROI/이벤트/샘플 영상 개수)는 여전히 실제 파일 시스템 값을 반영한다(하드코딩된 예시 숫자가 아님).
- [ ] 기존 핵심 동작이 전부 회귀 없이 동작한다 — ROI 점 찍고 저장/삭제, 모니터링 시작/정지 및 로컬·RTSP 전환, 이벤트 다시보기 캘린더 선택, 성능 평가 기록 추가/삭제를 각 1회 이상 수동으로 확인한다.
- [ ] `git diff`에서 `st.radio`/`st.selectbox`/`st.expander`/`st.text_input` 등 기존 위젯 호출의 **위젯 종류와 인자 구조**가 바뀌지 않았다 — 영상 소스 선택(`st.radio`), 로컬 영상 선택(`st.selectbox`+`st.expander`), RTSP 프리셋 선택/등록(`st.selectbox`+`st.expander`+`st.text_input`), ROI 저장 목록(`st.selectbox`)이 전부 작업 전과 동일한 위젯 타입·배치 순서로 남아 있다. `style=`/`class=` 등 시각적 속성 추가만 허용된다.
- [ ] `core/detector.py`, `core/parked_detector.py`, `core/danger_logic.py`, `core/roi_manager.py`, `core/performance_eval.py`가 단 한 줄도 바뀌지 않는다(`git diff` 확인).
- [ ] 모니터링 페이지에서 위험 판정 시 영상 위 경고 문구가 배경 없는 큰 외곽선 텍스트로 표시되고, 위험 판정이 뜨는 **조건**(언제 뜨는지)은 이전과 동일하다.
- [ ] `pages/` 디렉토리 자동 라우팅 방식이 그대로 유지된다(`st.navigation`/`st.Page`로 바뀌지 않음).

## 5. 예상 변경 파일

- `app.py`
- `pages/0_대시보드.py`
- `pages/1_모니터링.py`
- `pages/2_ROI_설정.py`
- `pages/3_이벤트_다시보기.py`
- `pages/4_성능_평가.py`
- `docs/tasks/current.md`
- `docs/tasks/archive/2026-10-08-playback-control-ui-v2-rollback.md` (이전 작업 종료 시 Claude가 이미 생성해둔 아카이브 파일 — 이번 UI/UX 작업과 무관하게 그대로 존재하던 미추적 파일)

## 6. 파일 소유권

| 파일 | 소유자 | 상태 |
|---|---|---|
| `app.py`, `pages/*.py` | Codex (구현/테스트) | 착수 가능 |
| `docs/tasks/current.md` | Claude (계획/리뷰) | 계획 작성 완료 |

Claude는 계획 수립과 구현 후 리뷰만 수행하며 제품 코드는 직접 수정하지 않는다.

## 7. 위험 요소 또는 주의사항

- 사이드바 커스터마이징이 Streamlit 내부 DOM 구조(`data-testid="stSidebarNav"` 등 비공개 구현 세부사항)에 의존한다 — 적용한 선택자를 주석으로 남겨둘 것.
- 색상 대비(contrast) — 다크 네이비 배경 위 텍스트 명도 대비가 너무 낮지 않은지 확인한다.
- 대시보드 통계 카드는 반드시 실제 값을 표시해야 한다(목업의 예시 숫자를 그대로 쓰지 않도록 주의).
- `draw_text_korean_centered`는 프레임에 직접 그리는 함수이고 `malgunbd.ttf`/`malgun.ttf` 폴백 로직이 있다 — 이 예외 처리는 유지한다.
- "공개 디스플레이 페이지"나 "공유 자원 구조"를 이번 범위에 끌어들이지 않는다 — 2단계에서 별도 계획으로 진행한다.
- **디자인 열정에 휩쓸려 위젯을 "더 예쁜" 다른 위젯으로 바꾸고 싶은 유혹을 조심할 것** — 사용자가 명시적으로 "기능과 구조는 작업 전과 동일해야 한다"고 못박았다. CSS로 기존 위젯을 꾸미는 것과, 다른 위젯으로 교체하는 것은 완전히 다른 일이다. 애매하면 바꾸지 않는 쪽으로 판단한다.

## 구현 결과
- 실제 변경 파일:
  - `app.py`
  - `pages/0_대시보드.py`
  - `pages/1_모니터링.py`
  - `pages/2_ROI_설정.py`
  - `pages/3_이벤트_다시보기.py`
  - `pages/4_성능_평가.py`
  - `docs/tasks/current.md`
- 계획 대비 변경 요약:
  - 전역 Noto Sans KR 타이포그래피와 공통 네이비·슬레이트·블루·레드·그린 토큰을 적용하고, Streamlit 내부 `data-testid` 선택자에 대한 유지보수 주석과 다크 사이드바/활성 페이지 강조 스타일을 추가했다.
  - 대시보드를 세이프뷰 브랜드 히어로, 실제 파일 시스템 집계 기반 통계 카드, 3단계 시작 안내, 간결한 위험 판단 기준으로 재구성하고 개발자용 전면 안내를 제거했다.
  - 모니터링 상태 패널·영상 카드 톤을 통일하고, 위험 판정 조건은 유지한 채 프레임 크기에 대응하는 배경 없는 큰 외곽선 문구 `보행자 위험`으로 바꿨다.
  - ROI 설정·성능 평가에 공통 제목/설명·입력/폼/데이터 카드 스타일을 추가하고, 다시보기의 배경·폰트를 공통 토큰과 일치시켰다.
  - 사용자 화면 확인에서 발견된 아이콘 리거처 깨짐을 수정하기 위해 전역 폰트 선택자에서 `[class*="st-"]`와 중복 앱 컨테이너 선택자를 제거하고 `html, body`에만 폰트를 지정했다. Streamlit 아이콘 요소의 전용 폰트는 더 이상 덮어쓰지 않는다.
  - Streamlit 1.55의 `data-testid`/BaseWeb DOM을 대상으로 라디오를 세그먼트형 트랙, 셀렉트박스·텍스트/숫자 입력·텍스트 영역을 브랜드 테두리/포커스 스타일, 업로더·확장 패널을 카드 스타일, primary/secondary 버튼을 블루/네이비 스타일로 통일했다.
  - 모니터링·ROI 설정의 첫 설정 열에는 비가시성 표식만 추가하고 CSS `:has()` 선택자로 흰 배경·둥근 모서리·그림자의 소스 설정 카드 외양을 적용했다.
  - Streamlit 1.55 프런트엔드 번들에서 `st.navigation()` 메뉴의 실제 DOM 식별자 `stSidebarNavLink`/`stSidebarNavLinkContainer`를 확인한 뒤, 해당 요소에 밝은 글자색·옅은 테두리·활성 블루 테두리를 적용했다.
  - 대시보드 카드 외형과 실제 파일 시스템 통계는 유지하면서 프로젝트 개요, 사용 방법 3단계, 위험 판단 규칙 5행 표, 기술 스택, 시작 전 확인 문구를 기준 커밋의 원문 그대로 복원했다.
  - 버튼과 사이드바 메뉴·푸터에 `white-space: nowrap`을 적용하고 버튼 좌우 패딩만 16px에서 10px로 줄여, 기존 글자 크기와 버튼 색상을 유지하면서 줄바꿈을 방지했다.
  - 모니터링·ROI 설정이 공유하는 소스 선택 라디오의 `label`과 내부 자식 요소에도 `white-space: nowrap`을 적용해 `📡 RTSP` 라벨이 두 줄로 갈라지지 않도록 했다. 기존 글자 크기·패딩·위젯 호출은 유지했다.
  - Streamlit 1.55 프런트엔드 번들에서 메인 컨테이너의 기본 좌우 패딩이 `theme.spacing.lg`로 적용되는 것을 확인하고, 소스 설정 표식이 있는 모니터링·ROI 설정 페이지만 좌측 여백을 조정했다. 5차의 10px이 실제 화면에서 너무 타이트하다는 사용자 확인을 반영해 카드 내부 16px 여백보다 한 단계 넉넉한 20px로 미세조정했으며, 다른 페이지의 메인 여백과 영상/컬럼 비율은 유지했다.
  - 사이드바 메뉴·버튼·폼 버튼·소스 라디오·사이드바 푸터에 흩어져 있던 `white-space: nowrap`을 하나의 공통 선택자 규칙으로 통합하고, 라벨형 위젯 추가 시 같은 목록을 갱신하도록 한국어 유지보수 주석을 남겼다.
  - 모니터링 소스 설정 패널의 시스템 상태를 야간 밝기 보정 라디오 아래 마지막 요소로 옮기고 FPS 한 줄만 남겼다. 중복 ROI 상태 안내와 프레임·추론 placeholder/갱신 코드는 제거했으며, 실제 판정용 ROI 로드는 실행 루프에 그대로 유지했다.
  - 사이드바 맨 아래에 렌더링되던 `SAFEVIEW · 세이프뷰` 문구를 최상위 사이드바의 `::after`에서 실제 내비게이션 컨테이너인 `[data-testid="stSidebarNav"]::before`로 옮겼다. 이에 따라 로고 이미지 → 브랜드 문구 → 메뉴 목록 순서가 되며 기존 글자 크기·색상·구분선·줄바꿈 방지 스타일은 유지했다.
  - Streamlit 1.55 프런트엔드 번들에서 로고와 내비게이션 사이의 실제 추가 간격이 `stSidebarNav`가 아니라 `stSidebarHeader`의 `headerHeight`와 `spacing.lg` 하단 여백에서 생기는 것을 확인했다. 접기 버튼이 포함된 헤더를 우상단 절대 위치로 옮기고 빈 로고 스페이서를 숨겨 문서 흐름의 간격을 제거했으며, 로고의 기존 하단 8px만 브랜드 문구와의 간격으로 남겼다.
  - 기존 `st.radio`/`st.selectbox`/`st.expander`/`st.text_input`/`st.file_uploader` 호출과 인자 구조, 탐지·판정 로직, 라우팅 코드는 변경하지 않았다.
- 계획 이탈 사항: 없음. 계획에는 현재 라우팅을 `pages/` 자동 감지 방식으로 서술했지만 기준 커밋의 실제 코드는 이미 `st.navigation`/`st.Page` 방식이었다. 작업 전 라우팅을 그대로 보존한다는 제약에 따라 해당 코드는 수정하지 않았다.
- 종료 시점 git 상태 (`git -c core.quotepath=false status --porcelain`):
  ```text
   M app.py
   M docs/tasks/current.md
   M pages/0_대시보드.py
   M pages/1_모니터링.py
   M pages/2_ROI_설정.py
   M pages/3_이벤트_다시보기.py
   M pages/4_성능_평가.py
  ?? docs/tasks/archive/2026-10-08-playback-control-ui-v2-rollback.md
  ```
  `docs/tasks/archive/2026-10-08-playback-control-ui-v2-rollback.md`는 착수 전부터 존재한 계획 기재 미추적 파일이며 수정하지 않았다. `git status`는 기존 접근 불가 임시 디렉터리들과 AppTest가 시스템 임시 경로에 만든 정리 불가 디렉터리에 대한 경고도 출력했으나 porcelain 변경 목록에는 포함되지 않았다.

## 테스트 결과
- 실행 명령/검증:
  - `git diff --check` — PASS (공백 오류 없음; Git의 LF→CRLF 안내만 출력)
  - Python `ast.parse`로 변경된 6개 제품 Python 파일 구문 검사 — PASS
  - 기준 커밋과 현재 파일에서 `st.radio`/`st.selectbox`/`st.expander`/`st.text_input`/`st.file_uploader` 호출 AST 전체 비교 — PASS (모니터링/ROI 설정/다시보기/성능 평가 모두 동일)
  - 보호 대상 `core/detector.py`, `core/parked_detector.py`, `core/danger_logic.py`, `core/roi_manager.py`, `core/performance_eval.py`의 `git diff --name-only` — PASS (출력 없음)
  - `app.py`의 `st.navigation`/`st.Page` diff 검색 — PASS (출력 없음)
  - `python -m streamlit run app.py --server.headless true --server.port 8765 --browser.gatherUsageStats false` 후 `http://127.0.0.1:8765/_stcore/health` 요청 — PASS (`200`, `ok`)
  - `streamlit.testing.v1.AppTest`에서 홈 실행 후 모니터링·ROI 설정·성능 평가로 `switch_page(...).run(timeout=30)` — PASS (세 페이지 모두 `exceptions 0`; 라디오/셀렉트박스/확장 패널/버튼 렌더 트리 생성 확인)
  - 동일 AppTest 렌더 트리에서 `_arr`/`arrow_right`/`arrow_drop_down` 검색 — PASS (깨진 리거처 문자열 0건)
  - Streamlit 1.55 설치본 프런트엔드 번들(`index.RuhrnD1v.js`) 검색 — PASS (`stSidebarNav`, `stSidebarNavItems`, `stSidebarNavLinkContainer`, `stSidebarNavLink` 실제 식별자 존재 확인)
  - AppTest 홈 렌더 트리의 HTML 마크다운 검사 — PASS (프로젝트 개요 전문, 사용 방법 3문장, 위험 판단 5개 조건, 기술 스택 3개 항목, 시작 전 확인 전문 모두 존재; 예외 0건)
  - AppTest에서 모니터링·ROI 설정·성능 평가 페이지 전환 후 재실행 — PASS (세 페이지 모두 예외 0건, 위젯 렌더 트리 생성 확인)
  - `app.py` CSS 정적 검사 — PASS (실제 `stSidebarNavLink` 대상 밝은 글자색/테두리/활성 상태, 링크 자식·버튼 자식·사이드바 푸터의 `white-space: nowrap` 존재)
  - `app.py` 라디오 CSS 정적 검사 — PASS (`[data-testid="stRadio"] div[role="radiogroup"] > label`과 그 직계 자식 블록 모두에 `white-space: nowrap` 존재)
  - `📡 RTSP` 한 줄 최소 폭 보수 계산 — PASS (16px 기준 이모지 16px + 공백 4px + 영문 4자×9px + 기존 좌우 패딩 20.8px = 라벨 약 76.8px, 두 옵션 트랙 약 165.6px; `white-space: nowrap`으로 내부 개행 금지)
  - 기준 커밋과 현재 모니터링·ROI 설정의 `st.radio` 호출 AST 비교 — PASS (호출 종류·인자·순서 동일)
  - `streamlit.testing.v1.AppTest` 홈 실행 후 모니터링·ROI 설정 전환 — PASS (두 페이지 예외 0건, 각각 라디오 2개/1개 렌더 트리 확인; 종료 시 시스템 임시 디렉터리 정리 권한 경고만 발생)
  - Streamlit 1.55 설치본 프런트엔드 번들의 `StyledAppViewBlockContainer` 정의 확인 — PASS (기본 좌우 패딩이 `theme.spacing.lg`이고 실제 메인 DOM 식별자가 `stMainBlockContainer block-container`임을 확인)
  - `app.py` 소스 패널 여백 CSS 정적 검사 — PASS (`.block-container:has(.sv-source-panel-marker)`에 사용자 재확인 범위 18~24px 안의 `padding-left: 20px !important` 적용 확인)
  - `app.py` 공통 줄바꿈 방지 CSS 정적 검사 — PASS (사이드바 링크/하위 요소, 일반·폼 버튼/하위 요소, 라디오 라벨/하위 요소, 사이드바 푸터가 한 규칙에 모였고 한국어 유지보수 주석 존재; 기존 개별 중복 선언 제거)
  - 첫 CSS 정적 검사 스크립트의 정규식이 Python f-string 소스에 쓰인 이중 중괄호(`{{`)를 고려하지 않아 선택자를 찾지 못함 — 고정 문자열 검사로 바로잡아 재실행 PASS (제품 코드 실패 아님)
  - 5차 수정 후 `streamlit.testing.v1.AppTest` 홈→모니터링→ROI 설정→성능 평가 전환 — PASS (모든 페이지 예외 0건; 모니터링 라디오 2·셀렉트박스 1·버튼 10개, ROI 설정 라디오 1·셀렉트박스 2·버튼 12개, 성능 평가 셀렉트박스 2·버튼 2개 렌더 확인; 종료 시 시스템 임시 디렉터리 정리 권한 경고만 발생)
  - 첫 AST/AppTest 검증 시 인라인 Python의 한글 경로 리터럴이 PowerShell에서 손상되어 파일 탐색 실패 — 재실행 PASS (숫자 접두사 glob으로 파일을 찾아 같은 검증 완료; 제품 코드 실패 아님)
  - 실행 중 앱 `http://127.0.0.1:8765/_stcore/health` 요청 — PASS (`200`, `ok`)
  - 6차 수정 후 Python `ast.parse`로 6개 제품 Python 파일 구문 검사 — PASS
  - 6차 정적 구조 검사 — PASS (밝기 보정 라디오 뒤에 FPS placeholder가 위치하고, 시스템 상태/FPS placeholder는 각 1개이며 `__frame_ph_count`/`__infer_ph`/프레임·추론 placeholder와 ROI 상태 표시 문구가 남지 않음)
  - 6차 수정 후 `streamlit.testing.v1.AppTest` 홈→모니터링→ROI 설정→성능 평가 전환 — PASS (모든 페이지 예외 0건; 모니터링 렌더 트리에서 FPS 마크다운 정확히 1개 확인; 종료 시 시스템 임시 디렉터리 정리 권한 경고만 발생)
  - 6차 수정 후 Streamlit 서버 기동 및 `http://127.0.0.1:8765/_stcore/health` 요청 — PASS (`200`, `ok`)
  - 첫 6차 정적 검사에서 PowerShell 파이프를 거친 인라인 Python의 한글 리터럴이 손상되어 위치 검색 실패 — 한글 리터럴을 배제한 구조 검사와 UTF-8 `rg` 검사로 분리해 재실행 PASS (제품 코드 실패 아님)
  - 7차 사이드바 CSS 정적 검사 — PASS (`[data-testid="stSidebarNav"]::before`에 브랜드 문구와 기존 스타일이 존재하고, 기존 `[data-testid="stSidebar"] > div:first-child::after` 선택자는 제거됐으며 브랜드 문구 선언은 1개만 존재)
  - Streamlit 1.55 설치본 프런트엔드 번들 재검사 — PASS (`stSidebarNav`와 그 자식 메뉴 목록 식별자 `stSidebarNavItems`가 실제 번들에 함께 존재하여, 컨테이너 `::before`가 메뉴 목록보다 앞에 배치되는 구조 확인)
  - 7차 수정 후 `streamlit.testing.v1.AppTest` 홈 실행 — PASS (예외 0건; 종료 시 시스템 임시 디렉터리 정리 권한 경고만 발생)
  - 7차 검증의 첫 인라인 Python 정적 검사 명령은 PowerShell 따옴표 처리로 `SyntaxError` 발생 — 따옴표를 `chr(34)`로 구성하는 검사로 바로잡아 재실행 PASS (제품 코드 실패 아님)
  - Streamlit 1.55 설치본 프런트엔드 번들의 사이드바 구조 재검사 — PASS (`stSidebarHeader`가 `stSidebarNav` 바로 앞에 렌더링되고 기본 `headerHeight`와 `marginBottom: spacing.lg`를 가지며, `stSidebarNav` 자체에는 상단 margin/padding 선언이 없음을 확인)
  - 8차 사이드바 간격 CSS 정적 검사 — PASS (`stSidebarHeader`를 흐름에서 분리해 `top: 12px; right: 0`에 유지하고 기본 높이·하단 여백을 제거했으며, `stLogoSpacer`는 숨기고 로고의 기존 `margin-bottom: 8px`은 유지)
  - 8차 수정 후 Python `ast.parse`로 6개 제품 Python 파일 구문 검사 — PASS
  - 8차 수정 후 `streamlit.testing.v1.AppTest` 홈 실행 — PASS (예외 0건; 종료 시 시스템 임시 디렉터리 정리 권한 경고만 발생)
  - 8차 수정 후 Streamlit 서버 기동 및 `http://127.0.0.1:8765/_stcore/health` 요청 — PASS (`200`, `ok`)
  - 8차 수정 후 보호 대상 `core/*.py`와 `st.navigation`/`st.Page` diff 검사 — PASS (출력 없음)
  - 8차 검증용 Chrome/Edge 프로필 디렉터리는 브라우저 실패 후 `git clean -fd -- .edge-headless-profile .chrome-headless-profile`로 제거했으며 제품 파일이나 기존 미추적 파일은 삭제하지 않았다.
  - Chrome/Edge headless DOM 덤프 — 미실행 (샌드박스의 Windows 프로세스/Crashpad 권한 제한으로 브라우저 프로세스가 렌더 전에 종료됨)
- 수용 기준 체크리스트:
  - [ ] **미실행** — 5개 페이지(대시보드/모니터링/ROI 설정/다시보기/성능 평가) 모두에서 동일한 색상 팔레트·폰트가 적용된 것이 육안으로 확인된다.
  - [ ] **미실행** — 사이드바가 모든 페이지에서 일관된 다크 톤으로 보이고, 현재 열려 있는 페이지가 강조 표시된다.
  - [x] **PASS** — 대시보드 홈 최초 화면에 "세이프뷰"/SafeView 브랜딩이 보이고, "data/ 폴더에 mp4 넣어주세요" 같은 개발자용 안내가 전면에 노출되지 않는다. (코드 및 AppTest 초기 렌더 예외 없음 확인)
  - [x] **PASS** — 대시보드의 통계 수치(저장된 ROI/이벤트/샘플 영상 개수)는 여전히 실제 파일 시스템 값을 반영한다(하드코딩된 예시 숫자가 아님). (기존 `os.listdir` 집계 유지 확인)
  - [ ] **미실행** — 기존 핵심 동작이 전부 회귀 없이 동작한다 — ROI 점 찍고 저장/삭제, 모니터링 시작/정지 및 로컬·RTSP 전환, 이벤트 다시보기 캘린더 선택, 성능 평가 기록 추가/삭제를 각 1회 이상 수동으로 확인한다.
  - [x] **PASS** — `git diff`에서 `st.radio`/`st.selectbox`/`st.expander`/`st.text_input` 등 기존 위젯 호출의 위젯 종류와 인자 구조가 바뀌지 않았다 — 기준 커밋 대비 AST 비교로 확인했다.
  - [x] **PASS** — `core/detector.py`, `core/parked_detector.py`, `core/danger_logic.py`, `core/roi_manager.py`, `core/performance_eval.py`가 단 한 줄도 바뀌지 않는다(`git diff` 확인).
  - [x] **PASS** — 모니터링 페이지에서 위험 판정 시 영상 위 경고 문구가 배경 없는 큰 외곽선 텍스트로 표시되고, 위험 판정이 뜨는 조건(언제 뜨는지)은 이전과 동일하다. (`if is_danger` 조건과 도우미의 `stroke_width=5` 유지, 호출 인자만 변경 확인)
  - [x] **PASS** — 작업 전 라우팅 방식이 그대로 유지된다(`st.navigation`/`st.Page` 호출 diff 없음).
- 추가 반려 항목 확인:
  - [x] **PASS** — `[class*="st-"]` 전역 폰트 강제 적용을 제거했으며 AppTest의 모니터링·ROI 설정 렌더 트리에 `_arr`/`arrow_right`/`arrow_drop_down` 문자열이 나타나지 않는다.
  - [x] **PASS** — 라디오·셀렉트박스·파일 업로더·확장 패널·텍스트 입력·일반/폼 버튼에 브랜드 색상, 둥근 모서리, 포커스/선택 상태 CSS가 존재하며 모니터링·ROI 설정의 소스 영역이 카드 선택자의 대상이 된다.
  - [x] **PASS** — Streamlit 1.55 프런트엔드 번들에서 확인한 실제 `stSidebarNavLink`/`stSidebarNavLinkContainer` 선택자에 비활성 `#E2E8F0`, 활성 `#FFFFFF`, 메뉴 테두리와 활성 블루 테두리가 적용된다. AppTest 페이지 렌더 예외는 0건이다.
  - [x] **PASS** — 대시보드의 프로젝트 개요/사용 방법/위험 판단 5행 표/기술 스택/시작 전 확인이 원문 그대로 AppTest 렌더 트리에 존재한다.
  - [x] **PASS** — 버튼·사이드바 메뉴·사이드바 푸터의 텍스트 요소에 `white-space: nowrap`이 적용되고 버튼 좌우 패딩만 축소됐다. 글자 크기와 버튼 색상 선언은 변경하지 않았다.
  - [x] **PASS** — 모니터링·ROI 설정의 소스 선택 라디오 `label`과 내부 자식 요소에 `white-space: nowrap`이 적용됐다. `📡 RTSP`의 보수 추정 필요 폭은 약 76.8px이고 두 옵션 트랙은 약 165.6px이며, 기존 라디오 호출·글자 크기·패딩은 변경하지 않았다.
  - [x] **PASS** — 모니터링·ROI 설정의 소스 설정 카드 왼쪽 간격을 사용자 지정 범위 안의 20px로 조정했다. 선택자를 소스 패널 표식이 있는 페이지로 제한해 다른 페이지의 기본 메인 여백과 기존 컬럼 비율은 바꾸지 않았다.
  - [x] **PASS** — 줄바꿈 금지 대상 선택자를 공통 규칙 한곳으로 통합했으며, 향후 라벨형 위젯 추가 시 목록 갱신을 안내하는 한국어 주석을 추가했다.
  - [x] **PASS** — 모니터링 시스템 상태가 소스 설정 패널의 마지막 요소이며 FPS 한 줄만 렌더링된다. ROI 상태·프레임·추론 표시는 제거했고 실제 판정용 ROI 로드와 FPS 실시간 갱신은 유지했다.
  - [x] **PASS** — 사이드바 브랜드 문구가 실제 내비게이션 컨테이너의 `::before`로 이동했고 기존 최상위 컨테이너의 `::after`는 제거됐다. CSS 생성 순서상 로고 이미지 → 브랜드 문구 → 메뉴 목록 순서이며 문구가 사이드바 맨 아래에 중복 렌더링되지 않는다.
  - [x] **PASS** — Streamlit 기본 헤더의 높이·하단 여백을 문서 흐름에서 제거하고 접기 버튼은 우상단에 유지했다. 로고와 브랜드 문구 사이에는 로고의 8px 하단 여백만 남도록 CSS 구조와 설치 번들을 대조 확인했다.
- 미실행 항목과 사유: AppTest로 홈 원문과 모니터링·ROI 설정·성능 평가의 렌더 예외 및 위젯 트리는 확인했으나 실제 브라우저 프로세스가 샌드박스의 Windows Mojo/Crashpad 권한 오류로 렌더 전에 종료됐다. 따라서 최종 픽셀/계산 스타일 기준의 사이드바 글자 대비·텍스트 오버플로와 8차 로고-브랜드 문구 간격의 육안 확인, ROI/모니터링/RTSP/다시보기/성능평가의 수동 상호작용 검증은 미실행했다. 사용자 환경에서의 화면·기능 확인이 필요하다.

## 리뷰 및 남은 위험

- 리뷰 결과: approved
- 요약: 자동화 검증 가능한 6개 수용 기준(core 5개 파일 무변경, 위젯 AST 보존, 대시보드 브랜딩·통계 실제값, 경고 문구 조건 유지, 라우팅 유지)이 전부 PASS했고 파일 범위도 계획과 일치한다. not_run 3건(5페이지 색상·폰트 육안, 사이드바 다크톤·활성 강조, 핵심 기능 수동 1회 조작)은 브라우저 렌더링이 필요해 샌드박스 내 검증 불가 — 사용자가 앱을 직접 실행·조작해 확인한 뒤 State를 verified로 전환해야 한다.
- scope_ok: True
- 수용 기준 판정:
  - [not_run] 5개 페이지(대시보드/모니터링/ROI 설정/다시보기/성능 평가) 모두에서 동일한 색상 팔레트·폰트가 적용된 것이 육안으로 확인된다
  - [not_run] 사이드바가 모든 페이지에서 일관된 다크 톤으로 보이고, 현재 열려 있는 페이지가 강조 표시된다
  - [pass] 대시보드 홈 최초 화면에 세이프뷰/SafeView 브랜딩이 보이고, 개발자용 안내가 전면에 노출되지 않는다
  - [pass] 대시보드의 통계 수치(저장된 ROI/이벤트/샘플 영상 개수)는 실제 파일 시스템 값을 반영한다(하드코딩 아님)
  - [not_run] 기존 핵심 동작 전부 회귀 없이 동작 — ROI 저장/삭제, 모니터링 시작/정지·로컬·RTSP 전환, 다시보기 캘린더, 성능 평가 추가/삭제 각 1회 이상 수동 확인
  - [pass] git diff에서 st.radio/st.selectbox/st.expander/st.text_input 위젯 종류와 인자 구조가 바뀌지 않았다
  - [pass] core/detector.py, parked_detector.py, danger_logic.py, roi_manager.py, performance_eval.py 단 한 줄도 바뀌지 않는다
  - [pass] 모니터링 페이지에서 위험 판정 시 영상 위 경고 문구가 배경 없는 큰 외곽선 텍스트로 표시되고, 판정 조건(언제 뜨는지)은 이전과 동일하다
  - [pass] 기존 라우팅 방식이 그대로 유지된다(st.navigation/st.Page 방식 보존)
- 남은 위험/후속 작업:
  - not_run 3건(5페이지 색상·폰트 육안, 사이드바 다크톤·활성 강조, ROI/모니터링/RTSP/다시보기/성능평가 핵심 기능 수동 1회) — 사용자가 앱을 직접 실행·조작해 확인 후 current.md State를 verified로 전환 필요
  - stSidebarNavLink 등 Streamlit 내부 data-testid CSS 의존 — 향후 Streamlit 업그레이드 시 사이드바 시각 깨짐 점검 필요 (app.py 주석 있음)
  - 변경 사항이 아직 워킹트리에만 있고 미커밋 상태 — verified 확인 후 커밋 필요
- (Harness가 검증된 Claude 리뷰 JSON을 기계적으로 반영한 결과입니다.)

### 추가 리뷰 — 사용자 실제 화면 확인 결과 반영 (2026-10-10, Claude)

위 harness 자동 리뷰의 `approved` 판정은 **반려한다.** 사용자가 실제 브라우저(대시보드/모니터링/ROI 설정 페이지)를 확인한 결과 아래 2가지 문제가 확인됐다:

**1. 버그 — 아이콘 글자가 텍스트로 깨져 보임(확인·원인 파악 완료)**

모니터링·ROI 설정 페이지의 "저장된 영상 삭제" `st.expander` 바로 위/옆에 `_arr🗑️저장된영상 삭제` 같은 깨진 문자열이 그대로 노출된다. 원인은 `app.py:47`의 전역 CSS다:

```css
html, body, [class*="st-"], [data-testid="stAppViewContainer"] {
    font-family: 'Noto Sans KR', sans-serif;
}
```

`[class*="st-"]`는 클래스명에 `st-`가 들어간 **모든** Streamlit 내부 요소에 적용되는 너무 넓은 선택자다. 여기에는 Streamlit이 화살표/아이콘을 그릴 때 쓰는 전용 아이콘 폰트(리거처 기반, 예: `arrow_right` 같은 이름이 특수 폰트에서만 화살표 글리프로 렌더링됨)를 쓰는 요소도 포함돼, 그 요소의 폰트가 Noto Sans KR로 강제로 바뀌면서 리거처가 깨지고 아이콘 이름이 날것 텍스트로 노출된다.

**수정 방향**: `font-family`는 상속되는 속성이므로 `html, body`에만 지정해도 전체에 자연히 적용된다. `[class*="st-"]`를 선택자에서 완전히 제거하라(`[data-testid="stAppViewContainer"]`도 중복이라 제거해도 무방하지만, 유지해도 문제는 없다 — 문제의 핵심은 `[class*="st-"]`다). 수정 후 **반드시 모니터링·ROI 설정 페이지를 실제로 열어서 그 깨진 텍스트가 사라졌는지 육안으로 재확인**하고 테스트 결과에 스크린샷 대신 확인 절차를 구체적으로 기록하라(예: "F12 개발자 도구로 해당 요소의 computed font-family가 Material 아이콘 폰트로 되돌아왔는지 확인" 또는 최소한 "해당 문자열이 더 이상 페이지 텍스트에 나타나지 않음을 `curl`/`AppTest` 렌더 결과에서 확인").

**2. 디자인 — 입력 위젯이 Streamlit 기본 스타일 그대로라 "안 바뀐 것처럼" 보임**

대시보드 페이지는 브랜드 히어로·통계 카드·스텝 카드로 확실히 개선됐다고 사용자가 확인했다. 하지만 모니터링·ROI 설정 페이지는 사이드바와 페이지 배경만 바뀌었을 뿐, 실제로 사용자가 조작하는 핵심 위젯들이 전부 Streamlit 기본 흰색/회색 박스 그대로 남아있어 "거의 안 바뀐 것 같다"는 인상을 준다. 확인된 범위: `st.radio`(파일/RTSP 선택), `st.selectbox`(영상 파일/ROI 선택), `st.file_uploader`("Drag and drop file here" 박스), `st.expander`, `st.text_input`, `st.button`("▶ 시작" 버튼이 Streamlit 기본 녹색 primary 버튼 그대로라 브랜드 블루/네이비 톤과 어긋남).

**중요**: 이 작업의 "위젯·구조 100% 보존" 제약은 여전히 유효하다 — **위젯 종류(`st.radio`→`st.selectbox` 같은 교체)나 배치 순서를 바꾸라는 뜻이 아니다.** 각 위젯을 감싸는 Streamlit의 `data-testid` 컨테이너에 **CSS만** 추가해 브랜드 톤(색상 토큰, 둥근 모서리, 카드 배경)을 입히라는 뜻이다. 아이콘 폰트를 건드리지 않도록 1번 버그를 먼저 고친 뒤, 아래를 CSS로 추가하라(정확한 선택자는 Codex가 Streamlit 1.55.0의 실제 렌더링 결과를 보고 확인할 것 — 아래는 방향성 제시):

- `[data-testid="stRadio"]` (소스 선택 라디오): 목업의 세그먼트 버튼(pill) 느낌으로 — 배경 `var(--sv-border)` 트랙 안에 흰 배경 선택 상태.
- `[data-testid="stSelectbox"]` 내부 입력 박스: 둥근 모서리(`border-radius`), `var(--sv-border)` 테두리, 포커스 시 `var(--sv-blue)` 강조.
- `[data-testid="stFileUploaderDropzone"]` 또는 해당 컨테이너: 점선 대신 `var(--sv-border)` 실선 + 둥근 모서리로 다른 카드들과 톤 통일.
- `[data-testid="stExpander"]`: 다른 카드와 같은 흰 배경 + `border-radius` + 옅은 그림자.
- `div[data-testid="stButton"] button`, `div[data-testid="stFormSubmitButton"] button`: 기본 Streamlit 빨강/초록 테마 대신 `var(--sv-navy)`(보조 버튼) / `var(--sv-blue)`(주요 버튼) 톤으로.
- "영상 소스 설정" 섹션 전체를 흰 배경 카드(`var(--sv-surface)`, `border-radius`, 옅은 그림자)로 감싸 페이지 배경 위에 떠 있는 느낌을 주면 대시보드의 카드들과 톤이 맞아떨어질 것이다.

**범위 재확인**: 이번 수정도 CSS(그리고 꼭 필요한 최소한의 wrapper `st.container`/`st.markdown` div 추가)로만 하고, 각 `st.radio`/`st.selectbox`/`st.expander`/`st.text_input`/`st.file_uploader` 호출 자체(인자·위치·순서)는 여전히 건드리지 않는다. `core/*.py`, 탐지/판정 로직도 여전히 무변경 대상이다.

**State를 `approved` → `implementing`으로 되돌린다.** 수정 후 반드시 모니터링·ROI 설정·성능 평가 페이지를 실제로 렌더링해(AppTest 또는 가능하면 실행 중 HTML 스냅샷) 위젯들이 더 이상 기본 Streamlit 톤이 아님을 확인하고, 1번 버그의 재발 여부도 같이 확인하라.

### 3차 리뷰 — 사용자 2차 화면 확인 결과 반영 (2026-10-10, Claude)

2차 수정(아이콘 버그 수정 + 위젯 CSS)은 반영됐고 사용자가 버튼 색상·배경 전환은 마음에 든다고 확인했다. 다만 실제 화면에서 아래 3가지 문제가 추가로 발견되어 **`approved` 판정을 다시 반려한다.**

**1. 사이드바 개별 메뉴 글자가 안 보임(원인 파악 완료) + 테두리 요청**

`app.py`는 실제로 `st.navigation`/`st.Page`를 쓴다(기존 리뷰에서도 이미 확인된 사실). 그런데 사이드바 CSS는 `[data-testid="stSidebarNav"] a` 선택자로 글자색(`#CBD5E1`)·패딩·hover·`aria-current` 강조를 지정하고 있다 — 이건 **Streamlit이 `pages/` 폴더를 자동 감지해 만드는 옛날 멀티페이지 내비게이션의 구조**이고, `st.navigation()`으로 직접 구성한 내비게이션은 각 항목이 다른 DOM 구조/`data-testid`를 쓸 가능성이 높다. 컨테이너 배경(`[data-testid="stSidebar"]`)은 선택자가 맞아서 네이비로 잘 나오지만, 그 안의 개별 링크 글자 스타일은 선택자가 안 맞아 적용되지 않고 Streamlit 기본(어두운 글자) 그대로 남아 어두운 배경과 겹쳐 안 보이는 것으로 보인다.

**수정 방향**: 추측으로 선택자를 또 바꾸지 말고, 실제 실행 중인 앱의 사이드바 내비게이션 HTML을 직접 확인(예: `streamlit.testing.v1.AppTest`로 렌더링 후 사이드바 섹션의 실제 HTML을 출력해보거나, `--server.headless true`로 띄운 뒤 페이지 소스를 받아서 확인)해서 `st.navigation()`이 실제로 어떤 `data-testid`/`class`로 각 네비게이션 항목을 렌더링하는지 먼저 알아낸 뒤, 그 실제 구조에 맞춰 글자색을 **밝은 흰색 계열**(`#F8FAFC` 등, 비활성 상태도 최소 `#E2E8F0` 이상)로 분명히 보이도록 고쳐라. 추가로 각 메뉴 항목에 옅은 테두리를 그려라(예: `border: 1px solid rgba(255,255,255,0.08)`, 활성 항목은 `var(--sv-blue)` 톤의 테두리/강조 유지).

**2. 대시보드 문구가 원본 내용 대신 새로 짧게 쓴 문구로 통째로 교체됨**

사용자는 "프로젝트 소개글과 위험판단기준, 각주, 설명글들은 기존 스트림릿에 작성했던 내용들과 동일하게 해달라"고 명시적으로 요청했다. 2차 구현에서 `pages/0_대시보드.py`가 원본 문구를 전부 지우고 새로운 짧은 카피로 바꿔버렸다 — 이건 계획의 "시각 스타일만 바꾸고 문구는 보존" 원칙에서 벗어난 것이다(계획에 "짧은 태그라인으로 교체"라고 쓴 Claude의 실수이기도 하다 — 정정한다). **아래 원본 문구를 전부 그대로(토씨 하나 안 바꾸고) 살리되, 새로 만든 히어로/카드 스타일 안에 넣어서 보여줘라:**

- "프로젝트 개요" 문단 전문: "생활도로·골목·주차장·도로변 주차 구간에서 **주차 차량 및 구조물**로 인해 시야가 제한되는 환경에서 CCTV 또는 저장 영상으로 **사람과 차량을 실시간 인식**하고, 사용자가 지정한 **ROI(관심구역) 내 위험 상황**을 감지하여 화면 및 청각 경고와 이벤트 클립 영상을 저장하는 프로토타입입니다."
- "사용 방법" 원래 3단계 문구 그대로: "1. **👈 왼쪽 사이드바**에서 페이지를 선택하세요.", "2. **🗺️ ROI 설정** 페이지에서 관심구역을 먼저 설정하세요.", "3. **🎥 모니터링** 페이지에서 영상을 선택하고 감지를 시작하세요." (새로 만든 "시작하기" 3칸 스텝 카드의 문구를 이 원문으로 교체 — 지금 카드에 들어간 "ROI 설정/모니터링 시작/이벤트 확인" 창작 문구가 아니라 위 원문을 쓴다)
- "위험 판단 규칙" **5행 표 전체**를 그대로 복원(지금은 한 문장으로 축약돼 있다): 아무것도 없음→🟢 정상 / 사람만 있음→🟢 정상 / 자동차만 있음→🟢 정상 / 사람+자동차(사람이 ROI 밖)→🟢 정상 / **사람+자동차(사람이 ROI 안)**→🔴 **위험**. 표 형태 그대로(마크다운 테이블이든 새 카드 스타일의 표든) 5행 다 보여야 한다.
- "기술 스택" 목록이 완전히 삭제됐다 — 복원: 🐍 Python + Streamlit / 👁️ YOLOv8 (Ultralytics) / 📹 OpenCV.
- "💡 시작 전 확인" 안내 문구도 삭제됐다 — 복원: "테스트용 영상 파일(.mp4)은 미리 `data/` 폴더에 넣어주세요. YOLOv8 모델은 처음 실행할 때 자동으로 다운로드됩니다." (작게 캡션 처리는 괜찮지만 내용 자체는 지우지 않는다)

**3. 버튼·사이드바 메뉴 글자가 제멋대로 줄바꿈됨**

스크린샷에서 확인된 구체적 사례: 모니터링 페이지의 "⏸ 일시정지" 버튼이 "일시정"/"지" 두 줄로 쪼개짐, 사이드바의 "세이프뷰 다시보기" 메뉴가 두 줄로 쪼개짐, 사이드바 하단 "SAFEVIEW · 세이프뷰" 푸터도 두 줄로 쪼개짐. **글자 크기는 지금 그대로 유지하고(사용자가 명시적으로 "지금이 딱 좋다"고 확인), 버튼 색상도 그대로 유지한 채(마음에 든다고 확인)**, 줄바꿈만 없애고 글자가 버튼 밖으로 넘치지도 않게 고쳐라. 방법 예시(강제하지 않음, Codex가 실제 렌더링을 보고 판단):
- 버튼/메뉴 텍스트에 `white-space: nowrap` 추가.
- 그것만으로 글자가 버튼 밖으로 넘치면, 해당 버튼이 들어있는 컬럼 폭을 넓히거나(`st.columns` 비율 조정 — 단, 전체 레이아웃 구조가 크게 틀어지지 않는 선에서) 버튼 좌우 패딩을 살짝 줄여라.
- 사이드바 "세이프뷰 다시보기" 라벨은 사이드바 폭 대비 유독 길다 — 사이드바 각 페이지 상단에는 이미 "세이프뷰"/SAFEVIEW 브랜딩이 보이므로, 메뉴 라벨에서 "세이프뷰"를 빼고 "다시보기"만 쓰는 것도 고려하되, 이건 사용자에게 먼저 확인받거나 최소 침습적인 다른 방법(사이드바 폭을 약간 넓히기 등)을 먼저 시도하라.
- 사이드바 하단 푸터("SAFEVIEW · 세이프뷰")도 같은 원칙으로 줄바꿈 없이 한 줄에 들어가게 하라.

**범위 재확인**: 이번에도 CSS/문구 복원 중심이며, 위젯 종류·`core/*.py`·판정 로직·라우팅은 여전히 무변경 대상이다. 대시보드 문구 복원은 `pages/0_대시보드.py`의 표시 텍스트만 바꾸는 것이라 "현재 상태를 실제 파일 시스템 값으로 표시"하는 기존 수용 기준과 충돌하지 않는다.

**State를 `implementing`으로 유지. 완료 후 current.md의 구현/테스트 결과를 다시 채우고, 특히 이번엔 "사이드바 메뉴 글자가 흰색으로 또렷하게 보인다", "대시보드 5개 항목(개요/사용법/위험판단표/기술스택/시작전확인)이 전부 원문 그대로 보인다", "버튼·메뉴 텍스트가 한 줄로 안 깨진다"를 실제 렌더링 결과로 구체적으로 확인해 기록하라.**

### 4차 리뷰 — 사용자 3차 화면 확인 결과 반영 (2026-10-10, Claude)

3차 수정(사이드바 글자색·테두리, 대시보드 원문 복원, 버튼/사이드바 nowrap)은 반영됐다. 다만 사용자가 "모든 페이지의 RTSP 글자가 여전히 줄바뀜이 있다"고 확인해 **`approved` 판정을 다시 반려한다.**

**원인(확인 완료)**: `app.py`의 `[data-testid="stRadio"] div[role="radiogroup"] > label` 블록(영상 소스 선택 "📁 파일"/"📡 RTSP" 세그먼트 라디오를 스타일링하는 바로 그 블록, 2차 수정에서 추가됨)에는 `white-space: nowrap`이 빠져 있다. 3차 수정은 사이드바 메뉴(`stSidebarNavLink`)와 버튼(`stButton`/`stFormSubmitButton`)에만 `white-space: nowrap`을 추가했고, 이 라디오 블록은 손대지 않아 "RTSP" 라벨이 좁은 세그먼트 폭에서 계속 줄바꿈된다. `pages/1_모니터링.py`와 `pages/2_ROI_설정.py` 둘 다 이 전역 CSS를 공유하므로 "모든 페이지"에서 재현되는 것도 이 때문이다(실제로는 이 라디오가 쓰이는 두 페이지뿐이지만 둘 다 같은 증상).

**수정 방향**: `[data-testid="stRadio"] div[role="radiogroup"] > label`에 `white-space: nowrap`을 추가하라(버튼에 적용한 것과 동일한 방식). 라벨 안의 자식 요소(아이콘+텍스트를 감싸는 내부 span 등)에도 필요하면 같이 적용하라 — 버튼 수정 때 `[data-testid="stButton"] > button > *`에도 별도로 nowrap을 추가했던 것과 같은 이유로, 라디오도 `label` 자체뿐 아니라 그 자식에도 필요할 수 있다. 세그먼트 폭이 부족해 넘치면(사용자 요청대로 글자 크기는 유지) 좌우 패딩을 버튼 때처럼 살짝 줄이거나, 두 세그먼트("📁 파일"/"📡 RTSP")의 폭 비율이 아니라 전체 라디오 트랙의 최소 폭을 늘려라.

**수정 후 검증**: AppTest 렌더 트리 확인만으로는 이번 버그를 못 잡았다(2차 때도 못 잡았던 것과 같은 한계 — CSS가 실제로 한 줄에 들어맞는지는 레이아웃 계산이 필요해 AppTest의 예외 유무 체크로는 안 보인다). 이번엔 최소한 **"RTSP" 라벨 문자열 길이와 라디오 label의 padding/min-width 값을 계산해 한 줄 폭 안에 들어가는지"**를 정적으로 근거를 대거나(예: 폰트 크기·패딩·대략적인 문자폭 추정), 가능하면 실제 브라우저 스크린샷으로 확인하라. 코드 diff에 `white-space: nowrap`이 라디오 블록에 추가됐는지는 `git diff`로 기계적으로 확인 가능하니 테스트 결과에 반드시 포함하라.

**범위**: 이번에도 CSS 한 줄 추가 수준이며 `st.radio` 호출 자체(인자·위치)는 변경하지 않는다. `core/*.py`도 무변경 대상이다.

### 5차 리뷰 — 사용자 4차 확인 결과 반영 + 재발 방지 조치 (2026-10-10, Claude)

4차 수정(RTSP 라디오 줄바꿈)은 사용자가 확인했다. 이번 5차는 새 요청 1건과, 지금까지 4차례 반복된 "줄바꿈/글자 안 보임을 한 위젯에만 고치고 비슷한 다른 위젯에는 빠뜨리는" 패턴에 대한 재발 방지 조치를 함께 지시한다.

**1. 모니터링 페이지 "영상 소스 설정" 패널(사용자가 "서브 사이드바"라 부르는 흰 카드)의 좌측 여백 축소 요청**

현재 `.block-container`(`app.py` 약 56행)는 `padding-top`/`padding-bottom`/`max-width`만 지정하고 좌우 패딩은 Streamlit 기본값 그대로다. 그 결과 메인 네이비 사이드바 오른쪽과 "영상 소스 설정" 카드(`[data-testid="stColumn"]:has(.sv-source-panel-marker)`, `app.py` 약 144행) 왼쪽 사이에 Streamlit 기본 여백만큼 큰 공백이 남아있다.

사용자 요청: 이 공백을 좁혀서 카드를 좌측으로 더 넓게(더 왼쪽까지) 쓰도록 하되, 그 공백의 크기를 **메인 사이드바 안에서 이미 쓰고 있는 여백과 같은 리듬으로** 맞춰달라는 것이다 — 구체적으로 사이드바 메뉴 항목(`[data-testid="stSidebarNavLinkContainer"]`)이 사이드바 좌우 테두리에서 `margin: 3px 10px`(즉 10px)만큼 떨어져 있는 것과 같은 정도의 여유만 남기면 된다.

**수정 방향**: `.block-container`의 좌측 패딩(또는 메인 콘텐츠 영역 첫 컬럼의 좌측 여백)을 줄여서, 사이드바 오른쪽 테두리와 "영상 소스 설정" 카드 왼쪽 테두리 사이 간격이 대략 10px 전후가 되도록 맞춰라. 정확한 Streamlit 기본 패딩 값은 실행 중인 앱에서 직접 확인(AppTest 또는 렌더된 CSS)하고, 임의로 추측한 숫자를 넣지 마라. 이 변경이 다른 페이지(대시보드·ROI 설정 등)의 좌측 여백에도 똑같이 적용되는 게 자연스러운지 판단해서, 전역으로 통일하는 쪽을 권장하되 판단은 Codex에게 맡긴다. 모니터링 페이지의 다른 레이아웃 비율(컬럼 구성, 영상 카드 크기 등)은 건드리지 않는다.

**2. 재발 방지 — 유사 위젯군 CSS 통합**

지금까지 "텍스트 줄바꿈 금지(`white-space: nowrap`)"를 사이드바 메뉴 → 버튼 → 라디오 순서로 **한 번에 하나씩, 사용자가 실제로 발견할 때마다** 추가해왔다. 같은 종류의 문제를 매번 개별 선택자에 하나씩 패치하는 방식 자체가 "어딘가 빠뜨리는" 실수를 반복시킨다. `app.py`의 CSS에서 아래를 적용하라:

- 지금 `[data-testid="stSidebarNavLink"]`, `[data-testid="stSidebarNavLink"] > *`, `[data-testid="stButton"] > button`, `[data-testid="stFormSubmitButton"] > button`, `[data-testid="stButton"] > button > *`, `[data-testid="stFormSubmitButton"] > button > *`, `[data-testid="stRadio"] div[role="radiogroup"] > label`에 각각 따로 걸려있는 `white-space: nowrap` 선언들을, **하나의 공통 규칙**으로 묶어라. 예: `[data-testid="stSidebarNavLink"], [data-testid="stSidebarNavLink"] *, [data-testid="stButton"] button, [data-testid="stButton"] button *, [data-testid="stFormSubmitButton"] button, [data-testid="stFormSubmitButton"] button *, [data-testid="stRadio"] div[role="radiogroup"] > label, [data-testid="stRadio"] div[role="radiogroup"] > label * { white-space: nowrap; }` 같은 형태(선택자 목록은 Codex가 실제 구조에 맞게 정리) — 기존 개별 규칙에 중복으로 들어있던 `white-space: nowrap` 선언은 지워도 되고 남겨둬도 된다(중복 자체는 문제가 아니다), 핵심은 **앞으로 비슷한 라벨 텍스트를 갖는 새 위젯이 추가돼도 이 공통 규칙 목록에 선택자 하나만 추가하면 되도록** 한곳에 모아두는 것이다.
- 코드에 이 공통 규칙 바로 위에 "텍스트 줄바꿈이 없어야 하는 라벨형 위젯을 새로 추가하면 여기 선택자 목록에도 추가할 것"이라는 한국어 주석을 남겨라.

**범위**: 1번은 레이아웃 CSS(패딩/마진) 조정, 2번은 기존 CSS 선언들을 재배치하는 리팩터일 뿐 새 동작을 추가하지 않는다. 위젯 종류·`core/*.py`·판정 로직·라우팅은 여전히 무변경 대상이다.

### 6차 리뷰 — 사용자 5차 확인 결과 반영 (2026-10-10, Claude)

5차 수정(10px 좌측 여백, nowrap 통합)은 반영됐다. 사용자가 실제 화면을 보고 2가지를 추가 요청했다.

**1. 좌측 여백이 너무 타이트함 — 조금 더 넓혀라**

`app.py`의 `.block-container:has(.sv-source-panel-marker) { padding-left: 10px !important; }`(5차에서 추가)이 사용자 체감상 너무 빡빡하다. 10px보다 확실히 넉넉하게, 대략 **18~24px** 범위에서 Codex가 다른 카드 내부 여백(`[data-testid="stColumn"]:has(.sv-source-panel-marker)`의 `padding: 1rem` = 16px, 대시보드 카드 간격 등)과 비교해 자연스러운 값을 골라 적용하라. 정확히 10px이어야 한다는 전제가 틀렸던 것이니, 이번엔 "사이드바 메뉴 여백과 완전히 동일"보다 "비슷한 리듬이되 답답하지 않은 정도"를 기준으로 삼아라.

**2. 모니터링 페이지 "영상 소스 설정" 패널 안의 "시스템 상태" 섹션 — FPS만 남기고, 패널 맨 아래로 이동**

`pages/1_모니터링.py` 약 587~610행의 "시스템 상태" 블록(`st.markdown("### 시스템 상태")`부터 시작, ROI 로드됨/미설정 메시지 + FPS/프레임 표시)을 아래와 같이 바꿔라:

- 표시 내용을 **FPS 한 줄만** 남긴다. ROI 로드됨/미설정 `st.success`/`st.warning`/`st.caption` 메시지와 "프레임" 카운트 표시는 더 이상 렌더링하지 않는다(완전히 숨긴다 — 삭제해도 되고 조건부로 렌더링을 끄는 방식이어도 된다). `fps_ph`/`frame_ph_count`/`infer_ph` placeholder와 `st.session_state["__fps_ph"]` 등 세션 상태 연동 로직은 FPS 갱신에 필요한 부분만 남기고, 더 이상 안 쓰는 `frame_ph_count`/`infer_ph` 관련 placeholder 생성·세션 저장은 정리해도 된다(단, 실시간 루프 쪽에서 `st.session_state["__fps_ph"]` 등을 참조하는 다른 코드가 있다면 깨지지 않는지 확인할 것 — grep으로 `__fps_ph`/`__frame_ph_count`/`__infer_ph` 참조처를 전부 찾아서 정리 범위를 판단하라).
- 이 "시스템 상태"(FPS만 남은 버전) 블록을 **"영상 소스 설정" 패널(`settings_col`) 안에서 가장 마지막 요소**로 옮겨라 — 현재는 "야간 밝기 보정" 라디오(`enhance_mode`, 약 616행)보다 위에 있는데, 이 라디오 아래로 이동시켜서 패널 맨 아래에 오도록 한다. "야간 밝기 보정" 라디오 자체의 위치·동작은 바뀌지 않고, 단지 그보다 아래로 내려갈 뿐이다.
- ROI 로드 여부에 따라 내부적으로 분기하던 `roi_polygon = load_roi(source_label) if source_label else None` 계산 자체(판정 로직에 쓰이는 값)는 다른 곳에서 더 안 쓰이는지 확인한 뒤에만 지워라 — 화면 표시만 숨기는 것이지, 이 값이 실제 위험 판정이나 다른 로직에 쓰이고 있다면 계산은 유지하고 화면 출력만 생략해야 한다.

**범위**: 둘 다 레이아웃/표시 내용 조정이며 위젯 종류·`core/*.py`·판정 로직(화면에 안 보여도 내부 계산이 필요하면 유지)·라우팅은 변경하지 않는다.

### 7차 리뷰 — 사용자 6차 확인 결과 반영 (2026-10-10, Claude)

6차 수정(여백 20px, 시스템 상태 FPS만+패널 맨 아래 이동)은 사용자가 확인했다. 이번 요청은 사이드바 브랜드 문구 위치다.

**요청**: 메인 사이드바 맨 아래에 있는 "SAFEVIEW · 세이프뷰" 문구를, 맨 위 로고 이미지 바로 아래로 옮겨달라(로고 이미지와 자연스럽게 붙어 보이도록).

**원인(확인 완료)**: `app.py`에 아래 두 규칙이 있다:

```css
[data-testid="stSidebar"] > div:first-child::before {
    content: "";
    /* 로고 이미지 배경 */
}
[data-testid="stSidebar"] > div:first-child::after {
    content: "SAFEVIEW  ·  세이프뷰";
    /* 브랜드 문구 */
}
```

같은 요소(`div:first-child`)의 `::before`는 그 요소 콘텐츠의 **맨 앞**에, `::after`는 콘텐츠의 **맨 끝**에 렌더링된다. `div:first-child` 안에는 로고(`::before`) 다음에 실제 내비게이션 메뉴 전체(`[data-testid="stSidebarNav"]` 등)가 자식으로 들어있으므로, `::after`는 그 메뉴 전체보다 더 뒤, 즉 사이드바 맨 아래에 나타난다. 지금 로고(위)와 문구(아래)가 떨어져 있는 게 바로 이 구조 때문이다.

**수정 방향**: 브랜드 문구를 `div:first-child::after`에서 떼어내, **내비게이션 목록을 감싸는 컨테이너의 `::before`**로 옮겨라 — 즉 로고 바로 다음, 메뉴 목록 바로 앞에 오도록 `[data-testid="stSidebarNav"]::before`(또는 실제 내비게이션 컨테이너의 정확한 `data-testid` — 지금까지 선택자 추측이 여러 번 틀렸으니 이번에도 실제 렌더링된 DOM을 직접 확인해서 정확한 컨테이너를 찾아라) 같은 선택자에 `content: "SAFEVIEW  ·  세이프뷰"`와 기존 스타일(글자 크기, 굵기, 색상, 하단 테두리, `white-space: nowrap` 등)을 그대로 옮겨 적용하라. `div:first-child::after`는 제거한다(또는 빈 `content: ""`로 비워 더 이상 아무것도 그리지 않게 한다).

**확인**: 실제 렌더링에서 로고 이미지 → "SAFEVIEW · 세이프뷰" 문구 → 메뉴 목록 순서로 위에서부터 자연스럽게 이어지는지, 문구가 더 이상 사이드바 맨 아래에 나타나지 않는지 확인하고 테스트 결과에 기록하라.

**범위**: CSS 선택자/위치 조정만이며 `st.navigation`/`st.Page` 호출, 라우팅, `core/*.py`는 변경하지 않는다.

### 8차 리뷰 — 사용자 7차 확인 결과 반영 (2026-10-10, Claude)

7차 수정(로고 바로 아래로 문구 이동)은 위치상으로는 맞았지만, 사용자가 로고 이미지와 문구 사이 간격이 너무 크다고 확인했다.

**현재 값(참고)**: 로고(`[data-testid="stSidebar"] > div:first-child::before`)는 `margin: 18px auto 8px auto` — 아래쪽 8px. 문구(`[data-testid="stSidebarNav"]::before`)는 `margin-top` 지정이 없다(기본 0). 8px만으로는 "너무 크다"는 체감이 설명되지 않으므로, `[data-testid="stSidebarNav"]` 요소 자체(가상 요소가 아니라 실제 컨테이너)가 Streamlit 기본 `padding-top`/`margin-top`을 갖고 있어서 로고와 문구 사이에 추가 공백이 끼어 있을 가능성이 높다.

**수정 방향**: 추측으로 숫자만 줄이지 말고, 실제 렌더링된 `[data-testid="stSidebarNav"]`의 computed padding/margin을 확인(AppTest 또는 실행 중 앱에서)한 뒤 그 여백을 0에 가깝게 줄이고, 필요하면 로고의 `margin-bottom`(현재 8px)도 같이 줄여서 두 요소가 "로고+문구가 한 묶음"처럼 가깝게 붙어 보이게 하라. 너무 붙어서 답답해 보이지 않을 정도의 적당한 간격(대략 4~8px 선에서 Codex가 실제 화면을 보고 판단)은 남겨도 된다 — 완전히 0으로 붙이라는 요청은 아니다.

**범위**: 간격 CSS 값 조정뿐이며 로고/문구 내용·폰트·색상·위치 순서(로고→문구→메뉴)는 7차에서 확정된 대로 유지한다.

### 최종 종결 — 사용자 최종 확인 (2026-10-10, Claude)

8차 수정(사이드바 로고-문구 간격, `stSidebarHeader`/`stLogoSpacer` 숨김)까지 사용자가 실제 화면에서 확인했다. 총 8차례 반려·수정 사이클을 거쳤다:

1차 아이콘 리거처 깨짐(`[class*="st-"]` 전역 폰트 선택자) + 위젯 기본 스타일 미적용 → 2차 사이드바 메뉴 글자 안 보임(옛 멀티페이지 선택자 vs 실제 `st.navigation` 구조) + 대시보드 원문 유실 + 버튼 줄바꿈 → 3차 RTSP 라디오 라벨 줄바꿈 누락 → 4차 소스 패널 좌측 여백 요청(10px) → 5차 여백 재조정(20px) + 시스템 상태 FPS만 남기고 패널 맨 아래로 이동 → 6차 사이드바 로고 문구를 맨 아래에서 로고 바로 아래로 이동(`::after`→`::before` 구조 변경) → 7차 로고-문구 간격 축소. 매 단계 Claude가 코드를 직접 읽어 원인을 확인한 뒤 Codex에게 구체적 수정 방향을 지시했고, 재발 방지 차원에서 `white-space: nowrap`류 선언을 공통 선택자로 통합했다(`docs/RULES.md`에도 이 원칙을 반영할 예정).

최종 범위 확인: `core/detector.py`/`core/parked_detector.py`/`core/danger_logic.py`/`core/roi_manager.py`/`core/performance_eval.py` 전 라운드에서 단 한 줄도 변경되지 않았고(각 라운드 `git diff` 확인), `st.radio`/`st.selectbox`/`st.expander`/`st.text_input`/`st.file_uploader` 등 기존 위젯의 종류·인자·배치 순서도 전부 보존됐다(AST 비교로 매 라운드 재확인). 페이지 라우팅(`st.navigation`/`st.Page`)도 무변경.

**State를 `verified`로 확정하고 이 작업(UI/UX 디자인 통일 1단계)을 종료한다.** 다음 단계(2단계: `st.cache_resource` 공유 자원 구조 전환 + 공개 디스플레이 전용 페이지 신설)는 별도 계획으로 진행한다.
