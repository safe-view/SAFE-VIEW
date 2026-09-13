# 협업 및 변경 규칙

## 계획과 기록

- 실제 구현 전에 반드시 `docs/tasks/current.md`에 목표, 계획, 수용 기준, 예상 변경 파일을 작성한다.
- 구현 후 같은 문서에 수행한 테스트, 결과, 실제 변경 파일, 남은 위험을 기록한다.
- 계획이 달라지면 코드보다 먼저 또는 동시에 이유와 새 범위를 기록한다.

## 역할과 파일 소유권

- Claude는 Planner / Reviewer, Codex는 Builder / Tester를 기본 역할로 한다.
- 작업 시작 전에 각 수정 파일의 소유자를 `current.md`에 지정한다.
- 한 시점에 한 파일은 한 에이전트만 소유한다. 같은 파일을 동시에 수정하지 않는다.
- 소유권 인계 전 변경 상태와 다음 작업을 기록하고 상대가 인계를 확인한 뒤 수정한다.

## 변경 범위

- 기존 기능, 데이터 형식, 실행 방식과 사용자 흐름을 가능한 한 보존한다.
- 요청 해결에 필요한 최소 범위만 변경하고 관련 없는 포맷팅·정리·이름 변경을 섞지 않는다.
- 명시적 승인 없이는 대규모 리팩터링, 디렉터리 재구성, 프레임워크·모델·의존성 교체를 하지 않는다.
- `config.py`의 판정 임계값, 녹화 시간, 탐지 클래스 변경은 제품 동작 변경으로 취급해 계획에 명시한다.
- RTSP URL의 계정 정보, 개인 영상, 생성 이벤트, 로그 등 민감하거나 큰 런타임 데이터를 커밋하지 않는다.

## 검증

- 변경 파일과 직접 관련된 가장 작은 검증부터 수행하고, 가능하면 통합 실행까지 확인한다.
- 테스트를 실행하지 못했다면 성공으로 기록하지 말고 사유와 수동 확인 절차를 남긴다.
- 영상·RTSP·YOLO 검증은 장치, 모델, 코덱, 네트워크 조건을 결과에 함께 기록한다.
- 위험 판정 변경 시 최소한 정상, 사람만, 차량만, ROI 밖 동시 탐지, ROI 안 동시 탐지, 정지 차량 사례를 확인한다.

## 작업 상태(State)

`docs/tasks/current.md` 최상단 상태 필드는 다음 6개 값 중 하나로만 표기한다. 자동으로 전환을 검사·강제하는 도구는 두지 않으며, 각 담당자가 자기 단계를 마칠 때 값을 직접 갱신한다.

```
planned → implementing → implemented → reviewing → approved → verified
```

문제가 발견되면 `reviewing` / `approved` / `verified` 어느 단계에서도 `implementing`으로 되돌릴 수 있다.

### 상태별 의미

| 상태 | 의미 |
|---|---|
| `planned` | Claude가 목표·범위·계획·수용 기준·파일 소유권을 작성 완료. 코드 변경 없음. |
| `implementing` | Codex가 승인된 계획에 따라 소유한 파일을 실제로 수정하는 중. |
| `implemented` | Codex가 구현과 가능한 테스트를 마치고 결과를 `current.md`에 기록 완료. Reviewer 검토 대기. |
| `reviewing` | Claude가 diff와 `current.md`를 대조하며 검토 진행 중. |
| `approved` | Claude가 리뷰 기준(계획 범위 준수, 로직 보존, 회귀 없음 등)을 확인하고 통과. |
| `verified` | 사용자가 실제 화면·동작을 직접 확인하고 최종 확정. 작업 종료 지점. |

### 전환 주체

| 전환 | 주체 |
|---|---|
| (신규 작업) → `planned` | Claude |
| `planned` → `implementing` | Codex (아래 승인 규칙 적용) |
| `implementing` → `implemented` | Codex |
| `implemented` → `reviewing` | Claude |
| `reviewing` → `approved` | Claude (하네스 자동 호출 시 예외는 아래 "하네스 사용 시 Reviewer 권한" 참고) |
| `approved` → `verified` | 사용자만 |
| `reviewing` / `approved` / `verified` → `implementing` (반려) | 문제를 발견한 쪽 (Claude 또는 사용자) |

### `planned` → `implementing` 승인 규칙

이 전환에는 기본적으로 매번 사용자 승인이 필요하지 않다. 계획이 명확하고 이 문서의 다른 규칙(변경 범위, 파일 소유권 등)을 충족하는 일반적인 소규모 기능 추가·버그 수정은, Planner가 계획을 `current.md`에 작성 완료하면 Codex가 바로 `implementing`으로 넘어갈 수 있다.

다만 다음 중 하나에 해당하면 `implementing` 전환 전 반드시 사용자 승인을 받는다.

