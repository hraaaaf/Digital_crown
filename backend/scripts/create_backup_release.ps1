# SCHEDULED-BACKUP-RELEASE-EXECUTION-FIX-1
# Creates an immutable release dedicated to the scheduled backup task, extracted via
# `git archive` from an exact commit -- never a copy of the (possibly dirty) working
# tree. Does NOT touch the active backend release, does NOT update backup-current.json
# (that pointer update is a separate, explicit step -- see STATE.md controlled window).

[CmdletBinding(PositionalBinding = $false)]
param(
    [string]$Commit = "bb779cc",
    [string]$RepoRoot = "C:\Users\lenovo\Documents\Cabinet\DigitalCrown",
    [string]$RuntimeRoot = "C:\Users\lenovo\DigitalCrown-Runtime",
    [string]$PythonExecutable = "C:\Users\lenovo\Documents\Cabinet\DigitalCrown\venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
Write-Host "=== create_backup_release.ps1 ===" -ForegroundColor Yellow

Push-Location $RepoRoot
try {
    $fullCommit = (git rev-parse $Commit 2>$null)
    if (-not $fullCommit) {
        Write-Host "ERROR: commit not found: $Commit" -ForegroundColor Red
        exit 1
    }
    $commitShort = $fullCommit.Substring(0, 12)
    Write-Host "Resolved commit: $fullCommit"

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $releaseId = "$timestamp-$commitShort"
    $releaseDir = Join-Path (Join-Path $RuntimeRoot "backup-releases") $releaseId

    if (Test-Path $releaseDir) {
        Write-Host "ERROR: release $releaseId already exists." -ForegroundColor Red
        exit 1
    }
    New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null

    # git archive : snapshot exact du commit, jamais le working tree (meme dirty).
    # -o (pas un pipe PowerShell, qui corromprait le tar binaire) laisse git ecrire
    # le fichier directement.
    $archivePath = Join-Path $releaseDir "src.tar"
    git archive --format=tar -o $archivePath $fullCommit -- backend requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: git archive failed." -ForegroundColor Red
        exit 1
    }

    tar -xf $archivePath -C $releaseDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: tar extraction failed." -ForegroundColor Red
        exit 1
    }
    Remove-Item $archivePath -Force

    $backendPath = Join-Path $releaseDir "backend"
    if (-not (Test-Path (Join-Path $backendPath "scripts\scheduled_backup.py"))) {
        Write-Host "ERROR: scheduled_backup.py missing from extracted release -- commit $fullCommit may predate it." -ForegroundColor Red
        exit 1
    }

    $criticalFiles = @(
        "backend\scripts\scheduled_backup.py",
        "backend\scripts\backup_db.py",
        "backend\scripts\backup_media.py",
        "backend\scripts\backup_offsite.py",
        "backend\services\backup_service.py",
        "backend\database.py"
    )
    $hashes = [ordered]@{}
    foreach ($f in $criticalFiles) {
        $fullPath = Join-Path $releaseDir $f
        if (-not (Test-Path $fullPath)) {
            Write-Host "ERROR: critical file missing in release: $f" -ForegroundColor Red
            exit 1
        }
        $hash = (Get-FileHash -Path $fullPath -Algorithm SHA256).Hash.ToLower()
        $hashes[$f] = $hash
    }

    $manifest = [ordered]@{
        purpose               = "scheduled-backup"
        environment           = "cabinet-real"
        git_commit            = $fullCommit
        created_at            = (Get-Date).ToString("o")
        release_id            = $releaseId
        release_root          = $releaseDir
        python_executable     = $PythonExecutable
        entrypoint            = "backend.scripts.scheduled_backup"
        critical_file_hashes  = $hashes
    }
    $manifest | ConvertTo-Json -Depth 6 | Set-Content -Path (Join-Path $releaseDir "backup-release-manifest.json") -Encoding utf8

    Write-Host ""
    Write-Host "=== Backup release created (pointer NOT updated) ===" -ForegroundColor Green
    Write-Host "release_id : $releaseId"
    Write-Host "path       : $releaseDir"
    Write-Host "commit     : $fullCommit"
    Write-Host ""
    Write-Host "This release is not yet in use. Update backup-current.json explicitly (atomic write) to activate it." -ForegroundColor Yellow
} finally {
    Pop-Location
}

exit 0
