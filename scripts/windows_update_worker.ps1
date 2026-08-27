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

$script:WorkerContract = "windows-inno-v1"
$script:NewRuntime = $null
$script:ApplyStarted = $false
$script:Job = $null
$script:ResolvedJobPath = [IO.Path]::GetFullPath($JobPath)
$script:JobDir = Split-Path -Parent $script:ResolvedJobPath
$script:LogPath = Join-Path $script:JobDir "windows-update-worker.log"

function Write-WorkerLog {
    param([string]$Message)
    $line = "{0} {1}" -f ([DateTime]::UtcNow.ToString("o")), $Message
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

function Normalize-Path {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
}

function Assert-ChildPath {
    param(
        [Parameter(Mandatory = $true)][string]$Parent,
        [Parameter(Mandatory = $true)][string]$Child,
        [Parameter(Mandatory = $true)][string]$ErrorCode
    )
    $parentNorm = (Normalize-Path $Parent) + [IO.Path]::DirectorySeparatorChar
    $childNorm = Normalize-Path $Child
    if (-not $childNorm.StartsWith($parentNorm, [StringComparison]::OrdinalIgnoreCase)) {
        throw $ErrorCode
    }
}

function Assert-NoPathOverlap {
    param(
        [Parameter(Mandatory = $true)][string]$A,
        [Parameter(Mandatory = $true)][string]$B
    )
    $aNorm = (Normalize-Path $A) + [IO.Path]::DirectorySeparatorChar
    $bNorm = (Normalize-Path $B) + [IO.Path]::DirectorySeparatorChar
    if (
        $aNorm.StartsWith($bNorm, [StringComparison]::OrdinalIgnoreCase) -or
        $bNorm.StartsWith($aNorm, [StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "UPDATE_WINDOWS_PATH_OVERLAP"
    }
}

function Assert-SemVer {
    param([string]$Value, [string]$ErrorCode)
    if ($Value -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$') {
        throw $ErrorCode
    }
    return [Version]$Value
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Assert-LoopbackHealthUrl {
    param([Parameter(Mandatory = $true)][string]$Url)
    try {
        $uri = [Uri]$Url
    } catch {
        throw "UPDATE_WINDOWS_HEALTH_URL_INVALID"
    }
    if (
        $uri.Scheme -ne "http" -or
        $uri.Host -notin @("127.0.0.1", "localhost", "::1") -or
        $uri.AbsolutePath -ne "/health" -or
        $uri.Query -or
        $uri.Fragment
    ) {
        throw "UPDATE_WINDOWS_HEALTH_URL_NOT_LOOPBACK"
    }
    return $uri.AbsoluteUri
}

function Wait-ParentExit {
    param([int]$ProcessId, [int]$TimeoutSeconds = 30)
    if ($ProcessId -le 0 -or $ProcessId -eq $PID) {
        throw "UPDATE_WINDOWS_PARENT_PID_INVALID"
    }
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if (-not $process) {
            return
        }
        Start-Sleep -Milliseconds 250
    }
    throw "UPDATE_WINDOWS_PARENT_EXIT_TIMEOUT"
}

function Invoke-PackageSelfTest {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string]$ExpectedVersion,
        [Parameter(Mandatory = $true)][string]$ReportPrefix
    )
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        throw "UPDATE_WINDOWS_EXECUTABLE_MISSING"
    }
    $report = Join-Path $script:JobDir ("{0}-{1}.json" -f $ReportPrefix, [Guid]::NewGuid().ToString("N"))
    $previous = $env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT
    $env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT = $report
    try {
        $proc = Start-Process -FilePath $Executable -ArgumentList "--package-self-test" -WorkingDirectory (Split-Path -Parent $Executable) -Wait -PassThru
    } finally {
        if ($null -eq $previous) {
            Remove-Item Env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT -ErrorAction SilentlyContinue
        } else {
            $env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT = $previous
        }
    }
    try {
        if ($proc.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $report -PathType Leaf)) {
            throw "UPDATE_WINDOWS_PACKAGE_SELF_TEST_FAILED"
        }
        try {
            $payload = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
        } catch {
            throw "UPDATE_WINDOWS_PACKAGE_SELF_TEST_INVALID"
        }
        $checks = @(
            ($payload.status -eq "ok"),
            ($payload.frozen -eq $true),
            ([string]$payload.version -eq $ExpectedVersion),
            (@($payload.missing).Count -eq 0),
            (@($payload.forbidden_present).Count -eq 0),
            (@($payload.unqualified_scientific_weights_present).Count -eq 0),
            ($payload.scientific_manifest_policy_ok -eq $true),
            ([string]$payload.scientific_capabilities -eq "FAIL_CLOSED_NO_WEIGHTS")
        )
        if ($checks -contains $false) {
            throw "UPDATE_WINDOWS_PACKAGE_TRUTH_FAILED"
        }
    } finally {
        Remove-Item -LiteralPath $report -Force -ErrorAction SilentlyContinue
    }
}

