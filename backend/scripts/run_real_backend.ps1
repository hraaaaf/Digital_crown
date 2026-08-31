# REAL-RUNTIME-IMMUTABILITY-GUARD-1
# The ONE controlled launcher for the real cabinet runtime (port 8005).
# - Never uses --reload.
# - Only starts an immutable release produced by create_release.ps1 (never the working
#   repo directly).
# - Refuses anything that looks like rehearsal.
# - Enables HTTPS on the immutable runtime when the cabinet cert/key pair exists.
# - Requires explicit confirmation.
#
# Usage:
#   .\run_real_backend.ps1 -ReleaseId <id> -ConfirmRealActivation "YES"
#
# Never prints a secret (DATABASE_URL is masked when displayed).

[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(Mandatory = $true)][string]$ReleaseId,
    [Parameter(Mandatory = $true)][string]$ConfirmRealActivation,
    [string]$RuntimeRoot = "C:\Users\lenovo\DigitalCrown-Runtime",
    [string]$RealEnvFile = "C:\Users\lenovo\Documents\Cabinet\DigitalCrown\backend\.env.local",
    [int]$Port = 8005,
    [string]$VenvPython = "C:\Users\lenovo\Documents\Cabinet\DigitalCrown\venv\Scripts\python.exe",
    [string]$BindHost = "0.0.0.0",
    [string]$TlsCertFile = "",
    [string]$TlsKeyFile = ""
)

# Defense in depth : meme avec le binding positionnel desactive, on revalide explicitement
# que rien parmi les valeurs recues ne contient "--reload" (ceinture + bretelles - la
# commande uvicorn elle-meme est de toute facon construite plus bas sans passthrough).
foreach ($v in @($ReleaseId, $ConfirmRealActivation, $RuntimeRoot, $RealEnvFile, $Port, $BindHost, $TlsCertFile, $TlsKeyFile, $args)) {
    if ("$v" -like "*--reload*") {
        Write-Host "ERROR: a provided value contains --reload and is refused: $v" -ForegroundColor Red
        exit 1
    }
}

$ErrorActionPreference = "Stop"

function Mask-DatabaseUrl([string]$DatabaseUrl) {
    if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) { return '<missing>' }
    if ($DatabaseUrl -match '^(?<scheme>[^:]+://)(?<user>[^:@]+)(:(?<pwd>[^@]*))?@(?<rest>.+)$') {
        return "$($matches.scheme)$($matches.user):***@$($matches.rest)"
    }
    return $DatabaseUrl
}

Write-Host "=== run_real_backend.ps1 - controlled activation ===" -ForegroundColor Yellow

