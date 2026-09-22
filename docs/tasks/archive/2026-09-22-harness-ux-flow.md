# 현재 작업

## 상태

**State:** `verified`
**기준 커밋:** `c8160b118f16d3980b623180457c8bce0ca6d12e`
**승인 필요:** 예 — 이 작업은 하네스의 "정확히 한 단계만 진행하고 종료한다"(현재 스크립트 상단 주석)는 기존 자동화 원칙을 "성공 시 여러 단계를 한 번에 연쇄 실행"하는 쪽으로 바꾸고, 지금까지 사람이 수동으로 우회해온 `implementing` 상태도 조건부로 자동 재개하도록 만든다. 제품 코드는 건드리지 않지만 하네스의 자동 실행 범위·자율성이 커지는 변경이라 `docs/RULES.md`의 승인 기준이 애매할 때는 승인이 필요한 쪽으로 판단한다는 원칙에 따라 사용자 승인을 받는다. **사용자 승인: 완료** (2026-09-22, 아래 "2. 현재 상태"의 `implementing` 자동 재개 조건부 설계를 확인 후 승인)
**최종 갱신:** 사용자가 구현·리뷰 결과를 확인해 verified로 확정(단, Ctrl+Alt+H 단축키를 통한 실제 종단 E2E는 미검증 — 아래 "사용자 확인 완료" 절 참고), 2026-09-22T10:59:16Z