function Wait-RuntimeHealth {
    param(
        [Parameter(Mandatory = $true)][string]$HealthUrl,
        [int]$TimeoutSeconds = 45
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
            # Runtime may still be starting.
        }
        Start-Sleep -Milliseconds 500
    }
    throw "UPDATE_WINDOWS_RUNTIME_HEALTH_FAILED"
}

function Assert-NoReparsePoints {
    param([Parameter(Mandatory = $true)][string]$Root)
    $reparse = Get-ChildItem -LiteralPath $Root -Recurse -Force -ErrorAction Stop |
        Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 } |
        Select-Object -First 1
    if ($reparse) {
        throw "UPDATE_WINDOWS_INSTALL_REPARSE_POINT_FORBIDDEN"
    }
}

function Get-TreeManifest {
    param([Parameter(Mandatory = $true)][string]$Root)
    $rootNorm = Normalize-Path $Root
    $files = Get-ChildItem -LiteralPath $rootNorm -Recurse -File -Force | Sort-Object FullName
    return @(
        foreach ($file in $files) {
            $relative = $file.FullName.Substring($rootNorm.Length).TrimStart('\', '/')
            [pscustomobject]@{
                path = $relative.Replace('\', '/')
                length = [int64]$file.Length
                sha256 = Get-Sha256 $file.FullName
            }
        }
    )
}

function Assert-ManifestsEqual {
    param($Expected, $Actual, [string]$ErrorCode)
    $expectedJson = @($Expected) | ConvertTo-Json -Depth 6 -Compress
    $actualJson = @($Actual) | ConvertTo-Json -Depth 6 -Compress
    if ($expectedJson -ne $actualJson) {
        throw $ErrorCode
    }
}

function Copy-TreeVerified {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)]$ExpectedManifest,
        [Parameter(Mandatory = $true)][string]$ErrorCode
    )
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    & robocopy.exe $Source $Destination /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /NFL /NDL /NJH /NJS /NP | Out-Null
    $code = $LASTEXITCODE
    if ($code -gt 7) {
        throw "$ErrorCode`:ROBOCOPY_$code"
    }
    $actual = Get-TreeManifest $Destination
    Assert-ManifestsEqual $ExpectedManifest $actual $ErrorCode
}

function Snapshot-Program {
    param([Parameter(Mandatory = $true)][string]$InstallDir)
    Assert-NoReparsePoints $InstallDir
    $rescueRoot = Join-Path $script:JobDir "rescue"
    New-Item -ItemType Directory -Path $rescueRoot -Force | Out-Null
    $final = Join-Path $rescueRoot "program"
    $partial = Join-Path $rescueRoot "program.partial"
    if (Test-Path -LiteralPath $final) {
        throw "UPDATE_WINDOWS_PROGRAM_RESCUE_ALREADY_EXISTS"
    }
    Remove-Item -LiteralPath $partial -Recurse -Force -ErrorAction SilentlyContinue

    $manifest = Get-TreeManifest $InstallDir
    if (@($manifest).Count -eq 0) {
        throw "UPDATE_WINDOWS_PROGRAM_RESCUE_EMPTY"
    }
    Copy-TreeVerified $InstallDir $partial $manifest "UPDATE_WINDOWS_PROGRAM_RESCUE_VERIFY_FAILED"
    Move-Item -LiteralPath $partial -Destination $final
    $manifestPath = Join-Path $rescueRoot "program-manifest.json"
    [IO.File]::WriteAllText(
        $manifestPath,
        (@($manifest) | ConvertTo-Json -Depth 6),
        [Text.UTF8Encoding]::new($false)
    )
    return $final
}

