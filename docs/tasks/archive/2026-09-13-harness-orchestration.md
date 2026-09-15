# 현재 작업

## 상태

**State:** `verified`
**기준 커밋:** `8300a45952521f5cfc33bc93e1eaa163e48eab2c`
**승인 필요:** 예 (사유: 신규 도구 체계 도입 — `tools/harness/` 오케스트레이션 스크립트, `.vscode/tasks.json` 신설은 저장소 구조 변경에 해당) — 사용자 승인: 완료 (이번 대화에서 방향·세부 요구사항을 사용자가 직접 지정함)
**최종 갱신:** 사용자, 2026-09-13T07:25:55Z (verified 확정 — 하네스 첫 실전 E2E 테스트로 넘어가며 확정)

하네스 4단계(경량 오케스트레이션) 정식 구현 계획. 이번에는 계획만 기록하며, PowerShell 스크립트·VS Code Task·제품 코드는 아직 만들지 않는다.

> **CLI 블로커 해소됨(2026-09-13)**: 사용자가 `codex-cli 0.154.0`으로 실제 비대화식 실행(`codex exec`)을 직접 시험해 확인했다. 아래 3-0에 확정된 호출 형식을 반영했다. 새로 발견된 두 가지 후속 과제(Windows 콘솔 한글 깨짐, 자동 호출 시 문서 읽기 범위로 인한 토큰 낭비)도 함께 설계에 반영했다.

> **권한 구조 개정(2026-09-13)**: Claude CLI help 재확인 결과, Edit 권한을 current.md 한 파일로만 제한하는 명확한 수단이 없어 `--permission-mode acceptEdits` 대신 **`--permission-mode plan` + 읽기 전용 `--allowedTools`**로 Reviewer를 완전 읽기 전용으로 바꿨다. 대신 Harness(스크립트)가 검증된 Claude JSON 리뷰 결과에 한해 State/리뷰 섹션만 제한적으로 쓰도록 3-5를 신설했다 — 이는 하네스 3단계에서 정한 "오케스트레이터는 State를 직접 수정하지 않는다"는 원칙의 명시적 예외다(3-4 항목 5 참고).

## 1. 목표

사용자가 매 단계 전환마다 "현재 작업 진행해"/"현재 작업 리뷰해"를 직접 타이핑하는 과정을 줄이기 위해, `docs/tasks/current.md`의 State를 읽고 **호출 1회당 정확히 한 단계만** 다음 에이전트를 실행하는 경량 PowerShell 오케스트레이션 스크립트를 도입한다. VS Code Task는 이 스크립트를 편하게 실행하는 진입점으로 추가한다. 완전 자동 루프, Claude/Codex 강결합 wrapper는 만들지 않는다.

## 2. 현재 상태 (CLI 확인 결과 — 추측 없이 직접 확인함)

- **Claude Code CLI**: 설치 확인됨. `claude --version` → `2.1.153 (Claude Code)`. `claude --help` 확인 결과 **`-p`/`--print` 플래그로 비대화식 실행이 공식 지원됨**. 이 외에 이번 설계에 쓰는 관련 플래그: `--permission-mode`(acceptEdits 등), `--output-format`(text/json/stream-json), `--no-session-persistence`(print 전용, 세션을 디스크에 남기지 않음), `--max-budget-usd`(API 비용 상한, print 전용), `--allowedTools`/`--disallowedTools`(도구 접근 제한). `-c`/`--continue` 플래그도 존재하나 자동 호출에는 사용하지 않는다(매 호출은 새 세션으로 독립 실행).
- **Codex CLI**: 사용자가 직접 확인 완료. `codex-cli 0.154.0`, ChatGPT 로그인 정상, 기본 모델 `gpt-5.6-sol`. `codex exec "<prompt>"`로 비대화식 실행 가능. `-C <경로>`로 작업 루트 지정 가능. `-s read-only`/`-s workspace-write`로 샌드박스 모드 지정 가능. `--ephemeral`로 세션 기록을 남기지 않고 실행 가능. **`-a`(승인 모드)는 `exec` 뒤가 아니라 최상위 `codex` 옵션이라 `codex -a never exec ...` 형태여야 한다** — 이 순서를 지키지 않으면 동작하지 않는다. `-a never` + `-s read-only` 조합으로 실제 read-only 실행이 정상 동작함을 사용자가 확인했다.
- **후속 확인 필요 사항 2가지 (2026-09-13 사용자 보고)**:
  1. Windows PowerShell 콘솔에서 한글 출력이 깨져 보임 — 오케스트레이터는 콘솔에 직접 텍스트를 출력/캡처하지 않고, 자식 프로세스 출력을 파일로 리다이렉트한 뒤 UTF-8로 다시 읽어 처리한다 (3-0-3 참고).
  2. 단순 read-only 확인에도 Codex가 `AGENTS.md`/`docs/RULES.md`/`docs/tasks/current.md`를 모두 읽으며 토큰 사용량이 컸다 — 자동 호출 프롬프트는 "current.md가 이미 규칙을 요약해 담고 있다"는 전제를 명시해 불필요한 재탐색을 줄인다 (3-0-4 참고).
- `docs/tasks/current.md` 표준 템플릿(하네스 2·3단계에서 확정)에는 아직 "구현 결과"/"테스트 결과" 섹션에 필수 필드가 미리 채워진 빈칸(placeholder) 형태가 아니라 자유 서술 안내문만 있다 — 이번 A안 적용 대상.
- `docs/RULES.md`의 "작업 상태(State)" 섹션에는 아직 "핸드오프 형식 완전성"을 리뷰의 반려 사유로 명시한 조항이 없다 — 이번 B안 적용 대상.

## 3. 구현 계획

### 3-0. CLI 호출 형식 확정 (사전 확인 완료)

**3-0-1. Codex 호출 형식 (`implementing` 단계, State가 `planned`일 때)**

```
codex -a never -C "<repo-root>" exec -s workspace-write --ephemeral "<고정 프롬프트>"
```

