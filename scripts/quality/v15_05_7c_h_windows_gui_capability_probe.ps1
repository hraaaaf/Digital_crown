# LOT05.7C-H - Ephemeral GitHub-hosted Windows GUI-capability probe.
# This script NEVER downloads, launches, or installs Open Dental.
# It creates only a disposable WinForms textbox and synthetic Button.
# Tests SendMessageTimeout(BM_CLICK) on that own button, never vendor UI.
# The published JSON is metadata only; no screenshots, patient data, credentials, or window titles.
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$probeMarker = 'FUE05H'
$reportPath = $null
$form = $null

if ($env:GITHUB_ACTIONS -cne 'true' -or
    $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
    $env:RUNNER_OS -cne 'Windows' -or
    [string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) {
  throw 'GITHUB_HOSTED_WINDOWS_ONLY_NO_LOCAL_PC'
}

$reportPath = Join-Path $env:RUNNER_TEMP 'lot05-7c-h-gui-capability-metadata-only.json'
$report = [ordered]@{
  evidence_kind = 'GITHUB_HOSTED_WIN32_GUI_CAPABILITY_ONLY_NOT_VENDOR_EXPORT'
  probe_version = '1'
  attempted_vendor_install = $false
  attempted_vendor_export = $false
  source_is_synthetic = $true
  runner_os = 'Windows'
  runner_environment = 'github-hosted'
  gui_capability = 'NOT_PROVEN'
  apartment_state = $null
  process_session_id = $null
  user_interactive_hint = $false
  input_desktop_opened = $false
  synthetic_form_created = $false
  synthetic_form_foreground = $false
  synthetic_textbox_keyboard_roundtrip = $false
  synthetic_bm_click_candidate_created = $false
  synthetic_bm_click_requested = $false
  synthetic_bm_click_returned_nonzero = $false
  synthetic_bm_click_win32_last_error = $null
  synthetic_bm_click_message_result = $null
  synthetic_bm_click_handler_fired = $false
  synthetic_bm_click_proven = $false
  failure_code = $null
  publisher_gui_csv_export_verified = $false
  vendor_format_compatible = $false
  mapping_human_approved = $false
  import_permitted = $false
  target_rows_written = 0
}
try {
  $report.apartment_state = [string][System.Threading.Thread]::CurrentThread.GetApartmentState()
  $report.process_session_id = [int](Get-Process -Id $PID).SessionId
  $report.user_interactive_hint = [bool][Environment]::UserInteractive

  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Lot05Win32GuiProbe {
  [DllImport("user32.dll", SetLastError = true)]
  public static extern IntPtr OpenInputDesktop(uint flags, bool inherit, uint access);
  [DllImport("user32.dll", SetLastError = true)]
  public static extern bool CloseDesktop(IntPtr desktop);
  [DllImport("user32.dll", SetLastError = true)]
  public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", SetLastError = true)]
  private static extern IntPtr SendMessageTimeout(
    IntPtr hwnd, uint message, IntPtr wparam, IntPtr lparam,
    uint flags, uint timeoutMs, out IntPtr result);
  public static bool BMClickOwnSyntheticButton(
    IntPtr hwnd, out int lastError, out long messageResult) {
    IntPtr rawResult;
    IntPtr delivered = SendMessageTimeout(
      hwnd, 0x00F5, IntPtr.Zero, IntPtr.Zero, 2, 1500, out rawResult);
    lastError = Marshal.GetLastWin32Error();
    messageResult = rawResult.ToInt64();
    return delivered != IntPtr.Zero;
  }
}
'@

  $desktop = [Lot05Win32GuiProbe]::OpenInputDesktop([uint32]0, $false, [uint32]1)
  if ($desktop -ne [IntPtr]::Zero) {
    $report.input_desktop_opened = $true
    $null = [Lot05Win32GuiProbe]::CloseDesktop($desktop)
  }

  # A process can create an offscreen WinForms handle without access to an
  # interactive desktop. Require session > 0, user-interactive, input desktop,
  # foreground focus, AND actual keyboard input before declaring proof.
  if ($report.apartment_state -eq 'STA' -and
      $report.process_session_id -gt 0 -and
      $report.user_interactive_hint -and
      $report.input_desktop_opened) {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $form = New-Object System.Windows.Forms.Form
    $form.Text = 'LOT05H-SYNTHETIC-GUI-CAPABILITY'
    $form.Size = New-Object System.Drawing.Size(360, 145)
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
    $form.Location = New-Object System.Drawing.Point(20, 20)
    $form.ShowInTaskbar = $false
    $field = New-Object System.Windows.Forms.TextBox
    $field.Location = New-Object System.Drawing.Point(16, 15)
    $field.Width = 280
    $form.Controls.Add($field)
    $button = New-Object System.Windows.Forms.Button
    $button.Name = 'LOT05H_SYNTHETIC_ONLY_BUTTON'
    $button.Text = 'Synthetic Click'
    $button.Location = New-Object System.Drawing.Point(16, 50)
    $button.Size = New-Object System.Drawing.Size(145, 28)
    $button.Add_Click({ $report.synthetic_bm_click_handler_fired = $true })
    $form.Controls.Add($button)
    $form.Show()
    [System.Windows.Forms.Application]::DoEvents()
    $report.synthetic_form_created = [bool]$form.IsHandleCreated
    $null = $form.Activate()
    $null = $field.Focus()
    [System.Windows.Forms.Application]::DoEvents()

    $report.synthetic_form_foreground = (
      [Lot05Win32GuiProbe]::GetForegroundWindow() -eq $form.Handle
    )
    if ($report.synthetic_form_foreground -and $field.Focused) {
      [System.Windows.Forms.SendKeys]::SendWait($probeMarker)
      [System.Windows.Forms.Application]::DoEvents()
      $report.synthetic_textbox_keyboard_roundtrip = ($field.Text -ceq $probeMarker)
    }
    # EXACT same native Win32 message signature as the failed vendor experiment,
    # but addressed ONLY to a Button handle created by this script's own form.
    # No PIDs/HWNDs, widget text, coordinates or desktop screenshots are saved.
    if ($report.synthetic_textbox_keyboard_roundtrip -and
        $report.synthetic_form_foreground -and
        $button.IsHandleCreated -and
        $button.Enabled -and $button.Visible) {
      $report.synthetic_bm_click_candidate_created = $true
      $lastError = [int]0
      $messageResult = [long]0
      $report.synthetic_bm_click_requested = $true
      $report.synthetic_bm_click_returned_nonzero = [bool](
        [Lot05Win32GuiProbe]::BMClickOwnSyntheticButton(
          $button.Handle, [ref]$lastError, [ref]$messageResult
        )
      )
      [System.Windows.Forms.Application]::DoEvents()
      $report.synthetic_bm_click_win32_last_error = $lastError
      $report.synthetic_bm_click_message_result = $messageResult
      $report.synthetic_bm_click_proven = (
        $report.synthetic_bm_click_returned_nonzero -and
        $report.synthetic_bm_click_handler_fired
      )
    }
  }

  if ($report.synthetic_form_created -and
      $report.synthetic_form_foreground -and
      $report.synthetic_textbox_keyboard_roundtrip) {
    $report.gui_capability = 'SYNTHETIC_WINFORMS_KEYBOARD_ROUNDTRIP_PROVEN'
  } else {
    $report.gui_capability = 'NOT_PROVEN'
  }
} catch {
  # Never echo exception details, process lists, paths, window titles, or secrets.
  $report.failure_code = 'ISOLATED_GUI_CAPABILITY_CHECK_FAILED'
  $report.gui_capability = 'NOT_PROVEN'
} finally {
  if ($null -ne $form) {
    try { $form.Close(); $form.Dispose() } catch {}
  }
  [System.IO.File]::WriteAllText(
    $reportPath, ($report | ConvertTo-Json -Depth 4),
    (New-Object System.Text.UTF8Encoding($false))
  )
}
Write-Host ('LOT05_H_GUI_CAPABILITY_RESULT=' + $report.gui_capability)
Write-Host 'LOT05_H_NO_VENDOR_INSTALL_NO_GUI_EXPORT_NO_IMPORT'
# A successful CI only means that the capability assessment completed.
# The JSON, not the checkmark, decides whether UI automation is demonstrated.
exit 0
