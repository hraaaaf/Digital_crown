# DIGITAL-CROWN-CERTIFIED-RELEASE-POLICY-2
# Compose an INSTALLABLE_CERTIFIED cabinet release from:
#   1) one GitHub CODE_CERTIFIED artifact for an exact master SHA;
#   2) one runtime-assets bundle bound to that same SHA.
#
# This script NEVER copies the working tree, NEVER resolves HEAD/master locally,
# NEVER activates the release, and NEVER touches cabinet DB/media.

[CmdletBinding(PositionalBinding = $false)]
param(
    [Parameter(Mandatory = $true)][string]$CertifiedArtifactZip,
    [Parameter(Mandatory = $true)][string]$RuntimeAssetsZip,
    [string]$RuntimeRoot = "C:\Users\lenovo\DigitalCrown-Runtime",
    [string]$VerifierPython = "python",
    [string]$GitHubCli = "gh",
    [string]$AttestationBundle = "",
    [string]$TrustedRoot = ""
)

$ErrorActionPreference = "Stop"
$RequiredPacks = @("BASIC", "GOLD", "ELITE")
$CertificateName = "release-certification.json"
$ShaMarkerName = ".digitalcrown-release-sha"
$ContentManifestName = "release-content.sha256"
$AssetCertificateName = "runtime-assets-certification.json"
$Repo = "hraaaaf/Digital_crown"
$SignerWorkflow = "hraaaaf/Digital_crown/.github/workflows/cabinet-release-certification.yml"