- `-a never`: 승인 프롬프트 없이 완전 비대화식 실행 (최상위 옵션, `exec` 앞에 위치 — 사용자가 확인한 필수 순서).
- `-C "<repo-root>"`: 항상 저장소 루트 절대경로를 명시 (실행 위치에 의존하지 않음).
- `exec -s workspace-write`: 파일 쓰기가 필요한 구현 단계이므로 `workspace-write` 샌드박스 사용. (읽기 전용 점검이 필요한 경우에만 `-s read-only`로 교체.)
- `--ephemeral`: 세션 기록을 남기지 않아 다음 호출에 이전 대화가 누적되지 않음 — 자동 호출이 반복돼도 컨텍스트/토큰이 쌓이지 않게 하는 핵심 장치.
- **남은 1가지 확인 사항**: `-s`와 `--ephemeral`이 `exec`의 하위 옵션인지 최상위 옵션인지는 이번 사용자 테스트에서 `-a`만큼 명시적으로 확인되지 않았다. 스크립트 작성 직전에 `codex --help`와 `codex exec --help`를 한 번 더 읽어 정확한 위치를 최종 고정한다(추측 금지 원칙 유지). 이 확인도 읽기 전용이라 별도 승인 없이 진행 가능하다.

**3-0-2. Claude 호출 형식 (`reviewing` 단계, State가 `implemented`이고 3-3 C안 형식 검사를 통과했을 때) — 2026-09-13 개정: 읽기 전용으로 변경**

```
claude -p --permission-mode plan --allowedTools "Read,Grep,Glob,Bash(git status:*),Bash(git diff:*),Bash(git rev-parse:*),Bash(git log:*)" --output-format json --json-schema "<3-0-7의 스키마>" --no-session-persistence "<고정 프롬프트>"
```

- `--permission-mode plan`: Claude가 파일을 수정하는 도구(Edit/Write 등)를 실행할 수 없는 모드. Reviewer는 이제 **어떤 파일도 직접 쓰지 않는다** — `docs/tasks/current.md`도 포함.
- `--allowedTools "Read,Grep,Glob,Bash(git status:*),Bash(git diff:*),Bash(git rev-parse:*),Bash(git log:*)"`: `plan` 모드로 이미 쓰기가 막히지만, 방어적으로 도구 목록 자체도 읽기 전용으로 좁힌다. Edit/Write는 목록에 없으므로 애초에 호출 대상이 아니다.
- `--output-format json` + `--json-schema`: 리뷰 결과를 자유 서술이 아니라 3-0-7에 정의한 스키마에 맞는 구조화된 JSON 하나로만 반환하게 한다. Harness가 이 JSON을 파싱해 검증한 뒤에만 State/리뷰 섹션에 반영한다(3-5 참고).
- `--no-session-persistence`: 세션을 디스크에 남기지 않음. 매 호출은 새 세션이며 `--resume`/`--continue`는 쓰지 않는다.
- `--json-schema`가 인라인 JSON 문자열과 파일 경로 중 무엇을 받는지는 `--help` 예시(인라인 JSON 객체)만 확인됐다 — 스크립트 작성 시 실제 호출 1회로 최종 확인한다.
- (이전 초안의 `--permission-mode acceptEdits`는 폐기한다 — Edit 권한을 current.md 한 파일로만 제한하는 CLI 수단이 명확하지 않아, 쓰기 권한 자체를 주지 않는 이 방식으로 대체한다.)

**3-0-3. UTF-8 처리 방식 (Windows PowerShell 한글 깨짐 대응)**

콘솔 인코딩에 의존하지 않도록, 스크립트는 **자식 프로세스의 표준 출력/에러를 콘솔로 바로 받지 않고 임시 파일로 리다이렉트한 뒤 UTF-8로 다시 읽는다.**

```
$proc = Start-Process -FilePath $exe -ArgumentList $args `
    -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile `
    -NoNewWindow -PassThru
$proc | Wait-Process -Timeout $timeoutSec -ErrorAction SilentlyContinue
if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force; <timeout 처리> }
$stdout = Get-Content -Raw -Encoding UTF8 -Path $stdoutFile
```

- `docs/tasks/current.md`를 스크립트가 파싱용으로 읽을 때도 `Get-Content -Raw -Encoding UTF8`을 명시적으로 사용한다(BOM 없는 UTF-8을 시스템 기본 코드페이지로 오인하는 PowerShell 5.1의 알려진 문제 회피).
- 스크립트 자신이 사람에게 보여줄 메시지를 콘솔에 출력할 때만 `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`을 스크립트 시작부에 설정한다. 이것으로도 터미널 폰트/코드페이지에 따라 완전히 해결 안 될 수 있음을 감안해, **중요 정보(성공/실패/timeout 여부, 남은 위험)는 영어 키워드 + 최소한의 한글로 이중 표기**해 콘솔 깨짐과 무관하게 상태를 판별할 수 있게 한다(예: `[OK] implemented`, `[FAIL] timeout`).

**3-0-4. 자동 호출 문서 읽기 범위 최소화 (토큰 낭비 방지)**

- 고정 프롬프트에 다음을 명시해 재탐색을 줄인다: "`docs/tasks/current.md`에 이번 작업에 필요한 계획·규칙 요약이 이미 들어 있다. `AGENTS.md`/`docs/RULES.md`의 규칙은 이미 계획에 반영되어 있으니 처음부터 다시 해석하지 말고 `current.md`와 `git diff`를 우선 근거로 삼아라. `docs/PRODUCT.md`/`docs/ARCHITECTURE.md`는 계획에 없는 제품 배경지식이 꼭 필요할 때만 읽어라."
- 이 지침은 하네스 3단계에서 정한 "작업 시작 전 확인 순서"(`AGENTS.md`→역할 문서→`RULES.md`→`current.md`→git) 자체를 없애지 않는다 — 사람이 직접 대화로 지시하는 수동 실행에는 그대로 적용된다. 다만 **자동 호출 1회는 좁고 반복적인 단일 작업**이므로, Planner(Claude)가 계획을 작성할 때 `current.md` 안에 그 작업에 필요한 규칙 요약을 이미 충분히 담아 자기완결적으로 만드는 것을 계획 작성 원칙으로 삼는다(이번에도 지금까지 그렇게 작성해왔음).
- Codex 쪽에 별도의 비용/토큰 상한 플래그가 있는지는 이번 사용자 테스트에서 확인되지 않았다 — 다음 구현 단계에서 `codex --help`로 함께 확인한다(있으면 3-0-1 명령에 추가).

