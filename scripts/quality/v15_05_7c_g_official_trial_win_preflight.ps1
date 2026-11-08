# LOT05.7C-G: GitHub-hosted Windows VM acquisition of OFFICIAL Open Dental trial.
# Supply-chain gate only: NEVER launch EXE, MariaDB, GUI, query, or clinical DB.
# Artifact is small JSON metadata; executable and any demo data remain on runner.
[CmdletBinding()]
param(
  [string]$InstallerUri = 'https://www.opendental.com/TrialDownload-25-3-48.exe',
  [string]$EvidenceDir = $env:RUNNER_TEMP
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
if ([string]::IsNullOrWhiteSpace($EvidenceDir)) { throw 'RUNNER_TEMP_REQUIRED' }
if ($InstallerUri -cne 'https://www.opendental.com/TrialDownload-25-3-48.exe') {
  throw 'OFFICIAL_INSTALLER_URL_PIN_REQUIRED'
}
$null = New-Item -ItemType Directory -Force -Path $EvidenceDir
$dest = Join-Path $EvidenceDir 'OpenDental_TrialDownload_25_3_48_executable_DO_NOT_RUN.exe'
$reportFile = Join-Path $EvidenceDir 'lot05-7c-g-official-installer-preflight.json'
$report = [ordered]@{
  evidence_kind = 'OPENDENTAL_OFFICIAL_TRIAL_WINDOWS_VM_SUPPLY_CHAIN_PREFLIGHT_ONLY'
  official_trial_url = $InstallerUri
  expected_trial_label = '25.3.48'
  runner_os = 'Windows'
  actual_installed_trial_version = $null
  installer_sha256 = $null
  installer_size_bytes = $null
  authenticode_status = 'NOT_CHECKED'
  signer_subject = $null
  pe_header_valid = $false
  file_version_declared_by_binary = $null
  installer_authenticated = $false
  installer_executed = $false
  demo_database_installed = $false
  demo_csv_export_produced = $false
  actual_demo_source_verified = $false
  source_provenance_verified = $false
  vendor_format_compatible = $false
  mapping_human_approved = $false
  target_rows_written = 0
  import_permitted = $false
  status = 'UNVERIFIED'
  failure_code = $null
  warnings = @(
    'TRIAL_DOWNLOAD_IS_NOT_DEMO_CSV_PROVENANCE',
    'NO_PUBLISHED_UNATTENDED_INSTALL_CONTRACT',
    'GITHUB_HOSTED_RUNNER_NO_INTERACTIVE_GUI_GUARANTEE',
    'NO_PATIENT_CONTENT_OR_INSTALLER_UPLOADED'
  )
}
try {
  # Never rely on a third-party mirror or execute a dynamically downloaded binary.
  Invoke-WebRequest -Uri $InstallerUri -OutFile $dest -UseBasicParsing -MaximumRedirection 3 -TimeoutSec 240
  $item = Get-Item -LiteralPath $dest
  if ($item.Length -lt 1000000 -or $item.Length -gt 400000000) {
    throw 'UNEXPECTED_INSTALLER_SIZE'
  }
  $report.installer_size_bytes = [int64]$item.Length
  $report.installer_sha256 = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLowerInvariant()

  $stream = [System.IO.File]::OpenRead($dest)
  try {
    $bytes = New-Object byte[] 2
    $read = $stream.Read($bytes, 0, 2)
    $report.pe_header_valid = ($read -eq 2 -and $bytes[0] -eq 77 -and $bytes[1] -eq 90)
  } finally { $stream.Dispose() }
  if (-not $report.pe_header_valid) { throw 'INVALID_WINDOWS_PE_HEADER' }

  $details = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($dest)
  $report.file_version_declared_by_binary = [string]$details.FileVersion

  $signature = Get-AuthenticodeSignature -LiteralPath $dest
  $report.authenticode_status = [string]$signature.Status
  if ($signature.SignerCertificate -ne $null) {
    $report.signer_subject = [string]$signature.SignerCertificate.Subject
  }
  if ($signature.Status -ne [System.Management.Automation.SignatureStatus]::Valid) {
    throw 'AUTHENTICODE_NOT_VALID'
  }
  if (-not $report.signer_subject -or $report.signer_subject -notmatch '(?i)Open\s*Dental') {
    throw 'UNEXPECTED_WINDOWS_SIGNER'
  }
  $report.installer_authenticated = $true
  $report.status = 'AUTHENTICATED_INSTALLER_ONLY_NOT_INSTALLED'
  Write-Host 'WIN_VM_OFFICIAL_TRIAL_INSTALLER_AUTHENTICATED_NO_EXECUTION'
} catch {
  # No raw exception contents or remote server responses: non-sensitive stable code only.
  $known = @('UNEXPECTED_INSTALLER_SIZE','INVALID_WINDOWS_PE_HEADER',
             'AUTHENTICODE_NOT_VALID','UNEXPECTED_WINDOWS_SIGNER')
  $code = [string]$_.Exception.Message
  if ($known -notcontains $code) { $code = 'OFFICIAL_TRIAL_DOWNLOAD_OR_INSPECTION_FAILED' }
  $report.status = 'REFUSED'
  $report.failure_code = $code
  Write-Host ('WIN_VM_TRIAL_PREFLIGHT_REFUSED: ' + $code)
} finally {
  $report | ConvertTo-Json -Depth 5 | Out-File -LiteralPath $reportFile -Encoding utf8
  # Only metadata JSON will be uploaded by workflow; scrub the executable.
  Remove-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue
}
if (-not $report.installer_authenticated) { exit 1 }