function Restore-Program {
    param([Parameter(Mandatory = $true)][string]$InstallDir)
    $rescueRoot = Join-Path $script:JobDir "rescue"
    $snapshot = Join-Path $rescueRoot "program"
    $manifestPath = Join-Path $rescueRoot "program-manifest.json"
    if (
        -not (Test-Path -LiteralPath $snapshot -PathType Container) -or
        -not (Test-Path -LiteralPath $manifestPath -PathType Leaf)
    ) {
        throw "UPDATE_WINDOWS_PROGRAM_RESCUE_MISSING"
    }
    $expected = @(Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json)
    if (Test-Path -LiteralPath $InstallDir) {
        Remove-Item -LiteralPath $InstallDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Copy-TreeVerified $snapshot $InstallDir $expected "UPDATE_WINDOWS_PROGRAM_ROLLBACK_VERIFY_FAILED"
}

function Get-UninstallRegistryMatch {
    param([Parameter(Mandatory = $true)][string]$InstallDir)
    $root = "Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall"
    if (-not (Test-Path $root)) {
        throw "UPDATE_WINDOWS_UNINSTALL_REGISTRY_ROOT_MISSING"
    }
    $installNorm = Normalize-Path $InstallDir
    $matches = @()
    foreach ($key in Get-ChildItem $root -ErrorAction Stop) {
        $props = Get-ItemProperty -LiteralPath $key.PSPath -ErrorAction SilentlyContinue
        if (-not $props -or [string]$props.DisplayName -ne "DigitalCrown") {
            continue
        }
        $locationMatches = $false
        if ($props.InstallLocation) {
            try {
                $locationMatches = (Normalize-Path ([string]$props.InstallLocation)) -eq $installNorm
            } catch {
                $locationMatches = $false
            }
        }
        $uninstallString = [string]$props.UninstallString
        $uninstallMatches = (
            $uninstallString -and
            $uninstallString.IndexOf($installNorm, [StringComparison]::OrdinalIgnoreCase) -ge 0
        )
        if ($locationMatches -or $uninstallMatches) {
            $matches += [pscustomobject]@{
                ProviderPath = $key.PSPath
                NativePath = "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\$($key.PSChildName)"
                DisplayVersion = [string]$props.DisplayVersion
            }
        }
    }
    if ($matches.Count -ne 1) {
        throw "UPDATE_WINDOWS_UNINSTALL_REGISTRY_NOT_UNIQUE"
    }
    return $matches[0]
}

function Assert-UninstallRegistryVersion {
    param(
        [Parameter(Mandatory = $true)][string]$InstallDir,
        [Parameter(Mandatory = $true)][string]$ExpectedVersion
    )
    $match = Get-UninstallRegistryMatch $InstallDir
    if ($match.DisplayVersion -ne $ExpectedVersion) {
        throw "UPDATE_WINDOWS_UNINSTALL_VERSION_MISMATCH"
    }
    return $match
}

function Export-UninstallRegistry {
    param(
        [Parameter(Mandatory = $true)][string]$InstallDir,
        [Parameter(Mandatory = $true)][string]$ExpectedVersion
    )
    $match = Assert-UninstallRegistryVersion $InstallDir $ExpectedVersion
    $target = Join-Path $script:JobDir "rescue\uninstall.reg"
    & reg.exe export $match.NativePath $target /y | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "UPDATE_WINDOWS_UNINSTALL_REGISTRY_EXPORT_FAILED"
    }
    return $target
}