**3-0-5. timeout 기본값**

- 두 호출 모두 기본 timeout **1200초(20분)**로 통일한다(구현 난이도를 낮추기 위해 단일 값 사용 — "가능한 한 단순한 구조" 원칙). timeout 도달 시 프로세스를 강제 종료하고 `[FAIL] timeout`으로 보고하며 다음 단계로 진행하지 않는다.
- 실사용 중 특정 작업이 반복적으로 timeout에 걸리면, 그때 스크립트 상단의 변수(`$TimeoutSec`) 하나만 조정하는 것으로 대응한다(개별 호출마다 다른 값을 주는 구조는 이번 단계에서 만들지 않는다).

**3-0-6. lock 파일 경로**

- 저장소 안에는 아무 것도 만들지 않는다. lock 파일은 시스템 임시 폴더에 둔다: `Join-Path $env:TEMP 'blind_spot_safety_harness.lock'` (예: `C:\Users\김영민\AppData\Local\Temp\blind_spot_safety_harness.lock`). 이렇게 하면 `.gitignore` 수정이나 저장소 내 별도 디렉터리가 필요 없다.
- lock 파일 내용: 실행 중인 PowerShell 프로세스 PID와 시작 시각.
- 두 번째 실행이 lock을 발견하면, 그 PID가 실제로 살아있는지(`Get-Process -Id <pid> -ErrorAction SilentlyContinue`) 확인해 참고 메시지에 포함하되(예: "PID 1234가 이미 존재하지 않아 stale로 보입니다"), **자동으로 지우지는 않는다** — 사용자가 확인 후 수동으로 지워야 한다(요구사항의 "자동 재시도/자동 정리 금지" 원칙 준수).
- CLI 호출의 stdout/stderr 임시 파일도 저장소 밖 `$env:TEMP`에 만든다. 성공 시 삭제하고, 실패/timeout 시에는 남겨두고 경로를 메시지에 출력해 사람이 직접 열어볼 수 있게 한다.

**3-0-7. Claude 리뷰 결과 JSON Schema (초안)**

