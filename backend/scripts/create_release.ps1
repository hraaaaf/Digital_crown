# DIGITAL-CROWN-CERTIFIED-RELEASE-POLICY-1
# Materialize an immutable cabinet release ONLY from a CI-certified artifact.
#
# Forbidden by design:
# - copying the current working tree;
# - resolving HEAD/master/a branch/tag locally;
# - creating an installable release without a certificate tied to an exact SHA;
# - accepting a release that is not certified for BASIC + GOLD + ELITE.
#
# This script never activates the release and never touches cabinet data.

[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(Mandatory = $true)][string]$CertifiedArtifactZip,
    [string]$RuntimeRoot = "C:\Users\lenovo\DigitalCrown-Runtime"
)

$ErrorActionPreference = "Stop"
$RequiredPacks = @("BASIC", "GOLD", "ELITE")
$CertificateName = "release-certification.json"
$ShaMarkerName = ".digitalcrown-release-sha"
$ContentManifestName = "release-content.sha256"

function Fail([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

Write-Host "=== create_release.ps1 - certified artifact import ===" -ForegroundColor Yellow

if (-not (Test-Path -LiteralPath $CertifiedArtifactZip -PathType Leaf)) {
    Fail "certified artifact ZIP not found: $CertifiedArtifactZip"
}
if ([IO.Path]::GetExtension($CertifiedArtifactZip).ToLowerInvariant() -ne ".zip") {
    Fail "only a downloaded certified .zip artifact is accepted"
}

$runtimeReleases = Join-Path $RuntimeRoot "releases"
$stagingRoot = Join-Path $RuntimeRoot ".certified-release-staging"
$staging = Join-Path $stagingRoot ([guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $runtimeReleases -Force | Out-Null
New-Item -ItemType Directory -Path $staging -Force | Out-Null

try {
    Expand-Archive -LiteralPath $CertifiedArtifactZip -DestinationPath $staging -Force

    $certCandidates = @(Get-ChildItem -LiteralPath $staging -Filter $CertificateName -File -Recurse)
    if ($certCandidates.Count -ne 1) {
        Fail "artifact must contain exactly one $CertificateName (found $($certCandidates.Count))"
    }
    $payloadRoot = Split-Path $certCandidates[0].FullName -Parent
    $certificatePath = Join-Path $payloadRoot $CertificateName
    $markerPath = Join-Path $payloadRoot $ShaMarkerName
    $contentManifestPath = Join-Path $payloadRoot $ContentManifestName

    foreach ($requiredFile in @($certificatePath, $markerPath, $contentManifestPath)) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
            Fail "certified artifact is incomplete: missing $requiredFile"
        }
    }

    $certificate = Get-Content -LiteralPath $certificatePath -Raw | ConvertFrom-Json
    if ($certificate.certificate_version -ne 1) {
        Fail "unsupported certificate_version: $($certificate.certificate_version)"
    }
    if ($certificate.artifact_type -ne "cabinet-certified-release") {
        Fail "artifact_type is not cabinet-certified-release"
    }
    if ($certificate.repository -ne "hraaaaf/Digital_crown") {
        Fail "unexpected certificate repository: $($certificate.repository)"
    }

    $commitSha = "$($certificate.commit_sha)".Trim().ToLowerInvariant()
    if ($commitSha -notmatch '^[0-9a-f]{40}$') {
        Fail "certificate commit_sha must be an exact immutable 40-character SHA"
    }
    $markerSha = (Get-Content -LiteralPath $markerPath -Raw).Trim().ToLowerInvariant()
    if ($markerSha -ne $commitSha) {
        Fail "SHA marker does not match certificate commit_sha"
    }

    $packs = @($certificate.certified_packs | ForEach-Object { "$($_)".Trim().ToUpperInvariant() })
    foreach ($pack in $RequiredPacks) {
        if ($packs -notcontains $pack) {
            Fail "release is not universal: missing certified pack $pack"
        }
    }

    $releaseId = "$($certificate.release_id)".Trim()
    if ([string]::IsNullOrWhiteSpace($releaseId) -or -not $releaseId.Contains($commitSha.Substring(0, 12))) {
        Fail "release_id must contain the certified SHA prefix"
    }
    if ([int64]$certificate.certification_run_id -le 0) {
        Fail "certificate has no valid GitHub certification_run_id"
    }

    $manifestDigest = (Get-FileHash -LiteralPath $contentManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($manifestDigest -ne "$($certificate.content_manifest_sha256)".Trim().ToLowerInvariant()) {
        Fail "release-content.sha256 digest does not match the certificate"
    }

    $payloadRootResolved = [IO.Path]::GetFullPath($payloadRoot).TrimEnd('\') + '\'
    foreach ($line in Get-Content -LiteralPath $contentManifestPath) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line -notmatch '^([0-9a-f]{64})  (.+)$') {
            Fail "malformed content manifest line: $line"
        }
        $expectedHash = $matches[1]
        $relativePath = $matches[2].Replace('/', '\')
        $candidate = [IO.Path]::GetFullPath((Join-Path $payloadRoot $relativePath))
        if (-not $candidate.StartsWith($payloadRootResolved, [StringComparison]::OrdinalIgnoreCase)) {
            Fail "unsafe content manifest path: $relativePath"
        }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            Fail "certified file missing: $relativePath"
        }
        $actualHash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) {
            Fail "certified file changed: $relativePath"
        }
    }

    $releaseDir = Join-Path $runtimeReleases $releaseId
    if (Test-Path -LiteralPath $releaseDir) {
        Fail "immutable release already exists and will never be overwritten: $releaseDir"
    }

    New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
    Copy-Item -Path (Join-Path $payloadRoot '*') -Destination $releaseDir -Recurse -Force
    Copy-Item -LiteralPath $markerPath -Destination (Join-Path $releaseDir $ShaMarkerName) -Force

    $releaseManifest = [ordered]@{
        environment          = "cabinet-real"
        release_id           = $releaseId
        commit               = $commitSha
        certified_packs      = $RequiredPacks
        certification_run_id = [int64]$certificate.certification_run_id
        imported_at          = (Get-Date).ToString("o")
        backend_path         = (Join-Path $releaseDir "backend")
        frontend_dist_path   = (Join-Path $releaseDir "frontend\dist")
        artifact_sha256      = (Get-FileHash -LiteralPath $CertifiedArtifactZip -Algorithm SHA256).Hash.ToLowerInvariant()
        created_by_script    = "create_release.ps1"
    }
    $releaseManifest | ConvertTo-Json -Depth 6 | Set-Content -Path (Join-Path $releaseDir "release-manifest.json") -Encoding utf8

    Write-Host "" 
    Write-Host "=== CERTIFIED immutable release imported (NOT ACTIVATED) ===" -ForegroundColor Green
    Write-Host "release_id : $releaseId"
    Write-Host "path       : $releaseDir"
    Write-Host "commit     : $commitSha"
    Write-Host "packs      : BASIC / GOLD / ELITE"
    Write-Host "CI run     : $($certificate.certification_run_id)"
    Write-Host ""
    Write-Host "Activation still requires run_real_backend.ps1 and its independent certificate verification." -ForegroundColor Yellow
}
finally {
    if (Test-Path -LiteralPath $staging) {
        Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
    }
}

exit 0