function Restore-UninstallRegistry {
    $target = Join-Path $script:JobDir "rescue\uninstall.reg"
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "UPDATE_WINDOWS_UNINSTALL_REGISTRY_RESCUE_MISSING"
    }
    & reg.exe import $target | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "UPDATE_WINDOWS_UNINSTALL_REGISTRY_IMPORT_FAILED"
    }
}

function Invoke-InnoInstaller {
    param(
        [Parameter(Mandatory = $true)][string]$Installer,
        [Parameter(Mandatory = $true)][string]$InstallDir
    )
    $log = Join-Path $script:JobDir "installer-apply.log"
    $arguments = @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/SP-",
        "/DIR=`"$InstallDir`"",
        "/LOG=`"$log`""
    )
    $proc = Start-Process -FilePath $Installer -ArgumentList $arguments -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "UPDATE_WINDOWS_INSTALLER_FAILED:$($proc.ExitCode)"
    }
}

function Start-DigitalCrown {
    param([Parameter(Mandatory = $true)][string]$Executable)
    $previous = $env:DIGITALCROWN_RESTORE_RESTART
    $env:DIGITALCROWN_RESTORE_RESTART = "1"
    try {
        return Start-Process -FilePath $Executable -WorkingDirectory (Split-Path -Parent $Executable) -PassThru
    } finally {
        if ($null -eq $previous) {
            Remove-Item Env:DIGITALCROWN_RESTORE_RESTART -ErrorAction SilentlyContinue
        } else {
            $env:DIGITALCROWN_RESTORE_RESTART = $previous
        }
    }
}

