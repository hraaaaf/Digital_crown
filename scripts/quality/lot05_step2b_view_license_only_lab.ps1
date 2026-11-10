# LOT05 Step2B — only a signed publisher "View License" action.
# Disposable GitHub-hosted Windows VM. NO Install / Next / Accept / DB / patients.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($env:GITHUB_ACTIONS -cne 'true' -or
    $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
    $env:RUNNER_OS -cne 'Windows' -or
    [string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) {
  throw 'HOSTED_WINDOWS_ONLY'
}

$exe = Join-Path $env:RUNNER_TEMP 'OD_LAB_VIEW_LICENSE_ONLY_DO_NOT_INSTALL.exe'
$reportPath = Join-Path $env:RUNNER_TEMP 'lot05-2b-view-license-metadata.json'
$screen = Join-Path $env:RUNNER_TEMP 'lot05-2b-view-license-window-only.png'
$proc = $null
$knownIds = @()
$report = [ordered]@{
  evidence_kind = 'OFFICIAL_SIGNED_VENDOR_VIEW_LICENSE_ONLY'
  os = 'Windows-hosted-ephemeral'
  source_version = '25.3.48'
  signed_binary_validated = $false
  trusted_publisher = $false
  vendor_launcher_started = $false
  launcher_window_verified = $false
  uia_tree_accessible = $false
  license_text_label_candidate_count = 0
  license_exact_button_candidate_count = 0
  license_control_same_vendor_process = $false
  license_invoke_pattern_supported = $false
  view_license_invoked_once = $false
  licensed_window_title_observed = $false
  license_window_printwindow_success = $false
  license_png_retained = $false
  window_only_dimensions = $null
  license_text_read = $false
  license_accepted = $false
  install_button_invoked = $false
  setup_wizard_next_invoked = $false
  database_service_present_before = $false
  database_service_created = $false
  product_installed = $false
  csv_exported = $false
  real_patient_data_accessed = $false
  target_rows_written = 0
  status = 'NOT_PROVEN'
  refusal_code = $null
}

