#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$JobPath,
    [Parameter(Mandatory = $true)][int]$ParentPid
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedJob = [IO.Path]::GetFullPath($JobPath)
$jobDir = Split-Path -Parent $resolvedJob
$lockPath = Join-Path $jobDir "worker.lock"
$logPath = Join-Path $jobDir "windows-update-worker.log"
$lock = $null
$child = $null

function Write-EntryLog {
    param([string]$Message)
    Add-Content -LiteralPath $logPath -Value ("{0} entry {1}" -f ([DateTime]::UtcNow.ToString("o")), $Message) -Encoding utf8
}

function Set-JobField {
    param($Job, [string]$Name, $Value)
    if ($Job.PSObject.Properties.Name -contains $Name) { $Job.$Name = $Value }
    else { $Job | Add-Member -NotePropertyName $Name -NotePropertyValue $Value }
}

function Save-Job {
    param($Job)
    Set-JobField $Job "updated_at" ([DateTime]::UtcNow.ToString("o"))
    $tmp = "$resolvedJob.partial"
    [IO.File]::WriteAllText($tmp, ($Job | ConvertTo-Json -Depth 24), [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $resolvedJob -Force
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

try {
    if (-not (Test-Path -LiteralPath $resolvedJob -PathType Leaf)) { throw "UPDATE_WINDOWS_JOB_MISSING" }
    $job = Get-Content -LiteralPath $resolvedJob -Raw | ConvertFrom-Json
    $expectedEntrySha = ([string]$job.'windows_update_worker_entry.ps1_sha256').ToLowerInvariant()
    if (-not $expectedEntrySha -or (Get-Sha256 $PSCommandPath) -ne $expectedEntrySha) {
        throw "UPDATE_WINDOWS_WORKER_SHA256_MISMATCH"
    }
    if (
        [int]$job.schema -ne 1 -or
        [string]$job.status -ne "scheduled" -or
        [string]$job.worker_contract -ne "windows-inno-v1" -or
        [string]$job.recovery_contract -ne "windows-interruption-v1" -or
        $job.apply_certified -ne $true
    ) {
        throw "UPDATE_WINDOWS_JOB_STATE_INVALID"
    }

    $stream = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::ReadWrite)
    if ($stream.Length -eq 0) { $stream.SetLength(1) }
    try { $stream.Lock(0, 1); $lock = $stream }
    catch { $stream.Dispose(); Write-EntryLog "lock=busy"; exit 5 }

    Set-JobField $job "worker_pid" $PID
    Set-JobField $job "worker_role" "apply"
    Set-JobField $job "worker_owned_at" ([DateTime]::UtcNow.ToString("o"))
    Save-Job $job

    $wrapper = Join-Path $PSScriptRoot "windows_update_worker.ps1"
    $core = Join-Path $PSScriptRoot "windows_update_worker_core.ps1"
    $recovery = Join-Path $PSScriptRoot "windows_update_recovery.ps1"
    foreach ($item in @(
        @{ Path = $wrapper; Field = "windows_update_worker.ps1_sha256" },
        @{ Path = $core; Field = "windows_update_worker_core.ps1_sha256" },
        @{ Path = $recovery; Field = "windows_update_recovery.ps1_sha256" }
    )) {
        if (-not (Test-Path -LiteralPath $item.Path -PathType Leaf)) { throw "UPDATE_WINDOWS_WORKER_SOURCE_MISSING" }
        $expected = ([string]$job.PSObject.Properties[$item.Field].Value).ToLowerInvariant()
        if (-not $expected -or (Get-Sha256 $item.Path) -ne $expected) { throw "UPDATE_WINDOWS_WORKER_SHA256_MISMATCH" }
    }

    $nativePs = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    if (-not (Test-Path -LiteralPath $nativePs -PathType Leaf)) { throw "UPDATE_WINDOWS_POWERSHELL51_MISSING" }
    $child = Start-Process -FilePath $nativePs -ArgumentList @(
        "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
        ('"{0}"' -f $wrapper), "-JobPath", ('"{0}"' -f $resolvedJob), "-ParentPid", $ParentPid
    ) -PassThru
    $child.WaitForExit()
    $childExitCode = [int]$child.ExitCode
    Write-EntryLog "wrapper_exit=$childExitCode"
    exit $childExitCode
} catch {
    Write-EntryLog "failure=$($_.Exception.Message)"
    exit 1
} finally {
    if ($child) {
        $child.Dispose()
    }
    if ($lock) {
        try { $lock.Unlock(0, 1) } catch {}
        $lock.Dispose()
    }
}