`tools/harness/review-schema.json`(가칭)로 저장소에 둔다(제품 코드 아님, 스크립트와 같은 위치).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "additionalProperties": false,
  "required": ["verdict", "base_commit_checked", "scope_ok", "acceptance_criteria", "summary"],
  "properties": {
    "verdict": {
      "type": "string",
      "enum": ["approved", "rejected"],
      "description": "리뷰 최종 판단. approved면 State를 approved로, rejected면 implementing으로 되돌린다."
    },
    "base_commit_checked": {
      "type": "string",
      "description": "리뷰 시점에 확인한 git rev-parse HEAD 값 (Harness가 current.md의 기준 커밋과 대조)"
    },
    "scope_ok": {
      "type": "boolean",
      "description": "계획한 예상 변경 파일 범위만 변경됐는지 (git diff --stat 기준)"
    },
    "acceptance_criteria": {
      "type": "array",
      "description": "계획의 수용 기준 각 항목에 대한 판정",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["criterion", "result"],
        "properties": {
          "criterion": { "type": "string" },
          "result": { "type": "string", "enum": ["pass", "fail", "not_run"] }
        }
      }
    },
    "rejection_reasons": {
      "type": "array",
      "items": { "type": "string" },
      "description": "verdict가 rejected일 때 구체적 반려 사유 목록 (형식 누락 포함)"
    },
    "risks_or_followups": {
      "type": "array",
      "items": { "type": "string" },
      "description": "승인하더라도 남는 위험이나 사용자가 verified 전 확인해야 할 사항"
    },
    "summary": {
      "type": "string",
      "description": "1~3문장 리뷰 요약. current.md의 '리뷰 및 남은 위험' 섹션에 그대로 기록된다."
    }
  },
  "if": { "properties": { "verdict": { "const": "rejected" } } },
  "then": { "required": ["rejection_reasons"], "properties": { "rejection_reasons": { "type": "array", "minItems": 1 } } }
}
```

- `verdict`/`base_commit_checked`/`scope_ok`/`acceptance_criteria`/`summary`는 항상 필수. `rejected`일 때만 `rejection_reasons`가 최소 1개 이상 필수(스키마의 `if/then`으로 강제).
- 필드 수를 의도적으로 적게 유지했다(토큰 낭비 방지 원칙과 동일한 이유 — 스키마가 크고 복잡할수록 Claude가 채워야 할 출력도 커진다).
- 이 스키마는 초안이며, 실제 첫 호출 결과를 보고 다음 구현 단계에서 최종 조정한다.

### 3-1. 기본 구조

- `tools/harness/`(가칭) 아래에 PowerShell 스크립트(예: `run-next-step.ps1`)를 둔다. 제품 코드(`app.py`, `pages/`, `core/`, `config.py`)와 완전히 분리된 위치.
- `.vscode/tasks.json`에 이 스크립트를 실행하는 Task 1개(예: "Harness: Run Next Step")를 추가한다. Task는 스크립트를 감싸는 진입점일 뿐, 별도 로직을 갖지 않는다.
- 스크립트는 실행될 때마다 다음을 수행하고 **즉시 종료**한다(반복/watch 없음):
  1. lock 파일 확인 (요구사항 1)
  2. `docs/tasks/current.md` 파싱 (`State`/`기준 커밋`/`승인 필요`/`사용자 승인`)
  3. `git rev-parse HEAD`와 `기준 커밋` 비교 — 다르면 stale로 보고 종료
  4. State에 따라 Claude 또는 Codex를 **최대 1회** 호출하거나, 호출 대상이 없으면 상태만 출력하고 종료
  5. 호출한 CLI의 종료 코드/timeout 여부 확인 후 결과 보고

### 3-2. State별 분기 (스크립트가 판단만 하고, State 자체는 건드리지 않음)

| State | 승인 필요/완료 여부 | 스크립트 동작 |
|---|---|---|
| `planned` | 승인 필요 아니오, 또는 승인 완료 | Codex를 1회 호출(고정 프롬프트: "docs/tasks/current.md를 읽고 계획대로 구현을 진행해") |
| `planned` | 승인 필요 예, 미완료 | 아무 것도 호출하지 않고 "사용자 승인 필요" 출력 후 종료 |
| `implemented` | — | **3-3의 C(최소 형식 검사) 통과 시에만** Claude를 읽기 전용으로 1회 호출(고정 프롬프트: "현재 작업을 리뷰해") → 응답 JSON을 3-5 절차로 검증 후 Harness가 State/리뷰 섹션 갱신 |
| `implemented` (형식 검사 실패) | — | Claude를 호출하지 않고 "핸드오프 형식 미완성 — Codex 재작업 필요" 출력 후 종료 |
| `implementing`/`reviewing`/`approved`/`verified`/없음 | — | 아무 것도 호출하지 않고 "지금은 자동 실행할 단계 아님" 출력 후 종료 |

### 3-3. 핸드오프 형식 강제 (A + B + C)

- **A. 템플릿 선채움**: `docs/tasks/current.md`의 표준 템플릿(구현 결과/테스트 결과 섹션)을 자유 서술 안내문 대신, 아래처럼 **미리 빈칸이 있는 형태**로 바꾼다. Planner가 계획 작성 시 이 형태 그대로 남겨두면 Codex는 자유 서술이 아니라 빈칸 채우기를 하게 된다.
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
- **B. 리뷰 반려 규칙**: `docs/RULES.md`의 리뷰 관련 조항에 "리뷰의 0번째 항목 = 핸드오프 형식 완전성 확인"을 추가한다. "계획 이탈 사항", "종료 시점 git 상태", 수용 기준 체크리스트(`- [ ]` 형태) 중 하나라도 비어 있거나 placeholder 문구(`(Codex 작성)`)가 그대로 남아 있으면, Claude는 diff를 대신 확인해주지 않고 **형식 누락 자체를 반려 사유**로 기록하며 State를 `implementing`으로 되돌린다.
- **C. 오케스트레이터 최소 형식 검사**: 스크립트가 `implemented` 상태에서 Claude를 호출하기 전에, "계획 이탈 사항"/"종료 시점 git 상태" 문자열과 `- [ ]` 패턴이 문서에 존재하는지 단순 문자열 검사를 한다. 없거나 `(Codex 작성)` placeholder가 남아 있으면 Claude를 호출하지 않고 종료한다. 완벽한 내용 검증이 아니라 "명백히 비어있는 경우"만 걸러내는 용도임을 명시한다.

### 3-4. 추가 안전장치 (요구사항 1~6)

1. **중복 실행 방지**: 스크립트 시작 시 3-0-6에서 확정한 `$env:TEMP` 아래 lock 파일(`blind_spot_safety_harness.lock`)을 생성 시도한다. 이미 존재하면(이전 실행이 아직 끝나지 않음) 두 번째 실행은 **어떤 에이전트도 호출하지 않고** "이미 실행 중" 메시지만 출력하고 종료한다. 스크립트 정상/비정상 종료 시 lock을 해제한다(비정상 종료 대비 stale lock은 PID 생존 여부만 안내하고 자동 삭제하지 않음).
2. **실제 CLI 확인**: 3-0에서 확정한 대로, 추측 명령을 쓰지 않고 실제 `--help`/`--version` 확인 결과만 사용한다. Codex/Claude 모두 확인 완료(3-0-1, 3-0-2) — 다만 3-0-1의 "남은 1가지 확인 사항"(`-s`/`--ephemeral` 위치)은 스크립트 작성 직전에 마지막으로 재확인한다.
3. **실패 처리**: 호출한 CLI의 종료 코드가 0이 아니면 State를 변경하지 않고(스크립트는 애초에 State를 쓰지 않음) "실패" 메시지와 함께 종료. `implementing`/`reviewing` 도중 실패가 관찰되면 복구 방법을 안내하는 문구만 출력하고(예: "current.md를 확인하고 필요 시 Claude/Codex에게 직접 상황을 알려주세요") 자동 재시도·자동 롤백은 절대 하지 않는다.
4. **timeout**: 3-0-5에서 확정한 대로 두 호출 모두 기본 1200초(20분)를 적용하고, 초과 시 프로세스를 종료하고 "timeout으로 실패 처리"하며 다음 단계를 진행하지 않는다.
5. **오케스트레이터 권한 제한 (2026-09-13 개정)**: 스크립트는 원칙적으로 `docs/tasks/current.md`를 직접 수정하지 않는다. **단, 3-5에서 정의한 절차에 따라 검증된 Claude 리뷰 JSON 결과를 반영해 `State` 줄(`approved`/`implementing`)·`최종 갱신` 줄·`## 리뷰 및 남은 위험` 섹션, 이 세 곳만 기계적으로 갱신하는 것은 예외로 허용한다.** 그 외에는 여전히 (a) `기준 커밋`/`승인 필요` 등 다른 고정 필드나 계획 섹션(1~7)을 건드리지 않음, (b) `git commit`/`git push`를 호출하지 않음(읽기 전용 `rev-parse`/`status`/`diff`/`log`만 사용), (c) 제품 코드를 절대 수정하지 않음, (d) Claude/Codex 호출·lock 관리·3-5의 제한적 갱신 외의 어떤 부수효과도 갖지 않는다.
6. **verified 및 수동 스킬 보존**: `approved → verified`는 계속 사용자만 수행하며 스크립트는 이 전환을 절대 트리거하지 않는다(스크립트가 쓸 수 있는 값은 `approved` 또는 `implementing`뿐이고 `verified`는 스크립트의 쓰기 대상에 아예 포함하지 않는다). `/프로토타입`, `/깃업데이트`, `/노션`, `/서버열기`는 이번에도 스크립트가 호출하지 않으며 사용자가 기존처럼 수동 실행한다.

