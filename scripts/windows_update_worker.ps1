#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$JobPath,
    [Parameter(Mandatory = $true)]
    [int]$ParentPid
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:ResolvedJobPath = [IO.Path]::GetFullPath($JobPath)
$script:JobDir = Split-Path -Parent $script:ResolvedJobPath
$script:LogPath = Join-Path $script:JobDir "windows-update-worker.log"

function Write-OrchestratorLog {
    param([string]$Message)
    $line = "{0} orchestrator {1}" -f ([DateTime]::UtcNow.ToString("o")), $Message
    Add-Content -LiteralPath $script:LogPath -Value $line -Encoding utf8
}

function Set-JobField {
    param(
        [Parameter(Mandatory = $true)]$Job,
        [Parameter(Mandatory = $true)][string]$Name,
        $Value
    )
    if ($Job.PSObject.Properties.Name -contains $Name) {
        $Job.$Name = $Value
    } else {
        $Job | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    }
}

function Save-Job {
    param([Parameter(Mandatory = $true)]$Job)
    Set-JobField $Job "updated_at" ([DateTime]::UtcNow.ToString("o"))
    $tmp = "$script:ResolvedJobPath.partial"
    $json = $Job | ConvertTo-Json -Depth 24
    [IO.File]::WriteAllText($tmp, $json, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $script:ResolvedJobPath -Force
}

function Assert-LoopbackHealthUrl {
    param([Parameter(Mandatory = $true)][string]$Url)
    try {
        $uri = [Uri]$Url
    } catch {
        throw "UPDATE_WINDOWS_DB_ROLLBACK_HEALTH_URL_INVALID"
    }
    if (
        $uri.Scheme -ne "http" -or
        $uri.Host -notin @("127.0.0.1", "localhost", "::1") -or
        $uri.AbsolutePath -ne "/health" -or
        $uri.Query -or
        $uri.Fragment
    ) {
        throw "UPDATE_WINDOWS_DB_ROLLBACK_HEALTH_URL_NOT_LOOPBACK"
    }
    return $uri.AbsoluteUri
}

function Wait-RuntimeHealth {
    param(
        [Parameter(Mandatory = $true)][string]$HealthUrl,
        [int]$TimeoutSeconds = 60
    )
    $url = Assert-LoopbackHealthUrl $HealthUrl
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 2
            if ($response.status -eq "ok" -and $response.db -eq "ok") {
                return
            }
        } catch {
            # Restored runtime may still be starting.
        }
        Start-Sleep -Milliseconds 500
    }
    throw "UPDATE_WINDOWS_DB_ROLLBACK_RUNTIME_HEALTH_FAILED"
}

$core = Join-Path $PSScriptRoot "windows_update_worker_core.ps1"
if (-not (Test-Path -LiteralPath $core -PathType Leaf)) {
    throw "UPDATE_WINDOWS_WORKER_CORE_MISSING"
}
$nativePs = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
if (-not (Test-Path -LiteralPath $nativePs -PathType Leaf)) {
    throw "UPDATE_WINDOWS_POWERSHELL51_MISSING"
}

& $nativePs -NoProfile -ExecutionPolicy Bypass -File $core -JobPath $script:ResolvedJobPath -ParentPid $ParentPid
$coreExit = $LASTEXITCODE

if ($coreExit -eq 0) {
    $finalizeJob = $null
    try {
        $finalizeJob = Get-Content -LiteralPath $script:ResolvedJobPath -Raw | ConvertFrom-Json
        if (
            [string]$finalizeJob.status -ne "health_pending" -or
            [string]$finalizeJob.worker_result -ne "install_verified" -or
            [string]$finalizeJob.package_self_test -ne "passed" -or
            [string]$finalizeJob.runtime_health -ne "passed" -or
            [string]$finalizeJob.rollback -ne "not_needed"
        ) {
            throw "UPDATE_WINDOWS_FINALIZE_JOB_TRUTH_INVALID"
        }
        $installDir = [IO.Path]::GetFullPath([string]$finalizeJob.install_dir)
        $executable = Join-Path $installDir "DigitalCrown.exe"
        if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
            throw "UPDATE_WINDOWS_FINALIZE_EXECUTABLE_MISSING"
        }
        $finalizeArgs = @(
            "--update-finalize-worker",
            ('"{0}"' -f $script:ResolvedJobPath)
        )
        $finalizer = Start-Process -FilePath $executable -ArgumentList $finalizeArgs -WorkingDirectory $installDir -Wait -PassThru
        if ($finalizer.ExitCode -ne 0) {
            throw "UPDATE_WINDOWS_FINALIZE_WORKER_FAILED:$($finalizer.ExitCode)"
        }
        $finalized = Get-Content -LiteralPath $script:ResolvedJobPath -Raw | ConvertFrom-Json
        if (
            [string]$finalized.status -ne "healthy" -or
            [string]$finalized.version -ne [string]$finalizeJob.version -or
            [int]$finalized.sequence -ne [int]$finalizeJob.sequence
        ) {
            throw "UPDATE_WINDOWS_FINALIZE_COMMIT_INVALID"
        }
        Write-OrchestratorLog "finalization=passed version=$([string]$finalized.version) sequence=$([int]$finalized.sequence)"
        exit 0
    } catch {
        $failure = $_.Exception.Message
        $failureJob = $finalizeJob
        try {
            $failureJob = Get-Content -LiteralPath $script:ResolvedJobPath -Raw | ConvertFrom-Json
        } catch {}
        if ($failureJob) {
            $failedRuntimePid = 0
            try { $failedRuntimePid = [int]$failureJob.runtime_pid } catch {}
            if ($failedRuntimePid -gt 0) {
                Stop-Process -Id $failedRuntimePid -Force -ErrorAction SilentlyContinue
            }
            Set-JobField $failureJob "finalization" "failed"
            Set-JobField $failureJob "finalization_failure_reason" $failure
            Save-Job $failureJob
        }
        Write-OrchestratorLog "finalization=failed reason=$failure"
        exit 4
    }
}

