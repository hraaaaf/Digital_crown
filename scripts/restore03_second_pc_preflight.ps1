#Requires -Version 5.1
<#
RESTORE-03 / Windows B : NON-DESTRUCTIVE preflight only.
Never applies a restore, launches Digital Crown, reads active patient data,
decrypts the bundle or copies machine-bound secrets.
This cannot attest that a PC is physically distinct or that data is synthetic.
The operator must verify those facts off-line.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $BundlePath,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-fA-F0-9]{64}$')]
    [string] $ExpectedSha256,

    [Parameter(Mandatory = $true)]
    [switch] $SyntheticOnly,

    [string] $CabinetExecutablePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-Lab([bool] $Condition, [string] $Code) {
    if (-not $Condition) { throw "RESTORE03_PRECHECK_BLOCKED:$Code" }
}

# No side effects on the clinical installation are permitted.
Assert-Lab ($PSVersionTable.PSEdition -eq 'Desktop' -or $PSVersionTable.PSEdition -eq 'Core') 'UNSUPPORTED_SHELL'
Assert-Lab ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) 'WINDOWS_REQUIRED'
Assert-Lab ([bool]$SyntheticOnly.IsPresent) 'SYNTHETIC_ONLY_ACK_REQUIRED'
Assert-Lab (-not $env:DATABASE_URL) 'DATABASE_ENV_PRESENT'
Assert-Lab (-not $env:DIGITALCROWN_USER_DATA_DIR) 'CABINET_APPDATA_ENV_PRESENT'
Assert-Lab (-not $env:CABINET_MASTER_KEY_HEX) 'CABINET_MASTER_KEY_ENV_PRESENT'
Assert-Lab (-not $env:SQLCIPHER_KEY_HEX) 'SQLCIPHER_KEY_ENV_PRESENT'
Assert-Lab ($env:ENVIRONMENT -ne 'cabinet') 'LIVE_CABINET_RUNTIME_ENV_PRESENT'

# Read only the explicitly supplied bundle. Reject network paths and file links.
Assert-Lab ([IO.Path]::IsPathRooted($BundlePath)) 'ABSOLUTE_BUNDLE_PATH_REQUIRED'
$fullPath = [IO.Path]::GetFullPath($BundlePath)
Assert-Lab (-not $fullPath.StartsWith('\\')) 'NETWORK_BUNDLE_PATH_NOT_ALLOWED'
$file = Get-Item -LiteralPath $fullPath -ErrorAction Stop
Assert-Lab (-not $file.PSIsContainer) 'BUNDLE_NOT_FILE'
Assert-Lab (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'BUNDLE_REPARSE_POINT'
Assert-Lab ($file.Extension -eq '.dcbundle') 'PORTABLE_BUNDLE_REQUIRED'
Assert-Lab ($file.Length -gt 0) 'EMPTY_BUNDLE'
$drive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($fullPath))
Assert-Lab ($drive.DriveType -eq [IO.DriveType]::Fixed) 'LOCAL_FIXED_DRIVE_REQUIRED'

$actualSha = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToLowerInvariant()
Assert-Lab ($actualSha -eq $ExpectedSha256.ToLowerInvariant()) 'BUNDLE_SHA256_MISMATCH'

# Inspect only outer manifest metadata; do not open/decrypt the clinical payload.
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::OpenRead($fullPath)
try {
    $entries = @($zip.Entries)
    Assert-Lab ($entries.Count -eq 2) 'BUNDLE_ENTRY_COUNT'
    $names = @($entries | ForEach-Object { $_.FullName })
    Assert-Lab (($names -contains 'manifest.json') -and ($names -contains 'payload.enc')) 'BUNDLE_ENTRY_NAMES'
    $manifestEntry = $entries | Where-Object { $_.FullName -eq 'manifest.json' } | Select-Object -First 1
    $payloadEntry = $entries | Where-Object { $_.FullName -eq 'payload.enc' } | Select-Object -First 1
    Assert-Lab ($manifestEntry.Length -gt 0 -and $manifestEntry.Length -le 65536) 'MANIFEST_SIZE'
    Assert-Lab ($payloadEntry.Length -gt 0) 'PAYLOAD_EMPTY'
    $stream = $manifestEntry.Open()
    try {
        $reader = [IO.StreamReader]::new($stream, [Text.Encoding]::UTF8)
        try {
            $manifest = $reader.ReadToEnd() | ConvertFrom-Json
        } finally { $reader.Dispose() }
    } finally { $stream.Dispose() }
    Assert-Lab ($manifest.format -eq 'digital-crown-cabinet-bundle') 'BUNDLE_FORMAT'
    Assert-Lab ([int]$manifest.version -eq 1) 'BUNDLE_VERSION'
    Assert-Lab ($manifest.kdf.name -eq 'scrypt') 'KDF_FORMAT'
    Assert-Lab ($manifest.cipher.name -eq 'AES-256-GCM') 'CIPHER_FORMAT'
    $excluded = @($manifest.machine_bound_excluded)
    Assert-Lab (($excluded -contains 'backup.key') -and ($excluded -contains '.env') -and ($excluded -contains 'license_vault.bin')) 'MACHINE_SECRETS_EXCLUSION'
} finally { $zip.Dispose() }

