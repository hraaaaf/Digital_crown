# LOT05.7A-G — Windows-native negative FUE, no cert/issuer provisioning.
# This test NEVER signs, generates keys, installs or executes any EXE.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$verifier = Join-Path $PSScriptRoot '..\..\scripts\verify_lot05_windows_publisher_preflight.ps1'
$verifier = (Resolve-Path -LiteralPath $verifier).Path
$root = Join-Path $env:RUNNER_TEMP ("dc05g_" + [Guid]::NewGuid().ToString('N'))
$artifactDir = Join-Path $root 'artifacts'
$externalDir = Join-Path $root 'independent-provisioning-simulated'
New-Item -ItemType Directory -Path $artifactDir, $externalDir -Force | Out-Null

function ExpectDenied([string]$Case, [string]$Expected, [string]$Installer, [string]$App, [string]$PinPath) {
  $actual = ''
  try {
    & $verifier -InstallerPath $Installer -ApplicationPath $App -PublisherCertSha256PinFile $PinPath | Out-Null
    throw ('05G_FAIL_OPEN_' + $Case)
  } catch {
    $actual = $_.Exception.Message
  }
  if (-not $actual.Contains($Expected)) {
    throw ('05G_WRONG_DENIAL_' + $Case + ': ' + $actual)
  }
  Write-Output ('05G_DENIED_' + $Case)
}

try {
  $installer = Join-Path $artifactDir 'DigitalCrownSetup-INSTALLABLE-CERTIFIED.exe'
  $app = Join-Path $artifactDir 'DigitalCrown.exe'
  # Arbitrary bytes are NOT real signatures; this FUE is negative-only.
  [IO.File]::WriteAllBytes($installer, [byte[]](0x4d,0x5a,0x00,0x01,0x02))
  [IO.File]::WriteAllBytes($app, [byte[]](0x4d,0x5a,0x00,0x03,0x04))
  $pin = Join-Path $externalDir 'approved-publisher-cert-sha256.txt'
  [IO.File]::WriteAllText($pin, ('a' * 64), [Text.Encoding]::ASCII)

  ExpectDenied 'MISSING_EXTERNAL_PIN' '05G_PUBLISHER_DENIED_TRUST_PIN_MISSING' $installer $app (Join-Path $externalDir 'missing.txt')

  [IO.File]::WriteAllText($pin, 'ATTACKER-KEY', [Text.Encoding]::ASCII)
  ExpectDenied 'UNVERIFIED_PIN' '05G_PUBLISHER_DENIED_TRUST_PIN_INVALID' $installer $app $pin
  [IO.File]::WriteAllText($pin, ('a' * 64), [Text.Encoding]::ASCII)

  $localPin = Join-Path $artifactDir 'publisher-pin.txt'
  [IO.File]::WriteAllText($localPin, ('a' * 64), [Text.Encoding]::ASCII)
  ExpectDenied 'ARTIFACT_PROVIDED_PIN' '05G_PUBLISHER_DENIED_TRUST_PIN_WITHIN_ARTIFACT_DIRECTORY' $installer $app $localPin

  $nested = Join-Path $artifactDir 'attacker-nested-pin'
  New-Item -ItemType Directory -Path $nested -Force | Out-Null
  $nestedPin = Join-Path $nested 'publisher-pin.txt'
  [IO.File]::WriteAllText($nestedPin, ('a' * 64), [Text.Encoding]::ASCII)
  ExpectDenied 'NESTED_ARTIFACT_PIN' '05G_PUBLISHER_DENIED_TRUST_PIN_WITHIN_ARTIFACT_DIRECTORY' $installer $app $nestedPin

  ExpectDenied 'UNSIGNED_INSTALLER' '05G_PUBLISHER_DENIED_INSTALLER_AUTHENTICODE_NOT_VALID' $installer $app $pin

  $otherInstaller = Join-Path $artifactDir 'renamed-malicious-installer.exe'
  [IO.File]::Copy($installer, $otherInstaller)
  ExpectDenied 'WRONG_INSTALLER_NAME' '05G_PUBLISHER_DENIED_UNEXPECTED_INSTALLER_NAME' $otherInstaller $app $pin

  ExpectDenied 'MISSING_APP_BINARY' '05G_PUBLISHER_DENIED_APPLICATION_MISSING' $installer (Join-Path $artifactDir 'missing.exe') $pin

  ExpectDenied 'ONE_FILE_FOR_BOTH' '05G_PUBLISHER_DENIED_SAME_INSTALLER_APPLICATION' $installer $installer $pin

  # No-positive scenario: actual Digital Crown independently signed product
  # and out-of-band authorized publisher certificate have not been provided.
  Write-Output '05G_WINDOWS_NATIVE_UNSIGNED_AND_FAKE_PUBLISHER_REJECTIONS_CONFIRMED'
  Write-Output '05G_NO_CI_GENERATED_PUBLISHER_KEY_OR_SIGNED_PRODUCT_USED'
  Write-Output '05G_REAL_SIGNED_PRODUCT_AND_INDEPENDENT_ISSUER_REMAIN_NO_GO'
} finally {
  Remove-Item -LiteralPath $root -Force -Recurse -ErrorAction SilentlyContinue
  Write-Output '05G_EPHEMERAL_NEGATIVE_FUE_FILES_CLEANED'
}
