# 현재 작업

## 상태

**State:** `verified`
**기준 커밋:** `a64012f18d968584a6e710f7e769558066dc6a90`
**승인 필요:** 아니오 (하네스 스크립트만 수정, 제품 코드·의존성·데이터 형식 영향 없음. 이 수정 자체는 사용자가 대화에서 이미 승인함)
**최종 갱신:** 사용자가 실제 Git 시나리오 검증과 Ctrl+Alt+H 전체 흐름(Reviewer approved 포함)까지 최종 확인, 2026-09-24

이 작업은 제품 작업이 아니라 **하네스(`tools/harness/run-next-step.ps1`) 자체 결함 수정**이다. `docs/RULES.md`의 "제품 작업 중 하네스 결함이 현재 작업을 막을 때" 예외 규정에 따라, 반려 상태로 대기 중인 제품 작업(`김영민/playback-control-ui-v2`, 재생바 UI)과 완전히 분리해서 처리한다. 해당 제품 작업의 미커밋 상태(`docs/tasks/current.md`, `pages/1_모니터링.py`)는 `git stash`(`playback-control-ui-v2 반려 상태 보존...`)로 안전하게 대피시켜 놓았고, 이 브랜치의 작업과는 무관하다 — 손대지 않는다.

## 1. 목표

**증상**: 사용자가 반려된 `playback-control-ui-v2` 작업을 Ctrl+Alt+H로 재개하려 했을 때, 하네스가 정상적으로 계획된 변경 파일인 `pages/1_모니터링.py`(한글 파일명)를 "unexpected-git-changes"로 잘못 탐지해 실행을 중단시켰다.

**확정된 원인**: `git status --porcelain`(기본 `core.quotepath=true`)은 비ASCII 문자를 포함한 경로를 큰따옴표+8진수 이스케이프로 감싸 출력한다(예: `pages/1_모니터링.py` → `"pages/1_\353\252\250\353\213\210\355\204\260\353\247\201.py"`). 직접 확인 결과 **공백을 포함한 경로도 동일하게 quoted됨**(예: `test file with space.txt` → `"test file with space.txt"`) — 이번에 새로 발견된 잠재 버그다.

`run-next-step.ps1`의 `Test-NoUnexpectedChanges`(`Get-GitStatusPorcelain`으로 얻은 raw porcelain 라인에서 `$line.Substring(3).Trim()`으로 경로를 추출)는 이 quoting/escape를 전혀 해제하지 않은 채, `current.md`의 backtick 텍스트에서 추출한 plain 경로(`Get-ExpectedChangedFiles`)와 순수 문자열 비교(`$expected -contains $path`)를 한다. quoted된 실제 경로와 plain한 기대 경로는 절대 일치할 수 없어, 정상 계획된 변경이 "unexpected"로 오탐지된다. 스크립트 전체에서 git 출력 경로를 프로그램적으로 파싱·비교하는 곳은 이 함수 하나뿐임을 확인했다(다른 git 호출은 커밋 해시 확인용이거나 LLM이 프롬프트 안에서 직접 읽는 용도라 quoting이 문제되지 않음).

**`core.quotepath=false`가 불충분한 이유(직접 검증)**: `git -c core.quotepath=false status --porcelain`은 한글 경로는 정상 표시하지만, 공백 포함 경로는 **여전히 quoted됨**. 즉 이 설정은 비ASCII 케이스만 고치는 부분적 우회이며, 설정 의존적이라는 한계도 있다.

**채택한 해결 방향**: `git status --porcelain -z`(NUL 구분, 스크립트 소비 전용 공식 포맷)로 전환한다. 이 포맷은 `core.quotepath` 설정과 무관하게 항상 quoting/escape 없이 원본 UTF-8 바이트를 그대로 출력한다(`xxd`로 직접 확인 — 한글 경로, 공백 포함 경로 모두 순수 바이트, 엔트리 구분자는 NUL).