function Fail([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Expand-SafeZip([string]$ZipPath, [string]$Destination) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $destRoot = [IO.Path]::GetFullPath($Destination).TrimEnd([char[]]@('\', '/')) + [IO.Path]::DirectorySeparatorChar
    $archive = [IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        foreach ($entry in $archive.Entries) {
            $target = [IO.Path]::GetFullPath((Join-Path $Destination $entry.FullName))
            if (-not $target.StartsWith($destRoot, [StringComparison]::OrdinalIgnoreCase)) {
                Fail "ZIP path traversal refused: $($entry.FullName)"
            }
            if ([string]::IsNullOrEmpty($entry.Name)) {
                New-Item -ItemType Directory -Path $target -Force | Out-Null
                continue
            }
            $parent = Split-Path $target -Parent
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $true)
        }
    }
    finally {
        $archive.Dispose()
    }
}

function Get-SinglePayloadRoot([string]$SearchRoot, [string]$Filename) {
    $candidates = @(Get-ChildItem -LiteralPath $SearchRoot -Filter $Filename -File -Recurse)
    if ($candidates.Count -ne 1) {
        Fail "archive must contain exactly one $Filename (found $($candidates.Count))"
    }
    return (Split-Path $candidates[0].FullName -Parent)
}

Write-Host "=== create_release.ps1 - INSTALLABLE certification composition ===" -ForegroundColor Yellow

foreach ($zip in @($CertifiedArtifactZip, $RuntimeAssetsZip)) {
    if (-not (Test-Path -LiteralPath $zip -PathType Leaf)) {
        Fail "required ZIP not found: $zip"
    }
    if ([IO.Path]::GetExtension($zip).ToLowerInvariant() -ne ".zip") {
        Fail "only .zip certification artifacts are accepted: $zip"
    }
}
if (-not (Get-Command $VerifierPython -ErrorAction SilentlyContinue)) {
    Fail "Python verifier not found: $VerifierPython"
}
if (-not (Get-Command $GitHubCli -ErrorAction SilentlyContinue)) {
    Fail "GitHub CLI is required to verify Sigstore provenance: $GitHubCli"
}
if ([string]::IsNullOrWhiteSpace($AttestationBundle) -xor [string]::IsNullOrWhiteSpace($TrustedRoot)) {
    Fail "offline attestation verification requires BOTH -AttestationBundle and -TrustedRoot"
}
if (-not [string]::IsNullOrWhiteSpace($AttestationBundle)) {
    if (-not (Test-Path -LiteralPath $AttestationBundle -PathType Leaf)) { Fail "attestation bundle not found" }
    if (-not (Test-Path -LiteralPath $TrustedRoot -PathType Leaf)) { Fail "trusted root not found" }
}

$stagingRoot = Join-Path $RuntimeRoot ".certified-release-staging"
$staging = Join-Path $stagingRoot ([guid]::NewGuid().ToString("N"))
$codeStaging = Join-Path $staging "code"
$assetStaging = Join-Path $staging "assets"
New-Item -ItemType Directory -Path $codeStaging -Force | Out-Null
New-Item -ItemType Directory -Path $assetStaging -Force | Out-Null

try {
    # 1. Safe extraction only. No code from the artifact is executed yet.
    Expand-SafeZip $CertifiedArtifactZip $codeStaging
    $payloadRoot = Get-SinglePayloadRoot $codeStaging $CertificateName
    $certificatePath = Join-Path $payloadRoot $CertificateName
    $markerPath = Join-Path $payloadRoot $ShaMarkerName
    $contentManifestPath = Join-Path $payloadRoot $ContentManifestName

    foreach ($requiredFile in @($certificatePath, $markerPath, $contentManifestPath)) {
        if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
            Fail "CODE_CERTIFIED artifact incomplete: missing $requiredFile"
        }
    }

    # 2. Verify CODE_CERTIFIED metadata without executing artifact code.
    $certificate = Get-Content -LiteralPath $certificatePath -Raw | ConvertFrom-Json
    if ($certificate.certificate_version -ne 1) { Fail "unsupported CODE certificate version" }
    if ($certificate.artifact_type -ne "cabinet-certified-release") { Fail "invalid CODE artifact_type" }
    if ($certificate.certification_level -ne "CODE_CERTIFIED") { Fail "artifact is not CODE_CERTIFIED" }
    if ($certificate.repository -ne $Repo) { Fail "unexpected certificate repository" }

    $commitSha = "$($certificate.commit_sha)".Trim().ToLowerInvariant()
    if ($commitSha -notmatch '^[0-9a-f]{40}$') { Fail "CODE certificate requires an exact 40-char SHA" }
    $markerSha = (Get-Content -LiteralPath $markerPath -Raw).Trim().ToLowerInvariant()
    if ($markerSha -ne $commitSha) { Fail "SHA marker does not match CODE certificate" }

    $packs = @($certificate.certified_packs | ForEach-Object { "$($_)".Trim().ToUpperInvariant() })
    foreach ($pack in $RequiredPacks) {
        if ($packs -notcontains $pack) { Fail "CODE release missing certified profile $pack" }
    }

    $manifestDigest = (Get-FileHash -LiteralPath $contentManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($manifestDigest -ne "$($certificate.content_manifest_sha256)".Trim().ToLowerInvariant()) {
        Fail "release-content.sha256 digest does not match CODE certificate"
    }

    # Verify every listed byte AND reject any unlisted appended file.
    # Avoid Path.GetRelativePath: cabinet may run Windows PowerShell 5.1/.NET Framework.
    $payloadRootResolved = [IO.Path]::GetFullPath($payloadRoot).TrimEnd([char[]]@('\', '/')) + [IO.Path]::DirectorySeparatorChar
    $expectedFiles = @{}
    $expectedFiles[$CertificateName.ToLowerInvariant()] = $true
    $expectedFiles[$ShaMarkerName.ToLowerInvariant()] = $true
    $expectedFiles[$ContentManifestName.ToLowerInvariant()] = $true

    foreach ($line in Get-Content -LiteralPath $contentManifestPath) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        if ($line -notmatch '^([0-9a-f]{64})  (.+)$') { Fail "malformed CODE content manifest line: $line" }
        $expectedHash = $matches[1]
        $relativeSlash = $matches[2].Replace('\', '/')
        $relativeKey = $relativeSlash.ToLowerInvariant()
        if ($expectedFiles.ContainsKey($relativeKey)) { Fail "duplicate CODE content path: $relativeSlash" }
        $expectedFiles[$relativeKey] = $true
        $relativePath = $relativeSlash.Replace('/', [IO.Path]::DirectorySeparatorChar)
        $candidate = [IO.Path]::GetFullPath((Join-Path $payloadRoot $relativePath))
        if (-not $candidate.StartsWith($payloadRootResolved, [StringComparison]::OrdinalIgnoreCase)) {
            Fail "unsafe CODE content path: $relativeSlash"
        }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { Fail "CODE file missing: $relativeSlash" }
        $actualHash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedHash) { Fail "CODE file changed: $relativeSlash" }
    }

    $actualFiles = @(Get-ChildItem -LiteralPath $payloadRoot -File -Recurse)
    foreach ($actualFile in $actualFiles) {
        $actualFull = [IO.Path]::GetFullPath($actualFile.FullName)
        if (-not $actualFull.StartsWith($payloadRootResolved, [StringComparison]::OrdinalIgnoreCase)) {
            Fail "CODE file escaped payload root: $actualFull"
        }
        $relativeActual = $actualFull.Substring($payloadRootResolved.Length).Replace('\', '/')
        if (-not $expectedFiles.ContainsKey($relativeActual.ToLowerInvariant())) {
            Fail "unlisted appended CODE file refused: $relativeActual"
        }
    }
    if ($expectedFiles.Count -ne $actualFiles.Count) { Fail "CODE artifact file-set mismatch" }

    # 3. Cryptographic provenance: repo + exact signer workflow + exact master SHA.
    $attestationArgs = @(
        "attestation", "verify", $contentManifestPath,
        "--repo", $Repo,
        "--signer-workflow", $SignerWorkflow,
        "--source-digest", $commitSha,
        "--source-ref", "refs/heads/master",
        "--deny-self-hosted-runners",
        "--format", "json"
    )
    if (-not [string]::IsNullOrWhiteSpace($AttestationBundle)) {
        $attestationArgs += @("--bundle", $AttestationBundle, "--custom-trusted-root", $TrustedRoot)
    }
    $attestationOutput = & $GitHubCli @attestationArgs
    if ($LASTEXITCODE -ne 0) { Fail "GitHub/Sigstore provenance verification failed" }
    $attestationText = $attestationOutput -join [Environment]::NewLine
    try { $attestationParsed = $attestationText | ConvertFrom-Json } catch { Fail "invalid gh attestation JSON output" }
    if (@($attestationParsed).Count -lt 1) { Fail "gh attestation verify returned no verified attestation" }
    $attestationEvidencePath = Join-Path $staging "github-attestation-verification.json"
    $attestationText | Set-Content -LiteralPath $attestationEvidencePath -Encoding utf8

    # 4. Runtime assets are safely extracted but not trusted yet.
    Expand-SafeZip $RuntimeAssetsZip $assetStaging
    $assetRoot = Get-SinglePayloadRoot $assetStaging $AssetCertificateName

    # 5. Only now execute the compose script from the hash-verified + Sigstore-verified
    # exact code artifact. It re-verifies CODE + assets and promotes atomically.
    $composeScript = Join-Path $payloadRoot "backend\scripts\compose_installable_release.py"
    if (-not (Test-Path -LiteralPath $composeScript -PathType Leaf)) {
        Fail "attested compose_installable_release.py missing"
    }
    $codeArtifactHash = (Get-FileHash -LiteralPath $CertifiedArtifactZip -Algorithm SHA256).Hash.ToLowerInvariant()
    $assetBundleHash = (Get-FileHash -LiteralPath $RuntimeAssetsZip -Algorithm SHA256).Hash.ToLowerInvariant()

    $oldPythonPath = $env:PYTHONPATH
    $env:PYTHONPATH = $payloadRoot
    try {
        & $VerifierPython $composeScript `
            --code-release-dir $payloadRoot `
            --runtime-assets-dir $assetRoot `
            --runtime-root $RuntimeRoot `
            --attestation-evidence $attestationEvidencePath `
            --code-artifact-sha256 $codeArtifactHash `
            --runtime-asset-bundle-sha256 $assetBundleHash
        if ($LASTEXITCODE -ne 0) { Fail "INSTALLABLE composition verifier rejected the release" }
    }
    finally {
        $env:PYTHONPATH = $oldPythonPath
    }

    Write-Host ""
    Write-Host "=== INSTALLABLE_CERTIFIED release composed (NOT ACTIVATED) ===" -ForegroundColor Green
    Write-Host "commit     : $commitSha"
    Write-Host "profiles   : BASIC / GOLD / ELITE"
    Write-Host "provenance : GitHub/Sigstore VERIFIED"
    Write-Host "activation : still forbidden until run_real_backend.ps1 explicit activation" -ForegroundColor Yellow
}
finally {
    if (Test-Path -LiteralPath $staging) {
        Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
    }
}

exit 0