### 3-5. Harness의 State/리뷰 결과 갱신 절차 (신규 예외 권한, 2026-09-13 추가)

Claude Reviewer가 쓰기 권한을 완전히 잃은 대신, Harness가 **검증을 통과한 JSON에 한해서만** 아래 절차로 current.md를 기계적으로 갱신한다. 이는 "판단은 Claude, 실행은 결정론적 스크립트"로 책임을 분리해 최소 권한을 지키기 위한 구조다.

1. Claude 호출(3-0-2) 결과 stdout(JSON)을 3-0-3의 UTF-8 방식으로 읽는다.
2. **형식 검증**: JSON 파싱이 성공하고 3-0-7 스키마의 필수 필드가 모두 존재하는지 확인한다. 실패하면 즉시 중단하고 State를 바꾸지 않는다("리뷰 결과 파싱 실패 — 수동 확인 필요"만 출력).
3. **정합성 검증**: `base_commit_checked` 값이 (a) `current.md`의 `기준 커밋`, (b) 현재 `git rev-parse HEAD`와 모두 일치하는지 확인한다. 하나라도 다르면 stale 리뷰로 간주해 중단하고 State를 바꾸지 않는다.
4. **사유 검증**: `verdict`가 `rejected`인데 `rejection_reasons`가 비어 있으면(스키마상 불가능하지만 방어적으로 재확인) 중단한다.
5. 위 검증을 모두 통과하면:
   - `verdict: approved` → `**State:**` 줄을 `approved`로 치환.
   - `verdict: rejected` → `**State:**` 줄을 `implementing`으로 치환.
   - `**최종 갱신:**` 줄을 `Harness (Claude 리뷰 검증 결과 반영), <타임스탬프>`로 치환.
   - `## 리뷰 및 남은 위험` 섹션 본문을 JSON의 `summary`/`acceptance_criteria`/`rejection_reasons`/`risks_or_followups`를 그대로 옮겨 적은 고정 형식 텍스트로 치환.
6. 이 세 곳 외의 어떤 줄도 쓰지 않는다 — 구현 시 정규식/문자열 치환 범위를 이 세 지점으로 하드코딩해, 실수로 다른 섹션을 건드릴 수 없는 구조로 만든다(코드 리뷰 시 grep으로 "이 세 지점 외 쓰기 없음"을 확인 가능해야 함).
7. 갱신 후 스크립트는 즉시 종료한다. 다음 단계(사용자의 `verified` 확인)는 여전히 사람의 몫이다.

## 4. 수용 기준

- `docs/tasks/current.md` 표준 템플릿의 "구현 결과"/"테스트 결과" 섹션이 A안대로 빈칸 placeholder 형식으로 바뀐다.
- `docs/RULES.md`에 "리뷰 0번째 항목: 핸드오프 형식 완전성" 반려 규칙(B안)이 명시된다.
- 오케스트레이션 스크립트 설계 문서(또는 스크립트 자체, 다음 구현 단계에서)에 C안의 최소 형식 검사 로직이 포함된다.
- 스크립트는 호출 1회당 정확히 한 단계만 진행하고 종료하며, watch/loop/자동 재호출 코드가 없다.
- 스크립트에 lock 파일 기반 중복 실행 방지가 구현된다.
- Claude Reviewer 호출은 `--permission-mode plan`과 읽기 전용 `--allowedTools`만 사용하며, `acceptEdits`나 그 외 쓰기 가능 모드를 쓰지 않는다.
- Claude Reviewer 응답은 3-0-7 스키마를 따르는 JSON 하나뿐이며(`--output-format json` + `--json-schema`), 자유 서술 텍스트로 current.md를 직접 편집하지 않는다.
- Harness가 current.md에 쓰는 코드 경로는 3-5에서 정의한 세 지점(`State` 줄, `최종 갱신` 줄, `## 리뷰 및 남은 위험` 섹션)으로 한정되고, 그 외 라인은 건드리지 않는다 — 이는 grep/diff로 확인 가능해야 한다.
- Harness는 JSON 형식 검증(파싱·필수 필드)과 정합성 검증(`base_commit_checked`가 `기준 커밋`·현재 `HEAD`와 일치)을 통과했을 때만 State를 갱신하며, 검증 실패 시 State를 바꾸지 않고 수동 확인 안내만 출력한다.
- 스크립트는 `git commit`/`git push`를 호출하지 않으며, 제품 코드를 수정하지 않는다 — 코드 리뷰 시 grep으로 확인 가능해야 한다(스크립트 내 `git commit`, `git push` 패턴이 없어야 함).
- CLI 호출에 timeout이 설정되어 있고, 실패/timeout 시 다음 단계를 진행하지 않는 분기가 코드로 확인된다.
- Codex 호출 명령(`-a`/`-C`/`-s`/`--ephemeral` 조합)은 3-0-1에서 확정한 형식을 그대로 쓰며, `-s`/`--ephemeral` 위치만 스크립트 작성 직전 `--help` 재확인으로 최종 고정한 뒤 구현한다.
- `approved → verified` 전환과 4개 수동 스킬(`/프로토타입`, `/깃업데이트`, `/노션`, `/서버열기`) 호출이 스크립트 어디에도 없다 — 스크립트가 State에 쓸 수 있는 값은 `approved`/`implementing`뿐임을 코드로 확인 가능해야 한다.

## 5. 예상 변경 파일 (다음 구현 단계 — 이번에는 미수정)

