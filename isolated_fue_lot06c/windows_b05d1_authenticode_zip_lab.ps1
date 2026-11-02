#Requires -Version 7.0
# LOT06 B05D1 synthetic Windows Authenticode ZIP rehearsal, hosted CI only.
$ErrorActionPreference='Stop'
if (-not $IsWindows -or $env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows' -or $env:ENVIRONMENT -ne 'test' -or $env:DIGITALCROWN_ISOLATED_RUNTIME -ne 'true' -or $env:DC06B05D1_LAB -ne '1') { throw 'DC06B05D1_NON_LAB_DENIED' }
$id=[guid]::NewGuid().ToString('N')
$source=Join-Path $env:ProgramData ('DC06B05C-LAB-'+$id+'-source')
$target=Join-Path $env:ProgramData ('DC06B05C-LAB-'+$id+'-target')
$zip=Join-Path $env:RUNNER_TEMP ('DC06B05D-LAB-'+$id+'.zip')
$pin=Join-Path $env:RUNNER_TEMP ('DC06B05C-pub-'+$id+'.bin')
$publisherPin=Join-Path $env:RUNNER_TEMP ('DC06B05D-publisher-'+$id+'.txt')
$unsigned=Join-Path $env:RUNNER_TEMP ('DC06B05D-unsigned-'+$id+'.exe')
$foreignExe=Join-Path $env:RUNNER_TEMP ('DC06B05D-foreign-'+$id+'.exe')
$project=Join-Path $PSScriptRoot 'scm_fixture_c05b03r/ScmPipeFixture.csproj'
$admission=Join-Path $PSScriptRoot 'b05c1_admission_lab.py'
$pub=$null
$other=$null
$rootStore=[System.Security.Cryptography.X509Certificates.X509Store]::new('Root','CurrentUser')
$rootOpen=$false
function Make-TestCert([string]$role) {
    New-SelfSignedCertificate -Type CodeSigningCert -Subject ('CN=DC06B05D-LAB-'+$role+'-'+$id) -CertStoreLocation 'Cert:\CurrentUser\My' -KeyAlgorithm RSA -KeyLength 2048 -HashAlgorithm SHA256 -KeyExportPolicy NonExportable -NotAfter (Get-Date).AddDays(1) -ErrorAction Stop
}
function Trust-TestCert($c) { $rootStore.Add($c) }
function Sign-Exe([string]$path,$c) {
    $s=Set-AuthenticodeSignature -FilePath $path -Certificate $c -HashAlgorithm SHA256 -ErrorAction Stop
    if ($s.Status -ne 'Valid') { throw ('DC06B05D1_SIGNING_NOT_VALID_'+$s.Status) }
}
function Test-Authenticode([string]$path) {
    $s=Get-AuthenticodeSignature -FilePath $path -ErrorAction Stop
    $expected=(Get-Content -LiteralPath $publisherPin -Raw).Trim()
    if ($expected -notmatch '^[0-9a-fA-F]{40}$') { throw 'DC06B05D1_INVALID_PUBLISHER_PIN' }
    return @{ Valid=($s.Status -eq 'Valid'); Pinned=($null -ne $s.SignerCertificate -and $s.SignerCertificate.Thumbprint -eq $expected) }
}
function Test-Seal([string]$path) {
    $null=@(& python -I $admission verify $path $pin 1)
    return ($LASTEXITCODE -eq 0)
}
function Assert-Package {
    $exe=Join-Path $target 'ScmPipeFixture.exe'
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw 'DC06B05D1_EXTRACTED_EXE_MISSING' }
    $a=Test-Authenticode $exe
    if (-not $a.Valid -or -not $a.Pinned -or -not (Test-Seal $target)) { throw 'DC06B05D1_AUTH_OR_CLOSED_MANIFEST_REJECTED' }
}
try {
    $rootStore.Open('ReadWrite')
    $rootOpen=$true
    & dotnet publish $project -c Release -r win-x64 --self-contained true '-p:PublishSingleFile=true' '-p:DebugType=None' '-p:DebugSymbols=false' -o $source
    if ($LASTEXITCODE -ne 0) { throw 'DC06B05D1_PUBLISH_FAILED' }
    $original=Join-Path $source 'ScmPipeFixture.exe'
    if (-not (Test-Path -LiteralPath $original -PathType Leaf)) { throw 'DC06B05D1_NATIVE_EXE_MISSING' }
    Copy-Item -LiteralPath $original -Destination $unsigned
    $pub=Make-TestCert 'publisher'
    Trust-TestCert $pub
    [IO.File]::WriteAllText($publisherPin,$pub.Thumbprint)
    Sign-Exe $original $pub
    Write-Output 'DC06B05D1_EPHEMERAL_AUTHENTICODE_VALID_PASS'
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'scm_spool_read_b03.py') -Destination (Join-Path $source 'scm_spool_read_b03.py')
    New-Item -ItemType Directory -Path (Join-Path $source 'tools') -Force | Out-Null
    Copy-Item -LiteralPath 'tools/imaging_gateway' -Destination (Join-Path $source 'tools/imaging_gateway') -Recurse
    & python -I $admission seal $source $pin
    if ($LASTEXITCODE -ne 0) { throw 'DC06B05D1_ED25519_SEAL_FAILED' }
    Compress-Archive -Path (Join-Path $source '*') -DestinationPath $zip -CompressionLevel Optimal -ErrorAction Stop
    Expand-Archive -LiteralPath $zip -DestinationPath $target -ErrorAction Stop
    Assert-Package
    Write-Output 'DC06B05D1_EXTRACTED_SIGNED_ZIP_AND_MANIFEST_PASS'
    $exe=Join-Path $target 'ScmPipeFixture.exe'
    # Alter a signed byte and demand real Authenticode verification failure.
    $h=[IO.File]::Open($exe,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    try { $first=$h.ReadByte(); if ($first -lt 0) { throw 'DC06B05D1_EMPTY_EXE' }; $null=$h.Seek(0,[IO.SeekOrigin]::Begin); $h.WriteByte([byte]($first -bxor 1)) }
    finally { $h.Dispose() }
    try {
        if ((Test-Authenticode $exe).Valid) { throw 'DC06B05D1_ALTERED_EXE_VALID' }
        if (Test-Seal $target) { throw 'DC06B05D1_ALTERED_EXE_MANIFEST_VALID' }
        Write-Output 'DC06B05D1_TAMPERED_EXE_WINDOWS_AND_MANIFEST_DENIED_PASS'
    } finally { Copy-Item -LiteralPath $original -Destination $exe -Force }
    Assert-Package
    # A different self-signed cert is also trusted by this test VM, but NOT pinned.
    $other=Make-TestCert 'foreign'
    Trust-TestCert $other
    Copy-Item -LiteralPath $unsigned -Destination $foreignExe
    Sign-Exe $foreignExe $other
    Copy-Item -LiteralPath $foreignExe -Destination $exe -Force
    try {
        $a=Test-Authenticode $exe
        if (-not $a.Valid -or $a.Pinned) { throw 'DC06B05D1_WRONG_SIGNER_TEST_INVALID' }
        if (Test-Seal $target) { throw 'DC06B05D1_FOREIGN_SIGNER_MANIFEST_VALID' }
        Write-Output 'DC06B05D1_TRUSTED_BUT_UNPINNED_PUBLISHER_DENIED_PASS'
    } finally { Copy-Item -LiteralPath $original -Destination $exe -Force }
    Assert-Package
    Copy-Item -LiteralPath $unsigned -Destination $exe -Force
    try {
        if ((Test-Authenticode $exe).Valid) { throw 'DC06B05D1_UNSIGNED_VALID' }
        if (Test-Seal $target) { throw 'DC06B05D1_UNSIGNED_MANIFEST_VALID' }
        Write-Output 'DC06B05D1_UNSIGNED_EXE_DENIED_PASS'
    } finally { Copy-Item -LiteralPath $original -Destination $exe -Force }
    Assert-Package
    $extra=Join-Path $target 'unsigned-extra.ps1'
    try {
        [IO.File]::WriteAllText($extra,'LAB only')
        if (Test-Seal $target) { throw 'DC06B05D1_EXTRA_FILE_ADMITTED' }
        Write-Output 'DC06B05D1_EXTRA_FILE_DENIED_BY_CLOSED_MANIFEST_PASS'
    } finally { Remove-Item -LiteralPath $extra -Force -ErrorAction SilentlyContinue }
    $helper=Join-Path $target 'scm_spool_read_b03.py'
    $helperSnapshot=[IO.File]::ReadAllBytes($helper)
    try {
        Remove-Item -LiteralPath $helper -Force
        if (Test-Seal $target) { throw 'DC06B05D1_MISSING_HELPER_ADMITTED' }
        Write-Output 'DC06B05D1_MISSING_HELPER_DENIED_BY_CLOSED_MANIFEST_PASS'
    } finally { [IO.File]::WriteAllBytes($helper,$helperSnapshot) }
    Assert-Package
    Write-Output 'DC06B05D1_RESTORED_EXTRACTED_PACKAGE_ADMITTED_PASS'
    Write-Output 'DC06B05D1_ONLY_SELF_SIGNED_EPHEMERAL_LAB_NOT_PRODUCTION_PASS'
}
finally {
    foreach ($cert in @($other,$pub)) {
        if ($null -eq $cert) { continue }
        if ($rootOpen) { $rootStore.Remove($cert) }
        Remove-Item -LiteralPath ('Cert:\CurrentUser\My\' + $cert.Thumbprint) -Force -ErrorAction SilentlyContinue
    }
    if ($rootOpen) { $rootStore.Close() }
    foreach ($entry in @($source,$target,$zip,$pin,$publisherPin,$unsigned,$foreignExe)) {
        if (Test-Path -LiteralPath $entry) { Remove-Item -LiteralPath $entry -Recurse -Force -ErrorAction Stop }
    }
    Write-Output 'DC06B05D1_DISPOSABLE_TEST_CERTS_AND_PACKAGE_DELETE_PASS'
}
