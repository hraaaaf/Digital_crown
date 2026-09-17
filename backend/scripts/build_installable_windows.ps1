param(
    [Parameter(Mandatory = $false)]
    [string]$ReleaseDir = "."
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($env:OS -ne "Windows_NT") {
    throw "Digital Crown Windows package must be built on Windows."
}

$releaseRoot = (Resolve-Path $ReleaseDir).Path
$verifyScript = Join-Path $releaseRoot "backend\scripts\verify_installable_release.py"
$contractScript = Join-Path $releaseRoot "scripts\windows_build_dependency_contract.py"
$buildRequirements = Join-Path $releaseRoot "backend\requirements-windows-build.txt"
$specPath = Join-Path $releaseRoot "DigitalCrown.spec"

foreach ($required in @($verifyScript, $contractScript, $buildRequirements, $specPath)) {
    if (-not (Test-Path $required -PathType Leaf)) {
        throw "Required build input missing: $required"
    }
}

# Verify the immutable release before reading/installing its dependency lock.
& py -3.12 $verifyScript --release-dir $releaseRoot
if ($LASTEXITCODE -ne 0) {
    throw "INSTALLABLE_CERTIFIED verification failed before build."
}

$marker = Join-Path $releaseRoot ".digitalcrown-release-sha"
$sha = (Get-Content $marker -Raw).Trim()
if ($sha -notmatch '^[0-9a-f]{40}$') {
    throw "Invalid certified SHA marker."
}

$buildRoot = Join-Path $env:TEMP ("DigitalCrownBuild-" + $sha.Substring(0, 12))
if (Test-Path $buildRoot) {
    Remove-Item -Recurse -Force $buildRoot
}
New-Item -ItemType Directory -Path $buildRoot | Out-Null
$venv = Join-Path $buildRoot ".venv"

try {
    & py -3.12 -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create Python 3.12 build environment." }

    $python = Join-Path $venv "Scripts\python.exe"
    & $python -m pip install --upgrade "pip==26.0.1"
    if ($LASTEXITCODE -ne 0) { throw "Failed to provision pinned pip." }

    & $python -m pip install -r $buildRequirements
    if ($LASTEXITCODE -ne 0) { throw "Failed to install canonical Windows build dependencies." }

    & $python -m pip check
    if ($LASTEXITCODE -ne 0) { throw "pip check failed for Windows build environment." }

    & $python $contractScript
    if ($LASTEXITCODE -ne 0) { throw "Windows dependency contract rejected the build environment." }

    Push-Location $releaseRoot
    try {
        & $python -m PyInstaller --clean --noconfirm $specPath
        if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }
    }
    finally {
        Pop-Location
    }

    $distRoot = Join-Path $releaseRoot "dist\DigitalCrown"
    $exe = Join-Path $distRoot "DigitalCrown.exe"
    if (-not (Test-Path $exe -PathType Leaf)) {
        throw "Expected Windows executable missing after build: $exe"
    }

    & $python -m pip freeze | Set-Content -Encoding UTF8 (Join-Path $distRoot "build-environment.txt")
    Set-Content -Encoding ASCII (Join-Path $distRoot "build-source-sha.txt") ($sha + "`n")

    $exeHash = (Get-FileHash -Algorithm SHA256 $exe).Hash.ToLowerInvariant()
    Set-Content -Encoding ASCII (Join-Path $distRoot "DigitalCrown.exe.sha256") ($exeHash + "  DigitalCrown.exe`n")

    Write-Host "WINDOWS_PACKAGE_BUILD=SUCCESS"
    Write-Host "SOURCE_SHA=$sha"
    Write-Host "EXE_SHA256=$exeHash"
}
finally {
    if (Test-Path $buildRoot) {
        Remove-Item -Recurse -Force $buildRoot
    }
}
