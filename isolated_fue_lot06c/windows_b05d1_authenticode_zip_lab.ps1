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
$trustedThumbs=@()
function Make-TestCert([string]$role) {
    # Isolate Windows PKI work in a bounded background process so CI cannot
    # silently hang the entire 30-minute job on hosted certificate generation.
    $label='CN=DC06B05D-LAB-'+$role+'-'+$id
    Write-Host ('DC06B05D1_CERT_' + $role.ToUpperInvariant() + '_BEGIN')
    $job=Start-Job -ArgumentList $label -ScriptBlock {
        param([string]$subject)
        $cert=New-SelfSignedCertificate -Type CodeSigningCert -Subject $subject -CertStoreLocation 'Cert:\CurrentUser\My' -KeyAlgorithm RSA -KeyLength 2048 -HashAlgorithm SHA256 -KeyExportPolicy NonExportable -NotAfter (Get-Date).AddDays(1) -ErrorAction Stop
        $cert.Thumbprint
    } -ErrorAction Stop
    try {
        if ($null -eq (Wait-Job -Job $job -Timeout 75 -ErrorAction Stop)) {
            throw 'DC06B05D1_TEST_CERT_GENERATION_TIMEOUT'
        }
        if ($job.State -ne 'Completed') { throw 'DC06B05D1_TEST_CERT_GENERATION_FAILED' }
        $thumb=[string](Receive-Job -Job $job -ErrorAction Stop | Select-Object -Last 1)
        if ($thumb -notmatch '^[A-Fa-f0-9]{40}$') { throw 'DC06B05D1_TEST_CERT_THUMBPRINT_INVALID' }
        $saved=Get-Item -LiteralPath ('Cert:\CurrentUser\My\'+$thumb) -ErrorAction Stop
        if (-not $saved.HasPrivateKey) { throw 'DC06B05D1_TEST_CERT_PRIVATE_KEY_MISSING' }
        Write-Host ('DC06B05D1_CERT_' + $role.ToUpperInvariant() + '_CREATED_PASS')
        return $saved
    } finally {
        if ($job.State -eq 'Running') { Stop-Job -Job $job -ErrorAction SilentlyContinue }
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
}
function Invoke-BoundedCertutil([string[]]$arguments,[string]$failureTag) {
    # Disposable hosted Windows VM only. Never import a release trust root.
    $exe=Join-Path $env:SystemRoot 'System32/certutil.exe'
    $process=Start-Process -FilePath $exe -ArgumentList $arguments -NoNewWindow -PassThru -ErrorAction Stop
    try {
        if (-not $process.WaitForExit(45000)) {
            try { $process.Kill($true); $null=$process.WaitForExit(5000) } catch {}
            throw ($failureTag+'_TIMEOUT')
        }
        if ($process.ExitCode -ne 0) { throw ($failureTag+'_EXIT_'+$process.ExitCode) }
    } finally { $process.Dispose() }
}
function Trust-TestCert($c) {
    $thumb=[string]$c.Thumbprint
    if ($thumb -notmatch '^[A-Fa-f0-9]{40}$') { throw 'DC06B05D1_ROOT_THUMBPRINT_INVALID' }
    $certFile=Join-Path $env:RUNNER_TEMP ('DC06B05D1-public-'+$id+'-'+$thumb+'.cer')
    try {
        # Only public DER is exported; the test private key stays nonexportable.
        [IO.File]::WriteAllBytes($certFile,$c.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert))
        $script:trustedThumbs+= $thumb
        Write-Output 'DC06B05D1_BOUNDED_ROOT_IMPORT_ENTER'
        Invoke-BoundedCertutil @('-user','-f','-addstore','Root',('"'+$certFile+'"')) 'DC06B05D1_ROOT_IMPORT'
        if (-not (Test-Path -LiteralPath ('Cert:\CurrentUser\Root\'+$thumb) -PathType Leaf)) { throw 'DC06B05D1_ROOT_IMPORT_NOT_VISIBLE' }
        Write-Output 'DC06B05D1_BOUNDED_ROOT_IMPORT_VERIFIED_PASS'
    } finally {
        Remove-Item -LiteralPath $certFile -Force -ErrorAction SilentlyContinue
    }
}
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
    & dotnet publish $project -c Release -r win-x64 --self-contained true '-p:PublishSingleFile=true' '-p:DebugType=None' '-p:DebugSymbols=false' -o $source
    if ($LASTEXITCODE -ne 0) { throw 'DC06B05D1_PUBLISH_FAILED' }
    $original=Join-Path $source 'ScmPipeFixture.exe'
    if (-not (Test-Path -LiteralPath $original -PathType Leaf)) { throw 'DC06B05D1_NATIVE_EXE_MISSING' }
    Copy-Item -LiteralPath $original -Destination $unsigned
    Write-Output 'DC06B05D1_PUBLISHER_CERT_ENTER'
    $pub=Make-TestCert 'publisher'
    Write-Output 'DC06B05D1_PUBLISHER_TRUST_ENTER'
    Trust-TestCert $pub
    [IO.File]::WriteAllText($publisherPin,$pub.Thumbprint)
    Write-Output 'DC06B05D1_PUBLISHER_SIGN_ENTER'
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
    $cleanupErrors=@()
    foreach ($cert in @($other,$pub)) {
        if ($null -eq $cert) { continue }
        $thumb=[string]$cert.Thumbprint
        $rootPath='Cert:\CurrentUser\Root\'+$thumb
        if ($thumb -in $trustedThumbs -and (Test-Path -LiteralPath $rootPath)) {
            try {
                Invoke-BoundedCertutil @('-user','-delstore','Root',$thumb) 'DC06B05D1_ROOT_REMOVE'
                if (Test-Path -LiteralPath $rootPath) { throw 'DC06B05D1_ROOT_REMOVE_STILL_PRESENT' }
            } catch {
                $cleanupErrors+= 'DC06B05D1_ROOT_CLEANUP_FAILED'
            }
        }
        $myPath='Cert:\CurrentUser\My\'+$thumb
        try {
            if (Test-Path -LiteralPath $myPath) { Remove-Item -LiteralPath $myPath -Force -ErrorAction Stop }
            if (Test-Path -LiteralPath $myPath) { throw 'DC06B05D1_MY_CERT_REMAINS' }
        } catch {
            $cleanupErrors+= 'DC06B05D1_MY_CLEANUP_FAILED'
        }
    }
    foreach ($entry in @($source,$target,$zip,$pin,$publisherPin,$unsigned,$foreignExe)) {
        try {
            if (Test-Path -LiteralPath $entry) { Remove-Item -LiteralPath $entry -Recurse -Force -ErrorAction Stop }
        } catch {
            $cleanupErrors+= 'DC06B05D1_PACKAGE_CLEANUP_FAILED'
        }
    }
    if ($cleanupErrors.Count -gt 0) { throw ('DC06B05D1_TEARDOWN_FAILED_'+($cleanupErrors -join '_')) }
    Write-Output 'DC06B05D1_DISPOSABLE_TEST_CERTS_AND_PACKAGE_DELETE_PASS'
}
