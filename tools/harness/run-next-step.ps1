<#
  Harness: Run Next Step
  ------------------------
  docs/tasks/current.md의 State를 읽어 성공 시 planned/implementing → implemented → approved까지 연쇄 실행한다.
  implementing은 완결된 핸드오프 기록이 있을 때만 재개한다.
  watch/loop/자동 재시도는 없다. 실패·반려 시 즉시 중단한다.

  권한:
    - git commit / git push 를 호출하지 않는다 (읽기 전용 git 명령만 사용).
    - 제품 코드(app.py, pages/, core/, config.py 등)를 직접 수정하지 않는다.
    - docs/tasks/current.md는 원칙적으로 수정하지 않되, 검증된 Claude 리뷰 결과를
      반영할 때만 State 줄 / 최종 갱신 줄 / "## 리뷰 및 남은 위험" 섹션 세 곳만
      기계적으로 갱신한다 (docs/RULES.md "작업 상태(State)" 3-5 절 참고).

  이 스크립트는 하네스 인프라이며 제품 코드가 아니다.
#>

[CmdletBinding()]
param()

# ---------------------------------------------------------------------------
# 0. 콘솔/파일 인코딩 (Windows 한글 깨짐 대응)
# ---------------------------------------------------------------------------
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding  = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Read-Utf8File([string]$Path) {
    return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

function Write-Utf8File([string]$Path, [string]$Content) {
    [System.IO.File]::WriteAllText($Path, $Content, $Utf8NoBom)
}

function Write-HLog([string]$Tag, [string]$Message) {
    # 콘솔 코드페이지와 무관하게 상태를 판별할 수 있도록 영어 태그를 항상 앞에 붙인다.
    # Write-Output이 아닌 Write-Host를 쓴다 — Write-Output은 파이프라인에 실려서
    # 이 함수를 호출하는 다른 함수(예: Test-BaseCommitFresh)의 반환값을 배열로
    # 오염시켜 `-not (...)` 같은 불리언 판정을 깨뜨릴 수 있기 때문이다.
    Write-Host ("[{0}] {1}" -f $Tag, $Message)
}

# ---------------------------------------------------------------------------
# 1. 경로/상수
# ---------------------------------------------------------------------------
$RepoRoot      = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$CurrentMdPath = Join-Path $RepoRoot 'docs\tasks\current.md'
$SchemaPath    = Join-Path $PSScriptRoot 'review-schema.json'
$LockPath      = Join-Path $env:TEMP 'blind_spot_safety_harness.lock'
$TimeoutSec    = 1200

# ---------------------------------------------------------------------------
# 2. 중복 실행 방지 (lock)
# ---------------------------------------------------------------------------
if (Test-Path $LockPath) {
    $lockInfo = $null
    try { $lockInfo = Read-Utf8File $LockPath } catch { }
    Write-HLog 'STOP' 'already-running: lock file exists.'
    Write-HLog 'NEXT' '다른 실행이 끝날 때까지 기다리세요. 실행 중인 프로세스가 없음을 확인한 경우에만 남은 lock 파일을 수동 삭제하세요.'
    if ($lockInfo) {
        Write-Output $lockInfo
        if ($lockInfo -match 'pid=(\d+)') {
            $lockPid = [int]$Matches[1]
            $alive = Get-Process -Id $lockPid -ErrorAction SilentlyContinue
            if (-not $alive) {
                Write-HLog 'WARN' ("stale-lock-suspected: PID {0} not found. If you are sure no other run is active, delete `"{1}`" manually." -f $lockPid, $LockPath)
            }
        }
    }
    exit 1
}

$lockContent = "pid=$PID`nstarted=$(Get-Date -Format o)"
try {
    Write-Utf8File $LockPath $lockContent
} catch {
    Write-HLog 'FAIL' "cannot-create-lock: $($_.Exception.Message)"
    Write-HLog 'NEXT' '임시 폴더 접근 권한과 lock 경로를 확인한 뒤 다시 실행하세요.'
    exit 1
}

try {
    # -----------------------------------------------------------------------
    # 3. current.md 파싱
    # -----------------------------------------------------------------------
    if (-not (Test-Path $CurrentMdPath)) {
        Write-HLog 'FAIL' "current-md-not-found: $CurrentMdPath"
        Write-HLog 'NEXT' 'docs/tasks/current.md 경로와 계획 파일을 복구한 뒤 다시 실행하세요.'
        exit 1
    }

    $content = Read-Utf8File $CurrentMdPath

    function Get-FieldValue([string]$Text, [string]$Label) {
        $pattern = '(?m)^\*\*' + [regex]::Escape($Label) + ':\*\*\s*(.*)$'
        $m = [regex]::Match($Text, $pattern)
        if ($m.Success) { return $m.Groups[1].Value.Trim() }
        return $null
    }

    $stateRaw    = Get-FieldValue $content 'State'
    $baseRaw     = Get-FieldValue $content '기준 커밋'
    $approvalRaw = Get-FieldValue $content '승인 필요'

    $State      = $null
    $BaseCommit = $null
    if ($stateRaw)  { $State      = ($stateRaw  -replace '`','').Trim() }
    if ($baseRaw)   { $BaseCommit = ($baseRaw   -replace '`','').Trim() }

    if (-not $State -or $State -eq '없음') {
        Write-HLog 'SKIP' 'no-state: current.md에 진행 중인 작업이 없습니다.'
        exit 0
    }

    $ApprovalRequired = $false
    $ApprovalDone     = $false
    if ($approvalRaw) {
        $ApprovalRequired = [bool]($approvalRaw -match '^\s*예')
        $ApprovalDone     = [bool]($approvalRaw -match '사용자\s*승인\s*:\s*완료')
    }

    Write-HLog 'INFO' "state=$State base_commit=$BaseCommit approval_required=$ApprovalRequired approval_done=$ApprovalDone"

    # -----------------------------------------------------------------------
    # 4. HEAD 신선도 확인 (planned / implemented 에서만 의미가 있다)
    # -----------------------------------------------------------------------
    function Get-CurrentHead {
        Push-Location $RepoRoot
        try {
            $head = (& git rev-parse HEAD 2>$null)
            return ($head | Out-String).Trim()
        } finally {
            Pop-Location
        }
    }

    function Test-BaseCommitFresh {
        if ([string]::IsNullOrWhiteSpace($BaseCommit) -or $BaseCommit -eq '없음') {
            Write-HLog 'FAIL' 'no-base-commit: 기준 커밋이 없어 신선도를 확인할 수 없습니다.'
            Write-HLog 'NEXT' 'Planner에게 현재 HEAD와 계획을 확인하고 기준 커밋을 기록하도록 요청하세요.'
            return $false
        }
        $head = Get-CurrentHead
        if ($BaseCommit -ne $head) {
            Write-HLog 'FAIL' "stale: base_commit=$BaseCommit current_head=$head"
            Write-HLog 'NEXT' 'git log/git diff로 기준 커밋 이후 변경을 확인하고 Planner에게 계획과 기준 커밋 갱신을 요청하세요.'
            return $false
        }
        return $true
    }

    # -----------------------------------------------------------------------
    # 4.5. 예상 밖 변경 사전 체크 (Codex 호출 전에만 수행)
    #      docs/RULES.md의 "Stale State·불일치 감지" 런타임 산출물 예외와 동일한
    #      기준을 쓴다 — 확정 런타임 산출물(logs/)만 제외하고, data/·saved_events/는
    #      이미 gitignore 대상이라 애초에 git status에 나타나지 않으며,
    #      roi_configs/ 등 나머지 경로는 전부 그대로 검사한다.
    # -----------------------------------------------------------------------
    function Get-GitStatusPorcelain {
        Push-Location $RepoRoot
        try {
            $out = (& git status --porcelain -z 2>$null)
            if ($null -eq $out) { return @() }
            $tokens = ($out -join "`n").Split([char]0)
            for ($i = 0; $i -lt $tokens.Count; $i++) {
                $entry = $tokens[$i]
                if ($entry.Length -eq 0) { continue }
                $entry
                # With -z, rename/copy records contain destination then source.
                if ($entry.Substring(0, 2) -match '[RC]') { $i++ }
            }
        } finally {
            Pop-Location
        }
    }

    function Get-ExpectedChangedFiles([string]$Text) {
        $heading = [regex]::Match($Text, '(?m)^##\s*\d*\.?\s*예상 변경 파일\s*$')
        if (-not $heading.Success) { return @() }
        $rest = $Text.Substring($heading.Index + $heading.Length)
        $endMatch = [regex]::Match($rest, '(?m)^#{2,}\s')
        if ($endMatch.Success) { $rest = $rest.Substring(0, $endMatch.Index) }
        $paths = New-Object System.Collections.Generic.List[string]
        foreach ($m in [regex]::Matches($rest, '`([^`]+)`')) {
            $paths.Add($m.Groups[1].Value.Trim())
        }
        return $paths
    }

    function Test-NoUnexpectedChanges {
        $lines = Get-GitStatusPorcelain
        $expected = @(Get-ExpectedChangedFiles $content)
        # current.md는 계획 수립·구현 결과 기록을 위해 매 작업마다 항상 바뀌므로
        # "예상 변경 파일" 목록 표기 여부와 무관하게 관례적으로 예상된 변경으로 취급한다.
        $expected += 'docs/tasks/current.md'

        $unexpected = New-Object System.Collections.Generic.List[string]
        foreach ($line in $lines) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $path = $line.Substring(3)
            # 확정 런타임 산출물 예외: logs/ 아래 변경만 제외한다 (docs/RULES.md "Stale
            # State·불일치 감지" 3항 참고). data/, saved_events/는 이미 gitignore 대상이라
            # 여기 나타나지 않고, roi_configs/ 등 나머지 경로는 그대로 검사 대상이다.
            if ($path -match '^logs/') { continue }
            if ($expected -contains $path) { continue }
            $unexpected.Add($line)
        }
        if ($unexpected.Count -gt 0) {
            Write-HLog 'STOP' 'unexpected-git-changes: current.md의 "예상 변경 파일" 목록과 logs/ 예외를 벗어난 변경이 있어 Codex를 호출하지 않습니다 (불필요한 호출·토큰 낭비 방지). 아래 변경을 직접 확인하세요.'
            Write-HLog 'NEXT' 'git status/git diff로 아래 변경을 확인하고 계획 범위와 일치하도록 정리한 뒤 다시 실행하세요.'
            foreach ($u in $unexpected) { Write-HLog 'INFO' ('  ' + $u) }
            return $false
        }
        return $true
    }

    # -----------------------------------------------------------------------
    # 5. 외부 프로세스 실행 헬퍼 (timeout + UTF-8 리다이렉트)
    # -----------------------------------------------------------------------
    function Resolve-AgentExe([string]$Name) {
        $npmCmd = Join-Path $env:APPDATA ("npm\{0}.cmd" -f $Name)
        if (Test-Path $npmCmd) { return $npmCmd }
        $cmd = Get-Command $Name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
        return $null
    }

    function Format-ProcArg([string]$Value) {
        return '"' + ($Value -replace '"', '\"') + '"'
    }

    function Invoke-AgentProcess {
        param(
            [Parameter(Mandatory = $true)][string]$Exe,
            [Parameter(Mandatory = $true)][string[]]$ArgumentList,
            [int]$TimeoutSec = 1200
        )

        $token      = [guid]::NewGuid().ToString('N')
        $stdoutFile = Join-Path $env:TEMP ("harness_{0}_out.txt" -f $token)
        $stderrFile = Join-Path $env:TEMP ("harness_{0}_err.txt" -f $token)
        $stdinFile  = Join-Path $env:TEMP ("harness_{0}_in.txt" -f $token)
        Write-Utf8File $stdinFile ''

        $argString = ($ArgumentList | ForEach-Object { Format-ProcArg $_ }) -join ' '

        $proc = $null
        try {
            $proc = Start-Process -FilePath $Exe -ArgumentList $argString `
                -NoNewWindow -PassThru `
                -RedirectStandardOutput $stdoutFile `
                -RedirectStandardError $stderrFile `
                -RedirectStandardInput $stdinFile
        } catch {
            return [PSCustomObject]@{
                TimedOut = $false; ExitCode = -1; Ok = $false
                StdOut = ''; StdErr = "process-start-failed: $($_.Exception.Message)"
                StdOutFile = $stdoutFile; StdErrFile = $stderrFile
            }
        }

        Wait-Process -InputObject $proc -Timeout $TimeoutSec -ErrorAction SilentlyContinue

        if (-not $proc.HasExited) {
            try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch { }
            Remove-Item $stdinFile -ErrorAction SilentlyContinue
            return [PSCustomObject]@{
                TimedOut = $true; ExitCode = $null; Ok = $false
                StdOut = ''; StdErr = 'timeout'
                StdOutFile = $stdoutFile; StdErrFile = $stderrFile
            }
        }

        $exitCode = $proc.ExitCode
        $stdout = ''
        $stderr = ''
        try { $stdout = Read-Utf8File $stdoutFile } catch { }
        try { $stderr = Read-Utf8File $stderrFile } catch { }
        Remove-Item $stdinFile -ErrorAction SilentlyContinue

        # 성공(종료코드 0)이면 임시 로그 파일을 정리한다. 실패/비정상 종료 시에는
        # 사람이 직접 열어볼 수 있도록 남겨둔다.
        if ($exitCode -eq 0) {
            Remove-Item $stdoutFile, $stderrFile -ErrorAction SilentlyContinue
        }

        return [PSCustomObject]@{
            TimedOut = $false; ExitCode = $exitCode; Ok = ($exitCode -eq 0)
            StdOut = $stdout; StdErr = $stderr
            StdOutFile = $stdoutFile; StdErrFile = $stderrFile
        }
    }

    # -----------------------------------------------------------------------
    # 6. 핸드오프 형식 최소 검사 (C안) — "구현 결과"/"테스트 결과" 섹션만 검사한다.
    # -----------------------------------------------------------------------
    function Get-SectionText([string]$Text, [string]$Heading) {
        $headingMatch = [regex]::Match($Text, '(?m)^' + [regex]::Escape($Heading) + '\s*$')
        if (-not $headingMatch.Success) { return '' }
        $startIdx = $headingMatch.Index
        $afterIdx = $startIdx + $Heading.Length
        $rest = $Text.Substring($afterIdx)
        $m = [regex]::Match($rest, '(?m)^#{2,}\s')
        if ($m.Success) { return $rest.Substring(0, $m.Index) }
        return $rest
    }

    function Test-HandoffFormat([string]$Text) {
        $impl = Get-SectionText $Text '## 구현 결과'
        $test = Get-SectionText $Text '## 테스트 결과'
        $combined = $impl + "`n" + $test

        $missing = @()
        if ($combined -match [regex]::Escape('(Codex 작성)')) { $missing += '(Codex 작성) placeholder 잔존' }
        if ($impl -notmatch [regex]::Escape('계획 이탈 사항')) { $missing += '구현 결과: 계획 이탈 사항 없음' }
        if ($impl -notmatch [regex]::Escape('종료 시점 git 상태')) { $missing += '구현 결과: 종료 시점 git 상태 없음' }
        if ($test -notmatch '-\s*\[[ xX]\]') { $missing += '테스트 결과: 수용 기준 체크리스트 없음' }
        return [PSCustomObject]@{ Ok = ($missing.Count -eq 0); Missing = $missing }
    }

    # -----------------------------------------------------------------------
    # 7. current.md 제한적 갱신 (3-5) — State / 최종 갱신 / 리뷰 섹션 세 곳만
    # -----------------------------------------------------------------------
    function Set-FieldLine([string]$Text, [string]$Label, [string]$NewValue) {
        $pattern = '(?m)^\*\*' + [regex]::Escape($Label) + ':\*\*.*$'
        $m = [regex]::Match($Text, $pattern)
        if (-not $m.Success) { throw "field-not-found: $Label" }
        $before = $Text.Substring(0, $m.Index)
        $after  = $Text.Substring($m.Index + $m.Length)
        return $before + ('**' + $Label + ':** ' + $NewValue) + $after
    }

    function Set-SectionBody([string]$Text, [string]$Heading, [string]$NewBody) {
        $headingMatch = [regex]::Match($Text, '(?m)^' + [regex]::Escape($Heading) + '\s*$')
        if (-not $headingMatch.Success) { throw "section-not-found: $Heading" }
        $startIdx = $headingMatch.Index
        $afterHeadingIdx = $startIdx + $Heading.Length
        $rest = $Text.Substring($afterHeadingIdx)
        $m = [regex]::Match($rest, '(?m)^#{2,}\s')
        if ($m.Success) {
            $endIdx = $afterHeadingIdx + $m.Index
        } else {
            $endIdx = $Text.Length
        }
        $before = $Text.Substring(0, $afterHeadingIdx)
        $after  = $Text.Substring($endIdx)
        return $before + "`n`n" + $NewBody.TrimEnd() + "`n`n" + $after
    }

    function Test-ReviewJson($ReviewObj, [string]$ExpectedBaseCommit, [string]$CurrentHead) {
        if ($null -eq $ReviewObj) {
            return [PSCustomObject]@{ Ok = $false; Reason = 'parse-failed' }
        }
        $required = @('verdict', 'base_commit_checked', 'scope_ok', 'acceptance_criteria', 'summary')
        foreach ($f in $required) {
            if (-not ($ReviewObj.PSObject.Properties.Name -contains $f)) {
                return [PSCustomObject]@{ Ok = $false; Reason = "missing-field:$f" }
            }
        }
        if ($ReviewObj.verdict -ne 'approved' -and $ReviewObj.verdict -ne 'rejected') {
            return [PSCustomObject]@{ Ok = $false; Reason = 'invalid-verdict' }
        }
        if ($ReviewObj.base_commit_checked -ne $ExpectedBaseCommit) {
            return [PSCustomObject]@{ Ok = $false; Reason = 'base-commit-mismatch-plan' }
        }
        if ($ReviewObj.base_commit_checked -ne $CurrentHead) {
            return [PSCustomObject]@{ Ok = $false; Reason = 'base-commit-mismatch-head' }
        }
        if ($ReviewObj.verdict -eq 'rejected') {
            if (-not $ReviewObj.rejection_reasons -or @($ReviewObj.rejection_reasons).Count -lt 1) {
                return [PSCustomObject]@{ Ok = $false; Reason = 'empty-rejection-reasons' }
            }
        }
        return [PSCustomObject]@{ Ok = $true; Reason = 'ok' }
    }

    function Format-ReviewBody($ReviewObj) {
        $lines = New-Object System.Collections.Generic.List[string]
        $lines.Add('- 리뷰 결과: ' + $ReviewObj.verdict)
        $lines.Add('- 요약: ' + $ReviewObj.summary)
        $lines.Add('- scope_ok: ' + $ReviewObj.scope_ok)
        if ($ReviewObj.acceptance_criteria) {
            $lines.Add('- 수용 기준 판정:')
            foreach ($c in $ReviewObj.acceptance_criteria) {
                $lines.Add(('  - [{0}] {1}' -f $c.result, $c.criterion))
            }
        }
        if ($ReviewObj.rejection_reasons -and @($ReviewObj.rejection_reasons).Count -gt 0) {
            $lines.Add('- 반려 사유:')
            foreach ($r in $ReviewObj.rejection_reasons) { $lines.Add('  - ' + $r) }
        }
        if ($ReviewObj.risks_or_followups -and @($ReviewObj.risks_or_followups).Count -gt 0) {
            $lines.Add('- 남은 위험/후속 작업:')
            foreach ($r in $ReviewObj.risks_or_followups) { $lines.Add('  - ' + $r) }
        }
        $lines.Add('- (Harness가 검증된 Claude 리뷰 JSON을 기계적으로 반영한 결과입니다.)')
        return ($lines -join "`n")
    }

    function Update-CurrentMdFromReview($ReviewObj, [string]$NewState) {
        $text = Read-Utf8File $CurrentMdPath
        $timestamp = Get-Date -Format o
        $text = Set-FieldLine $text 'State' ('`' + $NewState + '`')
        $text = Set-FieldLine $text '최종 갱신' ('Harness (Claude 리뷰 검증 결과 반영), ' + $timestamp)
        $body = Format-ReviewBody $ReviewObj
        $text = Set-SectionBody $text '## 리뷰 및 남은 위험' $body
        Write-Utf8File $CurrentMdPath $text
    }

    # -----------------------------------------------------------------------
    # 8. 고정 프롬프트 (짧게 유지 — current.md를 source of truth로 우선한다)
    # -----------------------------------------------------------------------
    $CodexPrompt = 'docs/tasks/current.md 한 파일을 읽고 그 계획대로 구현하라. ' +
        'AGENTS.md와 docs/RULES.md의 규칙은 이미 계획에 반영돼 있으니 필요할 때만 참고하고 처음부터 다시 해석하지 마라. ' +
        'docs/PRODUCT.md/docs/ARCHITECTURE.md는 계획에 없는 배경지식이 꼭 필요할 때만 읽어라. ' +
        '계획에 명시된 파일만 최소 범위로 수정하라. ' +
        '완료 후 current.md의 "## 구현 결과"와 "## 테스트 결과" 빈칸을 모두 채워라 — ' +
        '실제 변경 파일, 계획 대비 변경 요약, 계획 이탈 사항(없으면 "없음"), ' +
        '`git status --porcelain` 결과를 반영한 종료 시점 git 상태, 수용 기준 각 항목의 PASS/FAIL/미실행 체크리스트를 빠짐없이 적어라. ' +
        '마지막으로 current.md 상단의 State 줄을 `implemented`로 갱신하라. ' +
        'git commit/git push는 하지 마라.'

    $ReviewPrompt = 'docs/tasks/current.md를 읽고 이번 작업을 리뷰하라. ' +
        '너는 읽기 전용이며 어떤 파일도 수정할 수 없다 — current.md도 포함해서 절대 쓰지 마라. ' +
        'git status/diff/log(읽기 전용 명령만)로 실제 변경을 사실로 확인하라. ' +
        '가장 먼저 "## 구현 결과"/"## 테스트 결과"에 계획 이탈 사항, 종료 시점 git 상태, ' +
        '수용 기준 체크리스트가 모두 채워져 있는지 확인하고(0번째 확인), 비어 있으면 반려하라. ' +
        '계획한 파일 범위만 변경됐는지, 기존 로직이 보존됐는지, 수용 기준을 각각 충족하는지 확인하라. ' +
        'base_commit_checked 필드에는 `git rev-parse HEAD`로 직접 확인한 값을 넣어라. ' +
        '결과는 지정된 스키마 필드에만 채워 넣어라.'

    # -----------------------------------------------------------------------
    # 9. State 분기
    #    ExitCode 규약: 0 = 정상 종료(할 일이 없었거나 성공적으로 처리),
    #                   1 = 실패(stale, CLI 없음, timeout, 비정상 종료, 검증 실패 등)
    # -----------------------------------------------------------------------
    $ExitCode = 0

    switch ($State) {
        { $_ -in 'planned', 'implementing' } {
            if ($State -eq 'implementing') {
                $handoff = Test-HandoffFormat $content
                if (-not $handoff.Ok) {
                    Write-HLog 'STOP' 'implementing-incomplete-handoff: 이전 시도가 완료되지 않은 채 중단됐을 가능성이 있어 자동 재개하지 않습니다.'
                    foreach ($item in $handoff.Missing) { Write-HLog 'NEXT' ("기록 확인: $item") }
                    Write-HLog 'NEXT' 'git status/git diff로 실제 변경을 확인하고 필요시 보완하거나 되돌리세요. 문제없다고 판단하면 State를 planned로 직접 전환한 뒤 재실행하세요.'
                    exit 0
                }
            }
            if ($ApprovalRequired -and -not $ApprovalDone) {
                Write-HLog 'STOP' 'user-approval-required: 승인 필요 항목이 아직 완료되지 않았습니다.'
                Write-HLog 'NEXT' '계획에 대한 사용자 승인과 사용자 승인: 완료 기록을 확인한 뒤 다시 실행하세요.'
                $ExitCode = 0
                exit $ExitCode
            }
            if (-not (Test-BaseCommitFresh)) { $ExitCode = 1; exit $ExitCode }
            if (-not (Test-NoUnexpectedChanges)) { $ExitCode = 0; exit $ExitCode }

            $codexExe = Resolve-AgentExe 'codex'
            if (-not $codexExe) {
                Write-HLog 'FAIL' 'codex-not-found: PATH 또는 %APPDATA%\npm 에서 codex를 찾을 수 없습니다.'
                Write-HLog 'NEXT' 'Codex CLI 설치와 PATH를 확인한 뒤 다시 실행하세요.'
                $ExitCode = 1
                exit $ExitCode
            }

            $codexArgs = @(
                '-a', 'never',
                'exec',
                '-C', $RepoRoot,
                '-s', 'workspace-write',
                '--ephemeral',
                $CodexPrompt
            )

            Write-HLog 'RUNNING' "Codex implementing (state=$State)..."
            $result = Invoke-AgentProcess -Exe $codexExe -ArgumentList $codexArgs -TimeoutSec $TimeoutSec

            if ($result.TimedOut) {
                Write-HLog 'FAIL' "codex-timeout: ${TimeoutSec}s 초과. 프로세스를 종료했습니다. 다음 단계로 진행하지 않습니다."
                Write-HLog 'NEXT' '아래 임시 로그와 current.md, git diff로 중단된 작업을 확인하세요. implementing 기록이 불완전하면 변경을 정리하고 planned로 직접 전환한 뒤 재실행하세요.'
                Write-Output ('stdout log: ' + $result.StdOutFile)
                Write-Output ('stderr log: ' + $result.StdErrFile)
                $ExitCode = 1
                exit $ExitCode
            }
            if (-not $result.Ok) {
                Write-HLog 'FAIL' ("codex-exit-{0}: 구현이 실패했을 수 있습니다. current.md와 아래 로그를 직접 확인하세요." -f $result.ExitCode)
                Write-HLog 'NEXT' '아래 stdout/stderr 로그와 current.md, git diff로 실패 원인을 확인하세요. implementing 기록이 불완전하면 변경을 정리하고 planned로 직접 전환한 뒤 재실행하세요.'
                Write-Output ('stdout log: ' + $result.StdOutFile)
                Write-Output ('stderr log: ' + $result.StdErrFile)
                $ExitCode = 1
                exit $ExitCode
            }

            Write-HLog 'OK' 'codex-invoked: Codex 호출이 종료 코드 0으로 완료됐습니다.'
            $content = Read-Utf8File $CurrentMdPath
            $State = ((Get-FieldValue $content 'State') -replace '`', '').Trim()
            $BaseCommit = ((Get-FieldValue $content '기준 커밋') -replace '`', '').Trim()
            if ($State -ne 'implemented') {
                Write-HLog 'STOP' "codex-state-unchanged: Codex가 성공 종료했지만 State가 implemented가 아닙니다 (state=$State)."
                Write-HLog 'NEXT' 'current.md와 Codex 실행 결과를 확인하고 구현 기록 및 State를 보완하세요.'
                exit 0
            }
            break
        }
    }

    # 직접 implemented로 시작한 경우와 Codex 성공 이후에 같은 리뷰 경로를 사용한다.
    switch ($State) {
        'implemented' {
            $handoff = Test-HandoffFormat $content
            if (-not $handoff.Ok) {
                Write-HLog 'STOP' 'handoff-format-incomplete: 핸드오프 기록이 불완전하여 Claude를 호출하지 않습니다.'
                foreach ($item in $handoff.Missing) { Write-HLog 'NEXT' ("Codex에게 기록 보완을 요청하세요: $item") }
                $ExitCode = 0
                break
            }
            if (-not (Test-BaseCommitFresh)) { $ExitCode = 1; break }

            $claudeExe = Resolve-AgentExe 'claude'
            if (-not $claudeExe) {
                Write-HLog 'FAIL' 'claude-not-found: PATH 또는 %APPDATA%\npm 에서 claude를 찾을 수 없습니다.'
                Write-HLog 'NEXT' 'Claude CLI 설치와 PATH를 확인한 뒤 다시 실행하세요.'
                $ExitCode = 1
                break
            }

            $schemaJson = $null
            try {
                $schemaRaw = Read-Utf8File $SchemaPath
                $schemaJson = ($schemaRaw | ConvertFrom-Json | ConvertTo-Json -Depth 10 -Compress)
            } catch {
                Write-HLog 'FAIL' "schema-read-failed: $($_.Exception.Message)"
                Write-HLog 'NEXT' 'review-schema.json 경로와 JSON 형식을 확인하고 복구한 뒤 다시 실행하세요.'
                $ExitCode = 1
                break
            }

            $claudeArgs = @(
                '-p',
                '--permission-mode', 'plan',
                '--allowedTools', 'Read,Grep,Glob,Bash(git status:*),Bash(git diff:*),Bash(git rev-parse:*),Bash(git log:*)',
                '--output-format', 'json',
                '--json-schema', $schemaJson,
                '--no-session-persistence',
                $ReviewPrompt
            )

            Write-HLog 'RUNNING' 'Claude reviewing...'
            $result = Invoke-AgentProcess -Exe $claudeExe -ArgumentList $claudeArgs -TimeoutSec $TimeoutSec

            if ($result.TimedOut) {
                Write-HLog 'FAIL' "claude-timeout: ${TimeoutSec}s 초과. State를 바꾸지 않습니다."
                Write-HLog 'NEXT' '아래 임시 로그와 연결 상태를 확인하고 원인을 해결한 뒤 implemented 상태에서 다시 실행하세요.'
                Write-Output ('stdout log: ' + $result.StdOutFile)
                Write-Output ('stderr log: ' + $result.StdErrFile)
                $ExitCode = 1
                break
            }
            if (-not $result.Ok) {
                Write-HLog 'FAIL' ("claude-exit-{0}: 리뷰 호출이 실패했습니다. State를 바꾸지 않습니다." -f $result.ExitCode)
                Write-HLog 'NEXT' '아래 stdout/stderr 로그로 리뷰 호출 실패 원인을 해결한 뒤 다시 실행하세요.'
                Write-Output ('stdout log: ' + $result.StdOutFile)
                Write-Output ('stderr log: ' + $result.StdErrFile)
                $ExitCode = 1
                break
            }

            $envelope = $null
            try { $envelope = $result.StdOut | ConvertFrom-Json } catch { }
            if ($null -eq $envelope -or $envelope.is_error -eq $true) {
                Write-HLog 'FAIL' 'claude-response-error: CLI 응답 파싱 실패 또는 is_error=true. State를 바꾸지 않습니다.'
                Write-HLog 'NEXT' 'CLI 응답과 연결 상태를 확인하고 JSON 응답 오류를 해결한 뒤 다시 실행하세요.'
                Write-Output ('stdout log: ' + $result.StdOutFile)
                $ExitCode = 1
                break
            }

            $reviewObj = $envelope.structured_output

            $head = Get-CurrentHead
            $check = Test-ReviewJson $reviewObj $BaseCommit $head
            if (-not $check.Ok) {
                Write-HLog 'FAIL' ("review-validation-failed:{0}: State를 바꾸지 않습니다. 수동 확인이 필요합니다." -f $check.Reason)
                Write-HLog 'NEXT' '아래 structured_output과 계획의 기준 커밋을 확인하고 검증 실패 원인을 해결한 뒤 다시 실행하세요.'
                Write-Output ('raw structured_output: ' + ($reviewObj | ConvertTo-Json -Depth 10 -Compress))
                $ExitCode = 1
                break
            }

            if ($reviewObj.verdict -eq 'approved') {
                Update-CurrentMdFromReview $reviewObj 'approved'
                Write-HLog 'OK' 'review-approved: State를 approved로 갱신했습니다. 사용자 확인(verified) 대기.'
            } else {
                Update-CurrentMdFromReview $reviewObj 'implementing'
                Write-HLog 'STOP' 'review-rejected: State를 implementing으로 되돌렸습니다. current.md의 반려 사유를 확인하세요.'
                Write-HLog 'NEXT' 'current.md의 반려 사유와 보완 방향을 확인한 뒤 재실행하세요. 완결된 핸드오프 및 안전장치 검사 후 Codex가 implementing 작업을 재개합니다.'
            }
            $ExitCode = 0
            break
        }

        default {
            Write-HLog 'SKIP' "no-action-for-state: $State"
            $ExitCode = 0
            break
        }
    }

    exit $ExitCode
}
finally {
    Remove-Item $LockPath -ErrorAction SilentlyContinue
}
