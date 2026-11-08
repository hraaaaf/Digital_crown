# LOT05.7C-H - official trial GUI launch observation, GitHub-hosted ephemeral Windows only.
# Requires a proven synthetic interactive desktop on the SAME runner.
# Does NOT click Install, configure MariaDB, launch Open Dental product, export CSV,
# or upload binary/window text/screenshot/patient data. Never run on a cabinet PC.
[CmdletBinding()]
param(
  [switch]$LaunchSetupWizardOnly
)

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
  installer_uia_tree_accessible = $false
  installer_uia_element_count_bounded = 0
  installer_win32_install_candidate_count = 0
  installer_win32_install_visible = $false
  installer_win32_install_enabled = $false
  installer_win32_install_in_vendor_bounds = $false
  installer_win32_install_semantic_button_proven = $false
  install_wizard_probe_requested = [bool]$LaunchSetupWizardOnly
  install_wizard_probe_guard_passed = $false
  install_button_invocation_attempted = $false
  install_button_message_delivered = $false
  setup_wizard_new_window_observed = $false
  db_service_preexisting = $false
  db_service_created_observed = $false
  licence_or_eula_accepted = $false
  clicked_wizard_next = $false
  installer_win32_probe_completed = $false
  installer_uia_install_button_observed = $false
  installer_uia_new_server_option_observed = $false
  installer_uia_workstation_option_observed = $false
  installer_uia_license_button_observed = $false
  post_extraction_observation_cycles_budget = 0
  initial_installer_window_png_captured = $false
  initial_installer_window_png_dimensions = $null
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
  $installerHwnd = [IntPtr]::Zero

  # The publisher's first window is an extracting-progress screen (proved by
  # cropped screenshot artifact #13635604196). Do NOT treat it as an Install UI.
  # Observe the same publisher process tree for a bounded post-extraction window.
  # Never click, type, accept license, install or create a database.
  # Window titles remain in memory, never in metadata/logs.
  $report.post_extraction_observation_cycles_budget = 100
  for ($i = 0; $i -lt 100; $i++) {
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
        $installerHwnd = $candidate.MainWindowHandle
        break
      }
    }
    # Continue until the bounded observation expires. The earliest verified
    # window may still be self-extracting and expose only Pause/Cancel controls.
  }
  # Read-only UI Automation inventory from the verified vendor HWND.
  # No click, no title/text capture, no screenshots and no user data.
  if ($report.official_trial_window_title_allowlisted -and
      $installerHwnd -ne [IntPtr]::Zero) {
    try {
      Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
      Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop
      $uiRoot = [System.Windows.Automation.AutomationElement]::FromHandle($installerHwnd)
      if ($null -ne $uiRoot) {
        $report.installer_uia_tree_accessible = $true
        $elements = $uiRoot.FindAll(
          [System.Windows.Automation.TreeScope]::Descendants,
          [System.Windows.Automation.Condition]::TrueCondition
        )
        $limit = [Math]::Min([int]$elements.Count, 500)
        $report.installer_uia_element_count_bounded = $limit
        for ($idx = 0; $idx -lt $limit; $idx++) {
          $element = $elements.Item($idx)
          $label = [string]$element.Current.Name
          $kind = [string]$element.Current.ControlType.ProgrammaticName
          if ($kind -match '(?i)Button' -and $label -match '(?i)^Install$') {
            $report.installer_uia_install_button_observed = $true
          }
          if ($label -match '(?i)New\s+Server') {
            $report.installer_uia_new_server_option_observed = $true
          }
          if ($label -match '(?i)Workstation') {
            $report.installer_uia_workstation_option_observed = $true
          }
          if ($label -match '(?i)(View\s+Licen[cs]e|Licen[cs]e)') {
            $report.installer_uia_license_button_observed = $true
          }
        }
      }
    } catch {
      $report.installer_uia_tree_accessible = $false
    }
  }
  # Inspect Win32 child controls as an independent read-only oracle. The GUI
  # screenshot shows an Install button that was NOT recognized by UI Automation.
  # This code enumerates controls and compares ONLY an exact allowlisted label
  # in process memory; no button names, raw window text, coordinates or HWNDs
  # are uploaded. No click, WM_COMMAND, SendKeys, InvokePattern or elevation.
  if ($report.official_trial_window_title_allowlisted -and
      $installerHwnd -ne [IntPtr]::Zero) {
    try {
      Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class Lot05ReadOnlyInstallerWin32 {
  public delegate bool ChildProc(IntPtr hwnd, IntPtr data);
  [StructLayout(LayoutKind.Sequential)]
  public struct Rect {
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
  }
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern bool EnumChildWindows(IntPtr parent, ChildProc callback, IntPtr data);
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern int GetClassName(IntPtr hwnd, StringBuilder output, int capacity);
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern int GetWindowText(IntPtr hwnd, StringBuilder output, int capacity);
  [DllImport("user32.dll")]
  public static extern bool IsWindowVisible(IntPtr hwnd);
  [DllImport("user32.dll")]
  public static extern bool IsWindowEnabled(IntPtr hwnd);
  [DllImport("user32.dll")]
  public static extern bool GetWindowRect(IntPtr hwnd, out Rect rect);
}
'@
      $found = New-Object 'System.Collections.Generic.List[System.IntPtr]'
      $callback = [Lot05ReadOnlyInstallerWin32+ChildProc]{
        param([IntPtr]$child, [IntPtr]$unused)
        $klass = New-Object System.Text.StringBuilder(128)
        $null = [Lot05ReadOnlyInstallerWin32]::GetClassName(
          $child, $klass, $klass.Capacity
        )
        $klassName = $klass.ToString()
        if ($klassName -match '^(?i:Button|WindowsForms10\.BUTTON\..*)$') {
          $labelBuilder = New-Object System.Text.StringBuilder(128)
          $null = [Lot05ReadOnlyInstallerWin32]::GetWindowText(
            $child, $labelBuilder, $labelBuilder.Capacity
          )
          # Strict identity, allowing only a Windows accelerator marker (&).
          if ($labelBuilder.ToString() -cmatch '^\s*&?Install\s*$') {
            [void]$found.Add($child)
          }
        }
        return $true
      }
      $null = [Lot05ReadOnlyInstallerWin32]::EnumChildWindows(
        $installerHwnd, $callback, [IntPtr]::Zero
      )
      $report.installer_win32_probe_completed = $true
      $report.installer_win32_install_candidate_count = $found.Count
      if ($found.Count -eq 1) {
        $installHwnd = $found[0]
        $report.installer_win32_install_visible = [bool](
          [Lot05ReadOnlyInstallerWin32]::IsWindowVisible($installHwnd)
        )
        $report.installer_win32_install_enabled = [bool](
          [Lot05ReadOnlyInstallerWin32]::IsWindowEnabled($installHwnd)
        )
        $parentRect = New-Object Lot05ReadOnlyInstallerWin32+Rect
        $buttonRect = New-Object Lot05ReadOnlyInstallerWin32+Rect
        if ([Lot05ReadOnlyInstallerWin32]::GetWindowRect(
            $installerHwnd, [ref]$parentRect) -and
            [Lot05ReadOnlyInstallerWin32]::GetWindowRect(
            $installHwnd, [ref]$buttonRect)) {
          $parentWidth = $parentRect.Right - $parentRect.Left
          $parentHeight = $parentRect.Bottom - $parentRect.Top
          $buttonMidX = ($buttonRect.Left + $buttonRect.Right) / 2
          $buttonMidY = ($buttonRect.Top + $buttonRect.Bottom) / 2
          $report.installer_win32_install_in_vendor_bounds = (
            $parentWidth -ge 250 -and $parentHeight -ge 150 -and
            $buttonRect.Left -ge $parentRect.Left -and
            $buttonRect.Right -le $parentRect.Right -and
            $buttonRect.Top -ge $parentRect.Top -and
            $buttonRect.Bottom -le $parentRect.Bottom -and
            $buttonMidX -gt ($parentRect.Left + 0.65 * $parentWidth) -and
            $buttonMidY -gt ($parentRect.Top + 0.70 * $parentHeight)
          )
        }
        $report.installer_win32_install_semantic_button_proven = (
          $report.installer_win32_install_visible -and
          $report.installer_win32_install_enabled -and
          $report.installer_win32_install_in_vendor_bounds
        )
      }
    } catch {
      # No fallback to coordinate-based clicks; zero evidence means NO-GO.
      $report.installer_win32_probe_completed = $false
      $report.installer_win32_install_semantic_button_proven = $false
    }
  }
  # Screenshot ONLY the signed vendor launcher's first window, before any
  # Install click or database access. Never capture the desktop or patient UI.
  if ($report.official_trial_window_title_allowlisted -and
      $installerHwnd -ne [IntPtr]::Zero -and
      $report.official_binary_authenticode_valid -and
      -not $report.database_installed -and
      -not $report.gui_product_launched) {
    try {
      Add-Type -AssemblyName System.Drawing -ErrorAction Stop
      Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public struct Lot05InitialInstallerRect {
  public int Left;
  public int Top;
  public int Right;
  public int Bottom;
}
public static class Lot05InitialInstallerCapture {
  [DllImport("user32.dll", SetLastError = true)]
  public static extern bool GetWindowRect(IntPtr hwnd, out Lot05InitialInstallerRect bounds);
  [DllImport("user32.dll", SetLastError = true)]
  public static extern bool SetForegroundWindow(IntPtr hwnd);
  [DllImport("user32.dll", SetLastError = true)]
  public static extern IntPtr GetForegroundWindow();
}
'@
      $null = [Lot05InitialInstallerCapture]::SetForegroundWindow($installerHwnd)
      Start-Sleep -Milliseconds 350
      if ([Lot05InitialInstallerCapture]::GetForegroundWindow() -ne $installerHwnd) {
        throw 'SIGNED_INSTALLER_NOT_FOREGROUND'
      }
      $rectangle = New-Object Lot05InitialInstallerRect
      if (-not [Lot05InitialInstallerCapture]::GetWindowRect(
          $installerHwnd, [ref]$rectangle)) {
        throw 'SIGNED_INSTALLER_WINDOW_BOUNDS_UNAVAILABLE'
      }
      $width = [int]($rectangle.Right - $rectangle.Left)
      $height = [int]($rectangle.Bottom - $rectangle.Top)
      if ($width -lt 250 -or $height -lt 150 -or
          $width -gt 1500 -or $height -gt 1100) {
        throw 'SIGNED_INSTALLER_WINDOW_BOUNDS_REFUSED'
      }
      $bitmap = New-Object System.Drawing.Bitmap($width, $height)
      try {
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
          $graphics.CopyFromScreen(
            [int]$rectangle.Left, [int]$rectangle.Top, 0, 0,
            (New-Object System.Drawing.Size($width, $height)),
            [System.Drawing.CopyPixelOperation]::SourceCopy
          )
        } finally {
          $graphics.Dispose()
        }
        $screenshotPath = Join-Path $env:RUNNER_TEMP 'lot05-7c-h-OFFICIAL-INSTALLER-FIRST-WINDOW-NO-PATIENTS.png'
        $bitmap.Save($screenshotPath, [System.Drawing.Imaging.ImageFormat]::Png)
        if ((Get-Item -LiteralPath $screenshotPath).Length -gt 1024) {
          $report.initial_installer_window_png_captured = $true
          $report.initial_installer_window_png_dimensions = "$width" + 'x' + "$height"
        }
      } finally {
        $bitmap.Dispose()
      }
    } catch {
      # Evidence unavailable. Do not capture desktop or bypass focus/provenance.
      $report.initial_installer_window_png_captured = $false
    }
  }
  # Explicitly bounded owner-authorized synthetic/demo VM action.
  # The official trial instructions specify that Install FIRST opens the Setup
  # Wizard. This probe stops at that first screen, without any EULA acceptance,
  # wizard Next/Finish/confirmation, MariaDB configuration or patient access.
  if ($LaunchSetupWizardOnly) {
    if (-not $report.installer_win32_install_semantic_button_proven -or
        $report.installer_win32_install_candidate_count -ne 1 -or
        -not $report.installer_uia_new_server_option_observed -or
        -not $report.official_binary_authenticode_valid -or
        -not $report.synthetic_gui_prerequisite_verified -or
        $installerHwnd -eq [IntPtr]::Zero -or
        $null -eq $installHwnd -or
        $installHwnd -eq [IntPtr]::Zero) {
      throw 'INSTALL_WIZARD_PROBE_GUARDS_NOT_MET'
    }
    $existingDbService = @(
      Get-Service -Name 'MariaDB','MySQL*' -ErrorAction SilentlyContinue
    )
    if ($existingDbService.Count -gt 0) {
      $report.db_service_preexisting = $true
      throw 'ISOLATED_VM_REQUIRES_NO_DATABASE_SERVICE'
    }
    $report.install_wizard_probe_guard_passed = $true

    # BM_CLICK via bounded SendMessageTimeout: the exact identified native
    # Button child only. No simulated coordinates, keys, UIA fallback or UAC
    # circumvention. A failed delivery is a strict stop (no second attempt).
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Lot05WizardSingleClick {
  [DllImport("user32.dll", SetLastError=true)]
  public static extern IntPtr SendMessageTimeout(
    IntPtr hwnd, uint message, IntPtr wparam, IntPtr lparam,
    uint flags, uint timeoutMs, out IntPtr result);
  [DllImport("user32.dll", SetLastError=true)]
  public static extern bool SetForegroundWindow(IntPtr hwnd);
  [DllImport("user32.dll")]
  public static extern IntPtr GetForegroundWindow();
}
'@
    $null = [Lot05WizardSingleClick]::SetForegroundWindow($installerHwnd)
    Start-Sleep -Milliseconds 200
    if ([Lot05WizardSingleClick]::GetForegroundWindow() -ne $installerHwnd) {
      throw 'SIGNED_INSTALLER_NOT_FOREGROUND_NO_CLICK'
    }
    $output = [IntPtr]::Zero
    $report.install_button_invocation_attempted = $true
    $delivered = [Lot05WizardSingleClick]::SendMessageTimeout(
      $installHwnd, [uint32]0x00F5, [IntPtr]::Zero, [IntPtr]::Zero,
      [uint32]2, [uint32]1500, [ref]$output
    )
    $report.install_button_message_delivered = (
      $delivered -ne [IntPtr]::Zero
    )
    if (-not $report.install_button_message_delivered) {
      throw 'INSTALL_BUTTON_MESSAGE_TIMEOUT_NO_RETRY'
    }

    # After ONE click observe ONLY window existence in the launcher process
    # tree; never capture its content/titles or interact with the wizard.
    # A dialog could be EULA/UAC: presence is recorded but NOT accepted.
    for ($probeCycle = 0; $probeCycle -lt 25; $probeCycle++) {
      Start-Sleep -Seconds 1
      $allChildren = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
      for ($depth = 0; $depth -lt 3; $depth++) {
        foreach ($childProc in $allChildren) {
          if ($knownIds -contains [int]$childProc.ParentProcessId -and
              -not ($knownIds -contains [int]$childProc.ProcessId)) {
            $knownIds += [int]$childProc.ProcessId
          }
        }
      }
      foreach ($childId in $knownIds) {
        $childProcess = Get-Process -Id $childId -ErrorAction SilentlyContinue
        if ($null -ne $childProcess -and
            $childProcess.MainWindowHandle -ne [IntPtr]::Zero -and
            $childProcess.MainWindowHandle -ne $installerHwnd) {
          $report.setup_wizard_new_window_observed = $true
          break
        }
      }
      if ($report.setup_wizard_new_window_observed) { break }
    }
    $newDbService = @(
      Get-Service -Name 'MariaDB','MySQL*' -ErrorAction SilentlyContinue
    )
    $report.db_service_created_observed = ($newDbService.Count -gt 0)
    # No false claim of completed install, even if Win32 message delivered.
    $report.status = if ($report.setup_wizard_new_window_observed) {
      'FIRST_WIZARD_WINDOW_OBSERVED_NO_LICENSE_ACCEPTED_NO_IMPORT'
    } else {
      'INSTALL_BUTTON_MESSAGE_DELIVERED_WIZARD_NOT_PROVEN'
    }
  }
  if ($report.official_trial_window_title_allowlisted -and
      -not $LaunchSetupWizardOnly) {
    $report.status = 'SIGNED_OFFICIAL_VENDOR_GUI_LAUNCHER_WINDOW_OBSERVED_ONLY'
  } elseif (-not $report.official_trial_window_title_allowlisted) {
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
Write-Host 'LOT05_H_SINGLE_WIZARD_FIRST_SCREEN_ONLY_NO_EULA_ACCEPTANCE_NO_IMPORT'
# SUCCESS means bounded probe finished. Artifact JSON determines truth.
exit 0
