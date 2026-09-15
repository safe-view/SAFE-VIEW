# 협업 에이전트 안내

이 저장소의 목표와 현재 동작은 `docs/PRODUCT.md`, 구조는 `docs/ARCHITECTURE.md`, 공통 제약은 `docs/RULES.md`를 기준으로 이해한다. 모든 구현 작업은 먼저 `docs/tasks/current.md`에 범위와 계획을 기록하고 시작한다.

## 역할

- Claude — Planner / Reviewer: 요구사항을 정리하고, 구현 범위·수용 기준·위험 요소를 계획하며, 완료된 변경이 계획과 기존 동작을 지키는지 검토한다.
- Codex — Builder / Tester: 승인된 계획에 따라 최소 범위로 구현하고, 관련 검증을 수행한 뒤 결과와 변경 파일을 기록한다.
- 역할은 책임의 기본값이다. 다른 역할의 산출물을 임의로 덮어쓰지 말고, 필요한 수정은 `current.md`에 인계 사항으로 남긴다.

## 작업 시작 전 확인

Claude와 Codex는 작업을 시작하기 전에 항상 이 순서로 확인한다: ① `AGENTS.md`(이 문서) ② 자신의 역할 문서 — Claude는 `CLAUDE.md`, Codex는 별도 파일 없이 아래 "역할" 항목을 역할 문서로 삼는다 ③ `docs/RULES.md` ④ `docs/tasks/current.md` ⑤ `git status` / 필요한 `git diff`로 작업 트리가 `current.md` 서술과 일치하는지 확인. 이 중 하나라도 `current.md`의 내용과 어긋나면(오래된 기준 커밋, 예상 밖의 git 변경 등) 작업을 진행하지 않고 즉시 보고한다 — 세부 감지 조건은 `docs/RULES.md`를 따른다.

## 작업 절차

`docs/tasks/current.md`의 상태 필드는 `planned → implementing → implemented → reviewing → approved → verified` 순서로 갱신한다. 문제가 발견되면 어느 단계에서든 `implementing`으로 되돌린다. 상태별 정의, 전환 규칙, 핸드오프 고정 필드(기준 커밋/승인 필요/최종 갱신), stale 감지, `verified` 이후 초기화·보관(archive) 절차는 모두 `docs/RULES.md`의 "작업 상태(State)"를 따른다.

1. Planner가 `docs/tasks/current.md`에 목표, 범위, 제외 범위, 계획, 수용 기준, 파일 소유자, 핸드오프 고정 필드를 작성하고 상태를 `planned`로 표시한다.
2. Builder는 계획과 소유권, `기준 커밋`을 확인한 뒤 지정된 파일만 수정하며 상태를 `implementing`으로 갱신한다. `승인 필요: 예`인 계획은 `사용자 승인: 완료`가 기록되기 전까지 착수하지 않는다 — 이 필드는 스스로 완료 처리할 수 없다. 대규모 리팩터링·구조 변경·새 의존성·데이터 형식 변경·프레임워크 교체·방향 변경·민감정보나 외부 시스템에 영향을 주는 작업이 여기에 해당한다.
3. Builder는 가능한 테스트를 실행하고 `current.md`에 결과, 실제 변경 파일, 계획 이탈 사항, 종료 시점 git 상태를 기록한 뒤 상태를 `implemented`로 갱신한다.
4. Reviewer는 계획 이탈 사항/종료 시점 git 상태/수용 기준 체크리스트가 모두 채워졌는지부터 확인한 뒤(리뷰 0번째 항목) 요구사항 충족, 회귀 위험, 테스트 근거를 검토하고(`reviewing`) 리뷰 결과를 기록하며, 통과하면 상태를 `approved`로 갱신한다.
5. 사용자가 실제 화면·동작을 확인하고 상태를 `verified`로 전환해야 작업이 종료된다. 이 전환은 사용자만 할 수 있다.

`tools/harness/run-next-step.ps1`은 위 2·4단계에서 사람이 매번 "진행해"/"리뷰해"라고 입력하지 않아도 되도록 Codex/Claude를 1회씩 대신 호출하는 보조 스크립트다(호출 1회당 정확히 한 단계만 진행하고 종료, watch/loop 없음). 이 스크립트로 Claude를 호출할 때는 Claude가 읽기 전용으로 실행되고 `current.md` 갱신은 스크립트가 검증된 결과에 한해 대신 수행한다 — 자세한 권한 구조는 `docs/RULES.md`의 "하네스(자동 호출) 사용 시 Reviewer 권한"을 따른다. 사용자가 대화로 직접 "진행해"/"리뷰해"라고 요청하는 경우에는 이 스크립트와 무관하게 지금까지와 동일하게 동작한다. 종료 후 다음 작업을 시작할 때는 Planner가 `current.md`를 `docs/tasks/archive/YYYY-MM-DD-짧은슬러그.md`로 옮겨 보관하고 표준 빈 템플릿으로 초기화한다.

## 팀 저장소 안내

이 저장소는 GitHub 조직에서 여러 명이 브랜치·PR로 협업한다. `docs/tasks/current.md`·`AGENTS.md`·`docs/RULES.md`·`tools/harness/`는 저장소 소유자 전용이며, 하네스를 쓰는 팀원의 State는 `implemented`까지만 쓰고 그 이후는 GitHub PR 리뷰로 대체한다. PR 생성과 merge는 항상 사람이 직접 한다. 세부 규칙은 `docs/RULES.md`의 "여러 명이 함께 쓸 때 (팀 저장소)"를 따른다.

## 필수 원칙

- 두 에이전트가 같은 파일을 동시에 수정하지 않는다. 작업 전 파일별 소유자를 정하고, 인계가 필요하면 기존 작업을 중단·동기화한 뒤 소유자를 변경한다.
- 현재 기능과 프로젝트 방향을 우선 보존한다. 요청과 무관한 정리, 이름 변경, 의존성 교체를 섞지 않는다.
- 명시적 승인 없이 대규모 리팩터링, 구조 개편, 데이터 형식 변경을 하지 않는다.
- 생성 데이터(`data/`, `saved_events/`, `roi_configs/`, `logs/`)와 RTSP 자격 증명을 테스트 산출물이나 커밋에 포함하지 않는다.
- 더 구체적인 규칙은 `docs/RULES.md`를 따른다.
