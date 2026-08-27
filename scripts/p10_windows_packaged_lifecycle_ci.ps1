#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$CurrentInstaller,
    [Parameter(Mandatory = $true)][string]$NextInstaller,
    [Parameter(Mandatory = $true)][string]$CurrentVersion,
    [Parameter(Mandatory = $true)][string]$NextVersion
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Wait-Health {
    param([string]$Url, [int]$TimeoutSeconds = 120)
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            $payload = Invoke-RestMethod -Uri $Url -TimeoutSec 2
            if ($payload.status -eq "ok" -and $payload.db -eq "ok") {
                return
            }
        } catch {}
        Start-Sleep -Seconds 2
    }
    throw "P10_PACKAGED_HEALTH_TIMEOUT:$Url"
}

function Wait-JobTerminal {
    param([string]$JobPath, [int]$TimeoutSeconds = 240)
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-Path -LiteralPath $JobPath -PathType Leaf) {
            $job = Get-Content -LiteralPath $JobPath -Raw | ConvertFrom-Json
            if ([string]$job.status -eq "health_pending") {
                return $job
            }
            if ([string]$job.status -in @("failed_pre_apply", "rollback_failed", "rolled_back")) {
                throw "P10_PACKAGED_JOB_FAILED:$($job | ConvertTo-Json -Depth 12 -Compress)"
            }
        }
        Start-Sleep -Seconds 2
    }
    $tail = if (Test-Path -LiteralPath $JobPath) { Get-Content -LiteralPath $JobPath -Raw } else { "<missing>" }
    throw "P10_PACKAGED_JOB_TIMEOUT:$tail"
}