이 작업은 `docs/RULES.md`의 "제품 작업 중 하네스 자체 결함·개선점을 발견했을 때" 규칙에 따라 개선 후보로만 기록해뒀던 마지막 하네스 항목(프로젝트 메모리 `known_harness_issues.md` 3번, `implementing` 자동 재개 불가)과, 사용자가 이번에 새로 요청한 실행 흐름/터미널 UX 개선을 함께 다룬다. 새 브랜치 `김영민/harness-ux-flow`(origin/main 기준, PR #4/#5/#6 모두 반영된 최신 상태)에서 작업한다.

## 1. 목표

`tools/harness/run-next-step.ps1`을 Ctrl+Alt+H **한 번**으로 `planned → Codex 구현 → (핸드오프 재검사) → implemented → Claude 리뷰 → approved`까지 성공 시 한 번에 이어지도록 바꾸고, 실행 중 진행 상황과 중단 사유·다음 행동을 터미널에 명확하게 보여준다. 구체적으로:

1. **단일 실행 연쇄**: `planned`(또는 아래 3번의 `implementing`)에서 시작해 Codex 구현이 성공하면, 같은 실행 안에서 핸드오프 형식과 State를 다시 검사하고, 이상 없으면 곧바로 Claude 리뷰까지 자동 호출한다. 리뷰가 승인되면 `approved`에서 정상 종료한다. **반려·오류·안전장치 실패가 하나라도 발생하면 그 즉시 연쇄를 멈춘다** — 재시도하지 않는다(기존 "watch/loop/자동 재시도는 없다" 원칙은 "실패 시 재시도"에는 여전히 적용되고, 이번 변경은 "성공 시 다음 단계로 자동 진행"만 새로 허용하는 것임을 스크립트 상단 주석에도 명확히 반영한다).
2. **명확한 진행/결과 표시**: 각 단계 시작 시 `[RUNNING]`(예: `[RUNNING] Codex implementing...`, `[RUNNING] Claude reviewing...`), 완료 시 `[OK]`, 중단 시 `[STOP]`, 오류 시 `[FAIL]`을 태그로 일관되게 쓴다. 중단·오류가 나면 그 바로 뒤에 `[NEXT]` 한 줄(또는 여러 줄)로 사용자가 지금 뭘 해야 하는지 알려준다.
3. **`implementing` 상태 조건부 자동 재개**: 실행 시작 State가 `implementing`이면, 지금처럼 무조건 `[SKIP] no-action-for-state`로 끝내지 않는다. 다만 아래 "2. 현재 상태"에서 다시 조사한 결과, `implementing`은 반려를 통해서만 도달하는 게 아니라 **Codex의 timeout·비정상 종료·강제 종료·PC 종료·네트워크/Wi-Fi 단절·API 통신 실패 등으로 작업 도중에도 남을 수 있는 상태**임을 확인했다. 그래서 무조건 자동 재개하지 않고, **"이 `implementing`이 안전하게 재개 가능한 것인지"를 판별할 수 있는 신뢰할 만한 근거가 있을 때만** Codex를 자동 재호출한다 — 근거가 없으면(출처 불명확) `[STOP]` + `[NEXT]`로 원인과 수동 복구 방법을 안내하는 쪽을 우선한다. 판별 기준과 근거는 "2. 현재 상태"에 상세히 기록한다.
4. **`handoff-format-incomplete` 진단 개선**: 지금처럼 "누락 있음"이라고만 하지 않고, `계획 이탈 사항` / `종료 시점 git 상태` / 수용 기준 체크리스트(`- [ ]`/`- [x]`) 중 **정확히 무엇이 비어 있는지** 항목별로 터미널에 표시한다. 코드 구현 자체는 됐는데 기록만 부족한 경우, 사용자가 Codex에게 무엇을 보완해 달라고 요청해야 할지 바로 알 수 있어야 한다.

이번 작업은 위 네 가지(실행 흐름 연쇄, 로그 태그 체계, `implementing` 재개, handoff 진단 개선)와 그에 필요한 최소한의 리팩터링(예: `implemented` 단계 로직을 재사용 가능한 형태로 정리)만 다룬다. **새 기능이나 그 외 하네스 리팩터링은 포함하지 않는다.**

## 2. 현재 상태

`tools/harness/run-next-step.ps1`(현재 566줄대, 지난 세 작업으로 헤딩 경계·시작 탐지 버그와 Codex 사전 체크가 이미 반영된 상태)의 관련 부분:

- 상단 주석(4~5행)이 "정확히 한 단계만 진행하고 종료한다. watch/loop/자동 재시도는 없다"고 명시하지만, 이번 요청은 "성공 시에는 여러 단계를 한 실행에서 잇는다"는 것이라 이 주석과 충돌한다 — 실제 동작을 바꾸는 김에 주석도 정확하게 고쳐야 한다(실패 시 재시도하지 않는다는 원칙 자체는 유지).
- `switch ($State)`(429행~)는 `'planned'`(Codex 호출 후 그대로 종료)와 `'implemented'`(Claude 리뷰 호출 후 그대로 종료)만 별개로 처리하고, 성공하더라도 서로 이어지지 않는다 — 매번 사람이 다시 실행해야 한다.
- `'planned'` 분기 마지막(469~473행)은 Codex가 종료 코드 0으로 끝나면 `Write-HLog 'OK' 'codex-invoked: ... current.md의 State를 직접 확인하세요.'`라고 하고 그냥 끝낸다 — 실제로 State가 `implemented`로 바뀌었는지, 핸드오프 기록이 제대로 채워졌는지는 다음 실행 때(`'implemented'` 분기 시작에서)에야 확인한다.
- `Test-HandoffFormat`(299~309행)은 4가지(placeholder 잔존, "계획 이탈 사항" 부재, "종료 시점 git 상태" 부재, 체크리스트 패턴 부재) 중 하나라도 걸리면 그냥 `$false` 하나만 반환한다. 호출부(476~481행)는 "계획 이탈 사항/종료 시점 git 상태/수용 기준 체크리스트 중 누락이 있어"라고 셋을 뭉뚱그려 말할 뿐, 정확히 어떤 게 빠졌는지는 알려주지 않는다.
- `default` 분기(558~561행)는 State가 `'planned'`/`'implemented'`가 아니면 전부 `[SKIP] no-action-for-state: $State`로 끝난다. `implementing`도 지금은 여기 걸린다.
- `'implemented'` 분기에서 리뷰가 반려되면(550~552행) `Update-CurrentMdFromReview $reviewObj 'implementing'` 후 **`[OK]` 태그**로 "review-rejected: State를 implementing으로 되돌렸습니다"라고 로그한다 — 사용자 요청 기준으로는 반려는 연쇄를 멈춰야 하는 상황이라 `[OK]`가 아니라 `[STOP]`이어야 한다.
- 기존 안전장치 현황(이번 작업에서 모두 그대로 유지해야 함):
  - lock 파일(59~82행, `finally`에서 해제)로 중복 실행 방지.
  - `Test-BaseCommitFresh`(138~149행)로 `기준 커밋` vs 현재 `HEAD` 신선도 확인 — `'planned'`/`'implemented'` 양쪽에서 호출.
  - `Test-NoUnexpectedChanges`(182~206행)로 Codex 호출 전 `git status`를 `current.md`의 "예상 변경 파일" + `logs/` 예외와 대조.
  - `Invoke-AgentProcess`(223~283행)의 `TimeoutSec`(기본 1200초, 전역 상수) 및 `Wait-Process -Timeout`/강제 종료.
  - `Read-Utf8File`/`Write-Utf8File`(31~37행)로 UTF-8(BOM 없음) 파일 입출력.
  - Claude 호출(499~509행)은 `--permission-mode plan` + 읽기 전용 `--allowedTools` + `--json-schema`로 제한.
  - `Test-ReviewJson`(340~365행)으로 필수 필드·verdict 값·`base_commit_checked` 일치·반려 시 사유 존재를 검증.
  - `Update-CurrentMdFromReview`(390~398행)는 `Set-FieldLine`(State, 최종 갱신)과 `Set-SectionBody`(리뷰 섹션) 세 곳만 쓴다 — 그 외 필드/섹션은 건드리지 않는다.

**`implementing`의 모든 도달 경로 재조사** (사용자 요청에 따라 harness 스크립트뿐 아니라 `AGENTS.md`/`docs/RULES.md`까지 다시 확인):

1. `docs/RULES.md`의 "전환 주체" 표: `reviewing`/`approved`/`verified` → `implementing`(반려, "문제를 발견한 쪽"이 전환)이 문서화된 유일한 **반려** 경로다. 이 스크립트의 `Update-CurrentMdFromReview`도 반려 시 정확히 `'implementing'`으로 되돌린다.
2. **그러나 `AGENTS.md` "작업 절차" 2번은 이렇게 명시한다**: "Builder는 계획과 소유권, `기준 커밋`을 확인한 뒤 지정된 파일만 수정하며 **상태를 `implementing`으로 갱신한다**." 즉 Codex는 `planned`에서 처음 호출될 때도 작업을 시작하자마자(구현을 끝내기 전에) **스스로 State를 `implementing`으로 먼저 써야 한다**는 게 문서화된 절차다. `$CodexPrompt`(현재 스크립트, 403~411행)에는 이 "시작 시 implementing으로 갱신" 지시가 명시적으로 들어있지 않지만, Codex는 `AGENTS.md`/`docs/RULES.md`를 스스로 참고하도록 안내받으므로 실제로 이 절차를 따를 가능성이 있고, 따르지 않더라도 향후 그렇게 바뀔 수 있는 "문서화된 정상 동작"이다.
3. 결론적으로 `implementing`에 도달하는 경로는 최소 두 가지다: **(a) 반려**(이전 구현이 완결·기록까지 끝난 뒤 문제가 발견됨) **(b) Codex가 방금 작업을 시작했다는 표시**(구현이 끝나기 전, 기록이 아직 없거나 미완성인 상태). (b) 도중에 Codex가 **timeout(하네스의 `Wait-Process -Timeout`으로 강제 종료), 비정상 종료(크래시), 강제 종료(사람이 프로세스를 죽임), PC 종료, 네트워크/Wi-Fi 단절, Codex API 통신 실패** 등으로 끊기면, `implementing`만 남고 "## 구현 결과"/"## 테스트 결과"는 비어 있거나 절반만 쓰인 채로 남을 수 있다. 같은 문제는 **반려 이후 재개 중**(즉 이미 `implementing`인 상태에서 다시 Codex를 부른 경우)에도 똑같이 발생할 수 있다 — 재개 도중 또 다른 timeout/크래시/네트워크 단절이 나면 이전 반려 기록은 남아있지만 "## 구현 결과"가 새로 절반만 덮어써진 상태가 될 수 있다. Claude API 통신 실패(리뷰 호출 쪽)는 `'implemented'` 단계에서 발생하는 문제라 State를 `implementing`으로 되돌리지 않으므로 이 판별과는 무관하다(리뷰 호출 자체의 timeout/실패는 기존처럼 `[FAIL]` + `[NEXT]`로 별도 처리).
4. 즉 **"State가 `implementing`이다"라는 사실 하나만으로는 반려로 온 것인지, Codex가 작업 도중 끊긴 것인지 구분할 수 없다** — 지난번 계획(이 파일의 이전 버전)에서 "반려로만 도달한다"고 단정한 건 틀렸다. 무조건 자동 재개하면, 절반만 쓰인 "## 구현 결과"/"## 테스트 결과" 위에 Codex가 또 다른 내용을 덧쓰거나, 실제로는 끝나지도 않은 이전 시도를 마치 정상 반려처럼 취급해 재작업을 시킬 위험이 있다.

**신뢰할 만한 구분 근거**: 이번 작업에서 함께 개선하는 `Test-HandoffFormat`(현재 299~309행, "3. 구현 계획" 5번에서 상세 결과를 반환하도록 고침)을 재사용한다 — 이 함수는 "## 구현 결과"/"## 테스트 결과"에 `(Codex 작성)` placeholder가 없고, "계획 이탈 사항"·"종료 시점 git 상태"·수용 기준 체크리스트가 모두 채워져 있는지를 판정한다. 이 검사를 **`implementing` 진입 시점에도 그대로 실행**해서:
- **통과**(완전한 기록이 있음) → 이는 "적어도 한 번은 Codex 구현이 끝까지 완료되고 스스로 기록까지 마쳤다"는 뜻이다. 그 뒤에 `implementing`으로 돌아온 거라면 (i) 하네스/Claude가 리뷰 후 반려했거나 (ii) 사용자가 실제 화면 확인 후 문제를 발견해 되돌린 경우뿐이다 — 두 경우 모두 재개해도 Codex가 완결된 이전 기록과 반려/피드백 내용을 바탕으로 정상적으로 이어서 작업할 수 있다. **→ `planned`와 동일한 나머지 안전장치(승인 필요·기준 커밋 신선도·예상 밖 변경 검사)를 통과하면 자동 재개(Codex 재호출) 허용.**
- **불완전**(placeholder 잔존, 또는 세 항목 중 하나라도 없음) → "완결된 이전 기록이 없다"는 뜻이므로, Codex가 작업을 시작만 하고 기록을 채우기 전에 끊겼을 가능성을 배제할 수 없다(timeout/크래시/강제종료/PC종료/네트워크·API 단절 전부 이 형태로 나타난다). **→ 자동 재호출하지 않는다. `[STOP]`으로 "implementing-incomplete-handoff: 이전 시도가 완료되지 않은 채 중단된 것으로 보입니다" 같은 메시지를 내고, `[NEXT]`로 다음을 안내한다: (1) `git status`/`git diff`로 실제 코드 변경이 있는지 확인, (2) 있다면 의도한 작업인지 판단해 필요시 되돌리거나 보완, (3) 문제 없다고 판단되면 사용자가 직접 State를 `planned`로 되돌려 재시도.**

이 판별은 이미 이번 작업에서 개선하는 `Test-HandoffFormat`을 그대로 재사용하므로 별도의 새 검사 로직을 추가하는 게 아니다. 다만 완결된 기록이 있다는 것이 "그 시점 이후 코드 파일 자체가 완전히 일관된 상태"까지 보장하지는 않는다(예: 기록은 다 썼는데 마지막 파일 저장 직전에 끊긴 극단적 경우) — 이런 잔여 위험은 기존에도 모든 Codex 호출에 내재된 위험이며 이번 판별로 없앨 수 있는 범위가 아니다. 이 잔여 위험은 "7. 위험 요소"에 남긴다.

**결론**: `implementing`을 `planned`와 동일하게 취급하는 무조건 자동 재개는 하지 않는다. 대신 위 판별(핸드오프 완료 기록 존재 여부)을 먼저 거쳐, 통과할 때만 `planned`와 같은 방식으로 Codex를 재호출하고, 통과하지 못하면 `[STOP]` + `[NEXT]`로 사람에게 판단을 넘긴다.

## 3. 구현 계획

1. **상단 주석 갱신**: 4~5행 "정확히 한 단계만 진행하고 종료한다. watch/loop/자동 재시도는 없다"를 실제 새 동작(성공 시 `planned`/`implementing` → `implemented` → `approved`까지 한 실행에서 연쇄, 실패/반려 시 그 자리에서 즉시 중단하고 재시도하지 않음)에 맞게 고친다.
2. **State 분기 재구성 + `implementing` 진입 조건**: `'planned'`와 `'implementing'`을 같은 처리 블록으로 묶는다(예: `{ $_ -in 'planned', 'implementing' }` 형태의 스크립트블록 조건, 또는 두 라벨이 같은 블록을 타도록 하는 PowerShell 관용구 — 정확한 문법은 Codex가 정한다). 이 블록 진입 시 **`State`가 `'implementing'`일 때만 추가로** "2. 현재 상태"에서 정한 판별을 먼저 수행한다: 그 시점의 `content`(파일 내용)에 대해 (5번에서 상세화하는) `Test-HandoffFormat`을 실행해 "## 구현 결과"/"## 테스트 결과"가 완결된 기록인지 확인한다.
   - 완결돼 있으면 계속 진행한다(= 기존 `'planned'` 로직과 동일하게 승인 필요 체크 → `Test-BaseCommitFresh` → `Test-NoUnexpectedChanges` → Codex 호출).
   - 완결돼 있지 않으면 `[STOP]`으로 "implementing-incomplete-handoff: ..."(위 "2. 현재 상태"에 적은 문구 참고)를 내고, `[NEXT]`로 `git status`/`git diff` 확인 → 필요시 정리 → 문제 없으면 `planned`로 수동 전환 후 재시도를 안내한 뒤 Codex를 호출하지 않고 멈춘다. (State가 `'planned'`일 때는 이 판별을 하지 않는다 — `planned`는 애초에 아직 Codex가 손대지 않은 상태이므로 이 모호성이 없다.)
   - 두 경우 모두, Codex를 실제로 호출하는 경우 로그 메시지에 `State`값을 넣어 "처음 계획"인지 "반려/중단 후 재개"인지 구분할 수 있게 한다(예: `[RUNNING] Codex implementing (state=$State)...`).
3. **Codex 성공 후 즉시 재검사 + 연쇄**: Codex 호출이 성공(`Ok=$true`, 타임아웃 아님)하면, 그 자리에서 끝내지 않는다.
   - `docs/tasks/current.md`를 다시 읽어(`Read-Utf8File`) 최신 `State`/본문을 얻는다.
   - 새 `State`가 `implemented`가 아니면 `[STOP]`으로 "codex-state-unchanged: Codex가 종료 코드 0으로 끝났지만 State가 implemented로 바뀌지 않았습니다" 같은 메시지와 `[NEXT]`(current.md와 Codex 실행 로그를 직접 확인하라는 안내)를 내고 멈춘다.
   - `implemented`면 이어서 4번(핸드오프 재검사)으로 진행한다.
4. **`'implemented'` 로직 재사용 가능하게 정리**: 현재 `'implemented'` 분기 안에 있는 로직(핸드오프 검사 → `Test-BaseCommitFresh` → Claude 호출 → JSON 검증 → `Update-CurrentMdFromReview`)을 함수로 뽑거나, 스크립트 흐름상 Codex 성공 이후 경로와 원래 `'implemented'`로 시작한 실행 양쪽에서 **같은 코드가 실행**되도록 정리한다(중복 코드 작성 금지). `switch` 문의 `'implemented'` 케이스도 이 공용 로직을 호출하는 형태로 바뀔 수 있다 — 정확한 구조(함수 추출 vs 순차 흐름)는 Codex가 정하되, 동작은 계획대로여야 한다.
5. **`Test-HandoffFormat` 진단 개선**: 단순 `bool` 대신, 어떤 검사가 실패했는지 알 수 있는 결과(예: 문자열 배열 또는 `PSCustomObject`)를 반환하도록 바꾼다. 최소 아래 네 가지를 각각 개별적으로 판정하고, 실패한 항목만 이름을 붙여 반환한다:
   - `(Codex 작성)` placeholder가 아직 남아있음
   - "## 구현 결과"에 "계획 이탈 사항" 문구 없음
   - "## 구현 결과"에 "종료 시점 git 상태" 문구 없음
   - "## 테스트 결과"에 수용 기준 체크리스트(`- [ ]`/`- [x]`/`- [X]`) 패턴이 하나도 없음
   호출부는 `[STOP] handoff-format-incomplete`를 낸 뒤, 실패한 항목 각각을 `[NEXT]`(또는 그에 준하는) 줄로 나열한다 — "코드 구현은 됐는데 기록이 부족하다"는 걸 사용자가 한눈에 알 수 있어야 한다.
6. **로그 태그 정리**: 아래를 포함해 기존 `Write-HLog` 호출 지점을 사용자가 요청한 태그 체계에 맞게 다듬는다.
   - Codex/Claude 호출 직전에 `[RUNNING] Codex implementing...` / `[RUNNING] Claude reviewing...` (요청받은 예시 문구를 그대로 쓴다)을 추가한다.
   - 리뷰 반려(`review-rejected`)는 현재 `[OK]`인데, 연쇄를 멈추는 상황이므로 `[STOP]`으로 바꾸고 `[NEXT]`를 추가한다(반려 사유 확인 + "이제 State가 자동 재개 대상이니 보완 후 다시 실행하면 Codex가 이어서 작업합니다" 안내 — 3번의 `implementing` 자동 재개와 자연스럽게 연결).
   - 기존 `[FAIL]`/`[STOP]` 지점(락 충돌, 기준 커밋 stale, 예상 밖 변경, codex/claude 미발견, 스키마 읽기 실패, timeout, 비정상 종료, JSON 파싱/검증 실패 등) 각각에 그 상황에 맞는 `[NEXT]` 한 줄 이상을 추가한다 — 사용자가 요청한 목록(stale base commit / unexpected git changes / Codex 실패·timeout / handoff format incomplete / Claude review rejected / JSON 검증 실패·timeout)을 전부 포함해야 한다.
   - 최종 승인(`approved`)으로 연쇄가 정상 종료될 때는 `[OK]`로 마무리한다(성공 종료에는 `[NEXT]`를 붙이지 않는다 — 사용자 요청상 `[NEXT]`는 중단/오류 상황 전용).
   - `default` 분기(예: `reviewing`/`approved`/`verified`, 또는 알 수 없는 값)는 `[SKIP]`을 유지하되, `approved`처럼 사람의 다음 행동이 명확한 경우 가벼운 안내를 덧붙일 수 있다(예: "실제 화면 확인 후 verified로 전환하세요") — 선택 사항이며 안전장치나 State 판정 로직 자체는 바꾸지 않는다.
7. **안전장치 보존**: lock, `Test-BaseCommitFresh`, `Test-NoUnexpectedChanges`, `Invoke-AgentProcess`의 timeout/강제종료, UTF-8 입출력, Claude 호출의 읽기 전용 권한(`--permission-mode plan` + 제한된 `--allowedTools`), `Test-ReviewJson`, `current.md`의 State 줄/최종 갱신 줄/리뷰 섹션 세 곳만 쓰는 제한적 갱신은 로직·조건을 약화하지 않는다 — 연쇄 실행 중에도 각 단계 진입 전 기존과 동일한 조건을 그대로 다시 검사한다(예: Codex 성공 후 바로 Claude로 넘어가기 전에도 `Test-BaseCommitFresh`는 여전히 실행됨).
8. 이번 계획에 없는 다른 개선(새 State 값 추가, 단축키 자체 구현, 다른 함수 리팩터링 등)은 하지 않는다.

## 4. 수용 기준

- [x] `planned` 상태에서 실행했을 때, Codex 구현이 성공하고 핸드오프 형식도 갖춰지면, **같은 실행 안에서** 자동으로 Claude 리뷰까지 호출되고, 승인되면 `State: approved`로 끝난다(재실행 불필요).
- [x] Codex 구현이 실패/timeout하거나, 성공했지만 State가 `implemented`로 바뀌지 않았거나, 핸드오프 형식이 불완전하면, 그 지점에서 연쇄가 **즉시 멈추고** Claude는 호출되지 않는다.
- [x] Claude 리뷰가 반려되면 그 즉시 연쇄가 멈춘다(재시도하지 않음). 반려 결과 로그 태그는 `[OK]`가 아니라 `[STOP]`이고, `[NEXT]`로 반려 사유 확인과 재실행 안내가 나온다.
- [x] 실행 시작 State가 `implementing`이면 더 이상 무조건 `[SKIP] no-action-for-state`로 끝나지 않는다.
- [x] `implementing` 진입 시, 그 시점의 "## 구현 결과"/"## 테스트 결과"가 `Test-HandoffFormat` 기준으로 **완결된 기록**이면(적어도 한 번은 Codex 구현이 끝까지 완료됐다는 뜻) — `planned`와 동일한 나머지 안전장치(승인 필요·기준 커밋 신선도·예상 밖 변경 검사)를 통과하는 경우에 한해 Codex를 자동으로 재호출해 이어간다.
- [x] `implementing` 진입 시, "## 구현 결과"/"## 테스트 결과"가 **불완전**하면(placeholder 잔존 또는 필수 항목 누락 — 작업 도중 중단됐을 가능성) Codex를 자동 재호출하지 **않는다**. `[STOP]`으로 상태 원인을 설명하고, `[NEXT]`로 `git status`/`git diff` 확인 → 필요시 정리 → 문제 없으면 수동으로 `planned`로 되돌려 재시도하라는 복구 방법을 안내한다.
- [x] `planned` 상태 진입 시에는 이 판별을 하지 않는다(핸드오프 기록의 완결 여부와 무관하게 기존과 동일하게 진행) — `implementing` 전용 게이트다.
- [x] `handoff-format-incomplete` 발생 시, "(Codex 작성) placeholder 잔존" / "계획 이탈 사항 없음" / "종료 시점 git 상태 없음" / "수용 기준 체크리스트 없음" 중 **실제로 실패한 항목만** 터미널에 개별적으로 표시된다(넷 중 하나만 실패해도 그 하나만 나오고, 나머지는 나오지 않는다).
- [x] Codex/Claude 호출 직전에 각각 `[RUNNING] Codex implementing...` / `[RUNNING] Claude reviewing...`이 출력된다.
- [x] 사용자가 나열한 6개 실패 경로(stale base commit, unexpected git changes, Codex 실패/timeout, handoff format incomplete, Claude review rejected, JSON 검증 실패/timeout) 각각에서 `[STOP]` 또는 `[FAIL]` 태그와 함께 해당 상황에 맞는 `[NEXT]` 안내가 최소 한 줄 이상 출력된다.
- [x] 최종 성공(`approved`) 종료 시 `[OK]`로 표시되고 `[NEXT]`는 붙지 않는다.
- [x] lock, `Test-BaseCommitFresh`, `Test-NoUnexpectedChanges`, timeout/강제종료, UTF-8 입출력, Claude 읽기 전용 권한(`--permission-mode plan` + 제한된 `--allowedTools`), `Test-ReviewJson`의 필수 필드·verdict·base_commit_checked·반려 사유 검증, `current.md`의 State/최종 갱신/리뷰 섹션 세 곳만 쓰는 제한은 이번 변경 전후로 동작·조건이 모두 동일하다(약화되지 않았음을 diff로 확인 가능해야 한다).
- [x] 연쇄 실행 중에도 각 단계 진입 직전 안전장치가 매번 다시 실행된다(예: Codex 성공 후 Claude 호출 전에도 `Test-BaseCommitFresh`가 실행됨) — 한 번 통과했다고 이후 단계에서 생략되지 않는다.
- [x] 이번 계획에 없는 새 기능·State 값·다른 함수 리팩터링은 포함되지 않는다.
- [x] `tools/harness/run-next-step.ps1` 외의 파일은 변경되지 않는다(계획 기록용 `docs/tasks/current.md` 제외).
- [x] 새로 추가되거나 삭제된 파일이 없다.

## 5. 예상 변경 파일

- `tools/harness/run-next-step.ps1` (상단 주석 갱신, State 분기 재구성(`planned`+`implementing` 통합, Codex 성공 후 연쇄), `Test-HandoffFormat` 진단 개선, 로그 태그(`[RUNNING]`/`[NEXT]` 추가, 반려 태그 수정) 전반)
- `docs/tasks/current.md` (구현/테스트 결과 기록)

## 6. 파일 소유권

| 파일 | 소유자 | 상태 |
|---|---|---|
| tools/harness/run-next-step.ps1 | Codex (구현/테스트) | 사용자 승인 완료 후 `implementing` 착수 |
| docs/tasks/current.md | Claude (계획/리뷰) | 계획 작성 완료, 구현 후 리뷰 예정 |

Claude는 계획 수립과 구현 후 리뷰만 수행하며 `tools/harness/run-next-step.ps1`은 직접 수정하지 않는다.

## 7. 위험 요소 또는 주의사항

- **승인 필요**: 위 "상태" 절 참고 — 자동 실행 범위 확장(연쇄 실행)과 `implementing` 자동 재개는 하네스의 자율성을 넓히는 변경이라 사용자 승인 후에만 착수한다.
- 한 번의 실행이 Codex+Claude 두 외부 에이전트를 순차 호출할 수 있어, 최악의 경우 체감 실행 시간이 기존(최대 1200초) 대비 최대 2배(최대 2400초)로 늘어날 수 있다 — 각 호출의 `TimeoutSec`은 그대로 두므로 개별 안전장치는 약화되지 않지만, 사용자가 한 번의 Ctrl+Alt+H로 더 오래 기다릴 수 있다는 점은 인지해야 한다.
- `implementing`은 반려뿐 아니라 `AGENTS.md`가 Codex에게 지시하는 "작업 시작 시 State를 `implementing`으로 갱신"이라는 절차 때문에, Codex의 timeout/비정상 종료/강제 종료/PC 종료/네트워크·API 단절로도 남을 수 있다는 걸 "2. 현재 상태"에서 확인했다 — 그래서 무조건 자동 재개하지 않고 `Test-HandoffFormat` 통과 여부로 조건부 재개한다. 이 판별 기준으로도 "완결된 기록은 있지만 그 직후 파일 저장이 끊긴" 것 같은 극단적 경우까지 완전히 배제하지는 못한다 — 이 잔여 위험은 모든 Codex 호출에 원래 있던 것이며 이번 작업으로 새로 생기거나 악화되는 게 아니다. Codex나 Claude가 구현·리뷰 중 이 판별 기준 자체가 잘못됐다는 근거(예: 완결된 기록처럼 보이는데 실제로는 코드가 절반만 반영된 사례)를 발견하면, 그 사실과 대안을 "구현 결과"에 기록한다.
- `Test-HandoffFormat`을 bool에서 상세 결과로 바꾸면 그 반환값을 쓰는 호출부(`'implemented'` 진입 경로, 그리고 3번에서 새로 추가되는 Codex-성공-후 경로)가 모두 새 형태에 맞게 수정돼야 한다 — 한쪽만 고치고 다른 쪽을 놓치지 않도록 주의(같은 로직을 재사용하는 4번 리팩터링과 맞물려 있음).
- 리뷰 반려 로그의 태그를 `[OK]`→`[STOP]`으로 바꾸는 건 사용자에게 보이는 문구만 바뀌는 것이고, `Update-CurrentMdFromReview`가 `current.md`에 실제로 쓰는 내용(State를 `implementing`으로, 리뷰 섹션 갱신)은 이번 계획에서 변경하지 않는다.
- 기존 세 번의 하네스 작업(`harness-review-section-fix`, `harness-heading-indexof-fix`, 그리고 이번 작업의 사전 체크 기반이 된 첫 하네스 작업)에서 쓴 검증 방식(관련 함수를 추출해 PowerShell로 직접 실행하며 assert)을 이번에도 따르되, 이번엔 여러 함수가 연쇄로 상호작용하므로 개별 함수 단위 검증뿐 아니라 "Codex 성공 → 자동으로 Claude 호출까지 이어지는지"의 흐름 자체도 (실제 외부 CLI를 부르지 않고) 목(mock)이나 시뮬레이션으로 검증해야 한다 — 정확한 구성은 Codex가 정한다.

## 구현 결과

- 실제 변경 파일: `tools/harness/run-next-step.ps1`, `docs/tasks/current.md`.
- 계획 대비 변경 요약:
  - `planned`와 `implementing`의 Codex 실행 경로를 통합했다. `implementing`만 기존 핸드오프 완결 여부를 먼저 검사하며, 불완전하면 원인과 수동 복구 방법을 안내하고 종료한다.
  - Codex 성공 후 current.md의 본문, State, 기준 커밋을 다시 읽는다. State가 `implemented`인 경우에만 공통 리뷰 분기로 이어지며, 핸드오프와 기준 커밋 검사를 다시 수행한다. 직접 `implemented`로 시작해도 같은 리뷰 코드를 사용한다.
  - `Test-HandoffFormat`은 `Ok`와 `Missing`을 반환한다. placeholder, 구현 결과의 계획 이탈 사항/종료 시점 git 상태, 테스트 결과의 체크리스트를 개별 검사하고 실제 실패 항목만 안내한다.
  - 호출 직전 `[RUNNING]`, 완료 시 `[OK]`, 반려 시 `[STOP]`을 출력한다. 기존 STOP/FAIL 경로에 상황별 `[NEXT]`를 추가했으며 timeout에는 남은 로그 경로도 표시한다. 실패·반려 후 재시도하지 않는다.
  - lock, 기존 사전 검사 조건, 프로세스 timeout/강제 종료, UTF-8 입출력, Claude 읽기 전용 인자, 리뷰 JSON 검증, current.md 세 영역만 갱신하는 코드를 보존했다.
- 계획 이탈 사항: 없음. 테스트는 저장소 파일을 추가하지 않고 임시 PowerShell 스크립트로 수행하고 삭제했다. 초기 제한 언어 모드에서 .NET 파서 호출이 차단되어, 전체 스크립트를 호출하지 않는 함수 본문으로 감싸 구문을 검사하고 실제 함수/분기와 외부 경계 mock을 실행하는 방식으로 검증했다.
- 종료 시점 git 상태 (`git status --porcelain`):

```text
 M docs/tasks/current.md
 M logs/events_log.csv
 M tools/harness/run-next-step.ps1
```

- `logs/events_log.csv`는 착수 전부터 존재한 런타임 산출물 변경이며 이번 작업에서 수정하지 않았다. `current.md`의 기존 계획 변경을 보존하고 구현/테스트 결과 및 상태·최종 갱신만 기록했다. 추가/삭제 파일, git commit/git push는 없다.

## 테스트 결과

- 실행한 테스트 및 결과:
  - PASS — Windows PowerShell에서 전체 스크립트를 실행하지 않는 함수 본문으로 감싸 구문 검사. 실제 외부 CLI 호출 및 저장소 쓰기 없음.
  - PASS — 실제 State 분기와 `Get-FieldValue`, `Get-SectionText`, `Test-HandoffFormat`, `Test-BaseCommitFresh`, `Test-ReviewJson`을 추출한 30개 모의 흐름 시나리오. 종료 구문은 테스트 함수의 return으로 치환하고 외부 프로세스·파일 입출력·HEAD·예상 밖 변경 검사·리뷰 반영은 mock 처리했다. 호출 수/순서, 반영 State, HEAD 검사 횟수, RUNNING/NEXT 태그를 검증했다.
  - 시나리오: planned/implementing/implemented 성공, 빈 기록의 planned 허용 및 implementing/implemented 차단, Codex 실패/timeout/State 미변경/State 누락/핸드오프 누락, 리뷰 반려, 시작 시 및 Codex 이후 stale, 예상 밖 변경, 승인 미완료, CLI 미발견, 스키마 오류, Claude 실패/timeout/JSON 파싱 오류/is_error/잘못된 verdict, approved/reviewing/verified 건너뛰기. implementing에서도 승인·stale·예상 밖 변경 차단을 별도 확인했다.
  - PASS — 핸드오프 형식 8개 검사: 정상, 세 필수 항목 각각의 단독 누락, placeholder 단독 잔존, `[ ]`/`[X]` 허용, 다른 섹션에 잘못 기록된 필드/체크리스트 배제. 단독 누락은 Missing이 정확히 한 항목인지 확인했다.
  - PASS — HEAD 원본과 안전장치 코드 비교. 입출력/프로세스 실행/JSON 검증/제한적 갱신 관련 함수 7개는 동일하고, 사전 검사 함수 2개와 lock 코드는 NEXT 안내 외 동일함을 확인했다.
  - PASS — `git diff --check`, 변경 범위 및 추가/삭제 파일 확인.
- 수용 기준 체크리스트 (위 "4. 수용 기준"과 같은 순서; 동작 판정은 모의 실행 기준):
  - [x] PASS — 1. planned 성공 시 같은 실행에서 Codex → Claude 호출 후 approved 반영.
  - [x] PASS — 2. Codex 실패/timeout/State 미변경/핸드오프 불완전 시 Claude 호출 없이 중단.
  - [x] PASS — 3. 리뷰 반려 시 implementing 반영, STOP/NEXT 출력, 재시도 없음.
  - [x] PASS — 4. implementing을 SKIP으로 처리하지 않고 전용 진입 검사 수행.
  - [x] PASS — 5. 완결된 implementing 기록 및 나머지 안전장치 통과 시 Codex 재개.
  - [x] PASS — 6. 불완전한 implementing 기록은 호출 없이 STOP/NEXT로 변경 확인·정리·planned 수동 전환 안내.
  - [x] PASS — 7. planned에는 핸드오프 진입 게이트를 적용하지 않음.
  - [x] PASS — 8. 네 가지 핸드오프 진단 중 실제 실패 항목만 개별 반환·표시.
  - [x] PASS — 9. 각 에이전트 호출 직전 RUNNING 로그 출력.
  - [x] PASS — 10. 지정된 여섯 실패 경로에 STOP/FAIL 및 상황별 NEXT 안내 존재. 예상 밖 변경 검사는 원본 비교와 mock으로 분리 검증.
  - [x] PASS — 11. approved 성공 시 OK 출력, NEXT 없음.
  - [x] PASS — 12. 기존 안전장치와 읽기 전용 인자·제한적 갱신 보존을 원본 비교 및 호출 인자 검사로 확인.
  - [x] PASS — 13. Codex 성공 후 HEAD 검사를 다시 수행하며, 이때 stale이면 Claude 호출 차단.
  - [x] PASS — 14. 계획 밖 기능·State 값·관련 없는 함수 리팩터링 없음.
  - [x] PASS — 15. 이번 구현은 계획된 두 파일만 수정. 기존 logs/events_log.csv 변경은 보존.
  - [x] PASS — 16. 추가/삭제 파일 없음.
- 미실행 항목과 사유: 실제 Codex/Claude CLI 및 Ctrl+Alt+H 단축키를 통한 종단 실행, 실제 1200초 timeout/프로세스 강제 종료, 사용자 화면 검증은 미실행. 중첩 에이전트 호출이나 실제 작업 문서의 리뷰 상태 변경 없이 모의 실행 및 원본 비교로 검증했으며, 실제 화면/동작 확인은 사용자 검증 단계에 남긴다.

## 리뷰 및 남은 위험

- 리뷰 결과: approved
- 요약: 모든 수용 기준을 diff와 실제 파일로 확인했습니다. `Test-HandoffFormat` 상세 반환, `planned`/`implementing` 통합 분기, Codex 성공 후 자동 연쇄, 각 실패 경로의 `[NEXT]` 추가, 반려 태그 `[OK]→[STOP]` 수정이 계획대로 구현됐습니다. 기존 안전장치(lock, `Test-BaseCommitFresh`, 읽기 전용 Claude 인자, `Test-ReviewJson`)는 모두 보존됐고, `implemented` 케이스 진입 시 `Test-BaseCommitFresh`가 재실행되어 Codex 성공 후 연쇄 실행에서도 신선도 검사가 적용됩니다. 실제 CLI를 통한 종단 실행 테스트는 사용자 검증 단계에서 확인이 필요합니다.
- scope_ok: True
- 수용 기준 판정:
  - [pass] 1. planned 성공 시 같은 실행에서 Codex → Claude → approved
  - [pass] 2. Codex 실패/timeout/State 미변경/핸드오프 불완전 시 Claude 호출 없이 중단
  - [pass] 3. 리뷰 반려 시 [STOP]+[NEXT], 재시도 없음
  - [pass] 4. implementing을 무조건 [SKIP] no-action-for-state로 처리하지 않음
  - [pass] 5. 완결된 implementing 기록 + 안전장치 통과 시 Codex 자동 재개
  - [pass] 6. 불완전한 implementing 기록 시 Codex 미호출, [STOP]+[NEXT] 복구 안내
  - [pass] 7. planned에는 핸드오프 완결 게이트 미적용 (implementing 전용)
  - [pass] 8. handoff-format-incomplete 시 실패 항목만 개별 표시
  - [pass] 9. Codex/Claude 호출 직전 [RUNNING] 태그 출력
  - [pass] 10. 6개 실패 경로(stale/unexpected/codex실패·timeout/handoff/반려/JSON검증) 각각 [STOP]/[FAIL]+[NEXT]
  - [pass] 11. approved 성공 종료 시 [OK]만, [NEXT] 없음
  - [pass] 12. 기존 안전장치(lock, Test-BaseCommitFresh, Test-NoUnexpectedChanges, 읽기 전용 Claude 인자, Test-ReviewJson, 제한적 갱신) 동작 보존
  - [pass] 13. Codex 성공 후 implemented 케이스 진입 시 Test-BaseCommitFresh 재실행
  - [pass] 14. 계획 밖 새 기능·State 값·관련 없는 함수 리팩터링 없음
  - [pass] 15. 변경 파일은 계획된 두 파일(run-next-step.ps1, current.md)만 (logs/events_log.csv는 착수 전부터 있던 런타임 산출물)
  - [pass] 16. 추가/삭제 파일 없음
- 남은 위험/후속 작업:
  - 실제 Codex/Claude CLI 및 Ctrl+Alt+H 단축키를 통한 종단 실행 테스트 미완료 — 실제 화면에서 planned→approved 연쇄 흐름과 각 중단 경로를 확인해야 합니다.
  - 첫 번째 switch에서 `break` 대신 `exit $ExitCode`를 사용하게 됐는데, PowerShell에서 `exit`는 `finally` 블록을 실행하므로 lock 해제에는 문제가 없지만 실제 CLI 실행으로 확인 권장.
  - logs/events_log.csv는 Codex가 이번 작업에서 수정하지 않은 파일이지만 git status에 변경으로 표시됨 — PR 생성 전 커밋 범위에서 이 파일을 포함할지 여부를 사용자가 결정해야 합니다.
- (Harness가 검증된 Claude 리뷰 JSON을 기계적으로 반영한 결과입니다.)

---

### 사용자 확인 완료, 구현 완료·최종 E2E 미검증 (2026-09-22, State: `approved` → `verified`)

사용자가 구현 결과·테스트 결과·리뷰 결과를 검토하고 `verified`로 확정했다. **다만 아래 사항은 명확히 구분해 기록한다**:

- **구현 완료**: 계획한 16개 수용 기준 전부가 코드 diff·모의 실행(함수 추출 후 mock 기반 시나리오 30여 개, 핸드오프 진단 8개 케이스, 안전장치 원본 비교)으로 검증됐고 Claude 리뷰도 승인했다.
- **최종 E2E 미검증**: 그러나 실제 `codex`/`claude` CLI와 Ctrl+Alt+H 단축키를 통해 `planned → Codex 구현 → handoff 재검사 → implemented → Claude 리뷰 → approved` 전체를 한 번에 실제로 통과시켜보는 종단(End-to-End) 테스트는 아직 하지 않았다. "테스트 결과"의 "미실행 항목과 사유"에도 명시돼 있듯, 실제 1200초 timeout/프로세스 강제 종료, 실제 네트워크 오류, 실제 `implementing` 조건부 재개 분기(완결/불완전 두 갈래 모두)는 모의 실행으로만 확인됐고 실제 환경에서는 검증되지 않았다.

**후속 조치**: 다음에 이 스크립트로 실제 작업을 진행할 때(다음 제품/하네스 작업에서 Ctrl+Alt+H를 처음 눌렀을 때) 이 연쇄 흐름이 실제로도 계획대로 동작하는지 자연스럽게 확인하게 된다. 만약 실제 실행에서 계획과 다른 동작(예: 연쇄가 끊기거나, `[NEXT]` 안내가 부정확하거나, `implementing` 조건부 재개가 오작동)이 발견되면, 이는 새로운 버그로 별도 기록·처리한다.
