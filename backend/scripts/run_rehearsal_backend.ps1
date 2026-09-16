# Launch rehearsal backend with strict isolation & safety guards
# This script NEVER modifies persistent Windows variables
# All variables live only in this PowerShell process

Write-Host '=== Rehearsal Backend Isolation Safety ===' -ForegroundColor Yellow

function Mask-DatabaseUrl([string]$DatabaseUrl) {
    if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
        return '<missing>'
    }
    if ($DatabaseUrl -match '^(?<scheme>[^:]+://)(?<user>[^:@]+)(:(?<pwd>[^@]*))?@(?<rest>.+)$') {
        return "$($matches.scheme)$($matches.user):***@$($matches.rest)"
    }
    return $DatabaseUrl
}

function Test-UnsafeMediaRoot([string]$MediaRoot) {
    # Généralisé (REAL-BUILD-RUNTIME-ISOLATION-GUARD-1) : n'exigeait auparavant que le
    # literal exact "install_rehearsal_media", ce qui laissait passer tout autre dossier
    # de rehearsal nommé différemment (ex. "treatment_journey_rehearsal_media" en Phase B).
    # Le dossier doit maintenant seulement contenir "rehearsal", pas un nom figé.
    if ([string]::IsNullOrWhiteSpace($MediaRoot)) {
        return $true
    }
    $normalized = $MediaRoot.Replace('\', '/').ToLowerInvariant()
    $realMediaRoot = (Join-Path $env:APPDATA 'DigitalCrown\media').Replace('\', '/').ToLowerInvariant()
    if ($normalized -eq $realMediaRoot) {
        return $true
    }
    if ($normalized -like '*digitalcrown/media*') {
        return $true
    }
    if ($normalized -notlike '*rehearsal*') {
        return $true
    }
    return $false
}

# 1. Check if ENVIRONMENT is production/cabinet globally
$global_env = [Environment]::GetEnvironmentVariable("ENVIRONMENT", [EnvironmentVariableTarget]::Machine)
$user_env = [Environment]::GetEnvironmentVariable("ENVIRONMENT", [EnvironmentVariableTarget]::User)

if ($global_env -eq "production" -or $global_env -eq "cabinet" -or $user_env -eq "production" -or $user_env -eq "cabinet") {
    Write-Host 'ERROR: ENVIRONMENT=production/cabinet globally' -ForegroundColor Red
    exit 1
}

# 2. Check if PORT 8005 is set
$global_port = [Environment]::GetEnvironmentVariable("PORT", [EnvironmentVariableTarget]::Machine)
$user_port = [Environment]::GetEnvironmentVariable("PORT", [EnvironmentVariableTarget]::User)

if ($global_port -eq "8005" -or $user_port -eq "8005") {
    Write-Host 'ERROR: PORT=8005 globally (cabinet port)' -ForegroundColor Red
    exit 1
}

# 3. Load rehearsal env file
$env_file = '.env.e2e-install-rehearsal'
if (-not (Test-Path $env_file)) {
    Write-Host 'ERROR: .env.e2e-install-rehearsal not found' -ForegroundColor Red
    exit 1
}

Write-Host 'OK: Safety checks passed' -ForegroundColor Green

# Load env into current process only (NOT persistent)
Write-Host 'Loading rehearsal env...' -ForegroundColor Cyan
$env_content = Get-Content $env_file
$env_keys = @{}
foreach ($line in $env_content) {
    if ($line -match '^([^=]+)=(.*)$' -and -not $line.StartsWith('#')) {
        $key = $matches[1].Trim()
        $val = $matches[2].Trim()
        if ($key) {
            $env_keys[$key] = $true
            Set-Item "env:$key" $val -ErrorAction SilentlyContinue
        }
    }
}

# Verify isolation
if (-not $env_keys.ContainsKey('DATABASE_URL') -or [string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    Write-Host 'ERROR: rehearsal env must explicitly define DATABASE_URL' -ForegroundColor Red
    exit 1
}

if ($env:ENVIRONMENT -ne "e2e_install_rehearsal") {
    Write-Host 'ERROR: ENVIRONMENT != e2e_install_rehearsal' -ForegroundColor Red
    exit 1
}

if (-not $env:MEDIA_ROOT) {
    Write-Host 'ERROR: MEDIA_ROOT missing' -ForegroundColor Red
    exit 1
}

if (Test-UnsafeMediaRoot $env:MEDIA_ROOT) {
    Write-Host 'ERROR: MEDIA_ROOT points to an unsafe folder for rehearsal' -ForegroundColor Red
    exit 1
}

if ($env:PORT -and $env:PORT -eq "8005") {
    Write-Host 'ERROR: PORT=8005 forbidden for rehearsal' -ForegroundColor Red
    exit 1
}

# The application requires a process-local attestation for every persistent
# development/rehearsal target. Derive it from the exact target after the env
# file has been loaded; never hard-code or print the password-bearing URL.
$env:DIGITALCROWN_ISOLATED_RUNTIME = "true"
$fingerprint = (& .\.venv312\Scripts\python.exe -c "from backend.core.runtime_safety import database_target_fingerprint; import os; print(database_target_fingerprint(os.environ['DATABASE_URL']))").Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($fingerprint)) {
    Write-Host 'ERROR: unable to attest the isolated rehearsal database target' -ForegroundColor Red
    exit 1
}
$env:DIGITALCROWN_ISOLATION_DB_FINGERPRINT = $fingerprint

Write-Host ''
Write-Host '=== REHEARSAL ACTIVE (process-local) ===' -ForegroundColor Green
Write-Host 'ENVIRONMENT=e2e_install_rehearsal'
Write-Host "DB=$(Mask-DatabaseUrl $env:DATABASE_URL)"
Write-Host "DB_FINGERPRINT=$fingerprint"
Write-Host "PORT=8008"
Write-Host "MEDIA_ROOT=$($env:MEDIA_ROOT)"
Write-Host "Ctrl+C to stop"
Write-Host ''

# Launch backend
& .\.venv312\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8008

Write-Host ''
Write-Host '=== REHEARSAL STOPPED ===' -ForegroundColor Yellow
Write-Host 'No persistent changes made. Cabinet database untouched.'
