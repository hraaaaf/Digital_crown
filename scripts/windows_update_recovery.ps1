#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$JobPath,
    [Parameter(Mandatory = $true)][int]$ParentPid
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:ResolvedJobPath = [IO.Path]::GetFullPath($JobPath)
$script:JobDir = Split-Path -Parent $script:ResolvedJobPath
$script:LogPath = Join-Path $script:JobDir "windows-update-recovery.log"
$script:LockPath = Join-Path $script:JobDir "worker.lock"
$script:Lock = $null
$script:Runtime = $null

function Write-RecoveryLog {
    param([string]$Message)
    Add-Content -LiteralPath $script:LogPath -Value ("{0} recovery {1}" -f ([DateTime]::UtcNow.ToString("o")), $Message) -Encoding utf8
}

function Set-JobField {
    param($Job, [string]$Name, $Value)
    if ($Job.PSObject.Properties.Name -contains $Name) { $Job.$Name = $Value }
    else { $Job | Add-Member -NotePropertyName $Name -NotePropertyValue $Value }
}

function Save-Job {
    param($Job)
    Set-JobField $Job "updated_at" ([DateTime]::UtcNow.ToString("o"))
    $tmp = "$script:ResolvedJobPath.partial"
    [IO.File]::WriteAllText($tmp, ($Job | ConvertTo-Json -Depth 24), [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $script:ResolvedJobPath -Force
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Normalize-Path {
    param([string]$Path)
    return [IO.Path]::GetFullPath($Path).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
}

function Wait-ParentExit {
    param([int]$ProcessId, [int]$TimeoutSeconds = 30)
    if ($ProcessId -le 0 -or $ProcessId -eq $PID) { throw "UPDATE_RECOVERY_PARENT_PID_INVALID" }
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (-not (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)) { return }
        Start-Sleep -Milliseconds 250
    }
    throw "UPDATE_RECOVERY_PARENT_EXIT_TIMEOUT"
}

function Acquire-WorkerLock {
    $stream = [IO.File]::Open($script:LockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::ReadWrite)
    if ($stream.Length -eq 0) { $stream.SetLength(1) }
    try { $stream.Lock(0, 1); $script:Lock = $stream }
    catch { $stream.Dispose(); throw "UPDATE_RECOVERY_WORKER_BUSY" }
}

function Release-WorkerLock {
    if ($script:Lock) {
        try { $script:Lock.Unlock(0, 1) } catch {}
        $script:Lock.Dispose()
        $script:Lock = $null
    }
}

function Assert-LoopbackHealthUrl {
    param([string]$Url)
    try { $uri = [Uri]$Url } catch { throw "UPDATE_RECOVERY_HEALTH_URL_INVALID" }
    if (
        $uri.Scheme -ne "http" -or
        $uri.Host -notin @("127.0.0.1", "localhost", "::1") -or
        $uri.AbsolutePath -ne "/health" -or $uri.Query -or $uri.Fragment
    ) { throw "UPDATE_RECOVERY_HEALTH_URL_NOT_LOOPBACK" }
    return $uri.AbsoluteUri
}

function Wait-RuntimeHealth {
    param([string]$HealthUrl, [int]$TimeoutSeconds = 60)
    $url = Assert-LoopbackHealthUrl $HealthUrl
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 2
            if ($response.status -eq "ok" -and $response.db -eq "ok") { return }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    throw "UPDATE_RECOVERY_RUNTIME_HEALTH_FAILED"
}

function Invoke-PackageSelfTest {
    param([string]$Executable, [string]$ExpectedVersion, [string]$Prefix)
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { throw "UPDATE_RECOVERY_EXECUTABLE_MISSING" }
    $report = Join-Path $script:JobDir ("{0}-{1}.json" -f $Prefix, [Guid]::NewGuid().ToString("N"))
    $previous = $env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT
    $env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT = $report
    try {
        $proc = Start-Process -FilePath $Executable -ArgumentList "--package-self-test" -WorkingDirectory (Split-Path -Parent $Executable) -Wait -PassThru
    } finally {
        if ($null -eq $previous) { Remove-Item Env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT -ErrorAction SilentlyContinue }
        else { $env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT = $previous }
    }
    try {
        if ($proc.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $report -PathType Leaf)) { throw "UPDATE_RECOVERY_PACKAGE_SELF_TEST_FAILED" }
        $payload = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
        $checks = @(
            ($payload.status -eq "ok"), ($payload.frozen -eq $true),
            ([string]$payload.version -eq $ExpectedVersion),
            (@($payload.missing).Count -eq 0), (@($payload.forbidden_present).Count -eq 0),
            (@($payload.unqualified_scientific_weights_present).Count -eq 0),
            ($payload.scientific_manifest_policy_ok -eq $true),
            ([string]$payload.scientific_capabilities -eq "FAIL_CLOSED_NO_WEIGHTS")
        )
        if ($checks -contains $false) { throw "UPDATE_RECOVERY_PACKAGE_TRUTH_FAILED" }
    } finally { Remove-Item -LiteralPath $report -Force -ErrorAction SilentlyContinue }
}

function Get-TreeManifest {
    param([string]$Root)
    $rootNorm = Normalize-Path $Root
    $files = Get-ChildItem -LiteralPath $rootNorm -Recurse -File -Force | Sort-Object FullName
    return @(
        foreach ($file in $files) {
            $relative = $file.FullName.Substring($rootNorm.Length).TrimStart([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
            [pscustomobject]@{ path = $relative.Replace([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar); length = [int64]$file.Length; sha256 = Get-Sha256 $file.FullName }
        }
    )
}

function Expand-ManifestRows {
    param($Manifest)
    foreach ($candidate in @($Manifest)) {
        if ($candidate -is [System.Array]) { foreach ($nested in $candidate) { if ($null -ne $nested) { $nested } } }
        elseif ($null -ne $candidate) { $candidate }
    }
}

function Assert-ManifestsEqual {
    param($Expected, $Actual, [string]$ErrorCode)
    $expectedRows = @(Expand-ManifestRows $Expected | Sort-Object -Property path)
    $actualRows = @(Expand-ManifestRows $Actual | Sort-Object -Property path)
    if ($expectedRows.Count -ne $actualRows.Count) { throw "$ErrorCode`:COUNT" }
    for ($i = 0; $i -lt $expectedRows.Count; $i++) {
        $e = $expectedRows[$i]; $a = $actualRows[$i]
        if (
            [string]$e.path -cne [string]$a.path -or
            [int64]$e.length -ne [int64]$a.length -or
            ([string]$e.sha256).ToLowerInvariant() -cne ([string]$a.sha256).ToLowerInvariant()
        ) { throw "$ErrorCode`:ENTRY:$([string]$e.path)" }
    }
}

function Copy-TreeVerified {
    param([string]$Source, [string]$Destination, $ExpectedManifest, [string]$ErrorCode)
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    & robocopy.exe $Source $Destination /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -gt 7) { throw "$ErrorCode`:ROBOCOPY_$LASTEXITCODE" }
    Assert-ManifestsEqual $ExpectedManifest (Get-TreeManifest $Destination) $ErrorCode
}

function Restore-Program {
    param([string]$InstallDir)
    $snapshot = Join-Path $script:JobDir "rescue\program"
    $manifestPath = Join-Path $script:JobDir "rescue\program-manifest.json"
    if (-not (Test-Path -LiteralPath $snapshot -PathType Container) -or -not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "UPDATE_RECOVERY_PROGRAM_RESCUE_MISSING"
    }
    $expected = @(Expand-ManifestRows (Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json))
    Assert-ManifestsEqual $expected (Get-TreeManifest $snapshot) "UPDATE_RECOVERY_PROGRAM_RESCUE_INTEGRITY_FAILED"
    if (Test-Path -LiteralPath $InstallDir) { Remove-Item -LiteralPath $InstallDir -Recurse -Force }
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Copy-TreeVerified $snapshot $InstallDir $expected "UPDATE_RECOVERY_PROGRAM_ROLLBACK_VERIFY_FAILED"
}

function Restore-UninstallRegistry {
    $target = Join-Path $script:JobDir "rescue\uninstall.reg"
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "UPDATE_RECOVERY_UNINSTALL_REGISTRY_RESCUE_MISSING" }
    & reg.exe import $target | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "UPDATE_RECOVERY_UNINSTALL_REGISTRY_IMPORT_FAILED" }
}

function Get-UninstallRegistryMatch {
    param([string]$InstallDir)
    $root = "Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall"
    $installNorm = Normalize-Path $InstallDir
    $matches = @()
    foreach ($key in Get-ChildItem $root -ErrorAction Stop) {
        $props = Get-ItemProperty -LiteralPath $key.PSPath -ErrorAction SilentlyContinue
        if (-not $props) { continue }
        $displayName = [string]$props.DisplayName
        if (-not ($displayName -eq "DigitalCrown" -or $displayName.StartsWith("DigitalCrown ", [StringComparison]::OrdinalIgnoreCase))) { continue }
        $locationMatches = $false
        if ($props.InstallLocation) { try { $locationMatches = (Normalize-Path ([string]$props.InstallLocation)) -eq $installNorm } catch {} }
        $uninstallString = [string]$props.UninstallString
        $uninstallMatches = $uninstallString -and $uninstallString.IndexOf($installNorm, [StringComparison]::OrdinalIgnoreCase) -ge 0
        if ($locationMatches -or $uninstallMatches) { $matches += [pscustomobject]@{ DisplayVersion = [string]$props.DisplayVersion } }
    }
    if ($matches.Count -ne 1) { throw "UPDATE_RECOVERY_UNINSTALL_REGISTRY_NOT_UNIQUE" }
    return $matches[0]
}

function Assert-UninstallRegistryVersion {
    param([string]$InstallDir, [string]$ExpectedVersion)
    $match = Get-UninstallRegistryMatch $InstallDir
    if ($match.DisplayVersion -ne $ExpectedVersion) { throw "UPDATE_RECOVERY_UNINSTALL_VERSION_MISMATCH" }
}

function Stop-InstalledRuntime {
    param([string]$Executable)
    $target = Normalize-Path $Executable
    foreach ($proc in @(Get-Process -Name "DigitalCrown" -ErrorAction SilentlyContinue)) {
        $path = $null
        try { $path = $proc.Path } catch {}
        if ($path) {
            try {
                if ((Normalize-Path $path) -eq $target) {
                    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                    try { $proc.WaitForExit(5000) | Out-Null } catch {}
                }
            } catch {}
        }
    }
}

function Start-DigitalCrown {
    param([string]$Executable)
    $previous = $env:DIGITALCROWN_RESTORE_RESTART
    $env:DIGITALCROWN_RESTORE_RESTART = "1"
    try { return Start-Process -FilePath $Executable -WorkingDirectory (Split-Path -Parent $Executable) -PassThru }
    finally {
        if ($null -eq $previous) { Remove-Item Env:DIGITALCROWN_RESTORE_RESTART -ErrorAction SilentlyContinue }
        else { $env:DIGITALCROWN_RESTORE_RESTART = $previous }
    }
}

function Invoke-Finalizer {
    param($Job, [string]$Executable)
    Invoke-PackageSelfTest -Executable $Executable -ExpectedVersion ([string]$Job.version) -Prefix "recovery-target-self-test"
    Assert-UninstallRegistryVersion -InstallDir ([string]$Job.install_dir) -ExpectedVersion ([string]$Job.version)
    $runtime = Start-DigitalCrown -Executable $Executable
    $script:Runtime = $runtime
    Wait-RuntimeHealth -HealthUrl ([string]$Job.health_url) -TimeoutSeconds ([int]$Job.health_timeout_seconds)
    $finalizer = Start-Process -FilePath $Executable -ArgumentList @("--update-finalize-worker", ('"{0}"' -f $script:ResolvedJobPath)) -WorkingDirectory (Split-Path -Parent $Executable) -Wait -PassThru
    if ($finalizer.ExitCode -ne 0) { throw "UPDATE_RECOVERY_FINALIZER_FAILED:$($finalizer.ExitCode)" }
    $finalized = Get-Content -LiteralPath $script:ResolvedJobPath -Raw | ConvertFrom-Json
    if ([string]$finalized.status -ne "healthy") { throw "UPDATE_RECOVERY_FINALIZER_COMMIT_INVALID" }
    Write-RecoveryLog "finalized version=$([string]$finalized.version) sequence=$([int]$finalized.sequence)"
}

function Invoke-DatabaseFallback {
    param($Job, [string]$Executable)
    Set-JobField $Job "status" "database_rolling_back"
    Set-JobField $Job "worker_result" "rollback_failed"
    Set-JobField $Job "rollback" "failed"
    Set-JobField $Job "rollback_failure_reason" "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED"
    Set-JobField $Job "database_rollback" "running"
    Set-JobField $Job "database_rollback_started_at" ([DateTime]::UtcNow.ToString("o"))
    Save-Job $Job

    $dbWorker = Start-Process -FilePath $Executable -ArgumentList @("--update-db-rollback-worker", ('"{0}"' -f $script:ResolvedJobPath)) -WorkingDirectory (Split-Path -Parent $Executable) -Wait -PassThru
    if ($dbWorker.ExitCode -ne 0) { throw "UPDATE_RECOVERY_DB_ROLLBACK_WORKER_FAILED:$($dbWorker.ExitCode)" }
    $runtime = Start-DigitalCrown -Executable $Executable
    $script:Runtime = $runtime
    Wait-RuntimeHealth -HealthUrl ([string]$Job.health_url) -TimeoutSeconds ([int]$Job.health_timeout_seconds)
    Set-JobField $Job "status" "rolled_back"
    Set-JobField $Job "worker_result" "rolled_back"
    Set-JobField $Job "rollback" "passed"
    Set-JobField $Job "database_rollback" "passed"
    Set-JobField $Job "database_rollback_report" "db-rollback-report.json"
    Set-JobField $Job "runtime_pid" ([int]$runtime.Id)
    Save-Job $Job
    Write-RecoveryLog "database_rollback=passed runtime_pid=$($runtime.Id)"
}

function Invoke-PackageRollback {
    param($Job)
    $installDir = Normalize-Path ([string]$Job.install_dir)
    $oldExecutable = Join-Path $installDir "DigitalCrown.exe"
    Stop-InstalledRuntime -Executable $oldExecutable
    Restore-Program -InstallDir $installDir
    Restore-UninstallRegistry
    $oldExecutable = Join-Path $installDir "DigitalCrown.exe"
    Invoke-PackageSelfTest -Executable $oldExecutable -ExpectedVersion ([string]$Job.current_version) -Prefix "recovery-rollback-self-test"
    Assert-UninstallRegistryVersion -InstallDir $installDir -ExpectedVersion ([string]$Job.current_version)

    $runtime = Start-DigitalCrown -Executable $oldExecutable
    $script:Runtime = $runtime
    try {
        Wait-RuntimeHealth -HealthUrl ([string]$Job.health_url) -TimeoutSeconds ([int]$Job.health_timeout_seconds)
        Set-JobField $Job "status" "rolled_back"
        Set-JobField $Job "worker_result" "rolled_back"
        Set-JobField $Job "rollback" "passed"
        Set-JobField $Job "database_rollback" "not_needed"
        Set-JobField $Job "runtime_pid" ([int]$runtime.Id)
        Save-Job $Job
        Write-RecoveryLog "package_rollback=passed runtime_pid=$($runtime.Id)"
        return
    } catch {
        if ($runtime -and -not $runtime.HasExited) { Stop-Process -Id $runtime.Id -Force -ErrorAction SilentlyContinue }
        Set-JobField $Job "status" "rollback_failed"
        Set-JobField $Job "worker_result" "rollback_failed"
        Set-JobField $Job "rollback" "failed"
        Set-JobField $Job "rollback_failure_reason" "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED"
        Set-JobField $Job "database_rollback" "required_but_not_wired"
        Save-Job $Job
        Write-RecoveryLog "package_rollback_health=failed; escalating_db"
        Invoke-DatabaseFallback -Job $Job -Executable $oldExecutable
    }
}

function Validate-Job {
    if (-not (Test-Path -LiteralPath $script:ResolvedJobPath -PathType Leaf)) { throw "UPDATE_RECOVERY_JOB_MISSING" }
    $job = Get-Content -LiteralPath $script:ResolvedJobPath -Raw | ConvertFrom-Json
    if (
        [int]$job.schema -ne 1 -or
        [string]$job.platform -ne "windows" -or
        [string]$job.worker_contract -ne "windows-inno-v1" -or
        [string]$job.recovery_contract -ne "windows-interruption-v1" -or
        $job.apply_certified -ne $true
    ) {
        throw "UPDATE_RECOVERY_JOB_INVALID"
    }
    $expectedRecoverySha = ([string]$job.'windows_update_recovery.ps1_sha256').ToLowerInvariant()
    if (-not $expectedRecoverySha -or (Get-Sha256 $PSCommandPath) -ne $expectedRecoverySha) {
        throw "UPDATE_RECOVERY_WORKER_SHA256_MISMATCH"
    }
    if ([string]$job.job_id -notmatch '^[0-9a-f]{32}$') { throw "UPDATE_RECOVERY_JOB_ID_INVALID" }
    $installDir = Normalize-Path ([string]$job.install_dir)
    if (-not [IO.Path]::IsPathRooted($installDir)) { throw "UPDATE_RECOVERY_INSTALL_DIR_INVALID" }
    Assert-LoopbackHealthUrl ([string]$job.health_url) | Out-Null
    $timeout = 60
    if ($job.PSObject.Properties.Name -contains "health_timeout_seconds") { $timeout = [int]$job.health_timeout_seconds }
    if ($timeout -lt 3 -or $timeout -gt 180) { throw "UPDATE_RECOVERY_HEALTH_TIMEOUT_INVALID" }
    Set-JobField $job "health_timeout_seconds" $timeout
    return $job
}

$exitCode = 1
try {
    Acquire-WorkerLock
    $job = Validate-Job
    Set-JobField $job "recovery_worker_pid" $PID
    Set-JobField $job "worker_role" "recovery"
    Set-JobField $job "recovery_started_at" ([DateTime]::UtcNow.ToString("o"))
    Save-Job $job
    Wait-ParentExit -ProcessId $ParentPid

    $status = [string]$job.status
    Write-RecoveryLog "starting state=$status job=$([string]$job.job_id)"

    if ($status -eq "scheduled") {
        Set-JobField $job "status" "prepared"
        Set-JobField $job "apply_certified" $false
        Set-JobField $job "apply_blocker" "UPDATE_INTERRUPTED_BEFORE_APPLY"
        Set-JobField $job "worker_result" "interrupted_before_mutation"
        Save-Job $job
        Write-RecoveryLog "scheduled_without_mutation=reset_prepared"
        $exitCode = 0
    } elseif ($status -eq "health_pending") {
        $targetExecutable = Join-Path (Normalize-Path ([string]$job.install_dir)) "DigitalCrown.exe"
        try {
            Invoke-Finalizer -Job $job -Executable $targetExecutable
            $exitCode = 0
        } catch {
            Write-RecoveryLog "health_pending_recheck_failed=$($_.Exception.Message); rollback=starting"
            if ($script:Runtime -and -not $script:Runtime.HasExited) { Stop-Process -Id $script:Runtime.Id -Force -ErrorAction SilentlyContinue }
            $job = Get-Content -LiteralPath $script:ResolvedJobPath -Raw | ConvertFrom-Json
            Invoke-PackageRollback -Job $job
            $exitCode = 2
        }
    } elseif ($status -in @("applying", "rolling_back")) {
        Invoke-PackageRollback -Job $job
        $exitCode = 2
    } elseif (
        $status -eq "database_rolling_back" -or
        ($status -eq "rollback_failed" -and [string]$job.rollback_failure_reason -eq "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED")
    ) {
        $oldExecutable = Join-Path (Normalize-Path ([string]$job.install_dir)) "DigitalCrown.exe"
        Invoke-DatabaseFallback -Job $job -Executable $oldExecutable
        $exitCode = 2
    } else {
        throw "UPDATE_RECOVERY_STATE_NOT_RECOVERABLE:$status"
    }
} catch {
    $failure = $_.Exception.Message
    Write-RecoveryLog "failure=$failure"
    if ($failure -eq "UPDATE_RECOVERY_WORKER_BUSY") {
        # Never mutate job.json without owning worker.lock. The live apply/recovery
        # process remains the sole writer and will finish or leave recoverable truth.
        $exitCode = 5
    } else {
        try {
            if ($script:Runtime -and -not $script:Runtime.HasExited) { Stop-Process -Id $script:Runtime.Id -Force -ErrorAction SilentlyContinue }
            $job = Get-Content -LiteralPath $script:ResolvedJobPath -Raw | ConvertFrom-Json
            Set-JobField $job "recovery_failure_reason" $failure
            Set-JobField $job "recovery_failed_at" ([DateTime]::UtcNow.ToString("o"))
            Save-Job $job
        } catch {}
        $exitCode = 3
    }
} finally {
    Release-WorkerLock
}

exit $exitCode