- `docs/tasks/current.md` — 표준 템플릿 A안 반영 (구현 결과/테스트 결과 빈칸 placeholder)
- `docs/RULES.md` — 리뷰 0번째 항목(B안) 추가
- `AGENTS.md` — 오케스트레이션 스크립트 존재와 역할을 간단히 참조(스크립트가 Claude/Codex 호출을 대신할 뿐 규칙 자체는 바뀌지 않음을 명시)
- `tools/harness/run-next-step.ps1` (신규) — 오케스트레이션 스크립트 본체 (3-0 확정 형식 반영, Codex/Claude 호출부 모두 구현 가능, 3-5의 제한적 State/리뷰 섹션 갱신 로직 포함)
- `tools/harness/review-schema.json` (신규) — 3-0-7의 리뷰 결과 JSON Schema
- `.vscode/tasks.json` (신규 또는 수정) — 스크립트 실행 Task 추가
- (`.gitignore` 수정 불필요 — lock 파일과 CLI 출력 임시 파일 모두 저장소 밖 `$env:TEMP`에 두기로 확정했으므로 저장소 내 무시 대상이 생기지 않는다.)

## 6. 파일 소유권 (제안, 다음 단계에서 확정)

| 파일 | 소유자(제안) | 상태 |
|---|---|---|
| docs/tasks/current.md (템플릿) | Claude | 계획 완료, 구현 대기 |
| docs/RULES.md | Claude | 계획 완료, 구현 대기 |
| AGENTS.md | Claude | 계획 완료, 구현 대기 |
| tools/harness/run-next-step.ps1 | Claude (제안 — 하네스 도구는 지금까지 문서 작업과 동일하게 Claude가 직접 작성) | 3-0 CLI 확인 완료 후 착수 |
| tools/harness/review-schema.json | Claude | 3-0 CLI 확인 완료 후 착수 |
| .vscode/tasks.json | Claude | tools/harness 스크립트 완성 후 착수 |
| 제품 코드 | (수정 없음) | 해당 없음 |

## 7. 위험 요소 또는 주의사항

- **남은 확인 1가지 (블로커 아님)**: Codex의 `-s`/`--ephemeral`이 `exec`의 최상위/하위 어느 옵션인지는 `-a`만큼 명시적으로 확인되지 않았다 — 스크립트 작성 직전 `codex --help`/`codex exec --help` 재확인으로 해결 가능한 작은 항목이며, 전체 구현을 막지 않는다.
- lock 파일이 비정상 종료(강제 종료, 정전 등)로 남아있으면 이후 정상 실행까지 막힐 수 있다 — 자동 삭제는 하지 않기로 했으므로, PID 생존 여부를 안내 메시지에 포함하되 삭제는 항상 사용자 수동 조치로 남긴다.
- timeout 1200초가 너무 짧으면 정상적으로 오래 걸리는 구현/리뷰 작업이 실패로 처리될 수 있다 — 실사용 후 스크립트 상단 변수 하나만 조정해 대응한다.
- C안(최소 형식 검사)은 문자열 패턴 검사라 오탐(정상인데 걸러짐) 가능성이 있다 — "형식 검사 실패"는 항상 사람이 확인할 수 있게 이유를 구체적으로 출력해야 한다.
- 스크립트가 "판단"만 하고 "실행"은 CLI에 위임하는 구조이므로, Claude/Codex CLI 쪽 버전이 올라가며 플래그가 바뀌면 스크립트도 함께 깨질 수 있다 — 버전이 바뀌면 3-0의 확인 절차를 다시 수행하는 습관이 필요하다.
- 콘솔 인코딩 수정(`[Console]::OutputEncoding`)만으로는 모든 Windows 터미널/폰트 조합에서 한글이 완벽히 보인다고 보장할 수 없다 — 그래서 중요 상태 판별은 영어 키워드 병기로 이중화했다(3-0-3). 완전한 해결이 아니라 완화책임을 인지한다.
- 자동 호출 프롬프트에 "current.md를 우선하라"고 지시해도, Codex/Claude가 내부적으로 얼마나 문서를 재탐색할지는 스크립트가 강제할 수 없는 각 CLI의 판단 영역이다 — 이번 설계는 권고 수준의 완화책이며, 토큰 사용량은 실사용 후 다시 관찰해야 한다.
- Codex 쪽 비용/토큰 상한 플래그 유무는 아직 미확인 — 다음 구현 단계에서 `codex --help` 확인 시 함께 점검한다.
- **신규 위험 (Harness 쓰기 권한 예외, 2026-09-13 추가)**: Harness가 current.md를 쓰는 유일한 예외 경로가 생겼다 — 이 코드 경로에 버그가 있으면(예: 정규식이 의도보다 넓게 매치) 계획 섹션이 실수로 덮어써질 위험이 있다. 구현 시 이 세 지점(State/최종갱신/리뷰 섹션) 치환 로직에 대해서만 별도의 작은 단위 테스트(고정 입력 → 정확히 그 세 줄만 바뀌는지 diff로 확인)를 두는 것을 권장한다.
- `--permission-mode plan`이 비대화식(`-p`) 실행에서 정확히 어떤 도구 호출을 차단/허용하는지는 `--help`의 선택지 목록으로만 확인했고 상세 동작은 실제 호출로 아직 검증하지 않았다 — 스크립트 작성 시 "Edit을 시도하면 실패/거부되는지" 최소 1회 실제 확인한다.
- `--json-schema`가 인라인 문자열/파일 경로 중 무엇을 받는지 미확인 — 3-0-2에 기록한 대로 스크립트 작성 시 확인한다.
- 리뷰 스키마(3-0-7)는 초안이라 실제 Claude 출력이 스키마와 자연스럽게 맞는지(예: `summary`가 너무 길어지는 경향 등) 첫 실사용 후 조정이 필요할 수 있다.

## 구현 결과

