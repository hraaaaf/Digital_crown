# SCHEDULED-BACKUP-RELEASE-EXECUTION-FIX-1
# Launcher for DigitalCrown_DailyBackup_v2, VERSIONED in this repo (source of truth) and
# deployed (copied) to C:\Users\lenovo\DigitalCrown-Runtime\bin\run_scheduled_backup.ps1
# -- checksum-compared after deployment, see STATE.md.
#
# Unlike the earlier version of this launcher, it never runs the orchestrator from the
# working repo's cwd. It resolves the dedicated backup release via backup-current.json,
# verifies its manifest and critical-file hashes (catches tampering after creation), and
# executes python -m backend.scripts.scheduled_backup from *inside that release
# directory*. The repo's venv remains the pinned interpreter (documented residual
# dependency, RUNTIME-PYTHON-INDEPENDENCE-1) -- but the code itself never comes from the
# repo. backend.scripts.scheduled_backup's own _check_execution_provenance() re-verifies
# this from inside Python as a second, independent line of defense.
#
# Never prints or logs a secret.

[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$RuntimeRoot = "C:\Users\lenovo\DigitalCrown-Runtime",
    [string]$RealEnvFile = "C:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\.env.local",
    [string]$VenvPython = "C:\Users\lenovo\Documents\Cabinet\DigitalCrown\venv\Scripts\python.exe",
    [switch]$ApplyRetention,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$logDir = Join-Path $RuntimeRoot "backups\scheduled\logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$launcherLog = Join-Path $logDir ("launcher_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

function Write-Log {
    param([string]$Message)
    $line = "$(Get-Date -Format o) $Message"
    Write-Host $line
    Add-Content -Path $launcherLog -Value $line
}

Write-Log "=== run_scheduled_backup.ps1 (release-based) start ==="

# 1. Resoudre le pointeur backup-current.json.
$pointerPath = Join-Path $RuntimeRoot "backup-current.json"
if (-not (Test-Path $pointerPath)) {
    Write-Log "ERROR: backup-current.json pointer not found at $pointerPath."
    exit 1
}
$pointer = Get-Content $pointerPath -Raw | ConvertFrom-Json
$releaseRoot = $pointer.release_root
if (-not $releaseRoot -or -not (Test-Path $releaseRoot)) {
    Write-Log "ERROR: pointer release_root missing or invalid: $releaseRoot"
    exit 1
}
Write-Log "Backup release resolved via pointer: $releaseRoot (release_id=$($pointer.release_id))"

# 2. Valider le manifeste de la release.
$manifestPath = Join-Path $releaseRoot "backup-release-manifest.json"
if (-not (Test-Path $manifestPath)) {
    Write-Log "ERROR: backup-release-manifest.json missing at $manifestPath."
    exit 1
}
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
if ($manifest.purpose -ne "scheduled-backup") {
    Write-Log "ERROR: manifest purpose is not scheduled-backup (found: $($manifest.purpose))."
    exit 1
}
if ($manifest.environment -ne "cabinet-real") {
    Write-Log "ERROR: manifest environment is not cabinet-real (found: $($manifest.environment))."
    exit 1
}

# 3. Revalider les hashes critiques -- detecte toute alteration de la release
#    survenue apres sa creation.
foreach ($rel in $manifest.critical_file_hashes.PSObject.Properties.Name) {
    $expected = $manifest.critical_file_hashes.$rel
    $fullPath = Join-Path $releaseRoot $rel
    if (-not (Test-Path $fullPath)) {
        Write-Log "ERROR: critical file missing from release: $rel"
        exit 1
    }
    $actual = (Get-FileHash -Path $fullPath -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $expected) {
        Write-Log "ERROR: hash mismatch for $rel -- release may have been altered after creation."
        exit 1
    }
}
Write-Log "Manifest and critical-file hashes verified OK."

# 4. Interpreteur epingle -- jamais python du PATH.
if (-not (Test-Path $VenvPython)) {
    Write-Log "ERROR: pinned venv python not found: $VenvPython"
    exit 1
}

# 5. Charger la vraie config du cabinet (jamais presente dans la release elle-meme --
#    exclue par construction). Meme mecanisme que run_real_backend.ps1.
if (-not (Test-Path $RealEnvFile)) {
    Write-Log "ERROR: real env file not found: $RealEnvFile"
    exit 1
}
$env:DIGITALCROWN_ENV_FILE = $RealEnvFile
Write-Log "DIGITALCROWN_ENV_FILE set (path only, not printed in clear beyond this)."

$orchestratorArgs = @("-m", "backend.scripts.scheduled_backup")
if ($ApplyRetention) { $orchestratorArgs += "--apply-retention" }
if ($DryRun) { $orchestratorArgs += "--dry-run" }

Write-Log "Launching orchestrator (cwd=$releaseRoot, args=$($orchestratorArgs -join ' '))..."
Push-Location $releaseRoot
try {
    & $VenvPython @orchestratorArgs
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

Write-Log "Orchestrator exit code: $exitCode"
exit $exitCode
