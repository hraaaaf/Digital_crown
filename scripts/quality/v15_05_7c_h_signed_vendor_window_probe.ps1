# LOT05.7C-H - official trial GUI launch observation, GitHub-hosted ephemeral Windows only.
# Requires a proven synthetic interactive desktop on the SAME runner.
# Default is read-only. The optional bounded wizard switch can request one
# owner-authorized Install message; never accept EULA or complete a setup.
# Never run on a cabinet PC or access real patient data.
[CmdletBinding()]
param(
  [switch]$LaunchSetupWizardOnly,
  [switch]$ReadOnlyElevationProbe,
  [switch]$ReadOnlyButtonOwnershipProbe,
  [switch]$LaunchSetupWizardViaPhysicalInputOnly
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
  install_wizard_probe_requested = [bool]($LaunchSetupWizardOnly -or $LaunchSetupWizardViaPhysicalInputOnly)
  read_only_elevation_probe_requested = [bool]$ReadOnlyElevationProbe
  vendor_window_token_queryable = $false
  vendor_window_token_elevated = $null
  runner_token_queryable = $false
  runner_token_elevated = $null
  token_elevation_mismatch = $null
  read_only_button_ownership_probe_requested = [bool]$ReadOnlyButtonOwnershipProbe
  install_button_owner_queryable = $false
  install_button_same_process_as_vendor_window = $null
  install_button_same_thread_as_vendor_window = $null
  install_button_same_process_as_runner = $null
  install_button_native_class_verified = $false
  install_button_window_still_valid = $false
  install_button_parent_chain_contains_vendor_window = $false
  install_wizard_probe_guard_passed = $false
  install_button_invocation_attempted = $false
  install_button_message_delivered = $false
  physical_input_probe_requested = [bool]$LaunchSetupWizardViaPhysicalInputOnly
  physical_input_hit_target_verified = $false
  physical_input_events_accepted = 0
  physical_input_native_last_error = $null
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
  # READ ONLY: compare native Install child HWND owner PID/TID with the
  # allowlisted signed publisher window and current runner process.
  # Never upload numeric HWND, PID, TID, title, path or patient content.
  if ($ReadOnlyButtonOwnershipProbe -and
      $report.installer_win32_install_semantic_button_proven -and
      $report.installer_win32_install_candidate_count -eq 1 -and
      $installerHwnd -ne [IntPtr]::Zero -and
      $null -ne $installHwnd -and
      $installHwnd -ne [IntPtr]::Zero) {
    try {
      Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class Lot05ButtonOwnershipReadOnly {
  [DllImport("user32.dll", SetLastError=true)]
  public static extern uint GetWindowThreadProcessId(
    IntPtr hwnd, out uint processId);
  [DllImport("user32.dll")]
  public static extern bool IsWindow(IntPtr hwnd);
  [DllImport("user32.dll")]
  public static extern IntPtr GetParent(IntPtr hwnd);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)]
  public static extern int GetClassName(
    IntPtr hwnd, StringBuilder className, int capacity);
}
'@
      $report.install_button_window_still_valid = [bool](
        [Lot05ButtonOwnershipReadOnly]::IsWindow($installHwnd)
      )
      $vendorPid = [uint32]0
      $buttonPid = [uint32]0
      $vendorTid = [Lot05ButtonOwnershipReadOnly]::GetWindowThreadProcessId(
        $installerHwnd, [ref]$vendorPid
      )
      $buttonTid = [Lot05ButtonOwnershipReadOnly]::GetWindowThreadProcessId(
        $installHwnd, [ref]$buttonPid
      )
      if ($vendorTid -ne 0 -and $buttonTid -ne 0 -and
          $vendorPid -ne 0 -and $buttonPid -ne 0 -and
          $report.install_button_window_still_valid) {
        $report.install_button_owner_queryable = $true
        $report.install_button_same_process_as_vendor_window = (
          $buttonPid -eq $vendorPid
        )
        $report.install_button_same_thread_as_vendor_window = (
          $buttonTid -eq $vendorTid
        )
        $report.install_button_same_process_as_runner = (
          $buttonPid -eq [uint32]$PID
        )
        $classBuilder = New-Object System.Text.StringBuilder(128)
        $null = [Lot05ButtonOwnershipReadOnly]::GetClassName(
          $installHwnd, $classBuilder, $classBuilder.Capacity
        )
        $report.install_button_native_class_verified = (
          $classBuilder.ToString() -match
          '^(?i:Button|WindowsForms10\.BUTTON\..*)$'
        )
        $walk = $installHwnd
        for ($depth = 0; $depth -lt 12; $depth++) {
          $walk = [Lot05ButtonOwnershipReadOnly]::GetParent($walk)
          if ($walk -eq [IntPtr]::Zero) { break }
          if ($walk -eq $installerHwnd) {
            $report.install_button_parent_chain_contains_vendor_window = $true
            break
          }
        }
      }
    } catch {
      $report.install_button_owner_queryable = $false
    }
  }
  # READ-ONLY token elevation assessment: determine whether Windows blocked
  # cross-integrity GUI messages, without sending another BM_CLICK.
  # Never publish PIDs, usernames, token handles, paths or window contents.
  if ($ReadOnlyElevationProbe -and
      $report.official_trial_window_title_allowlisted -and
      $installerHwnd -ne [IntPtr]::Zero) {
    try {
      Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Lot05InstallerTokenReadOnly {
  [DllImport("user32.dll", SetLastError=true)]
  private static extern uint GetWindowThreadProcessId(
    IntPtr hwnd, out uint processId);
  [DllImport("kernel32.dll", SetLastError=true)]
  private static extern IntPtr OpenProcess(
    uint desiredAccess, bool inherit, uint processId);
  [DllImport("kernel32.dll", SetLastError=true)]
  private static extern IntPtr GetCurrentProcess();
  [DllImport("kernel32.dll")]
  private static extern bool CloseHandle(IntPtr handle);
  [DllImport("advapi32.dll", SetLastError=true)]
  private static extern bool OpenProcessToken(
    IntPtr process, uint access, out IntPtr token);
  [DllImport("advapi32.dll", SetLastError=true)]
  private static extern bool GetTokenInformation(
    IntPtr token, int infoClass, out int elevation,
    int bufferSize, out int resultSize);
  private static bool TryReadElevation(IntPtr process, out bool elevated) {
    elevated = false;
    IntPtr token = IntPtr.Zero;
    try {
      if (!OpenProcessToken(process, 0x0008, out token)) return false;
      int elevation = 0;
      int resultSize = 0;
      if (!GetTokenInformation(
          token, 20, out elevation, sizeof(int), out resultSize)) return false;
      elevated = (elevation != 0);
      return true;
    } finally {
      if (token != IntPtr.Zero) CloseHandle(token);
    }
  }
  public static bool TryCurrent(out bool elevated) {
    return TryReadElevation(GetCurrentProcess(), out elevated);
  }
  public static bool TryWindow(IntPtr hwnd, out bool elevated) {
    elevated = false;
    uint pid = 0;
    if (GetWindowThreadProcessId(hwnd, out pid) == 0 || pid == 0) {
      return false;
    }
    IntPtr process = OpenProcess(0x1000, false, pid);
    if (process == IntPtr.Zero) return false;
    try {
      return TryReadElevation(process, out elevated);
    } finally {
      CloseHandle(process);
    }
  }
}
'@
      $selfElevated = $false
      $vendorElevated = $false
      $report.runner_token_queryable = [bool](
        [Lot05InstallerTokenReadOnly]::TryCurrent([ref]$selfElevated)
      )
      $report.vendor_window_token_queryable = [bool](
        [Lot05InstallerTokenReadOnly]::TryWindow(
          $installerHwnd, [ref]$vendorElevated
        )
      )
      if ($report.runner_token_queryable) {
        $report.runner_token_elevated = [bool]$selfElevated
      }
      if ($report.vendor_window_token_queryable) {
        $report.vendor_window_token_elevated = [bool]$vendorElevated
      }
      if ($report.runner_token_queryable -and
          $report.vendor_window_token_queryable) {
        $report.token_elevation_mismatch = (
          $report.runner_token_elevated -ne
          $report.vendor_window_token_elevated
        )
      }
    } catch {
      # Unreadable token is a legitimate NOT_PROVEN outcome.
      $report.vendor_window_token_queryable = $false
      $report.token_elevation_mismatch = $null
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
  if ($LaunchSetupWizardOnly -or $LaunchSetupWizardViaPhysicalInputOnly) {
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
    if ($LaunchSetupWizardViaPhysicalInputOnly -and (
        -not $ReadOnlyButtonOwnershipProbe -or
        -not $report.install_button_owner_queryable -or
        -not $report.install_button_window_still_valid -or
        -not $report.install_button_native_class_verified -or
        -not $report.install_button_parent_chain_contains_vendor_window -or
        $report.install_button_same_process_as_vendor_window -ne $true -or
        $report.install_button_same_thread_as_vendor_window -ne $true -or
        $report.install_button_same_process_as_runner -ne $false)) {
      throw 'PHYSICAL_INPUT_OWNER_GUARD_NOT_PROVEN'
    }
    $report.install_wizard_probe_guard_passed = $true

    if ($LaunchSetupWizardViaPhysicalInputOnly) {
      # One owner-authorized, native mouse down/up at the exact child Button.
      # No UIA fallback, no WM_COMMAND or BM_CLICK, no alternate coordinates,
      # no key shortcuts, no permission escalation and NO SECOND ATTEMPT.
      if ([IntPtr]::Size -ne 8) { throw 'X64_WINDOWS_REQUIRED_NO_CLICK' }
      Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Lot05OneShotMouseInput {
  [StructLayout(LayoutKind.Sequential)]
  public struct Rect {
    public int Left, Top, Right, Bottom;
  }
  [StructLayout(LayoutKind.Sequential)]
  public struct Point {
    public int X, Y;
  }
  [StructLayout(LayoutKind.Sequential)]
  public struct MouseInput {
    public int dx, dy;
    public uint mouseData, dwFlags, time;
    public UIntPtr dwExtraInfo;
  }
  [StructLayout(LayoutKind.Explicit, Size=40)]
  public struct Input {
    [FieldOffset(0)] public uint type;
    [FieldOffset(8)] public MouseInput mouse;
  }
  [DllImport("user32.dll", SetLastError=true)]
  public static extern bool SetForegroundWindow(IntPtr hwnd);
  [DllImport("user32.dll")]
  public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", SetLastError=true)]
  public static extern bool GetWindowRect(IntPtr hwnd, out Rect rect);
  [DllImport("user32.dll", SetLastError=true)]
  public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")]
  public static extern IntPtr WindowFromPoint(Point point);
  [DllImport("user32.dll")]
  public static extern short GetAsyncKeyState(int vk);
  [DllImport("user32.dll", SetLastError=true)]
  private static extern uint SendInput(uint count, [In] Input[] input, int cbSize);
  public static uint ClickOnce() {
    Input down = new Input();
    down.type = 0;
    down.mouse.dwFlags = 0x0002;
    Input up = new Input();
    up.type = 0;
    up.mouse.dwFlags = 0x0004;
    return SendInput(2, new Input[] { down, up }, Marshal.SizeOf(typeof(Input)));
  }
}
'@
      $buttonBounds = New-Object Lot05OneShotMouseInput+Rect
      $vendorBounds = New-Object Lot05OneShotMouseInput+Rect
      if (-not [Lot05OneShotMouseInput]::GetWindowRect(
          $installHwnd, [ref]$buttonBounds) -or
          -not [Lot05OneShotMouseInput]::GetWindowRect(
          $installerHwnd, [ref]$vendorBounds)) {
        throw 'PHYSICAL_INPUT_BOUNDS_UNAVAILABLE_NO_CLICK'
      }
      $clickX = [int][Math]::Floor(
        ($buttonBounds.Left + $buttonBounds.Right) / 2)
      $clickY = [int][Math]::Floor(
        ($buttonBounds.Top + $buttonBounds.Bottom) / 2)
      if ($buttonBounds.Right -le $buttonBounds.Left -or
          $buttonBounds.Bottom -le $buttonBounds.Top -or
          $clickX -le $vendorBounds.Left -or
          $clickX -ge $vendorBounds.Right -or
          $clickY -le $vendorBounds.Top -or
          $clickY -ge $vendorBounds.Bottom) {
        throw 'PHYSICAL_INPUT_BAD_GEOMETRY_NO_CLICK'
      }
      $null = [Lot05OneShotMouseInput]::SetForegroundWindow($installerHwnd)
      Start-Sleep -Milliseconds 250
      if ([Lot05OneShotMouseInput]::GetForegroundWindow() -ne $installerHwnd) {
        throw 'PHYSICAL_INPUT_FOREGROUND_REFUSED_NO_CLICK'
      }
      if (([Lot05OneShotMouseInput]::GetAsyncKeyState(1) -band 0x8000) -ne 0) {
        throw 'PHYSICAL_INPUT_BUTTON_ALREADY_DOWN_NO_CLICK'
      }
      if (-not [Lot05OneShotMouseInput]::SetCursorPos($clickX, $clickY)) {
        throw 'PHYSICAL_INPUT_CURSOR_POSITION_REFUSED_NO_CLICK'
      }
      $point = New-Object Lot05OneShotMouseInput+Point
      $point.X = $clickX
      $point.Y = $clickY
      Start-Sleep -Milliseconds 100
      if ([Lot05OneShotMouseInput]::WindowFromPoint($point) -ne $installHwnd -or
          [Lot05OneShotMouseInput]::GetForegroundWindow() -ne $installerHwnd -or
          -not [Lot05ReadOnlyInstallerWin32]::IsWindowVisible($installHwnd) -or
          -not [Lot05ReadOnlyInstallerWin32]::IsWindowEnabled($installHwnd)) {
        throw 'PHYSICAL_INPUT_HIT_TEST_REFUSED_NO_CLICK'
      }
      $report.physical_input_hit_target_verified = $true
      $report.install_button_invocation_attempted = $true
      $report.physical_input_events_accepted = [int](
        [Lot05OneShotMouseInput]::ClickOnce()
      )
      $report.physical_input_native_last_error =
        [Runtime.InteropServices.Marshal]::GetLastWin32Error()
      if ($report.physical_input_events_accepted -ne 2) {
        throw 'PHYSICAL_INPUT_NOT_DELIVERED_NO_RETRY'
      }
    } else {
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
      -not $LaunchSetupWizardOnly -and
      -not $LaunchSetupWizardViaPhysicalInputOnly) {
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