function Invoke-Installer {
    param([string]$Path, [string]$InstallDir, [string]$LogPath)
    $args = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /DIR=`"$InstallDir`" /LOG=`"$LogPath`""
    $proc = Start-Process -FilePath $Path -ArgumentList $args -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        if (Test-Path $LogPath) { Get-Content $LogPath -Tail 250 | Out-Host }
        throw "P10_CURRENT_INSTALL_FAILED:$($proc.ExitCode)"
    }
}

function Get-UninstallVersion {
    param([string]$InstallDir)
    $resolved = [IO.Path]::GetFullPath($InstallDir).TrimEnd('\')
    $matches = @()
    Get-ChildItem "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall" -ErrorAction SilentlyContinue | ForEach-Object {
        $props = Get-ItemProperty $_.PSPath
        $location = [string]$props.InstallLocation
        if (
            [string]$props.DisplayName -eq "DigitalCrown" -and
            $location -and
            [IO.Path]::GetFullPath($location).TrimEnd('\').Equals($resolved, [StringComparison]::OrdinalIgnoreCase)
        ) {
            $matches += [string]$props.DisplayVersion
        }
    }
    if ($matches.Count -ne 1) {
        throw "P10_UNINSTALL_REGISTRY_NOT_UNIQUE:$($matches.Count)"
    }
    return $matches[0]
}

$CurrentInstaller = (Resolve-Path $CurrentInstaller).Path
$NextInstaller = (Resolve-Path $NextInstaller).Path
$root = Join-Path $env:RUNNER_TEMP ("dc-p10-packaged-" + [Guid]::NewGuid().ToString("N"))
$install = Join-Path $root "program"
$data = Join-Path $root "cabinet"
$manifest = Join-Path $root "signed-manifest.json"
$keyReport = Join-Path $root "signing-key.json"
$prepareReport = Join-Path $root "prepare-report.json"
$scheduleReport = Join-Path $root "schedule-report.json"
$installLog = Join-Path $root "install-current.log"
New-Item -ItemType Directory -Force $root,$install,$data | Out-Null

$port = 18820
$healthUrl = "http://127.0.0.1:$port/health"
$env:DIGITALCROWN_USER_DATA_DIR = $data
$env:DIGITALCROWN_CONFIG_DIR = $data
$env:DIGITALCROWN_LOG_DIR = Join-Path $data "logs"
$env:DIGITALCROWN_RUNTIME_DIR = Join-Path $data "runtime"
$env:CABINET_PORT = [string]$port
$env:DIGITALCROWN_RESTORE_RESTART = "1"

Invoke-Installer -Path $CurrentInstaller -InstallDir $install -LogPath $installLog
$exe = Join-Path $install "DigitalCrown.exe"
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw "P10_CURRENT_EXECUTABLE_MISSING"
}

$currentReport = Join-Path $root "current-self-test.json"
$env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT = $currentReport
$currentSelf = Start-Process -FilePath $exe -ArgumentList "--package-self-test" -WorkingDirectory $install -Wait -PassThru
Remove-Item Env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT -ErrorAction SilentlyContinue
if ($currentSelf.ExitCode -ne 0) { throw "P10_CURRENT_SELF_TEST_FAILED" }
$currentPayload = Get-Content $currentReport -Raw | ConvertFrom-Json
if ($currentPayload.status -ne "ok" -or $currentPayload.version -ne $CurrentVersion) {
    throw "P10_CURRENT_VERSION_TRUTH_FAILED"
}

$sentinel = Join-Path $data "P10_UPDATE_DATA_SENTINEL.txt"
Set-Content -LiteralPath $sentinel -Value "preserve-me" -NoNewline

$currentRuntime = Start-Process -FilePath $exe -WorkingDirectory $install -PassThru
Wait-Health -Url $healthUrl -TimeoutSeconds 120

$signer = Join-Path $root "sign_manifest.py"
@'
import base64, hashlib, json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

installer = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
report_path = Path(sys.argv[3])
next_version = sys.argv[4]
private = Ed25519PrivateKey.generate()
public_raw = private.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)
public_b64 = base64.b64encode(public_raw).decode()
key_id = hashlib.sha256(public_raw).hexdigest()
now = datetime.now(timezone.utc)
signed = {
    "schema": 1,
    "sequence": 1,
    "version": next_version,
    "issued_at": now.isoformat().replace("+00:00", "Z"),
    "expires_at": (now + timedelta(hours=4)).isoformat().replace("+00:00", "Z"),
    "targets": [{
        "os": "windows",
        "arch": "amd64",
        "filename": installer.name,
        "size_bytes": installer.stat().st_size,
        "sha256": hashlib.sha256(installer.read_bytes()).hexdigest(),
        "url": "https://updates.invalid/" + installer.name,
    }],
}
canonical = json.dumps(signed, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
signature = base64.b64encode(private.sign(canonical)).decode()
manifest_path.write_text(json.dumps({
    "signed": signed,
    "signature": {"keyid": key_id, "algorithm": "ed25519", "sig": signature},
}, separators=(",", ":")), encoding="utf-8")
report_path.write_text(json.dumps({"public_key_b64": public_b64, "keyid": key_id}), encoding="utf-8")
'@ | Set-Content -LiteralPath $signer -Encoding utf8
python $signer $NextInstaller $manifest $keyReport $NextVersion
if ($LASTEXITCODE -ne 0) { throw "P10_SIGNED_MANIFEST_BUILD_FAILED" }
$keyPayload = Get-Content $keyReport -Raw | ConvertFrom-Json
$env:DIGITALCROWN_UPDATE_PUBLIC_KEY_B64 = [string]$keyPayload.public_key_b64

$env:DIGITALCROWN_UPDATE_PREPARE_REPORT = $prepareReport
$prepareProc = Start-Process -FilePath $exe -ArgumentList @(
    "--prepare-signed-windows-update", "`"$manifest`"", "--artifact", "`"$NextInstaller`""
) -WorkingDirectory $install -Wait -PassThru
Remove-Item Env:DIGITALCROWN_UPDATE_PREPARE_REPORT -ErrorAction SilentlyContinue
if ($prepareProc.ExitCode -ne 0 -or -not (Test-Path $prepareReport)) {
    throw "P10_PACKAGED_PREPARE_FAILED:$($prepareProc.ExitCode)"
}
$prepared = Get-Content $prepareReport -Raw | ConvertFrom-Json
$jobId = [string]$prepared.job_id
if ($jobId -notmatch '^[0-9a-f]{32}$') { throw "P10_PREPARED_JOB_ID_INVALID" }
$jobPath = Join-Path $data "updates\jobs\$jobId\job.json"
$signedManifestCopy = Join-Path $data "updates\jobs\$jobId\signed-manifest.json"
if (-not (Test-Path -LiteralPath $signedManifestCopy -PathType Leaf)) {
    throw "P10_SIGNED_MANIFEST_NOT_STAGED"
}

