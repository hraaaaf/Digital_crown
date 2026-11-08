# LOT05.7C-H - official trial GUI launch observation, GitHub-hosted ephemeral Windows only.
# Requires a proven synthetic interactive desktop on the SAME runner.
# Does NOT click Install, configure MariaDB, launch Open Dental product, export CSV,
# or upload binary/window text/screenshot/patient data. Never run on a cabinet PC.
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -cne 'true' -or
    $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
    $env:RUNNER_OS -cne 'Windows' -or
    [string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) {
  throw 'GITHUB_HOSTED_WINDOWS_ONLY_NO_LOCAL_PC'
}

$trialUrl = 'https://www.opendental.com/TrialDownload-25-3-48.exe'
$expectedSha = 'b892db0d3b2fc0947fa25fe4fc07c2e81815d70119f72e7abf1f8b9b0671bcb9'
$reportFile = Join-Path $env:RUNNER_TEMP 'lot05-7c-h-official-vendor-gui-window-metadata-only.json'
$syntheticFile = Join-Path $env:RUNNER_TEMP 'lot05-7c-h-gui-capability-metadata-only.json'
$exe = Join-Path $env:RUNNER_TEMP 'LOT05_H_SIGNED_TRIAL_DO_NOT_INSTALL.exe'
$proc = $null
$knownIds = @()
$report = [ordered]@{
  evidence_kind = 'OFFICIAL_PINNED_TRIAL_FIRST_GUI_WINDOW_ONLY_NOT_INSTALL_NOT_EXPORT'
  trial_label = '25.3.48'
  trusted_hosted_runner = $true
  synthetic_gui_prerequisite_verified = $false
  official_binary_sha256_pinned = $false
  official_binary_authenticode_valid = $false
  official_binary_publisher_accepted = $false
  official_trial_launcher_started = $false
  official_trial_window_observed = $false
  official_trial_window_title_allowlisted = $false
  official_trial_installer_completed = $false
  database_installed = $false
  gui_product_launched = $false
  publisher_gui_csv_export_verified = $false
  vendor_format_compatible = $false
  mapping_human_approved = $false
  target_rows_written = 0
  import_permitted = $false
  status = 'NOT_PROVEN'
  failure_code = $null
}
try {
  $cap = Get-Content -LiteralPath $syntheticFile -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($cap.gui_capability -cne 'SYNTHETIC_WINFORMS_KEYBOARD_ROUNDTRIP_PROVEN' -or
      -not $cap.synthetic_textbox_keyboard_roundtrip) {
    throw 'SYNTHETIC_INTERACTIVE_GUI_GATE_NOT_MET'
  }
  $report.synthetic_gui_prerequisite_verified = $true

  # Exact publisher source, pinned size and SHA; no mirror, no silent flags.
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest -Uri $trialUrl -OutFile $exe -UseBasicParsing -MaximumRedirection 2 -TimeoutSec 240
  $size = (Get-Item -LiteralPath $exe).Length
  if ($size -ne 149781424) { throw 'SIGNED_TRIAL_SIZE_MISMATCH' }
  $digest = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($digest -cne $expectedSha) { throw 'SIGNED_TRIAL_SHA256_MISMATCH' }
  $report.official_binary_sha256_pinned = $true

  $signature = Get-AuthenticodeSignature -LiteralPath $exe
  if ($signature.Status -ne [System.Management.Automation.SignatureStatus]::Valid) {
    throw 'SIGNED_TRIAL_AUTHENTICODE_INVALID'
  }
  $report.official_binary_authenticode_valid = $true
  $subject = if ($null -ne $signature.SignerCertificate) {
    [string]$signature.SignerCertificate.Subject
  } else { '' }
  if ($subject -notmatch '(?i)Open\s*Dental') { throw 'SIGNED_TRIAL_PUBLISHER_UNEXPECTED' }
  $report.official_binary_publisher_accepted = $true

  # Start exactly the official signed trial launcher on the disposable runner.
  # Never elevate, bypass UAC/SmartScreen, pass install flags, or interact/click.
  $proc = Start-Process -FilePath $exe -PassThru -ErrorAction Stop
  $report.official_trial_launcher_started = $true
  $knownIds = @([int]$proc.Id)

  # Bootstrapper may spawn a child window; inspect ONLY its own process tree.
  # Window titles are assessed in memory against a fixed allowlist, never logged.
  for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    $all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    for ($depth = 0; $depth -lt 3; $depth++) {
      foreach ($candidate in $all) {
        if (($knownIds -contains [int]$candidate.ParentProcessId) -and
            -not ($knownIds -contains [int]$candidate.ProcessId)) {
          $knownIds += [int]$candidate.ProcessId
        }
      }
    }
    foreach ($processId in $knownIds) {
      $candidate = Get-Process -Id $processId -ErrorAction SilentlyContinue
      if ($null -eq $candidate) { continue }
      $candidate.Refresh()
      if ($candidate.MainWindowHandle -eq [IntPtr]::Zero) { continue }
      $report.official_trial_window_observed = $true
      $title = [string]$candidate.MainWindowTitle
      if ($title -match '(?i)(Open\s*Dental|OpenDental|Trial|Setup)') {
        $report.official_trial_window_title_allowlisted = $true
        break
      }
    }
    if ($report.official_trial_window_title_allowlisted) { break }
  }
  if ($report.official_trial_window_title_allowlisted) {
    $report.status = 'SIGNED_OFFICIAL_VENDOR_GUI_LAUNCHER_WINDOW_OBSERVED_ONLY'
  } else {
    $report.status = 'SIGNED_TRIAL_EXECUTED_BUT_GUI_WINDOW_NOT_PROVEN'
    $report.failure_code = 'VENDOR_GUI_WINDOW_NOT_PROVEN'
  }
} catch {
  # Fixed non-PHI error code. Never print exception text, title, user or path.
  $report.status = 'REFUSED_OR_NOT_PROVEN'
  $report.failure_code = 'VENDOR_WINDOW_OBSERVATION_REFUSED_OR_FAILED'
} finally {
  # Stop only the publisher process IDs started from this exact launch.
  foreach ($processId in @($knownIds | Select-Object -Unique)) {
    try {
      Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    } catch {}
  }
  try { Remove-Item -LiteralPath $exe -Force -ErrorAction SilentlyContinue } catch {}
  [System.IO.File]::WriteAllText(
    $reportFile, ($report | ConvertTo-Json -Depth 4),
    (New-Object System.Text.UTF8Encoding($false))
  )
}
Write-Host ('LOT05_H_SIGNED_VENDOR_WINDOW_PROBE=' + $report.status)
Write-Host 'LOT05_H_NO_INSTALL_NO_DATABASE_NO_CSV_NO_IMPORT'
# SUCCESS means bounded probe finished. Artifact JSON determines truth.
exit 0
