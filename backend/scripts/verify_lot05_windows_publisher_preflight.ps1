# LOT05.7A-G — Windows Authenticode product signer preflight, READ-ONLY.
#
# This gate does NOT sign, build, install, execute or authorize clinical import.
# It is usable only when a separately controlled publisher has supplied and
# authenticated the SHA256 DER fingerprint of the real signing certificate.
# A caller providing an arbitrary pin alongside the artifact is NOT an issuer.
# CODE_CERTIFIED / INSTALLABLE_CERTIFIED are independent mandatory gates.
#
# Run only on Windows. Both PE artifacts must have valid OS Authenticode trust,
# an embedded (not catalog) signature and the exact externally pinned signer.
# On success, a dedicated install/release review must still verify the signed
# source SHA, service identity, real installer behavior, and non-rollback witness.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$InstallerPath,
  [Parameter(Mandatory=$true)][string]$ApplicationPath,
  [Parameter(Mandatory=$true)][string]$PublisherCertSha256PinFile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Deny([string]$Reason) {
  throw ("05G_PUBLISHER_DENIED_" + $Reason)
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  Deny 'WINDOWS_REQUIRED'
}

function ResolveRegularFile([string]$Path, [string]$Label) {
  if (-not [IO.Path]::IsPathRooted($Path)) {
    Deny ("ABSOLUTE_" + $Label + "_PATH_REQUIRED")
  }
  try {
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  } catch {
    Deny ($Label + '_MISSING')
  }
  if ($item -isnot [System.IO.FileInfo]) {
    Deny ($Label + '_NOT_REGULAR_FILE')
  }
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Deny ($Label + '_REPARSE_POINT')
  }
  return $item.FullName
}

$installer = ResolveRegularFile $InstallerPath 'INSTALLER'
$app = ResolveRegularFile $ApplicationPath 'APPLICATION'
$pinPath = ResolveRegularFile $PublisherCertSha256PinFile 'TRUST_PIN'

if ([string]::Equals($installer, $app, [StringComparison]::OrdinalIgnoreCase)) {
  Deny 'SAME_INSTALLER_APPLICATION'
}
if ([IO.Path]::GetFileName($installer) -cne 'DigitalCrownSetup-INSTALLABLE-CERTIFIED.exe') {
  Deny 'UNEXPECTED_INSTALLER_NAME'
}
if ([IO.Path]::GetFileName($app) -cne 'DigitalCrown.exe') {
  Deny 'UNEXPECTED_APPLICATION_NAME'
}
foreach ($artifactDir in @([IO.Path]::GetDirectoryName($installer), [IO.Path]::GetDirectoryName($app))) {
  $artifactSubtree = $artifactDir.TrimEnd([char]'\') + [IO.Path]::DirectorySeparatorChar
  if ($pinPath.StartsWith($artifactSubtree, [StringComparison]::OrdinalIgnoreCase) -or
      [string]::Equals($pinPath, $artifactDir, [StringComparison]::OrdinalIgnoreCase)) {
    Deny 'TRUST_PIN_WITHIN_ARTIFACT_DIRECTORY'
  }
}

# The exact pin is provided by a separately controlled provisioning process.
# It is NOT inferred from the installer, repository, CI environment, or cert
# embedded in the executable. This preflight CANNOT attest that external origin.
try {
  $pin = ([IO.File]::ReadAllText($pinPath, [Text.Encoding]::ASCII)).Trim()
} catch {
  Deny 'TRUST_PIN_UNREADABLE'
}
if ($pin -cnotmatch '^[0-9a-fA-F]{64}$') {
  Deny 'TRUST_PIN_INVALID'
}
$pin = $pin.ToLowerInvariant()

function VerifyProductSignature([string]$Path, [string]$Label) {
  try {
    $signature = Get-AuthenticodeSignature -LiteralPath $Path -ErrorAction Stop
  } catch {
    Deny ($Label + '_AUTHENTICODE_UNAVAILABLE')
  }
  if ($null -eq $signature -or [string]$signature.Status -ne 'Valid') {
    Deny ($Label + '_AUTHENTICODE_NOT_VALID')
  }
  # A catalog trust result is not an embedded Digital Crown product signature.
  if ([string]$signature.SignatureType -ne 'Authenticode') {
    Deny ($Label + '_EMBEDDED_SIGNATURE_REQUIRED')
  }
  if ($null -eq $signature.SignerCertificate) {
    Deny ($Label + '_SIGNER_MISSING')
  }
  $sha256 = [System.Security.Cryptography.SHA256]::Create()
  try {
    $derDigest = ([BitConverter]::ToString(
      $sha256.ComputeHash($signature.SignerCertificate.RawData)
    )).Replace('-', '').ToLowerInvariant()
  } finally {
    $sha256.Dispose()
  }
  if (-not [string]::Equals($derDigest, $pin, [StringComparison]::Ordinal)) {
    Deny ($Label + '_PUBLISHER_PIN_MISMATCH')
  }
  try {
    $fileDigest = (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
  } catch {
    Deny ($Label + '_HASH_UNAVAILABLE')
  }
  return $fileDigest
}

$installerHash = VerifyProductSignature $installer 'INSTALLER'
$appHash = VerifyProductSignature $app 'APPLICATION'

# No automatic product admission, installation, publishing or clinical import.
Write-Output ("05G_SIGNATURE_PREFLIGHT_ONLY_INSTALLER_SHA256=" + $installerHash)
Write-Output ("05G_SIGNATURE_PREFLIGHT_ONLY_APPLICATION_SHA256=" + $appHash)
Write-Output '05G_BOTH_EMBEDDED_AUTHENTICODE_VALID_AND_EXTERNAL_CERT_PIN_MATCH'
Write-Output '05G_NOT_AN_ISSUER_ATTESTATION_NO_PRODUCT_OR_CLINICAL_IMPORT_GO'
