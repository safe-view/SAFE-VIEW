<#
  Harness: Run Next Step
  ------------------------
  docs/tasks/current.md의 State를 읽어 정확히 한 단계만 진행하고 종료한다.
  watch/loop/자동 재시도는 없다. 실패 시 다음 단계로 진행하지 않는다.

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
    exit 1
}

try {
    # -----------------------------------------------------------------------
    # 3. current.md 파싱
    # -----------------------------------------------------------------------
    if (-not (Test-Path $CurrentMdPath)) {
        Write-HLog 'FAIL' "current-md-not-found: $CurrentMdPath"
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
            return $false
        }
        $head = Get-CurrentHead
        if ($BaseCommit -ne $head) {
            Write-HLog 'FAIL' "stale: base_commit=$BaseCommit current_head=$head"
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
        $startIdx = $Text.IndexOf($Heading)
        if ($startIdx -lt 0) { return '' }
        $afterIdx = $startIdx + $Heading.Length
        $rest = $Text.Substring($afterIdx)
        $m = [regex]::Match($rest, '(?m)^## ')
        if ($m.Success) { return $rest.Substring(0, $m.Index) }
        return $rest
    }

    function Test-HandoffFormat([string]$Text) {
        $impl = Get-SectionText $Text '## 구현 결과'
        $test = Get-SectionText $Text '## 테스트 결과'
        $combined = $impl + "`n" + $test

        if ($combined -match [regex]::Escape('(Codex 작성)')) { return $false }
        if ($combined -notmatch [regex]::Escape('계획 이탈 사항')) { return $false }
        if ($combined -notmatch [regex]::Escape('종료 시점 git 상태')) { return $false }
        if ($combined -notmatch '-\s*\[[ xX]\]') { return $false }
        return $true
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
        $startIdx = $Text.IndexOf($Heading)
        if ($startIdx -lt 0) { throw "section-not-found: $Heading" }
        $afterHeadingIdx = $startIdx + $Heading.Length
        $rest = $Text.Substring($afterHeadingIdx)
        $m = [regex]::Match($rest, '(?m)^## ')
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
        'planned' {
            if ($ApprovalRequired -and -not $ApprovalDone) {
                Write-HLog 'STOP' 'user-approval-required: 승인 필요 항목이 아직 완료되지 않았습니다.'
                $ExitCode = 0
                break
            }
            if (-not (Test-BaseCommitFresh)) { $ExitCode = 1; break }

            $codexExe = Resolve-AgentExe 'codex'
            if (-not $codexExe) {
                Write-HLog 'FAIL' 'codex-not-found: PATH 또는 %APPDATA%\npm 에서 codex를 찾을 수 없습니다.'
                $ExitCode = 1
                break
            }

            $codexArgs = @(
                '-a', 'never',
                'exec',
                '-C', $RepoRoot,
                '-s', 'workspace-write',
                '--ephemeral',
                $CodexPrompt
            )

            Write-HLog 'INFO' 'invoking-codex (implementing)'
            $result = Invoke-AgentProcess -Exe $codexExe -ArgumentList $codexArgs -TimeoutSec $TimeoutSec

            if ($result.TimedOut) {
                Write-HLog 'FAIL' "codex-timeout: ${TimeoutSec}s 초과. 프로세스를 종료했습니다. 다음 단계로 진행하지 않습니다."
                $ExitCode = 1
                break
            }
            if (-not $result.Ok) {
                Write-HLog 'FAIL' ("codex-exit-{0}: 구현이 실패했을 수 있습니다. current.md와 아래 로그를 직접 확인하세요." -f $result.ExitCode)
                Write-Output ('stdout log: ' + $result.StdOutFile)
                Write-Output ('stderr log: ' + $result.StdErrFile)
                $ExitCode = 1
                break
            }

            Write-HLog 'OK' 'codex-invoked: Codex 호출이 종료 코드 0으로 완료됐습니다. current.md의 State를 직접 확인하세요.'
            $ExitCode = 0
            break
        }

        'implemented' {
            if (-not (Test-HandoffFormat $content)) {
                Write-HLog 'STOP' 'handoff-format-incomplete: 계획 이탈 사항/종료 시점 git 상태/수용 기준 체크리스트 중 누락이 있어 Claude를 호출하지 않습니다. Codex 재작업이 필요합니다.'
                $ExitCode = 0
                break
            }
            if (-not (Test-BaseCommitFresh)) { $ExitCode = 1; break }

            $claudeExe = Resolve-AgentExe 'claude'
            if (-not $claudeExe) {
                Write-HLog 'FAIL' 'claude-not-found: PATH 또는 %APPDATA%\npm 에서 claude를 찾을 수 없습니다.'
                $ExitCode = 1
                break
            }

            $schemaJson = $null
            try {
                $schemaRaw = Read-Utf8File $SchemaPath
                $schemaJson = ($schemaRaw | ConvertFrom-Json | ConvertTo-Json -Depth 10 -Compress)
            } catch {
                Write-HLog 'FAIL' "schema-read-failed: $($_.Exception.Message)"
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

            Write-HLog 'INFO' 'invoking-claude-reviewer (read-only)'
            $result = Invoke-AgentProcess -Exe $claudeExe -ArgumentList $claudeArgs -TimeoutSec $TimeoutSec

            if ($result.TimedOut) {
                Write-HLog 'FAIL' "claude-timeout: ${TimeoutSec}s 초과. State를 바꾸지 않습니다."
                $ExitCode = 1
                break
            }
            if (-not $result.Ok) {
                Write-HLog 'FAIL' ("claude-exit-{0}: 리뷰 호출이 실패했습니다. State를 바꾸지 않습니다." -f $result.ExitCode)
                Write-Output ('stdout log: ' + $result.StdOutFile)
                Write-Output ('stderr log: ' + $result.StdErrFile)
                $ExitCode = 1
                break
            }

            $envelope = $null
            try { $envelope = $result.StdOut | ConvertFrom-Json } catch { }
            if ($null -eq $envelope -or $envelope.is_error -eq $true) {
                Write-HLog 'FAIL' 'claude-response-error: CLI 응답 파싱 실패 또는 is_error=true. State를 바꾸지 않습니다.'
                Write-Output ('stdout log: ' + $result.StdOutFile)
                $ExitCode = 1
                break
            }

            $reviewObj = $envelope.structured_output

            $head = Get-CurrentHead
            $check = Test-ReviewJson $reviewObj $BaseCommit $head
            if (-not $check.Ok) {
                Write-HLog 'FAIL' ("review-validation-failed:{0}: State를 바꾸지 않습니다. 수동 확인이 필요합니다." -f $check.Reason)
                Write-Output ('raw structured_output: ' + ($reviewObj | ConvertTo-Json -Depth 10 -Compress))
                $ExitCode = 1
                break
            }

            if ($reviewObj.verdict -eq 'approved') {
                Update-CurrentMdFromReview $reviewObj 'approved'
                Write-HLog 'OK' 'review-approved: State를 approved로 갱신했습니다. 사용자 확인(verified) 대기.'
            } else {
                Update-CurrentMdFromReview $reviewObj 'implementing'
                Write-HLog 'OK' 'review-rejected: State를 implementing으로 되돌렸습니다. current.md의 반려 사유를 확인하세요.'
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