# 1. Strict explicit confirmation (not just "a flag is present")
if ($ConfirmRealActivation -ne "YES") {
    Write-Host "ERROR: missing or incorrect confirmation. Rerun with -ConfirmRealActivation `"YES`" (exact)." -ForegroundColor Red
    exit 1
}

# 2. The release must exist with a manifest
$releaseDir = Join-Path (Join-Path $RuntimeRoot "releases") $ReleaseId
$manifestPath = Join-Path $releaseDir "release-manifest.json"
if (-not (Test-Path $manifestPath)) {
    Write-Host "ERROR: no release manifest found for $ReleaseId ($manifestPath). Activation refused." -ForegroundColor Red
    exit 1
}
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
if ($manifest.environment -ne "cabinet-real") {
    Write-Host "ERROR: this release is not marked environment=cabinet-real (found: $($manifest.environment)). Refused." -ForegroundColor Red
    exit 1
}
if ($manifest.frontend_dist_path -match 'rehearsal|dist-test') {
    Write-Host "ERROR: this release's frontend_dist_path points to a rehearsal/test output ($($manifest.frontend_dist_path)). Refused." -ForegroundColor Red
    exit 1
}
$backendPath = $manifest.backend_path
if (-not (Test-Path $backendPath)) {
    Write-Host "ERROR: manifest backend_path not found: $backendPath" -ForegroundColor Red
    exit 1
}

# 3. Verify the real env file - never rehearsal, never printed in clear
if (-not (Test-Path $RealEnvFile)) {
    Write-Host "ERROR: real environment file not found: $RealEnvFile" -ForegroundColor Red
    exit 1
}
$envContent = Get-Content $RealEnvFile
$dbLine = $envContent | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
$envLine = $envContent | Where-Object { $_ -match '^ENVIRONMENT=' } | Select-Object -First 1
$mediaLine = $envContent | Where-Object { $_ -match '^MEDIA_ROOT=' } | Select-Object -First 1

$dbUrl = if ($dbLine) { $dbLine -replace '^DATABASE_URL=', '' } else { '' }
$envValue = if ($envLine) { ($envLine -replace '^ENVIRONMENT=', '').Trim() } else { 'development' }
$mediaRoot = if ($mediaLine) { ($mediaLine -replace '^MEDIA_ROOT=', '').Trim() } else { '' }

if ($dbUrl -match 'rehearsal') {
    Write-Host "ERROR: DATABASE_URL contains 'rehearsal' - the real runtime refuses a rehearsal DB." -ForegroundColor Red
    exit 1
}
if ($dbUrl -notmatch 'digitalcrown_db') {
    Write-Host "ERROR: DATABASE_URL does not point to digitalcrown_db - refused (required for the real runtime)." -ForegroundColor Red
    exit 1
}
if ($envValue -match 'rehearsal') {
    Write-Host "ERROR: ENVIRONMENT ($envValue) contains 'rehearsal' - refused for the real runtime." -ForegroundColor Red
    exit 1
}
if ($mediaRoot -match 'rehearsal') {
    Write-Host "ERROR: MEDIA_ROOT ($mediaRoot) contains 'rehearsal' - refused for the real runtime." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $VenvPython)) {
    Write-Host "ERROR: venv python interpreter not found: $VenvPython" -ForegroundColor Red
    exit 1
}

# 4. Resolve the cabinet TLS pair from the real repo, never from the immutable release.
$realBackendDir = Split-Path $RealEnvFile -Parent
$realRepoRoot = Split-Path $realBackendDir -Parent
if ([string]::IsNullOrWhiteSpace($TlsCertFile)) {
    $TlsCertFile = Join-Path $realRepoRoot "certs\cert.pem"
}
if ([string]::IsNullOrWhiteSpace($TlsKeyFile)) {
    $TlsKeyFile = Join-Path $realRepoRoot "certs\key.pem"
}

$certExists = Test-Path $TlsCertFile
$keyExists = Test-Path $TlsKeyFile
if ($certExists -xor $keyExists) {
    Write-Host "ERROR: incomplete TLS configuration: cert/key must either both exist or both be absent." -ForegroundColor Red
    exit 1
}
$httpsEnabled = $certExists -and $keyExists
if ($httpsEnabled -and $Port -ne 8005) {
    Write-Host "ERROR: HTTPS mobile/WebAuthn contract requires the real runtime on port 8005." -ForegroundColor Red
    exit 1
}

$env:PORT = "$Port"
$env:DIGITALCROWN_HTTPS_PORT = "$Port"
if ($httpsEnabled) {
    $env:DIGITALCROWN_ENABLE_HTTPS = "true"
    $env:DIGITALCROWN_WEBAUTHN_RP_ID = "digitalcrown.local"
    $env:DIGITALCROWN_WEBAUTHN_ORIGIN = "https://digitalcrown.local:$Port"
} else {
    $env:DIGITALCROWN_ENABLE_HTTPS = "false"
}

$runtimeOrigin = if ($httpsEnabled) { "https://digitalcrown.local:$Port" } else { "http://127.0.0.1:$Port" }

Write-Host "OK - checks passed." -ForegroundColor Green
Write-Host "Release     : $ReleaseId"
Write-Host "Backend     : $backendPath"
Write-Host "Frontend    : $($manifest.frontend_dist_path)"
Write-Host "DATABASE_URL: $(Mask-DatabaseUrl $dbUrl)"
Write-Host "ENVIRONMENT : $envValue"
Write-Host "Port        : $Port"
Write-Host "Bind host   : $BindHost"
Write-Host "Reload      : DISABLED (never used by this launcher)"
Write-Host "HTTPS       : $httpsEnabled"
Write-Host "Origin      : $runtimeOrigin"
Write-Host ""

# 5. Runtime manifest (before startup)
$runtimeManifest = [ordered]@{
    release_id    = $ReleaseId
    port          = $Port
    bind_host     = $BindHost
    reload        = $false
    https_enabled = [bool]$httpsEnabled
    origin        = $runtimeOrigin
    activated_at  = (Get-Date).ToString("o")
    backend_path  = $backendPath
}
$runtimeManifest | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $releaseDir "runtime-activation.json") -Encoding utf8

# 6. Startup - cwd = release folder (never the working repo), no --reload.
$uvicornArgs = @("-m", "uvicorn", "backend.main:app", "--host", $BindHost, "--port", "$Port")
if ($httpsEnabled) {
    $uvicornArgs += @("--ssl-certfile", $TlsCertFile, "--ssl-keyfile", $TlsKeyFile)
}

Write-Host "Starting (cwd = $releaseDir, no --reload)..." -ForegroundColor Cyan
$env:DIGITALCROWN_ENV_FILE = $RealEnvFile
Push-Location $releaseDir
try {
    & $VenvPython @uvicornArgs
} finally {
    Pop-Location
}