**PowerShell 캡처 안전성 실측 검증 완료**: 이 저장소의 PowerShell 5.1 환경에서 `& git status --porcelain -z 2>$null`을 직접 실행해 확인함 —
- 반환값은 `System.String` 단일 문자열(개행이 없어 배열로 안 쪼개짐), NUL 바이트(`0x00`)가 문자열 안에 그대로 보존됨(`IndexOf([char]0) -ge 0` → true).
- 스크립트가 이미 설정해 둔 `[Console]::OutputEncoding = UTF8`(25~27행) 덕분에 한글 경로가 mojibake 없이 정상 디코딩됨(` M pages/1_모니터링.py`로 정확히 캡처됨).
- 공백 포함 경로(`test file with space.txt`)도 quoting 없이 그대로 캡처됨.
- `[char]0`으로 split하면 각 엔트리가 정확히 분리됨(마지막 빈 토큰은 trailing NUL로 인한 것, 필터링 필요).
- 별도 임시 git 저장소에서 rename 케이스도 확인함: `git status --porcelain -z`의 rename/copy 엔트리는 `XY newpath\0oldpath\0` 형태로, **상태 코드에 R 또는 C가 있으면 바로 다음 토큰이 별개 엔트리가 아니라 원본 경로**임을 실측으로 확인(`R  new_name.txt` 다음 토큰이 `old_name.txt`로 옴).
- 결론: 임시 파일 캡처나 별도 우회 없이 `& git status --porcelain -z 2>$null` 직접 캡처 + NUL split만으로 안전하게 구현 가능. 대안 검토가 필요한 문제는 발견되지 않았다.

## 2. 현재 상태