- 대규모 리팩터링
- 아키텍처/디렉터리 구조 변경
- 새 의존성 설치
- 데이터 형식 변경
- 프레임워크·모델 교체
- 프로젝트 방향 변경
- 민감정보 또는 외부 시스템에 영향을 주는 작업 (RTSP 계정정보, git push, 외부 서버 공개 등)

해당 여부가 애매하면 승인이 필요한 쪽으로 판단한다.

### `approved` → `verified` 승인 규칙

이 전환은 항상 사용자만 할 수 있다. Claude의 리뷰는 diff와 계획의 일치 여부를 확인하는 정적 검토이므로, 실제 화면·동작은 사용자가 직접 확인해야 작업이 최종 종료된다.

### 작업 시작 전 확인 순서

Claude와 Codex는 작업을 시작하기 전에 항상 다음 순서로 확인한다.

1. `AGENTS.md`
2. 자신의 역할 문서 — Claude는 `CLAUDE.md`. Codex는 별도 파일이 없으므로 `AGENTS.md`의 "Codex — Builder / Tester" 항목을 역할 문서로 삼는다(중복 문서로 인한 드리프트를 막기 위해 `CODEX.md`는 만들지 않는다).
3. `docs/RULES.md` (이 문서)
4. `docs/tasks/current.md`
5. `git status` / 필요한 `git diff` — 작업 트리가 `current.md`의 서술과 실제로 일치하는지 확인

### 핸드오프 고정 필드

`docs/tasks/current.md` 최상단에는 아래 3개 고정 필드를 둔다. Planner가 계획 작성 시 채우고, 이후 갱신하는 쪽이 매번 값을 최신화한다.

```
**State:** <6개 값 중 하나>
**기준 커밋:** <git rev-parse HEAD 값, 계획 작성 시점 기록>
**승인 필요:** 아니오 | 예 (사유: <RULES.md 예외 카테고리>) — 사용자 승인: 대기 / 완료 (일시)
**최종 갱신:** <담당자>, <타임스탬프>
```

- **기준 커밋**: Codex는 착수 전 현재 `HEAD`와 이 값을 비교한다. 다르면 계획이 그 사이의 변경을 반영하지 못했을 수 있으므로 착수하지 않고 보고한다.
- **승인 필요**: "예"이고 "사용자 승인"이 "완료"로 기록되기 전까지 Codex는 `implementing`으로 전환하지 않는다. 이 필드를 "완료"로 바꾸는 주체는 사용자의 승인 의사를 받은 쪽(주로 Claude)이며, **Codex는 스스로 이 필드를 완료 처리할 수 없다.**
- **최종 갱신**: 다른 에이전트는 자신이 마지막으로 읽은 값과 비교해, 값이 달라져 있으면 자신이 못 본 변경이 있었다고 보고 문서를 처음부터 다시 읽는다.

Planner가 계획을 작성할 때 `current.md`의 "구현 결과"/"테스트 결과" 섹션을 자유 서술 안내문이 아니라 아래처럼 **미리 빈칸이 있는 형태**로 작성해 둔다. Codex는 이 빈칸을 채우기만 하면 된다.

```
## 구현 결과
- 실제 변경 파일: (Codex 작성)
- 계획 대비 변경 요약: (Codex 작성)
- 계획 이탈 사항: (Codex 작성 — 없으면 "없음"이라고 명시할 것)
- 종료 시점 git 상태: (Codex 작성 — `git status --porcelain` 결과 붙여넣기)

## 테스트 결과
- 실행 명령/검증: (Codex 작성)
- 수용 기준 체크리스트: (아래 수용 기준을 그대로 복사해 각 항목 옆에 PASS/FAIL/미실행 표기)
  - [ ] <수용 기준 1>
  - [ ] <수용 기준 2>
- 미실행 항목과 사유: (Codex 작성)
```

`(Codex 작성)` placeholder가 그대로 남아 있거나 위 항목이 비어 있으면 위 "리뷰 0번째 항목"에 따라 반려된다.

### State별 행동 규칙

| State | Claude | Codex |
|---|---|---|
| (State 없음/새 요청) | 확인 순서대로 점검 후 계획 작성, `planned`로 설정 | 대기 |
| `planned` (승인 필요 아니오, 또는 승인 완료) | 대기 | 점검 후 착수, `implementing`으로 전환 |
| `planned` (승인 필요 예, 미완료) | 사용자에게 승인 요청, 대기 | 착수 금지, 대기 |
| `implementing` | 대기 | 계획된 파일만 구현 |
| `implemented` | 점검 후 검토 시작, `reviewing`으로 전환 | 대기 |
| `reviewing` | 검토 → 통과 시 `approved`, 문제 시 `implementing`으로 반려하고 수정 항목 기록 | 대기 |
| `approved` | 대기, 사용자 확인 요청 | 대기 |
| `verified` | 작업 종료. 새 요청 시 아래 "verified 이후 초기화" 절차 수행 | 대기 |