$env:DIGITALCROWN_UPDATE_SCHEDULE_REPORT = $scheduleReport
$scheduleProc = Start-Process -FilePath $exe -ArgumentList @(
    "--schedule-windows-update", $jobId, "--parent-pid", [string]$currentRuntime.Id
) -WorkingDirectory $install -Wait -PassThru
Remove-Item Env:DIGITALCROWN_UPDATE_SCHEDULE_REPORT -ErrorAction SilentlyContinue
if ($scheduleProc.ExitCode -ne 0 -or -not (Test-Path $scheduleReport)) {
    throw "P10_PACKAGED_SCHEDULE_FAILED:$($scheduleProc.ExitCode)"
}
$scheduled = Get-Content $scheduleReport -Raw | ConvertFrom-Json
if ($scheduled.status -ne "scheduled") { throw "P10_PACKAGED_SCHEDULE_REPORT_INVALID" }

Stop-Process -Id $currentRuntime.Id -Force -ErrorAction SilentlyContinue
$currentRuntime.WaitForExit(10000) | Out-Null

$job = Wait-JobTerminal -JobPath $jobPath -TimeoutSeconds 240
if ($job.status -ne "health_pending" -or $job.worker_result -ne "install_verified") {
    throw "P10_PACKAGED_INSTALL_NOT_VERIFIED"
}
if ($job.package_self_test -ne "passed" -or $job.runtime_health -ne "passed" -or $job.rollback -ne "not_needed") {
    throw "P10_PACKAGED_POST_INSTALL_TRUTH_MISSING"
}
if ($job.apply_certified -ne $true -or $job.worker_contract -ne "windows-inno-v1") {
    throw "P10_PACKAGED_APPLY_CERTIFICATION_MISSING"
}
if (-not (Test-Path -LiteralPath $sentinel -PathType Leaf)) {
    throw "P10_PACKAGED_DATA_SENTINEL_LOST"
}

$nextReport = Join-Path $root "next-self-test.json"
$env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT = $nextReport
$nextSelf = Start-Process -FilePath $exe -ArgumentList "--package-self-test" -WorkingDirectory $install -Wait -PassThru
Remove-Item Env:DIGITALCROWN_PACKAGE_SELF_TEST_REPORT -ErrorAction SilentlyContinue
if ($nextSelf.ExitCode -ne 0) { throw "P10_NEXT_SELF_TEST_FAILED" }
$nextPayload = Get-Content $nextReport -Raw | ConvertFrom-Json
if ($nextPayload.status -ne "ok" -or $nextPayload.version -ne $NextVersion) {
    throw "P10_NEXT_VERSION_TRUTH_FAILED"
}

$displayVersion = Get-UninstallVersion -InstallDir $install
if ($displayVersion -ne $NextVersion) {
    throw "P10_NEXT_REGISTRY_VERSION_FAILED:$displayVersion"
}
Wait-Health -Url $healthUrl -TimeoutSeconds 60

if ($job.PSObject.Properties.Name -contains "runtime_pid") {
    Stop-Process -Id ([int]$job.runtime_pid) -Force -ErrorAction SilentlyContinue
}

$proofDir = $env:P10_PACKAGED_PROOF_DIR
if ($proofDir) {
    New-Item -ItemType Directory -Force $proofDir | Out-Null
    foreach ($source in @($jobPath, $prepareReport, $scheduleReport, $currentReport, $nextReport, $manifest, $installLog)) {
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            Copy-Item -LiteralPath $source -Destination $proofDir -Force
        }
    }
    $workerLog = Join-Path (Split-Path -Parent $jobPath) "windows-update-worker.log"
    if (Test-Path -LiteralPath $workerLog -PathType Leaf) {
        Copy-Item -LiteralPath $workerLog -Destination $proofDir -Force
    }
}

Write-Host "P10_WINDOWS_PACKAGED_LIFECYCLE=SUCCESS current=$CurrentVersion next=$NextVersion job=$jobId signed-manifest=Ed25519 DisplayVersion=$displayVersion status=health_pending"