if ($coreExit -ne 3) {
    exit $coreExit
}

try {
    $job = Get-Content -LiteralPath $script:ResolvedJobPath -Raw | ConvertFrom-Json
} catch {
    Write-OrchestratorLog "core_exit=3 job_unreadable"
    exit 3
}

$eligible = (
    [string]$job.status -eq "rollback_failed" -and
    [string]$job.worker_result -eq "rollback_failed" -and
    [string]$job.rollback_failure_reason -eq "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED" -and
    [string]$job.database_rollback -eq "required_but_not_wired"
)
if (-not $eligible) {
    Write-OrchestratorLog "core_exit=3 database_fallback=not_eligible reason=$([string]$job.rollback_failure_reason)"
    exit 3
}

$runtime = $null
try {
    $installDir = [IO.Path]::GetFullPath([string]$job.install_dir)
    if (-not [IO.Path]::IsPathRooted($installDir)) {
        throw "UPDATE_WINDOWS_DB_ROLLBACK_INSTALL_DIR_INVALID"
    }
    $executable = Join-Path $installDir "DigitalCrown.exe"
    if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
        throw "UPDATE_WINDOWS_DB_ROLLBACK_EXECUTABLE_MISSING"
    }
    $healthUrl = Assert-LoopbackHealthUrl ([string]$job.health_url)
    $healthTimeout = 60
    if ($job.PSObject.Properties.Name -contains "health_timeout_seconds") {
        $healthTimeout = [int]$job.health_timeout_seconds
    }
    if ($healthTimeout -lt 3 -or $healthTimeout -gt 180) {
        throw "UPDATE_WINDOWS_DB_ROLLBACK_HEALTH_TIMEOUT_INVALID"
    }

    Set-JobField $job "status" "database_rolling_back"
    Set-JobField $job "database_rollback" "running"
    Set-JobField $job "database_rollback_started_at" ([DateTime]::UtcNow.ToString("o"))
    Save-Job $job
    Write-OrchestratorLog "database_fallback=starting old_binary=$executable"

    $dbArgs = @(
        "--update-db-rollback-worker",
        ('"{0}"' -f $script:ResolvedJobPath)
    )
    $dbWorker = Start-Process -FilePath $executable -ArgumentList $dbArgs -WorkingDirectory $installDir -Wait -PassThru
    if ($dbWorker.ExitCode -ne 0) {
        throw "UPDATE_WINDOWS_DB_ROLLBACK_WORKER_FAILED:$($dbWorker.ExitCode)"
    }

    $previousRestart = $env:DIGITALCROWN_RESTORE_RESTART
    $env:DIGITALCROWN_RESTORE_RESTART = "1"
    try {
        $runtime = Start-Process -FilePath $executable -WorkingDirectory $installDir -PassThru
    } finally {
        if ($null -eq $previousRestart) {
            Remove-Item Env:DIGITALCROWN_RESTORE_RESTART -ErrorAction SilentlyContinue
        } else {
            $env:DIGITALCROWN_RESTORE_RESTART = $previousRestart
        }
    }
    Wait-RuntimeHealth -HealthUrl $healthUrl -TimeoutSeconds $healthTimeout

    Set-JobField $job "status" "rolled_back"
    Set-JobField $job "worker_result" "rolled_back"
    Set-JobField $job "rollback" "passed"
    Set-JobField $job "database_rollback" "passed"
    Set-JobField $job "database_rollback_report" "db-rollback-report.json"
    Set-JobField $job "runtime_pid" ([int]$runtime.Id)
    Save-Job $job
    Write-OrchestratorLog "database_fallback=passed runtime_pid=$($runtime.Id)"
    exit 2
} catch {
    $failure = $_.Exception.Message
    if ($runtime -and -not $runtime.HasExited) {
        Stop-Process -Id $runtime.Id -Force -ErrorAction SilentlyContinue
    }
    Set-JobField $job "status" "rollback_failed"
    Set-JobField $job "worker_result" "rollback_failed"
    Set-JobField $job "rollback" "failed"
    Set-JobField $job "database_rollback" "failed"
    Set-JobField $job "database_rollback_failure_reason" $failure
    Save-Job $job
    Write-OrchestratorLog "database_fallback=failed reason=$failure"
    exit 3
}
