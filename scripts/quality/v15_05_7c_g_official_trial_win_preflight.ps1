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
  static_archive_listing_supported = $false
  static_archive_type = $null
  archive_entry_count = 0
  database_related_path_count = 0
  possible_demo_payload_filename_count = 0
  demo_patient_triplet_present = $false
  demo_patient_file_count = 0
  mariadb_msi_candidate_count = 0
  nested_archive_candidate_count = 0
  archive_extensions = [ordered]@{ sql = 0; zip = 0; msi = 0; cab = 0; exe = 0; db = 0; sqlite = 0; ibd = 0; frm = 0; myd = 0; myi = 0; dat = 0 }
  runner_session_id = $null
  runner_user_interactive_hint = $false
  interactive_desktop_proven = $false
  actual_demo_payload_validated = $false
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
  if ($report.installer_sha256 -cne 'b892db0d3b2fc0947fa25fe4fc07c2e81815d70119f72e7abf1f8b9b0671bcb9') {
    throw 'PINNED_OFFICIAL_INSTALLER_SHA256_CHANGED'
  }

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
  # Snapshot runner session capabilities; a hint is NOT an UI automation proof.
  $report.runner_session_id = [int](Get-Process -Id $PID).SessionId
  $report.runner_user_interactive_hint = [bool][Environment]::UserInteractive
  $report.interactive_desktop_proven = $false

  # Static archive metadata only. Do not extract or execute payloads and NEVER
  # publish internal entry names. We only publish non-sensitive aggregate counts.
  $sevenZip = Get-Command -Name '7z.exe' -ErrorAction SilentlyContinue
  if ($sevenZip -ne $null) {
    $listPath = Join-Path $EvidenceDir 'lot05-7c-g-internal-archive-listing-DELETE.txt'
    try {
      & $sevenZip.Source 'l' '-slt' '-bd' $dest > $listPath 2>&1
      if ($LASTEXITCODE -eq 0) {
        $report.static_archive_listing_supported = $true
        $demoParts = @{}
        foreach ($line in [System.IO.File]::ReadLines($listPath)) {
          if ($line -match '^Type = ([A-Za-z0-9_+.-]{1,40})$') {
            if ($null -eq $report.static_archive_type) {
              $report.static_archive_type = [string]$Matches[1]
            }
          }
          if ($line -match '^Path = (.+)$') {
            $entry = [string]$Matches[1]
            $report.archive_entry_count = [int]$report.archive_entry_count + 1
            $ext = [System.IO.Path]::GetExtension($entry).ToLowerInvariant().TrimStart('.')
            if ($report.archive_extensions.Contains($ext)) {
              $report.archive_extensions[$ext] = [int]$report.archive_extensions[$ext] + 1
            }
            if ($entry -match '(?i)(demo|database|mariadb|mysql|patient)') {
              $report.database_related_path_count = [int]$report.database_related_path_count + 1
            }
            if ($entry -match '(?i)(^|[\\/])demo[^\\/]*\.(sql|zip|db|sqlite|bak)$') {
              $report.possible_demo_payload_filename_count = [int]$report.possible_demo_payload_filename_count + 1
            }
            # Match only the official demo patient table's physical MyISAM triplet.
            # Paths remain transient; only booleans and counts leave the runner.
            $normalized = $entry.Replace('\','/')
            if ($normalized -match '(?i)(^|/)demo/patient\.(frm|myd|myi)
              $report.nested_archive_candidate_count = [int]$report.nested_archive_candidate_count + 1
            }
          }
        }
        $report.demo_patient_triplet_present = ($demoParts.ContainsKey('frm') -and $demoParts.ContainsKey('myd') -and $demoParts.ContainsKey('myi'))
      }
    } catch {
      $report.static_archive_listing_supported = $false
    } finally {
      Remove-Item -LiteralPath $listPath -Force -ErrorAction SilentlyContinue
    }
  }
  $report.installer_authenticated = $true
  $report.status = 'AUTHENTICATED_INSTALLER_ONLY_NOT_INSTALLED'
  Write-Host 'WIN_VM_OFFICIAL_TRIAL_INSTALLER_AUTHENTICATED_NO_EXECUTION'
} catch {
  # No raw exception contents or remote server responses: non-sensitive stable code only.
  $known = @('UNEXPECTED_INSTALLER_SIZE','INVALID_WINDOWS_PE_HEADER',
             'AUTHENTICODE_NOT_VALID','UNEXPECTED_WINDOWS_SIGNER',
             'PINNED_OFFICIAL_INSTALLER_SHA256_CHANGED')
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
) {
              $demoParts[$Matches[2].ToLowerInvariant()] = $true
              $report.demo_patient_file_count = [int]$report.demo_patient_file_count + 1
            }
            if ($ext -eq 'msi' -and $normalized -match '(?i)(maria|mysql)') {
              $report.mariadb_msi_candidate_count = [int]$report.mariadb_msi_candidate_count + 1
            }
            if ($ext -in @('zip','msi','cab','7z','exe')) {
              $report.nested_archive_candidate_count = [int]$report.nested_archive_candidate_count + 1
            }
          }
        }
      }
    } catch {
      $report.static_archive_listing_supported = $false
    } finally {
      Remove-Item -LiteralPath $listPath -Force -ErrorAction SilentlyContinue
    }
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