$exeEvidence = @{ provided = $false; sha256 = $null; signature_status = 'NOT_CHECKED' }
if ($CabinetExecutablePath) {
    Assert-Lab ([IO.Path]::IsPathRooted($CabinetExecutablePath)) 'EXE_ABSOLUTE_PATH_REQUIRED'
    $exePath = [IO.Path]::GetFullPath($CabinetExecutablePath)
    Assert-Lab (-not $exePath.StartsWith('\\')) 'EXE_NETWORK_PATH_NOT_ALLOWED'
    $exeFile = Get-Item -LiteralPath $exePath -ErrorAction Stop
    Assert-Lab (-not $exeFile.PSIsContainer) 'EXE_NOT_FILE'
    Assert-Lab (($exeFile.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'EXE_REPARSE_POINT'
    Assert-Lab ($exeFile.Extension -eq '.exe') 'EXE_SUFFIX_REQUIRED'
    $exeEvidence = @{
        provided = $true
        sha256 = (Get-FileHash -LiteralPath $exePath -Algorithm SHA256).Hash.ToLowerInvariant()
        signature_status = (Get-AuthenticodeSignature -LiteralPath $exePath).Status.ToString()
    }
}

# The only filesystem mutation is a tiny evidence file in a new TEMP directory.
# No input is deleted or overwritten. Never write to application data directories.
$temporaryRoot = [IO.Path]::GetTempPath()
$tempDrive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($temporaryRoot))
Assert-Lab ($tempDrive.DriveType -eq [IO.DriveType]::Fixed) 'TEMP_NOT_LOCAL_FIXED_DRIVE'
$evidenceDirectory = Join-Path $temporaryRoot ('DigitalCrown-RESTORE03-B-PREFLIGHT-' + [Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($evidenceDirectory)

$evidence = [ordered]@{
    marker = 'RESTORE03_NONDESTRUCTIVE_PREFLIGHT_ONLY'
    verdict = 'PASS_FOR_MANIFEST_AND_LOCAL_READINESS_ONLY'
    created_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
    head_expected = 'OPERATOR_MUST_RECORD_EXACT_BUILD_HEAD'
    execution_context = $(if ($env:GITHUB_ACTIONS -eq 'true') { 'GITHUB_CI_RUNNER_NOT_PHYSICAL_PC_ATTESTATION' } else { 'LOCAL_WINDOWS_UNATTESTED' })
    windows_version = [Environment]::OSVersion.Version.ToString()
    os_architecture = [Environment]::GetEnvironmentVariable('PROCESSOR_ARCHITECTURE')
    bundle = [ordered]@{
        format = 'digital-crown-cabinet-bundle'
        version = 1
        sha256 = $actualSha
        source_os = $manifest.source.os
        encrypted = $true
        has_required_secret_exclusions = $true
    }
    executable = $exeEvidence
    independent_physical_pc_verified = $false
    packaged_app_guided_restore_apply = 'NOT_RUN'
    restore_db_media_oracle = 'NOT_RUN'
    forced_smoke_failure_rollback = 'NOT_RUN'
    license_rebind = 'NOT_RUN'
    nas_smb_real = 'NOT_RUN'
    clinical_go = $false
}
$proofPath = Join-Path $evidenceDirectory 'restore03-B-preflight-evidence.json'
$evidence | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $proofPath -Encoding UTF8 -NoNewline
Assert-Lab (Test-Path -LiteralPath $proofPath -PathType Leaf) 'EVIDENCE_NOT_WRITTEN'
Write-Output 'RESTORE03_B_PREFLIGHT_PASS_MANIFEST_ONLY'
Write-Output ('RESTORE03_B_EVIDENCE=' + $proofPath)