function Validate-Job {
    if (-not (Test-Path -LiteralPath $script:ResolvedJobPath -PathType Leaf)) {
        throw "UPDATE_WINDOWS_JOB_MISSING"
    }
    try {
        $job = Get-Content -LiteralPath $script:ResolvedJobPath -Raw | ConvertFrom-Json
    } catch {
        throw "UPDATE_WINDOWS_JOB_INVALID"
    }
    $script:Job = $job
    if ([int]$job.schema -ne 1) { throw "UPDATE_WINDOWS_JOB_SCHEMA_UNSUPPORTED" }
    if ([string]$job.status -ne "scheduled") { throw "UPDATE_WINDOWS_JOB_STATE_INVALID" }
    if ([string]$job.platform -ne "windows") { throw "UPDATE_WINDOWS_PLATFORM_INVALID" }
    if ([string]$job.worker_contract -ne $script:WorkerContract) { throw "UPDATE_WINDOWS_WORKER_CONTRACT_INVALID" }
    if ($job.apply_certified -ne $true) { throw "UPDATE_PLATFORM_APPLY_NOT_CERTIFIED" }

    $jobId = [string]$job.job_id
    if ($jobId -notmatch '^[0-9a-f]{32}$') { throw "UPDATE_WINDOWS_JOB_ID_INVALID" }
    $currentVersion = [string]$job.current_version
    $targetVersion = [string]$job.version
    $currentSemVer = Assert-SemVer $currentVersion "UPDATE_WINDOWS_CURRENT_VERSION_INVALID"
    $targetSemVer = Assert-SemVer $targetVersion "UPDATE_WINDOWS_TARGET_VERSION_INVALID"
    if ($targetSemVer -le $currentSemVer) { throw "UPDATE_WINDOWS_TARGET_NOT_NEWER" }

    $artifactName = [string]$job.artifact_filename
    if (
        -not $artifactName -or
        [IO.Path]::GetFileName($artifactName) -ne $artifactName -or
        -not $artifactName.EndsWith(".exe", [StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "UPDATE_WINDOWS_ARTIFACT_FILENAME_INVALID"
    }
    $artifact = Join-Path $script:JobDir $artifactName
    Assert-ChildPath $script:JobDir $artifact "UPDATE_WINDOWS_ARTIFACT_PATH_INVALID"
    if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) {
        throw "UPDATE_WINDOWS_ARTIFACT_MISSING"
    }
    if ([int64](Get-Item -LiteralPath $artifact).Length -ne [int64]$job.artifact_size_bytes) {
        throw "UPDATE_WINDOWS_ARTIFACT_SIZE_MISMATCH"
    }
    if ((Get-Sha256 $artifact) -ne ([string]$job.artifact_sha256).ToLowerInvariant()) {
        throw "UPDATE_WINDOWS_ARTIFACT_SHA256_MISMATCH"
    }

    $rescueName = [string]$job.rescue_backup_filename
    $rescueDb = Join-Path $script:JobDir $rescueName
    Assert-ChildPath $script:JobDir $rescueDb "UPDATE_WINDOWS_RESCUE_PATH_INVALID"
    if (-not (Test-Path -LiteralPath $rescueDb -PathType Leaf)) {
        throw "UPDATE_WINDOWS_RESCUE_BACKUP_MISSING"
    }
    if ((Get-Sha256 $rescueDb) -ne ([string]$job.rescue_backup_sha256).ToLowerInvariant()) {
        throw "UPDATE_WINDOWS_RESCUE_BACKUP_SHA256_MISMATCH"
    }

    $installDir = Normalize-Path ([string]$job.install_dir)
    if (-not [IO.Path]::IsPathRooted($installDir)) {
        throw "UPDATE_WINDOWS_INSTALL_DIR_INVALID"
    }
    Assert-NoPathOverlap $installDir $script:JobDir
    $executable = Join-Path $installDir "DigitalCrown.exe"
    if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
        throw "UPDATE_WINDOWS_CURRENT_EXECUTABLE_MISSING"
    }

    $healthUrl = Assert-LoopbackHealthUrl ([string]$job.health_url)
    $healthTimeout = 60
    if ($job.PSObject.Properties.Name -contains "health_timeout_seconds") {
        $healthTimeout = [int]$job.health_timeout_seconds
    }
    if ($healthTimeout -lt 3 -or $healthTimeout -gt 180) {
        throw "UPDATE_WINDOWS_HEALTH_TIMEOUT_INVALID"
    }

    return [pscustomobject]@{
        Job = $job
        Artifact = $artifact
        RescueDb = $rescueDb
        InstallDir = $installDir
        Executable = $executable
        CurrentVersion = $currentVersion
        TargetVersion = $targetVersion
        HealthUrl = $healthUrl
        HealthTimeout = $healthTimeout
    }
}

function Invoke-WindowsUpdateWorker {
    $context = Validate-Job
    $script:Job = $context.Job
    Write-WorkerLog "validated job=$($script:Job.job_id) current=$($context.CurrentVersion) target=$($context.TargetVersion)"

    Wait-ParentExit -ProcessId $ParentPid

    Invoke-PackageSelfTest -Executable $context.Executable -ExpectedVersion $context.CurrentVersion -ReportPrefix "current-self-test"
    Snapshot-Program -InstallDir $context.InstallDir | Out-Null
    Export-UninstallRegistry -InstallDir $context.InstallDir -ExpectedVersion $context.CurrentVersion | Out-Null

    Set-JobField $script:Job "status" "applying"
    Set-JobField $script:Job "worker_started_at" ([DateTime]::UtcNow.ToString("o"))
    Save-Job $script:Job

    $script:ApplyStarted = $true
    Invoke-InnoInstaller -Installer $context.Artifact -InstallDir $context.InstallDir

    $installedExecutable = Join-Path $context.InstallDir "DigitalCrown.exe"
    Invoke-PackageSelfTest -Executable $installedExecutable -ExpectedVersion $context.TargetVersion -ReportPrefix "target-self-test"
    Assert-UninstallRegistryVersion -InstallDir $context.InstallDir -ExpectedVersion $context.TargetVersion | Out-Null

    $script:NewRuntime = Start-DigitalCrown -Executable $installedExecutable
    Wait-RuntimeHealth -HealthUrl $context.HealthUrl -TimeoutSeconds $context.HealthTimeout

    Set-JobField $script:Job "status" "health_pending"
    Set-JobField $script:Job "worker_result" "install_verified"
    Set-JobField $script:Job "package_self_test" "passed"
    Set-JobField $script:Job "runtime_health" "passed"
    Set-JobField $script:Job "rollback" "not_needed"
    Set-JobField $script:Job "runtime_pid" ([int]$script:NewRuntime.Id)
    Save-Job $script:Job
    Write-WorkerLog "install verified target=$($context.TargetVersion) pid=$($script:NewRuntime.Id)"
    return 0
}