- 실제 변경 파일:
  - `docs/tasks/current.md` (이 문서 — 상태 필드 갱신 및 본 섹션)
  - `docs/RULES.md` — "리뷰 0번째 항목: 핸드오프 형식 완전성", "하네스(자동 호출) 사용 시 Reviewer 권한" 두 절 신설, "핸드오프 고정 필드"의 Codex→Claude 예시를 A안(빈칸 placeholder) 형식으로 교체, "전환 주체" 표의 `reviewing→approved` 행에 하네스 예외 참조 추가
  - `AGENTS.md` — 작업 절차 4번에 "리뷰 0번째 항목" 언급 추가, `tools/harness/run-next-step.ps1`의 존재와 역할·권한 구조를 요약하는 문단 추가
  - `tools/harness/run-next-step.ps1` (신규) — 오케스트레이션 스크립트 본체
  - `tools/harness/review-schema.json` (신규) — 리뷰 결과 JSON Schema
  - `.vscode/tasks.json` (신규) — "Harness: Run Next Step" task 1개
- 계획 대비 변경 요약: 3-0~3-5에서 확정한 설계를 그대로 구현했다. Codex 호출은 `codex -a never exec -C "<repo-root>" -s workspace-write --ephemeral "<prompt>"`, Claude 리뷰 호출은 `claude -p --permission-mode plan --allowedTools "Read,Grep,Glob,Bash(git status:*),Bash(git diff:*),Bash(git rev-parse:*),Bash(git log:*)" --output-format json --json-schema <review-schema.json 압축 내용> --no-session-persistence "<prompt>"` 형태로 구현했다(둘 다 실제 CLI로 검증 완료, 아래 테스트 결과 참고).
- 계획 이탈 사항: 없음. 다만 구현 중 실제 CLI/PowerShell 동작을 확인하는 과정에서 계획에 없던 세부 사항 2가지를 추가로 확정해 반영했다 — (1) `--bare` 모드는 이 환경(OAuth 로그인)에서 인증 실패("Not logged in")하므로 **사용하지 않는다**로 확정(계획엔 언급 없었음, 실제 테스트로 발견), (2) PowerShell 스크립트 파일(.ps1) 자체가 한글 리터럴을 포함하므로 **UTF-8 BOM 포함으로 저장**해야 Windows PowerShell 5.1이 올바르게 파싱한다는 점을 추가로 확정(계획의 UTF-8 절은 콘솔 출력/데이터 파일만 다뤘고 스크립트 파일 자체의 인코딩은 명시하지 않았었음).
- 종료 시점 git 상태 (`git status --porcelain`):
  ```
   M AGENTS.md
   M docs/RULES.md
   M docs/tasks/current.md
  ?? tools/
  ```
  (`.vscode/tasks.json`은 저장소의 기존 `.gitignore`에 `.vscode/`가 이미 등록돼 있어 `git status`에 나타나지 않는다 — 아래 위험 요소 참고.)

## 테스트 결과

- 실행한 검증:
  1. `codex --help` / `codex exec --help` 실제 확인 — `-a`(승인)는 top-level 전용, `-s`/`-C`/`--ephemeral`은 top-level과 `exec` 하위 모두 지원됨을 확인. 사용자가 제시한 `codex -a never exec -C ... -s workspace-write --ephemeral "<prompt>"` 순서가 유효함을 `codex exec --help`로 직접 확인.
  2. Codex 실제 호출(읽기 전용 `-s read-only`)을 PowerShell `Start-Process`로 실행해 정상 종료(ExitCode 0), UTF-8 출력 정상 확인.
  3. Claude 실제 호출(`--permission-mode plan --allowedTools Read --output-format json --json-schema <inline>`)을 PowerShell `Start-Process`로 실행해 `structured_output` 필드로 스키마에 맞는 JSON이 정상 반환됨을 확인.
  4. `--bare` 모드 테스트 — "Not logged in · Please run /login"으로 실패 확인(이 환경은 OAuth 로그인이라 API 키 전용인 `--bare`와 호환 안 됨) → 사용하지 않기로 확정.
  5. `.ps1` 스크립트 파일을 PowerShell AST 파서(`[System.Management.Automation.Language.Parser]::ParseFile`)로 문법 검사 — 최초 BOM 없이 저장했을 때 한글 리터럴이 깨져 파싱 오류 발생을 확인 → UTF-8 BOM으로 재저장 후 `PARSE_OK` 확인.
  6. `docs/tasks/current.md`를 임시로 여러 합성(synthetic) 시나리오로 교체해 가며 스크립트를 실제 실행 — 매번 원본은 백업해 두고 테스트 후 복원했다:
     - `State: 없음` → `[SKIP] no-state`, 종료 코드 0, 어떤 에이전트도 호출되지 않음 확인.
     - `State: planned`, 승인 필요 예/대기 → `[STOP] user-approval-required`, 에이전트 미호출 확인.
     - `State: planned`, 승인 필요 아니오, `기준 커밋`을 실제 HEAD와 다른 값으로 설정 → **최초 실행 시 버그 발견**(아래 참고), 수정 후 재실행하여 `[FAIL] stale`, 종료 코드 1, Codex 미호출, `current.md` 무변경 확인.
     - `State: implemented`, "구현 결과"에 `(Codex 작성)` placeholder가 남아있는 경우 → `[STOP] handoff-format-incomplete`, Claude 미호출 확인.
     - `State: reviewing` → `[SKIP] no-action-for-state`, 종료 코드 0 확인 (`approved`/`verified`/임의의 값도 동일한 default 분기이므로 대표로 확인).
     - lock 파일을 미리 만들어 둔 상태에서 실행 → `[STOP] already-running`, 존재하지 않는 PID에 대한 stale 경고 출력, lock 파일 자동 삭제하지 않음, 어떤 에이전트도 호출되지 않음 확인.
  7. `Set-FieldLine`/`Set-SectionBody`/`Test-ReviewJson` 핵심 로직을 별도 스크립트로 단위 테스트(9개 케이스) — State/최종갱신/리뷰 섹션 갱신이 서로를 침범하지 않는지, 승인/반려/필드누락/기준커밋불일치 판정이 올바른지 모두 통과 확인.
  8. `.vscode/tasks.json`이 실제로 실행할 명령(`powershell.exe -NoProfile -ExecutionPolicy Bypass -File <script>`)을 안전한 `State: 없음` 상태에 대해 직접 실행해 정상 동작 확인.
  9. `review-schema.json`, `.vscode/tasks.json`을 각각 JSON 파서로 문법 검증 — 둘 다 정상.