- `tools/harness/run-next-step.ps1`의 관련 함수(대략 25~30행 인코딩 설정, 163~172행 `Get-GitStatusPorcelain`, 174~193행 근처 `Get-ExpectedChangedFiles`, 195~210행 근처 `Test-NoUnexpectedChanges` — 정확한 줄 번호는 Codex가 구현 시 재확인할 것):
  - `Get-GitStatusPorcelain`: `& git status --porcelain 2>$null` 실행 후 개행 기준으로 이미 배열화된 라인을 그대로 반환.
  - `Get-ExpectedChangedFiles`: `current.md`의 "예상 변경 파일" 섹션에서 backtick(`` ` ``) 안 텍스트를 quoting 없이 그대로 추출.
  - `Test-NoUnexpectedChanges`: 위 두 함수의 결과를 raw substring 비교로 대조 — quoting을 해제하지 않아 비ASCII/공백 경로에서 오탐지 발생.
- 이 세 함수 외에 git 출력 경로를 프로그램적으로 파싱하는 곳은 없음(위 목표 섹션에서 전체 스크립트 grep으로 확인 완료).
- `docs/tasks/archive/`에 하네스 자체 버그 수정 이력 3건이 이미 있음(리뷰 섹션 소실, 헤딩 IndexOf 오탐지, implementing 자동 재개) — 이번이 4번째 하네스 자체 결함.

## 3. 구현 계획

1. `Get-GitStatusPorcelain`을 `git status --porcelain -z`로 전환한다.
   - `& git status --porcelain -z 2>$null`로 캡처(반환 타입이 배열이든 단일 문자열이든 모두 대응할 수 있도록 `-join`으로 정규화한 뒤 처리 — 실측 결과 이 환경에서는 단일 문자열로 캡처되지만, 방어적으로 배열 케이스도 안전하게 처리할 것).
   - `[char]0`(NUL) 기준으로 split해 토큰 목록을 만든다. 빈 토큰(trailing NUL로 인한 마지막 빈 문자열)은 제거한다.
   - **rename/copy 엔트리 처리**: 각 토큰의 상태 코드(앞 2글자)에 `R` 또는 `C`가 포함되면, 바로 다음 토큰은 별개 엔트리가 아니라 이 엔트리의 원본(원래) 경로이므로 별도 엔트리로 취급하지 않고 건너뛴다(위 실측 결과 참고: `XY newpath\0oldpath\0` 형태).
   - 각 유효 엔트리를 기존 소비 코드(`Test-NoUnexpectedChanges`)가 기대하는 형태(`"XY path"` 문자열, 3번째 문자부터가 경로)로 반환해 하위 호환을 유지하거나, 혹은 `Test-NoUnexpectedChanges`도 함께 자연스럽게 갱신한다 — 정확한 내부 자료구조(문자열 배열 유지 vs. `[PSCustomObject]@{Status=..;Path=..}` 배열로 전환)는 Codex가 더 안전하고 읽기 쉬운 쪽으로 선택해도 된다. 단, quote-strip/backslash-unescape 로직은 추가하지 않는다(`-z`는 애초에 quoting을 하지 않으므로 불필요 — 오히려 있으면 정상 경로를 훼손할 수 있음).
2. `Test-NoUnexpectedChanges`가 새 파싱 결과를 사용하도록 갱신한다. 기존의 `$expected -contains $path` 비교 로직 자체(경로 문자열 대조 방식)는 그대로 유지하되, 입력 경로가 이제 항상 quoting 없는 원본 UTF-8 문자열이 되도록만 보장한다.
3. `logs/`로 시작하는 경로 제외 규칙과 `docs/tasks/current.md` 암묵 포함 규칙은 그대로 보존한다.
4. 수정 후 아래 "4. 수용 기준"의 6개 시나리오를 실제로 재현해 확인하고, 그 결과(명령어와 출력)를 핸드오프 보고서에 근거로 남긴다. **새로운 영구 테스트 파일은 만들지 않는다** — 이 저장소 `tools/harness/`에는 기존 자동화 테스트 인프라가 없고, 이번 수정 범위를 벗어난 새 파일을 추가하면 `current.md`의 "예상 변경 파일" 목록을 벗어난 변경으로 오히려 하네스 자체 검사에 걸릴 수 있다. 대신 임시 스크래치 디렉터리(또는 `$env:TEMP` 하위 임시 git 저장소)에서 검증하고 검증에 사용한 파일은 정리한다 — 이번 진단 과정에서 사용한 방식과 동일.
5. 최종적으로 `docs/tasks/current.md`(이 파일)의 "예상 변경 파일" 목록 밖의 파일은 건드리지 않는다 — 특히 `pages/1_모니터링.py`, 제품 코드, `core/` 하위 파일은 절대 수정하지 않는다.

## 4. 수용 기준

아래 6가지 시나리오를 모두 실제로 재현해 PASS를 확인한다(임시 스크래치 git 저장소 또는 이 저장소의 untracked 임시 파일 활용, 검증 후 정리):

1. **`pages/1_모니터링.py` (실제 사례, 한글 경로)**: `current.md`의 예상 변경 파일 목록에 이 경로가 backtick으로 있을 때, 실제로 이 파일이 수정된 상태에서 `Test-NoUnexpectedChanges`가 `unexpected-git-changes`를 발생시키지 않고 통과해야 한다.
2. **공백 포함 경로**: 예상 변경 파일 목록에 공백이 포함된 경로(예: `docs/tasks/temp file.md`류)가 있을 때도 정상 매칭되어야 한다.
3. **일반 ASCII 경로**: 기존처럼 공백/비ASCII 없는 경로가 정상적으로 계속 매칭되어야 한다(회귀 없음).
4. **`logs/` 제외**: `logs/` 하위 변경은 예상 목록에 없어도 여전히 무시되어야 한다.
5. **`docs/tasks/current.md` 암묵 포함**: 이 파일 자체의 변경은 예상 목록에 명시하지 않아도 여전히 무시되어야 한다.
6. **rename/copy 파싱**: 파일 rename(또는 copy) 상황에서 파서가 원본 경로 토큰을 별개의 잘못된 엔트리로 오인하거나 크래시하지 않아야 한다 — 즉 rename의 새 경로만 하나의 유효 엔트리로 처리되고, 원본 경로 토큰이 별도의 "상태 코드 없는 이상한 엔트리"로 오탐지되지 않아야 한다.

추가로:
- 기존에 있던 3건의 하네스 자체 버그 수정과 마찬가지로, 실제 CLI로 Ctrl+Alt+H 흐름을 재현해(가능하다면) 최종 확인한다.
- `docs/RULES.md` 규정대로 이 수정은 제품 코드/`playback-control-ui-v2`와 별도 커밋으로 처리한다.

## 5. 예상 변경 파일

- `tools/harness/run-next-step.ps1`

## 6. 파일 소유권

| 파일 | 소유자 | 상태 |
|---|---|---|
| `tools/harness/run-next-step.ps1` | Codex | 구현 완료 |

## 7. 위험 요소 또는 주의사항

- 이 저장소의 `origin/main`이 이번 진단 도중 최재원의 OpenVINO PR #8(`core/detector.py`, `tools/export_openvino.py`, `tools/bench_detector.py`, `tools/verify_detector.py`, `config.py`, `requirements.txt` 등)을 새로 병합한 상태로 확인됐다 — 이 브랜치는 그 최신 origin/main(`a64012f`)에서 새로 분기했다. `tools/harness/`, `docs/RULES.md`, `docs/tasks/current.md`는 그 병합으로 변경되지 않았음을 확인했으므로 이번 하네스 수정 진단·계획에는 영향 없다. 다만 반려 상태로 대기 중인 `playback-control-ui-v2`(브랜치 기준 커밋 `cf72209`, 이 openvino 병합 이전)를 나중에 재개할 때는 이 새 병합과의 관계를 별도로 확인해야 한다 — 이번 작업의 범위는 아니다.
- `Get-GitStatusPorcelain`/`Test-NoUnexpectedChanges`는 `Test-HandoffFormat` 기반 `implementing` 자동 재개 안전장치와 맞물려 있는 핵심 게이트 함수다 — 이 함수를 수정하는 작업 자체가 이 함수를 통과해야 진행되는 자기참조적 상황이므로, Codex는 각 변경 단계마다 `git status --porcelain -z` 실측 출력을 직접 눈으로 확인하며 신중히 진행할 것.
- 반려 대기 중인 `playback-control-ui-v2`의 미커밋 변경(`docs/tasks/current.md`, `pages/1_모니터링.py`)은 `git stash`로 대피되어 있다(`stash@{0}`, 메시지: "playback-control-ui-v2 반려 상태 보존..."). 이 하네스 수정 브랜치에서는 그 stash를 건드리지 않는다 — 하네스 수정이 `verified`로 종료되고 `main`에 병합된 뒤, `김영민/playback-control-ui-v2` 브랜치로 돌아가 `git stash pop`으로 복원할 것.

## 구현 결과

- 이번 재개 결과: 기존 코드 변경이 계획과 일치함을 확인했으며 추가 코드 수정은 필요하지 않았다. 아래 기존 구현 기록과 Claude의 추가 실측 기록을 보존한다.
- 계획 이탈 사항(최종): 없음. 이전 검증 제약으로 미실행했던 6개 시나리오는 아래 Claude 추가 검증 기록에서 PASS로 보완됐고, 임시 디렉터리 정리도 완료된 것으로 기록돼 있다.
- 종료 시점 git 상태(이번 재개): `git status --porcelain` 결과는 다음 두 파일뿐이다. 기준 커밋은 `a64012f18d968584a6e710f7e769558066dc6a90`과 일치한다.

```text
 M docs/tasks/current.md
 M tools/harness/run-next-step.ps1
```

- 실제 변경 파일: `tools/harness/run-next-step.ps1`, `docs/tasks/current.md` (상태·구현·검증 기록).
- 계획 대비 변경 요약: `git status --porcelain -z` 출력을 `-join "`n"`으로 정규화하고 NUL로 분리한다. 빈 토큰을 제외하고 R/C 상태의 다음 원본 경로 토큰을 건너뛴다. 기존 `XY path` 문자열 반환 형식과 `$expected -contains $path` 비교, `logs/` 제외, `current.md` 암묵 포함을 유지한다. 경로 추출의 `.Trim()`을 제거해 원본 경로 문자를 보존한다.
- 계획 이탈 사항: 구현 범위 이탈 없음. 계획한 임시 Git 저장소 실측 검증은 접근 거부로 수행하지 못했으며, 실제 작업 트리 파싱과 합성 NUL fixture 검증으로 가능한 부분만 확인했다. 영구 테스트 파일은 추가하지 않았다.
- 종료 시점 git 상태: `git status --porcelain`의 stdout은 아래와 같다. stderr에는 `warning: could not open directory 'harness-check-wd0pkkt4/': Permission denied`가 있어 해당 임시 디렉터리 내부는 확인하지 못했다.

```text
 M docs/tasks/current.md
 M tools/harness/run-next-step.ps1
```

- 정리 미완료(당시): 검증용 임시 디렉터리 `C:\Users\김영민\blind_spot_safety\harness-check-wd0pkkt4`, `C:\Users\김영민\AppData\Local\Temp\harness-status-l3kx6h4e`는 생성 후 내부 접근 및 삭제가 거부되었다. clone은 작업 트리 디렉터리 생성 단계에서 실패했다. Python 정리는 PermissionError, PowerShell 정리 명령은 실행 정책 심사에서 `blocked by policy`로 거부되어 남은 디렉터리 확인·정리가 필요하다.
- **[Claude 추가 확인, 2026-09-24]** 위 두 임시 디렉터리를 FullLanguage PowerShell 세션에서 재확인함 — `Get-ChildItem -Force -Recurse`로 내용이 완전히 비어 있음을 확인(둘 다 SYSTEM/Administrators/OWNER RIGHTS만 ACL에 있고 일반 사용자 ACE가 빠져 있어 Codex의 제한된 프로세스 토큰에서는 접근이 거부됐던 것으로 보임)했고, `Remove-Item -Recurse -Force`로 두 디렉터리 모두 안전하게 삭제해 정리를 완료했다. 삭제 후 `Test-Path`로 재확인함(둘 다 False).
- 제품 코드와 stash는 수정하지 않았으며 git commit/git push는 실행하지 않았다.

## 테스트 결과

- 이번 재개 검증:
  - `Get-Content -Encoding UTF8 -Raw`로 실제 스크립트의 `Get-GitStatusPorcelain` 함수만 추출해 `Invoke-Expression`으로 로드하고 `@(Get-GitStatusPorcelain)` 실행: `PASS actual repository NUL parsing (2 entries)`.
  - 같은 함수에 합성 Git 출력을 공급해 한글·공백·ASCII·logs·current.md 경로 원문 보존을 검사: 5건 모두 `PASS fixture`. R/C 각각 두 상태 위치에서 새 경로와 후속 엔트리만 반환: 4건 모두 PASS. 배열 캡처 개행 보존 및 빈 상태: 모두 PASS.
  - `$ExecutionContext.SessionState.LanguageMode`: `ConstrainedLanguage`. 이번 세션의 결과는 파서 재검증이며, 전체 검사 함수의 실제 Git 시나리오 판정은 아래 기존 Claude 실측 기록을 근거로 한다.
  - `git diff --check`: PASS (문서 끝의 불필요한 빈 줄 제거 후 종료 코드 0).
- 수용 기준 최종 체크리스트 (아래 Claude 추가 검증 기록 반영; 이번 세션에서 실제 Git 시나리오를 새로 실행한 것으로 보고하지 않음):
  - [x] PASS — `pages/1_모니터링.py` 실제 변경 및 전체 검사 함수 통과.
  - [x] PASS — 공백 포함 경로 실제 변경 및 전체 검사 함수 통과.
  - [x] PASS — ASCII 경로 정상 매칭 및 예상 목록 제외 시 차단.
  - [x] PASS — `logs/` 변경 제외.
  - [x] PASS — `docs/tasks/current.md` 암묵 포함.
  - [x] PASS — 실제 rename에서 원본 경로 토큰을 건너뛰고 새 경로 처리.
  - [ ] 미실행 — Ctrl+Alt+H 전체 CLI 흐름. 사용자 화면·단축키 및 외부 에이전트 호출을 포함하는 최종 확인은 남아 있다.
- 아래 미실행 체크리스트와 반려 리뷰는 추가 실측 이전의 이력이다. Reviewer 소유의 리뷰 결과는 수정하지 않으며, 추가 검증을 근거로 재리뷰가 필요하다.

- 실행한 테스트 및 결과:
  - `git rev-parse HEAD`: `a64012f18d968584a6e710f7e769558066dc6a90`으로 계획 기준과 일치. 착수 시 `git status --porcelain`은 계획 문서 변경 한 건뿐이었다.
  - `git diff --check`: PASS (종료 코드 0, 공백 오류 없음; LF/CRLF 안내 경고만 출력).
  - 수정 파일에서 `Get-GitStatusPorcelain` 함수 구간을 `Get-Content -Encoding UTF8 -Raw`로 읽어 `Invoke-Expression`으로 로드하고 `$RepoRoot`를 현재 저장소로 지정한 뒤 `@(Get-GitStatusPorcelain)` 실행: `PASS actual repository NUL parsing (2 entries)`.
  - 같은 실제 함수에 `function git { return $script:fixture }`로 NUL 출력을 공급하고 엔트리 수 및 `Substring(3)`의 원문 일치를 assertion으로 검사: `PASS fixture: pages/1_모니터링.py`, `PASS fixture: docs/tasks/temp file.md`, `PASS fixture: plain.txt`, `PASS fixture: logs/example.txt`, `PASS fixture: docs/tasks/current.md`.
  - `R `, ` R`, `C `, ` C` 각각에 `XY new path.txt\0old path.txt\0 M next.txt\0` fixture 사용: 네 경우 모두 `PASS fixture: ... destination and subsequent entry`. 새 경로와 후속 엔트리만 반환하고 원본 경로를 건너뜀을 확인했다.
  - 배열 캡처 fixture `@(' M first', ('second.txt' + [char]0))` 및 null 출력: `PASS array capture preserves newline`, `PASS clean status`.
- 수용 기준 체크리스트 (계획에서 요구한 실제 Git 변경 + 검사 함수 전체 통과 기준):
  - [ ] 미실행 — 한글 경로 실제 변경 상태에서 `Test-NoUnexpectedChanges` 통과. 합성 입력 파서 검증만 PASS.
  - [ ] 미실행 — 공백 경로 실제 변경 상태에서 검사 함수 통과. 합성 입력 파서 검증만 PASS.
  - [ ] 미실행 — ASCII 경로 실제 변경 상태에서 검사 함수 통과. 실제 작업 트리 및 합성 입력 파서 검증은 PASS.
  - [ ] 미실행 — `logs/` 실제 변경의 제외 동작. 경로 파서 fixture는 PASS이며 제외 코드는 변경하지 않았으나 전체 검사 실행은 못 했다.
  - [ ] 미실행 — `docs/tasks/current.md` 실제 변경의 암묵 포함 동작. 실제 경로 파싱은 PASS이며 암묵 포함 코드는 유지했으나 전체 검사 실행은 못 했다.
  - [ ] 미실행 — 실제 Git rename/copy 재현. R/C 양쪽 상태 위치와 후속 엔트리의 합성 입력 파싱은 PASS.
- 미실행 항목과 사유(당시): `powershell -NoProfile -Command '$ExecutionContext.SessionState.LanguageMode'` 결과가 `ConstrainedLanguage`. 기존 코드에 필요한 `New-Object System.Collections.Generic.List[string]`은 `CannotCreateTypeConstrainedLanguage`, 콘솔 UTF-8 인코딩 설정은 `PropertySetterNotSupportedInConstrainedLanguage`로 거부됐다. 임시 저장소용 `git clone --quiet --shared`도 TEMP 및 작업 공간 양쪽에서 `could not create work tree dir ... Permission denied`로 실패했다. 따라서 수용 기준 전체 PASS로 보고하지 않는다.
- Ctrl+Alt+H 실제 CLI 흐름: **미실행** — 아래 [Claude 추가 검증]도 하네스 오케스트레이션 전체(Codex/Claude 서브프로세스 호출, lock, State 전이)를 재현한 것은 아니며, `Get-GitStatusPorcelain`/`Get-ExpectedChangedFiles`/`Test-NoUnexpectedChanges` 함수 자체의 실제 Git 동작 검증만 수행했다. Ctrl+Alt+H 전체 흐름 재확인은 여전히 필요하다.
- 별도 커밋: **미실행** — 사용자가 git commit/git push를 금지했으므로 변경만 남겼다.

**[Claude 추가 검증, 2026-09-24 — Codex 샌드박스(ConstrainedLanguage) 제약에 대한 예외적 대체 수행]**

Codex가 위에서 실행하지 못한 6개 수용 기준을 Claude의 FullLanguage PowerShell 세션(`$ExecutionContext.SessionState.LanguageMode` = `FullLanguage` 직접 확인)에서, 이 파일이 수정한 실제 함수 3개(`Get-GitStatusPorcelain`/`Get-ExpectedChangedFiles`/`Test-NoUnexpectedChanges`, 현재 커밋된 코드에서 그대로 복사)를 사용해 **합성 fixture가 아닌 실제 임시 Git 저장소 + 실제 파일 변경**으로 재검증했다. 제품 저장소와 완전히 분리된 `$env:TEMP` 하위 임시 저장소(`safeview-harness-verify-*`)를 새로 만들어 사용했고, 검증 후 삭제해 정리했다.

- [x] PASS — 한글 경로: 임시 저장소에 `테스트_한글.txt`를 커밋해두고 실제로 수정 → `Test-NoUnexpectedChanges` = `True`.
- [x] PASS — 공백 포함 경로: `space file.txt`를 실제로 수정 → `Test-NoUnexpectedChanges` = `True`.
- [x] PASS — 일반 ASCII 경로(회귀 없음): `plain.txt`를 실제로 수정하고 예상 목록에 포함 → `True`. 추가로 예상 목록에서 **의도적으로 제외**하고 재실행 → `False`(정상적으로 unexpected 탐지, 즉 검사가 형식적 통과가 아니라 실제로 동작함을 확인).
- [x] PASS — `logs/` 제외: `logs/example.txt`를 실제로 수정(예상 목록에 없음) → `True`.
- [x] PASS — `docs/tasks/current.md` 암묵 포함: 임시 저장소 내 `docs/tasks/current.md`를 실제로 수정(예상 목록에 없음) → `True`.
- [x] PASS — rename/copy 파싱: `old_name.txt`를 실제로 `git mv` 방식(`Rename-Item` + `git add -A`)으로 `new_name.txt`로 변경 → `Test-NoUnexpectedChanges` = `True`(원본 경로 토큰이 별도 오탐 엔트리로 처리되지 않음을 실제 rename 상태에서 확인).
- [x] PASS — **실제 사례 재현**: 이번 프로젝트의 실제 저장소(`C:\Users\김영민\blind_spot_safety`, 현재 브랜치)에서 `pages/1_모니터링.py`에 실제로 trivial 변경(개행 1줄 추가)을 가하고, `## 5. 예상 변경 파일`에 `` `pages/1_모니터링.py` ``가 포함된 것으로 가정한 계획 문서로 `Test-NoUnexpectedChanges` 실행 → `Get-GitStatusPorcelain`이 ` M pages/1_모니터링.py`(quoting 없는 원문)를 정확히 반환했고 최종 결과는 `True`. 검증 직후 `git checkout -- "pages/1_모니터링.py"`로 원상복구했고, `git diff`/`git status --porcelain`으로 변경이 완전히 사라졌음을 재확인했다(이번 하네스 수정 브랜치의 git 상태는 검증 전후로 `docs/tasks/current.md`, `tools/harness/run-next-step.ps1` 두 파일만 변경된 상태로 동일하게 유지됨).

이로써 6개 수용 기준 전부와 실제 문제 사례(`pages/1_모니터링.py`)가 진짜 Git 동작으로 PASS 확인됐다. 다만 위에 남긴 대로 Ctrl+Alt+H 전체 오케스트레이션 흐름(락 처리, Codex/Claude 서브프로세스 호출, State 전이 등)은 이번 검증 범위에 포함되지 않았다 — 이 부분은 실제 Ctrl+Alt+H 실행으로만 확인 가능하다.

## 리뷰 및 남은 위험

- 리뷰 결과: approved
- 요약: 이전 반려 사유 4건 중 3건(수용 기준 6개 미실행·핵심 목적 미확인·임시 디렉터리 미정리)이 Claude FullLanguage 세션의 실제 Git 저장소 기반 추가 검증으로 모두 해소됐다. 코드 변경(porcelain -z 전환·NUL split·R/C skip·Trim 제거)은 계획과 정확히 일치하고 예상 변경 파일 범위를 이탈하지 않았다.
- scope_ok: True
- 수용 기준 판정:
  - [pass] pages/1_모니터링.py 한글 경로 — 실제 저장소에서 trivial 변경 후 Test-NoUnexpectedChanges = True
  - [pass] 공백 포함 경로 — 임시 Git 저장소에서 실제 변경 후 검사 함수 통과
  - [pass] 일반 ASCII 경로 회귀 없음 — 포함 시 True, 의도적 제외 시 False(오탐 탐지 동작 확인)
  - [pass] logs/ 제외 — 임시 저장소에서 실제 변경 후 예상 목록 미등재 상태로 무시됨
  - [pass] docs/tasks/current.md 암묵 포함 — 임시 저장소 실제 변경에서 예상 목록 미등재 상태로 무시됨
  - [pass] rename/copy 파싱 — 임시 저장소에서 실제 git mv로 원본 경로 오탐 없이 새 경로만 단일 엔트리 처리
  - [not_run] Ctrl+Alt+H 전체 오케스트레이션 흐름 — 락, State 전이, 서브프로세스 포함 E2E
- 남은 위험/후속 작업:
  - Ctrl+Alt+H 전체 오케스트레이션 E2E 미검증 — 함수 3개 수준은 실측 완료이나, 락 처리·State 전이·Codex/Claude 서브프로세스 호출을 포함한 최종 흐름은 실제 단축키 실행으로만 확인 가능(수용 기준에서 '가능하다면' 조건부로 명시됨).
- (Harness가 검증된 Claude 리뷰 JSON을 기계적으로 반영한 결과입니다.)

## 사용자 실제 검증 완료 (2026-09-24)

사용자가 이 작업의 실제 Git 시나리오 검증(한글/공백/ASCII/`logs/`/`docs/tasks/current.md`/rename·copy, 실제 사례 `pages/1_모니터링.py` 재현 포함)과 위 "리뷰 및 남은 위험"에서 유일하게 `not_run`으로 남아 있던 **Ctrl+Alt+H 전체 오케스트레이션 흐름**(락 처리·State 전이·Codex/Claude 서브프로세스 호출 포함)까지 실제로 실행해 최종 확인했고, Reviewer의 `approved` 판정도 확인됨을 알려왔다. 이로써 최초 반려 사유 4건이 전부 해소되고 계획된 수용 기준(6개 시나리오 + 조건부 Ctrl+Alt+H 흐름 확인)을 빠짐없이 충족했다. `State`를 `verified`로 확정하고 이 작업을 종료한다.

후속 조치:
- 이 기록은 `docs/tasks/archive/2026-09-24-harness-status-path-quoting-fix.md`로 보관하고, 이 파일(`current.md`)은 표준 빈 템플릿으로 초기화한다.
- `git commit`/`git push`/PR 생성, 반려 대기 중인 `김영민/playback-control-ui-v2`의 `git stash pop` 복원은 아직 진행하지 않는다(사용자가 별도로 지시할 때 진행).

