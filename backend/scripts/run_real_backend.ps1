# DIGITAL-CROWN-CERTIFIED-RELEASE-POLICY-2
# The ONE controlled launcher for the real cabinet runtime (port 8005).
# Starts ONLY INSTALLABLE_CERTIFIED immutable releases. Never master/HEAD/branch/tag.
# Full code + runtime-asset verification happens BEFORE the real cabinet env is read.

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

foreach ($v in @($ReleaseId, $ConfirmRealActivation, $RuntimeRoot, $RealEnvFile, $Port, $BindHost, $TlsCertFile, $TlsKeyFile, $args)) {
    if ("$v" -like "*--reload*") {
        Write-Host "ERROR: a provided value contains --reload and is refused: $v" -ForegroundColor Red
        exit 1
    }
}

$ErrorActionPreference = "Stop"
$RequiredPacks = @("BASIC", "GOLD", "ELITE")

function Fail([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Mask-DatabaseUrl([string]$DatabaseUrl) {
    if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) { return '<missing>' }
    if ($DatabaseUrl -match '^(?<scheme>[^:]+://)(?<user>[^:@]+)(:(?<pwd>[^@]*))?@(?<rest>.+)$') {
        return "$($matches.scheme)$($matches.user):***@$($matches.rest)"
    }
    return $DatabaseUrl
}

Write-Host "=== run_real_backend.ps1 - INSTALLABLE_CERTIFIED activation ===" -ForegroundColor Yellow

if ($ConfirmRealActivation -ne "YES") {
    Fail "missing or incorrect confirmation. Use -ConfirmRealActivation `"YES`" (exact)."
}

# 1. Release proof. No cabinet env/data has been read yet.
$releaseDir = Join-Path (Join-Path $RuntimeRoot "releases") $ReleaseId
$manifestPath = Join-Path $releaseDir "release-manifest.json"
$certificatePath = Join-Path $releaseDir "release-certification.json"
$installablePath = Join-Path $releaseDir "installable-certification.json"
$shaMarkerPath = Join-Path $releaseDir ".digitalcrown-release-sha"
$contentManifestPath = Join-Path $releaseDir "release-content.sha256"
$assetCertificatePath = Join-Path $releaseDir "runtime-assets-certification.json"
$assetManifestPath = Join-Path $releaseDir "runtime-assets-content.sha256"
$attestationEvidencePath = Join-Path $releaseDir "github-attestation-verification.json"

foreach ($requiredFile in @(
    $manifestPath, $certificatePath, $installablePath, $shaMarkerPath,
    $contentManifestPath, $assetCertificatePath, $assetManifestPath, $attestationEvidencePath
)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        Fail "INSTALLABLE_CERTIFIED release incomplete: missing $requiredFile"
    }
}
if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    Fail "venv python interpreter not found: $VenvPython"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$certificate = Get-Content -LiteralPath $certificatePath -Raw | ConvertFrom-Json
$installable = Get-Content -LiteralPath $installablePath -Raw | ConvertFrom-Json
$certSha = "$($certificate.commit_sha)".Trim().ToLowerInvariant()
$markerSha = (Get-Content -LiteralPath $shaMarkerPath -Raw).Trim().ToLowerInvariant()

if ($manifest.environment -ne "cabinet-real") { Fail "release is not marked environment=cabinet-real" }
if ($manifest.certification_level -ne "INSTALLABLE_CERTIFIED") { Fail "release-manifest is not INSTALLABLE_CERTIFIED" }
if ($installable.certification_level -ne "INSTALLABLE_CERTIFIED" -or $installable.installable -ne $true) {
    Fail "final installable certificate is absent/invalid"
}
if ($certificate.certification_level -ne "CODE_CERTIFIED") { Fail "embedded code certificate is not CODE_CERTIFIED" }
if ($certSha -notmatch '^[0-9a-f]{40}$') { Fail "certificate commit_sha is not an exact immutable SHA" }
if ($markerSha -ne $certSha -or "$($manifest.commit)".Trim().ToLowerInvariant() -ne $certSha) {
    Fail "release-manifest / code certificate / SHA marker mismatch"
}
if ($ReleaseId -ne "$($certificate.release_id)" -or $ReleaseId -ne "$($installable.release_id)") {
    Fail "requested ReleaseId does not equal certified release_id"
}
$certPacks = @($installable.certified_packs | ForEach-Object { "$($_)".Trim().ToUpperInvariant() })
foreach ($pack in $RequiredPacks) {
    if ($certPacks -notcontains $pack) { Fail "activation refused: INSTALLABLE release missing $pack" }
}

$verifyScript = Join-Path $releaseDir "backend\scripts\verify_installable_release.py"
if (-not (Test-Path -LiteralPath $verifyScript -PathType Leaf)) {
    Fail "INSTALLABLE verifier missing: $verifyScript"
}
$oldPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = $releaseDir
try {
    & $VenvPython $verifyScript --release-dir $releaseDir
    if ($LASTEXITCODE -ne 0) { Fail "INSTALLABLE verifier rejected $ReleaseId" }
}
finally {
    $env:PYTHONPATH = $oldPythonPath
}

if ($manifest.frontend_dist_path -match 'rehearsal|dist-test') { Fail "release frontend points to rehearsal/test output" }
$backendPath = $manifest.backend_path
if (-not (Test-Path -LiteralPath $backendPath -PathType Container)) { Fail "manifest backend_path not found: $backendPath" }

# 2. Only after complete immutable release proof, inspect the real cabinet environment.
if (-not (Test-Path -LiteralPath $RealEnvFile -PathType Leaf)) {
    Fail "real environment file not found: $RealEnvFile"
}
$envContent = Get-Content $RealEnvFile
$dbLine = $envContent | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
$envLine = $envContent | Where-Object { $_ -match '^ENVIRONMENT=' } | Select-Object -First 1
$mediaLine = $envContent | Where-Object { $_ -match '^MEDIA_ROOT=' } | Select-Object -First 1

$dbUrl = if ($dbLine) { $dbLine -replace '^DATABASE_URL=', '' } else { '' }
$envValue = if ($envLine) { ($envLine -replace '^ENVIRONMENT=', '').Trim() } else { 'development' }
$mediaRoot = if ($mediaLine) { ($mediaLine -replace '^MEDIA_ROOT=', '').Trim() } else { '' }

if ($dbUrl -match 'rehearsal') { Fail "DATABASE_URL contains rehearsal" }
if ($dbUrl -notmatch 'digitalcrown_db') { Fail "DATABASE_URL does not point to digitalcrown_db" }
if ($envValue -match 'rehearsal') { Fail "ENVIRONMENT contains rehearsal" }
if ($mediaRoot -match 'rehearsal') { Fail "MEDIA_ROOT contains rehearsal" }

# 3. TLS and runtime startup contract.
$realBackendDir = Split-Path $RealEnvFile -Parent
$realRepoRoot = Split-Path $realBackendDir -Parent
if ([string]::IsNullOrWhiteSpace($TlsCertFile)) { $TlsCertFile = Join-Path $realRepoRoot "certs\cert.pem" }
if ([string]::IsNullOrWhiteSpace($TlsKeyFile)) { $TlsKeyFile = Join-Path $realRepoRoot "certs\key.pem" }

$certExists = Test-Path $TlsCertFile
$keyExists = Test-Path $TlsKeyFile
if ($certExists -xor $keyExists) { Fail "incomplete TLS configuration: cert/key must both exist or both be absent" }
$httpsEnabled = $certExists -and $keyExists
if ($httpsEnabled -and $Port -ne 8005) { Fail "HTTPS mobile/WebAuthn contract requires the real runtime on port 8005" }

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

Write-Host "OK - INSTALLABLE_CERTIFIED release checks passed." -ForegroundColor Green
Write-Host "Release     : $ReleaseId"
Write-Host "Commit      : $certSha"
Write-Host "Profiles    : BASIC / GOLD / ELITE"
Write-Host "CI run      : $($certificate.certification_run_id)"
Write-Host "Provenance  : GitHub/Sigstore VERIFIED at composition"
Write-Host "Backend     : $backendPath"
Write-Host "Frontend    : $($manifest.frontend_dist_path)"
Write-Host "DATABASE_URL: $(Mask-DatabaseUrl $dbUrl)"
Write-Host "ENVIRONMENT : $envValue"
Write-Host "Port        : $Port"
Write-Host "Bind host   : $BindHost"
Write-Host "Reload      : DISABLED"
Write-Host "HTTPS       : $httpsEnabled"
Write-Host "Origin      : $runtimeOrigin"
Write-Host ""

$runtimeManifest = [ordered]@{
    release_id            = $ReleaseId
    commit_sha            = $certSha
    certification_level   = "INSTALLABLE_CERTIFIED"
    certification_run_id  = [int64]$certificate.certification_run_id
    certified_packs       = $RequiredPacks
    port                  = $Port
    bind_host             = $BindHost
    reload                = $false
    https_enabled         = [bool]$httpsEnabled
    origin                = $runtimeOrigin
    activated_at          = (Get-Date).ToString("o")
    backend_path          = $backendPath
}
$runtimeManifest | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $releaseDir "runtime-activation.json") -Encoding utf8

$uvicornArgs = @("-m", "uvicorn", "backend.main:app", "--host", $BindHost, "--port", "$Port")
if ($httpsEnabled) { $uvicornArgs += @("--ssl-certfile", $TlsCertFile, "--ssl-keyfile", $TlsKeyFile) }

Write-Host "Starting INSTALLABLE_CERTIFIED release (cwd = $releaseDir, no --reload)..." -ForegroundColor Cyan
$env:DIGITALCROWN_ENV_FILE = $RealEnvFile
Push-Location $releaseDir
try {
    & $VenvPython @uvicornArgs
} finally {
    Pop-Location
}
