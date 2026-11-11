# CEPH J1.B3 — Windows certified installer SOURCE and negative trust gate.
# SAFETY: Only read source files and create synthetic unsigned stubs under RUNNER_TEMP.
# NEVER build, sign, install, start, activate or migrate Digital Crown.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ExpectedSha)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($ExpectedSha -cnotmatch '^[0-9a-f]{40}$') {
  throw 'J1B3_EXACT_SHA_REQUIRED'
}
if (-not $env:RUNNER_TEMP) {
  throw 'J1B3_ISOLATED_WINDOWS_RUNNER_TEMP_REQUIRED'
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw 'J1B3_WINDOWS_REQUIRED'
}

$root = (git rev-parse --show-toplevel).Trim()
$head = (git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -cne $ExpectedSha) {
  throw 'J1B3_EXACT_HEAD_MISMATCH'
}
$branch = if ($env:GITHUB_HEAD_REF) { $env:GITHUB_HEAD_REF } else { (git branch --show-current).Trim() }

# Existing source preflight is ALWAYS NO_GO for a source/PR SHA.
# A source contract is never CODE/INSTALLABLE certification.
$preflight = Join-Path $root 'scripts/v15_08_2_b_desktop_installable_preflight.py'
$raw = & python $preflight --repo-root $root --expected-sha $ExpectedSha --json
if ($LASTEXITCODE -ne 0) {
  throw 'J1B3_SOURCE_PREFLIGHT_FAILED'
}
$sourceReport = ($raw | Out-String | ConvertFrom-Json -ErrorAction Stop)
if ($sourceReport.source_status -cne 'PRESENT' -or
    $sourceReport.verdict -cne 'SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO' -or
    $sourceReport.installable_ready -ne $false -or
    $sourceReport.clinical_go -ne $false -or
    $sourceReport.source_checks.Count -ne 10) {
  throw 'J1B3_SOURCE_PREFLIGHT_CONTRACT_NOT_PROVEN'
}

# Arbitrary EXE-shaped bytes + a synthetic pin are NEVER a valid publisher.
# The actual Windows Authenticode verifier must reject them before install.
$negativeDir = Join-Path $env:RUNNER_TEMP 'j1b3-unsigned-stub-test-only'
$pin = Join-Path $env:RUNNER_TEMP 'j1b3-FAKE-pin-test-only.txt'
$installer = Join-Path $negativeDir 'DigitalCrownSetup-INSTALLABLE-CERTIFIED.exe'
$application = Join-Path $negativeDir 'DigitalCrown.exe'
$denial = ''
try {
  New-Item -ItemType Directory -Path $negativeDir -Force | Out-Null
  [IO.File]::WriteAllBytes($installer, [byte[]](0x4d,0x5a,0x00,0x01,0x02))
  [IO.File]::WriteAllBytes($application, [byte[]](0x4d,0x5a,0x00,0x03,0x04))
  [IO.File]::WriteAllText($pin, ('0' * 64), [Text.Encoding]::ASCII)
  $verifier = Join-Path $root 'backend/scripts/verify_lot05_windows_publisher_preflight.ps1'
  $ErrorActionPreference = 'Continue'
  $denial = (& pwsh -NoProfile -NonInteractive -File $verifier -InstallerPath $installer -ApplicationPath $application -PublisherCertSha256PinFile $pin 2>&1 | Out-String)
  $refusalExit = $LASTEXITCODE
  $ErrorActionPreference = 'Stop'
  if ($refusalExit -eq 0) {
    throw 'J1B3_UNSIGNED_STUB_FALSIFIED_VALID_SIGNATURE'
  }
  if ($denial -notmatch '05G_PUBLISHER_DENIED_INSTALLER_(AUTHENTICODE_NOT_VALID|AUTHENTICODE_UNAVAILABLE)') {
    throw ('J1B3_WRONG_AUTHENTICODE_FAILURE_REASON: ' + $denial.Substring(0, [Math]::Min(400, $denial.Length)))
  }
} finally {
  $ErrorActionPreference = 'Continue'
  if (Test-Path -LiteralPath $negativeDir) {
    Remove-Item -LiteralPath $negativeDir -Recurse -Force
  }
  if (Test-Path -LiteralPath $pin) {
    Remove-Item -LiteralPath $pin -Force
  }
  $ErrorActionPreference = 'Stop'
}

# Honest evidence: no certified binary or trusted publisher certificate was
# provided for this DRAFT PR. No installer, GUI, screenshots or clinical restore.
$report = [ordered]@{
  marker = 'J1B3_WINDOWS_INSTALLABLE_SOURCE_ONLY_NEGATIVE_GATE_PASS'
  tested_head = $head
  branch = $branch
  platform = 'windows-2022'
  source_checks_present = $sourceReport.source_checks.Count
  source_preflight_verdict = $sourceReport.verdict
  unsigned_installer_authenticode = 'DENIED'
  synthetic_negative_fixture_removed = (-not (Test-Path -LiteralPath $negativeDir))
  exact_sha_code_certified_release = 'NOT_PROVIDED'
  matching_certified_runtime_assets = 'NOT_PROVIDED'
  externally_authenticated_publisher_pin = 'NOT_PROVIDED'
  installable_certified = 'NOT_VERIFIED'
  physical_installation = 'NOT_RUN'
  before_install_screenshot = 'NOT_RUN'
  after_install_screenshot = 'NOT_RUN'
  application_launch = 'NOT_RUN'
  backup_restore_installed_exe = 'NOT_RUN'
  production_patient_data_used = $false
  clinical_go = $false
  merge_authorized = $false
  deploy_performed = $false
  installable_ready = $false
  verdict = 'NO_INSTALLABLE_CERTIFIED_FOR_THIS_PR_TEST_STOP'
}
if ($report.synthetic_negative_fixture_removed -ne $true) {
  throw 'J1B3_TEMPORARY_NEGATIVE_FIXTURE_NOT_CLEANED'
}
$artifact = Join-Path $env:RUNNER_TEMP 'j1b3-installable-readiness.json'
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $artifact -Encoding utf8
Write-Output 'J1B3_WINDOWS_SOURCE_CONTRACT_10_OF_10_PASS'
Write-Output 'J1B3_UNSIGNED_AUTHENTICODE_FAIL_CLOSED_PASS'
Write-Output 'J1B3_NO_CERTIFIED_PACKAGE_NO_INSTALL_VERIFIED'
Write-Output ('J1B3_ARTIFACT=' + $artifact)