$exitCode = 1
try {
    $exitCode = Invoke-WindowsUpdateWorker
} catch {
    $failure = $_.Exception.Message
    Write-WorkerLog "failure=$failure apply_started=$script:ApplyStarted"
    if ($script:Job -and $script:ApplyStarted) {
        try {
            if ($script:NewRuntime -and -not $script:NewRuntime.HasExited) {
                Stop-Process -Id $script:NewRuntime.Id -Force -ErrorAction SilentlyContinue
                $script:NewRuntime.WaitForExit(5000) | Out-Null
            }
            Set-JobField $script:Job "status" "rolling_back"
            Set-JobField $script:Job "failure_reason" $failure
            Save-Job $script:Job

            $installDir = Normalize-Path ([string]$script:Job.install_dir)
            Restore-Program -InstallDir $installDir
            Restore-UninstallRegistry
            $currentVersion = [string]$script:Job.current_version
            $restoredExecutable = Join-Path $installDir "DigitalCrown.exe"
            Invoke-PackageSelfTest -Executable $restoredExecutable -ExpectedVersion $currentVersion -ReportPrefix "rollback-self-test"
            Assert-UninstallRegistryVersion -InstallDir $installDir -ExpectedVersion $currentVersion | Out-Null

            $rollbackRuntime = Start-DigitalCrown -Executable $restoredExecutable
            try {
                $rollbackTimeout = 60
                if ($script:Job.PSObject.Properties.Name -contains "health_timeout_seconds") {
                    $rollbackTimeout = [int]$script:Job.health_timeout_seconds
                }
                Wait-RuntimeHealth -HealthUrl ([string]$script:Job.health_url) -TimeoutSeconds $rollbackTimeout
            } catch {
                if (-not $rollbackRuntime.HasExited) {
                    Stop-Process -Id $rollbackRuntime.Id -Force -ErrorAction SilentlyContinue
                }
                throw "UPDATE_WINDOWS_PACKAGE_ROLLBACK_HEALTH_FAILED"
            }

            Set-JobField $script:Job "status" "rolled_back"
            Set-JobField $script:Job "worker_result" "rolled_back"
            Set-JobField $script:Job "rollback" "passed"
            Set-JobField $script:Job "database_rollback" "not_needed"
            Set-JobField $script:Job "runtime_pid" ([int]$rollbackRuntime.Id)
            Save-Job $script:Job
            Write-WorkerLog "rollback verified current=$currentVersion pid=$($rollbackRuntime.Id)"
            $exitCode = 2
        } catch {
            $rollbackFailure = $_.Exception.Message
            Set-JobField $script:Job "status" "rollback_failed"
            Set-JobField $script:Job "worker_result" "rollback_failed"
            Set-JobField $script:Job "rollback" "failed"
            Set-JobField $script:Job "database_rollback" "required_but_not_wired"
            Set-JobField $script:Job "rollback_failure_reason" $rollbackFailure
            Save-Job $script:Job
            Write-WorkerLog "rollback_failure=$rollbackFailure"
            $exitCode = 3
        }
    } elseif ($script:Job) {
        Set-JobField $script:Job "status" "failed_pre_apply"
        Set-JobField $script:Job "worker_result" "blocked_before_mutation"
        Set-JobField $script:Job "failure_reason" $failure
        Save-Job $script:Job
        $exitCode = 1
    } else {
        Write-WorkerLog "job unavailable; no state mutation possible"
        $exitCode = 1
    }
}

exit $exitCode