- **테스트 중 발견하고 수정한 버그 2건**:
  1. **PowerShell 함수 반환값 오염**: `Test-BaseCommitFresh` 내부에서 로그 함수(`Write-HLog`)가 `Write-Output`을 쓰고 있어, 이 함수의 실제 반환값(`$true`/`$false`)이 "로그 문자열 + 불리언"의 2요소 배열로 오염됨 → `-not (배열)`이 배열의 truthy 여부(항상 참)로 평가되어 **stale 커밋 검사가 항상 통과된 것처럼 동작**하는 심각한 버그였다. 실제로 이 버그 상태에서 테스트를 실행했을 때 가짜 `기준 커밋`(`deadbeef...`)에도 불구하고 스크립트가 실제 Codex를 호출해버렸다(다행히 Codex 자신이 AGENTS.md/RULES.md의 stale 감지 규칙에 따라 스스로 판단해 아무 파일도 건드리지 않고 중단함 — 계층적 방어가 실제로 작동한 사례). `Write-HLog`를 `Write-Output` 대신 `Write-Host`로 바꿔 파이프라인 오염을 근본적으로 제거했다.
  2. **PowerShell 5.1 스크립트 파일 인코딩**: `.ps1` 파일에 BOM 없이 UTF-8로 저장하면 Windows PowerShell 5.1이 한글 리터럴을 시스템 코드페이지로 오인해 파싱 오류(또는 위 버그처럼 조용한 오동작)를 일으킴 → UTF-8 BOM 포함으로 저장하도록 확정.
- 수용 기준 체크리스트:
  - [x] 표준 템플릿 A안 반영 — `docs/RULES.md`의 "핸드오프 고정 필드"에 반영
  - [x] RULES.md 리뷰 0번째 항목(B안) 추가
  - [x] 스크립트에 C안 최소 형식 검사 포함 — `Test-HandoffFormat` 함수, "구현 결과"/"테스트 결과" 섹션만 스캔하도록 범위 한정
  - [x] 스크립트가 1회 호출당 1단계만 진행 (watch/loop 없음) — 코드에 반복문 없음, 매 실행이 switch 1회 평가 후 종료
  - [x] lock 파일 기반 중복 실행 방지 — 실제 테스트로 확인
  - [x] State 직접 미수정 / git commit·push 없음 / 제품 코드 미수정 — 스크립트에 `git commit`/`git push` 문자열 없음(grep 확인), current.md 쓰기는 3-5 예외 경로(Update-CurrentMdFromReview)로만 한정, `app.py`/`pages/`/`core/`/`config.py` 어디에도 손대지 않음
  - [x] CLI 호출 timeout 및 실패 시 다음 단계 미진행 — `Wait-Process -Timeout 1200`, timeout/실패 시 모두 `$ExitCode=1`로 종료하고 State 불변경
  - [x] Codex 호출부가 3-0-1 확정 형식(및 재확인된 `-s`/`--ephemeral` 위치)을 그대로 사용 — `codex exec --help`로 재확인 후 사용자가 제시한 순서 그대로 적용
  - [x] verified 전환 및 4개 수동 스킬 미호출 — 스크립트가 쓸 수 있는 State 값은 `approved`/`implementing`뿐(코드상 다른 값 대입 경로 없음), `/프로토타입`·`/깃업데이트`·`/노션`·`/서버열기` 호출 코드 없음
- 미실행 항목과 사유: `implemented` 상태에서 실제 Claude 리뷰 JSON을 받아 `Update-CurrentMdFromReview`가 진짜 `current.md`에 반영되는 전체 end-to-end는 실행하지 않았다 — 이 문서 자체가 살아있는 하네스 4단계 작업이라, 지금 그 경로를 실제로 태우면 이 작업 자체가 리뷰/승인 처리되어 버려 혼란을 줄 수 있기 때문이다. 대신 핵심 로직(`Set-FieldLine`/`Set-SectionBody`/`Test-ReviewJson`)은 별도 단위 테스트로, 실제 Claude 호출 자체는 별도의 무해한 스키마로 각각 검증했다. **다음 실제 기능 작업이 `implemented`에 도달하면 이 경로가 처음으로 실전 검증된다.**

## 리뷰 및 남은 위험

- 리뷰 결과: Claude가 구현과 동시에 자체 검토·테스트함(위 테스트 결과 참고). 계획한 6개 파일이 정확히 변경/생성됐고, 제품 코드는 무변경, git commit/push 없음, State 쓰기 권한은 3-5 예외 경로로만 한정됨을 확인했다.
- 남은 위험/후속 작업:
  - `implemented→reviewing` 전체 경로(Claude 실제 리뷰 → Harness의 3-5 갱신)는 아직 실전에서 태워보지 않았다 — 다음 실제 작업에서 처음 검증 필요.
  - `.vscode/tasks.json`이 저장소의 기존 `.gitignore`(`.vscode/` 항목)에 걸려 `git status`/커밋에 나타나지 않는다 — 이 파일을 팀/다른 클론에도 공유하고 싶다면 `.gitignore` 예외 처리가 필요하다(이번 파일 범위에는 `.gitignore` 수정이 없어 그대로 두었다).
  - timeout 1200초, lock 파일 경로 등은 실사용 후 조정 가능성이 있다.
  - 자동 호출 시 Claude 쪽 비용은 실측 기준 1회당 약 0.1달러 수준(프로젝트 문서 캐시 생성 비용 포함, 캐시가 유효한 동안 후속 호출은 더 저렴할 것으로 예상)이었다 — 참고용으로 기록.
  - 최종 `verified` 전환은 사용자가 스크립트/Task를 한 번 실제로 사용해 본 뒤 진행한다.