try {
  $before = @(Get-Service -Name 'MariaDB','MySQL*' -ErrorAction SilentlyContinue)
  if ($before.Count -gt 0) {
    $report.database_service_present_before = $true
    throw 'EXISTING_DATABASE_SERVICE_NO_GO'
  }
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest -Uri 'https://www.opendental.com/TrialDownload-25-3-48.exe' -OutFile $exe -MaximumRedirection 2 -TimeoutSec 240 -UseBasicParsing
  if ((Get-Item -LiteralPath $exe).Length -ne 149781424) { throw 'OFFICIAL_TRIAL_SIZE_MISMATCH' }
  if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'b892db0d3b2fc0947fa25fe4fc07c2e81815d70119f72e7abf1f8b9b0671bcb9') {
    throw 'OFFICIAL_TRIAL_DIGEST_MISMATCH'
  }
  $sig = Get-AuthenticodeSignature -LiteralPath $exe
  if ($sig.Status -ne [System.Management.Automation.SignatureStatus]::Valid) { throw 'AUTHENTICODE_INVALID' }
  $report.signed_binary_validated = $true
  if ($null -eq $sig.SignerCertificate -or $sig.SignerCertificate.Subject -notmatch '(?i)Open\s*Dental') {
    throw 'PUBLISHER_UNEXPECTED'
  }
  $report.trusted_publisher = $true

  # Read-only Windows native API. EnumWindows only observes; PrintWindow captures
  # one verified vendor-owned HWND. No desktop capture and no credentials.
  Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class Lot05ViewLicenseWin32 {
  public delegate bool EnumWindowsCallback(IntPtr hwnd, IntPtr lparam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsCallback callback, IntPtr lparam);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hwnd, StringBuilder buffer, int max);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT rect);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdc, uint flags);
}
'@
  Add-Type -AssemblyName System.Drawing -ErrorAction Stop
  Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
  Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop

  $proc = Start-Process -FilePath $exe -PassThru -ErrorAction Stop
  $report.vendor_launcher_started = $true
  $knownIds = @([int]$proc.Id)
  $root = $null
  $control = $null
  $launcherHwnd = [IntPtr]::Zero

  for ($cycle=0; $cycle -lt 110; $cycle++) {
    Start-Sleep -Milliseconds 1100
    if (($cycle % 4) -eq 0) {
      $all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
      for ($depth=0; $depth -lt 3; $depth++) {
        foreach ($child in $all) {
          if (($knownIds -contains [int]$child.ParentProcessId) -and
              -not ($knownIds -contains [int]$child.ProcessId)) {
            $knownIds += [int]$child.ProcessId
          }
        }
      }
    }
    foreach ($pidValue in @($knownIds | Select-Object -Unique)) {
      $p = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
      if ($null -eq $p) { continue }
      $p.Refresh()
      $hwnd = $p.MainWindowHandle
      if ($hwnd -eq [IntPtr]::Zero) { continue }
      if ([string]$p.MainWindowTitle -notmatch '(?i)(Open\s*Dental|OpenDental|Trial|Setup)') { continue }
      try {
        $entry = [System.Windows.Automation.AutomationElement]::FromHandle($hwnd)
        if ($null -eq $entry) { continue }
        $report.launcher_window_verified = $true
        $report.uia_tree_accessible = $true
        $items = $entry.FindAll(
          [System.Windows.Automation.TreeScope]::Descendants,
          [System.Windows.Automation.Condition]::TrueCondition
        )
        $candidates = @()
        $textCount = 0
        $max = [Math]::Min(500,[int]$items.Count)
        for ($idx=0; $idx -lt $max; $idx++) {
          $it = $items.Item($idx)
          $name = [string]$it.Current.Name
          $type = [string]$it.Current.ControlType.ProgrammaticName
          if ($name -match '(?i)Licen[cs]e') { $textCount++ }
          if ($type -eq 'ControlType.Button' -and
              $name -match '(?i)^\s*&?(?:View\s+)?Licen[cs]e(?:s)?\s*$' -and
              $it.Current.IsEnabled -and -not $it.Current.IsOffscreen -and
              [int]$it.Current.ProcessId -eq [int]$pidValue) {
            $candidates += $it
          }
        }
        $report.license_text_label_candidate_count = $textCount
        $report.license_exact_button_candidate_count = $candidates.Count
        if ($candidates.Count -eq 1) {
          $control = $candidates[0]
          $root = $entry
          $launcherHwnd = $hwnd
          $report.license_control_same_vendor_process = $true
          break
        }
      } catch {
        # Vendor may close an extracting window mid-enumeration; try next cycle.
        $report.uia_tree_accessible = $false
      }
    }
    if ($null -ne $control) { break }
  }

  if ($null -eq $control) {
    $report.status = 'VIEW_LICENSE_EXACT_BUTTON_NOT_FOUND_NO_CLICK'
  } else {
    $invoke = $null
    $canInvoke = $control.TryGetCurrentPattern(
      [System.Windows.Automation.InvokePattern]::Pattern,
      [ref]$invoke
    )
    $report.license_invoke_pattern_supported = [bool]$canInvoke
    if (-not $canInvoke -or $null -eq $invoke) {
      $report.status = 'VIEW_LICENSE_BUTTON_HAS_NO_INVOKE_PATTERN_NO_CLICK'
    } else {
      # Only one semantically verified View License control. Never Install/Accept.
      $invoke.Invoke()
      $report.view_license_invoked_once = $true
      for ($i=0; $i -lt 45; $i++) {
        Start-Sleep -Milliseconds 1000
        $matched = New-Object 'System.Collections.Generic.List[System.IntPtr]'
        $callback = [Lot05ViewLicenseWin32+EnumWindowsCallback]{
          param([IntPtr]$wh, [IntPtr]$unused)
          if (-not [Lot05ViewLicenseWin32]::IsWindowVisible($wh)) { return $true }
          $winPid = [uint32]0
          $null = [Lot05ViewLicenseWin32]::GetWindowThreadProcessId($wh,[ref]$winPid)
          if ($knownIds -notcontains [int]$winPid) { return $true }
          $sb = New-Object System.Text.StringBuilder(256)
          $null = [Lot05ViewLicenseWin32]::GetWindowText($wh,$sb,$sb.Capacity)
          if ($sb.ToString() -match '(?i)(Licen[cs]e|Agreement|Terms|EULA)' -and
              $wh -ne $launcherHwnd) { [void]$matched.Add($wh) }
          return $true
        }
        $null = [Lot05ViewLicenseWin32]::EnumWindows($callback,[IntPtr]::Zero)
        if ($matched.Count -ne 1) { continue }
        $win = $matched[0]
        $report.licensed_window_title_observed = $true
        $r = New-Object Lot05ViewLicenseWin32+RECT
        if (-not [Lot05ViewLicenseWin32]::GetWindowRect($win,[ref]$r)) { break }
        $w = [int]($r.Right - $r.Left)
        $h = [int]($r.Bottom - $r.Top)
        if ($w -lt 250 -or $h -lt 150 -or $w -gt 1600 -or $h -gt 1100) { break }
        $bmp = New-Object System.Drawing.Bitmap($w,$h)
        try {
          $graphics = [System.Drawing.Graphics]::FromImage($bmp)
          try {
            $hdc = $graphics.GetHdc()
            try {
              $report.license_window_printwindow_success = [bool](
                [Lot05ViewLicenseWin32]::PrintWindow($win,$hdc,[uint32]0)
              )
            } finally { $graphics.ReleaseHdc($hdc) }
          } finally { $graphics.Dispose() }
          if ($report.license_window_printwindow_success) {
            $bmp.Save($screen,[System.Drawing.Imaging.ImageFormat]::Png)
            if ((Get-Item -LiteralPath $screen).Length -gt 2048 -and
                (Get-Item -LiteralPath $screen).Length -lt 6000000) {
              $report.license_png_retained = $true
              $report.window_only_dimensions = "$w" + "x" + "$h"
            }
          }
        } finally { $bmp.Dispose() }
        break
      }
      $report.status = if ($report.license_png_retained) {
        'SIGNED_VENDOR_LICENSE_WINDOW_CAPTURED_NOT_ACCEPTED'
      } elseif ($report.licensed_window_title_observed) {
        'LICENSE_WINDOW_TITLE_ONLY_NO_VERIFIED_CAPTURE'
      } else {
        'VIEW_LICENSE_INVOKED_BUT_LICENSE_WINDOW_NOT_VERIFIED'
      }
    }
  }
} catch {
  $report.status = 'SAFE_VIEW_LICENSE_PROBE_REFUSED_OR_FAILED'
  $report.refusal_code = 'VIEW_LICENSE_RUNTIME_FAILURE'
} finally {
  foreach ($pId in @($knownIds | Select-Object -Unique)) {
    try { Stop-Process -Id $pId -Force -ErrorAction SilentlyContinue } catch {}
  }
  Remove-Item -LiteralPath $exe -Force -ErrorAction SilentlyContinue
  $report.database_service_created = (@(Get-Service -Name 'MariaDB','MySQL*' -ErrorAction SilentlyContinue).Count -gt 0)
  [System.IO.File]::WriteAllText(
    $reportPath,
    ($report | ConvertTo-Json -Depth 4),
    (New-Object System.Text.UTF8Encoding($false))
  )
}
Write-Host ('LOT05_2B_VIEW_LICENSE_STATUS=' + $report.status)
Write-Host ('LOT05_2B_VIEW_LICENSE_CANDIDATES=' + $report.license_exact_button_candidate_count)
Write-Host ('LOT05_2B_VIEW_LICENSE_INVOCATION=' + $report.view_license_invoked_once)
Write-Host 'LOT05_2B_NO_INSTALL_NO_ACCEPTANCE_NO_PATIENTS_NO_IMPORT'
exit 0
