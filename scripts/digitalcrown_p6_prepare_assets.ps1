$ErrorActionPreference = "Stop"

$MainRepo = "C:\Users\lenovo\Documents\Cabinet\DigitalCrown"
$Repo = "hraaaaf/Digital_crown"
$Tag = "p6-scientific-assets-v1"
$AssetName = "p6-scientific-assets-v1.zip"

$Pano = Join-Path $MainRepo "backend\ai_models\panoramic_model.onnx"
$Legacy = Join-Path $MainRepo "backend\ai_models\cephld_cca"
$Weight = Join-Path $Legacy "ceph_weights.pth"

foreach ($p in @($Pano, $Legacy, $Weight)) {
    if (-not (Test-Path $p)) { throw "P6 asset introuvable: $p" }
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "GitHub CLI 'gh' requis." }
gh auth status
if ($LASTEXITCODE -ne 0) { throw "gh n'est pas authentifié." }

$Stage = Join-Path $env:TEMP "digitalcrown-p6-assets"
if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
$Ai = Join-Path $Stage "backend\ai_models"
$LegacyDst = Join-Path $Ai "cephld_cca"
New-Item -ItemType Directory -Force $LegacyDst | Out-Null
Copy-Item $Pano (Join-Path $Ai "panoramic_model.onnx")
Copy-Item $Weight (Join-Path $LegacyDst "ceph_weights.pth")

$PyFiles = Get-ChildItem $Legacy -Recurse -File -Filter "*.py" | Where-Object {
    $_.FullName -notmatch "[\\/]__pycache__[\\/]" -and
    $_.FullName -notmatch "[\\/]model[\\/]"
}
if (-not $PyFiles) { throw "Aucune source Python runtime cephld_cca trouvée." }
foreach ($f in $PyFiles) {
    $Rel = $f.FullName.Substring($Legacy.Length).TrimStart("\", "/")
    $Dest = Join-Path $LegacyDst $Rel
    New-Item -ItemType Directory -Force (Split-Path $Dest -Parent) | Out-Null
    Copy-Item $f.FullName $Dest
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$Zip = Join-Path $Desktop $AssetName
if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path (Join-Path $Stage "backend") -DestinationPath $Zip -CompressionLevel Optimal
$BundleSha = (Get-FileHash $Zip -Algorithm SHA256).Hash.ToLowerInvariant()
$PanoSha = (Get-FileHash $Pano -Algorithm SHA256).Hash.ToLowerInvariant()
$WeightSha = (Get-FileHash $Weight -Algorithm SHA256).Hash.ToLowerInvariant()

# User explicitly chose the same repository for P6 assets. Until the repository
# is made private, this release asset is publicly retrievable.
gh release view $Tag --repo $Repo *> $null
if ($LASTEXITCODE -eq 0) {
    gh release upload $Tag $Zip --repo $Repo --clobber
} else {
    gh release create $Tag $Zip --repo $Repo --target portability/p6-windows-packaging --title "Digital Crown P6 scientific assets v1" --notes "P6 runtime-only bundle: panoramic ONNX + CephLD-CCA runtime source/weight. Historical SOTA 38-point model intentionally excluded."
}
if ($LASTEXITCODE -ne 0) { throw "Upload release P6 échoué." }

$BundleSha | gh secret set P6_SCIENTIFIC_BUNDLE_SHA256 --repo $Repo
if ($LASTEXITCODE -ne 0) { throw "Impossible de configurer P6_SCIENTIFIC_BUNDLE_SHA256." }

$payload = [ordered]@{
    repo = $Repo
    release_tag = $Tag
    asset_name = $AssetName
    bundle_sha256 = $BundleSha
    panoramic_sha256 = $PanoSha
    cephalo_legacy_sha256 = $WeightSha
}
Write-Host "P6_ASSET_UPLOAD=SUCCESS"
Write-Host ("P6_ASSET_HASHES=" + ($payload | ConvertTo-Json -Compress))