원칙: 자기 차례가 아닌 State를 보면 어떤 파일도 수정하지 않고 대기하거나 상태만 보고한다.

### 리뷰 0번째 항목: 핸드오프 형식 완전성

Claude(Reviewer)는 계획 범위 준수나 로직 보존 같은 실질 검토에 앞서, 가장 먼저 "구현 결과"/"테스트 결과"의 핸드오프 형식이 완전한지 확인한다 — 계획 이탈 사항, 종료 시점 git 상태, 수용 기준 체크리스트(`- [ ]` 형태) 중 하나라도 비어 있거나 `(Codex 작성)` 같은 placeholder가 그대로 남아 있으면, Reviewer가 그 자리를 대신 채우거나 diff로 대신 확인해주지 않는다. **형식 누락 자체를 반려 사유로 삼아** State를 `implementing`으로 되돌린다. Builder(Codex)의 기록 의무를 Reviewer가 대신 이행해주지 않기 위함이다.

### 하네스(자동 호출) 사용 시 Reviewer 권한

`tools/harness/run-next-step.ps1`을 통해 Claude를 비대화식으로 호출하는 경우, Claude는 다음 조건으로 실행된다.

- `--permission-mode plan` + 읽기 전용 `--allowedTools`(`Read`, `Grep`, `Glob`, 읽기 전용 git `Bash` 명령) — 어떤 파일도 직접 쓸 수 없다. `docs/tasks/current.md`도 포함한다.
- `--output-format json` + `--json-schema`(`tools/harness/review-schema.json`) — 자유 서술이 아니라 스키마에 맞는 구조화된 JSON 하나만 반환한다.

이 경우 `docs/tasks/current.md`의 `State` 줄 / `최종 갱신` 줄 / `## 리뷰 및 남은 위험` 섹션 세 곳을 실제로 갱신하는 것은 **Harness(스크립트)**다. Harness는 (1) JSON 파싱과 필수 필드 존재, (2) `base_commit_checked`가 `기준 커밋`·현재 `git rev-parse HEAD`와 모두 일치, (3) `rejected`이면 `rejection_reasons`가 비어 있지 않음을 모두 통과했을 때만 반영하며, 검증에 실패하면 State를 바꾸지 않고 수동 확인을 요청한다. 이는 "판단은 Claude, 쓰기 실행은 결정론적 스크립트"로 책임을 분리해 최소 권한을 지키기 위한 구조이며, 오케스트레이터가 `current.md`를 직접 수정하지 않는다는 원칙(위 "State별 행동 규칙" 참고)에 대한 명시적 예외다. 이 세 지점 외의 어떤 줄도 Harness는 쓰지 않는다.

**사용자가 대화로 직접 "현재 작업 리뷰해"라고 요청하는 경우에는 이 제한이 적용되지 않는다** — 지금까지처럼 Claude가 대화형 세션에서 직접 `current.md`를 읽고 갱신한다. 위 읽기 전용 제한과 Harness 예외는 사람 없이 Claude를 자동 호출할 때만 적용되는 자동화 전용 규칙이다.

### Stale State·불일치 감지

다음 중 하나라도 해당하면 발견한 쪽은 즉시 작업을 멈추고 무엇이 불일치하는지 보고한다.

1. `기준 커밋`이 현재 `git rev-parse HEAD`와 다르다.
2. `최종 갱신` 값이 자신이 마지막으로 확인했던 값과 다르다.
3. `git status`/`git diff` 결과가 `current.md`의 "예상 변경 파일" 또는 "구현 결과"에 없는 변경을 포함한다.
4. `State` 값이 정의된 6개 값 중 하나가 아니거나 필드가 비어 있거나 형식이 깨져 있다.
5. 이미 다른 에이전트가 진행 중인 파일을 소유권 확인 없이 건드리려 한다.

### `verified` 이후 초기화와 보관(Archive)

- `docs/tasks/current.md`는 항상 진행 중인 단일 작업만 담는다. 여러 작업의 이력을 이 파일 안에 누적하지 않는다.
- 작업이 `verified`로 종료되고 다음 작업을 시작할 때, Claude는 종료된 `current.md`의 전체 내용을 `docs/tasks/archive/YYYY-MM-DD-짧은슬러그.md`로 복사해 보관한 뒤 `current.md`를 표준 빈 템플릿(목표·범위·계획 등을 "없음"으로 둔 최초 형태)으로 초기화한다.
- 이 보관 절차는 2026-09-13 사용자 승인에 따라 **매번 재승인 없이 자동으로 수행한다.** `docs/tasks/archive/`에는 작업 기록만 두며 제품 코드나 실행 스크립트는 두지 않는다. 세부 규칙은 `docs/tasks/archive/README.md`를 따른다.
- 초기화 직후에는 State와 3개 고정 필드를 비우거나 "없음"으로 표시해, 이전 작업의 값이 새 작업에 남아 있지 않게 한다.
