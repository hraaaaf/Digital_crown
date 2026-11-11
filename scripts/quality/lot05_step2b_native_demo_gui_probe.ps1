# LOT05 2B — discover exact publisher app Choose Database after full server trial.
# Only disposable GitHub-hosted Windows + verified demo SQL metadata; no PHI.
$ErrorActionPreference='Stop'
$outFile=Join-Path $env:RUNNER_TEMP 'lot05_native_demo_gui_probe.json'
$png=Join-Path $env:RUNNER_TEMP 'lot05_native_demo_choose_database.png'
$appPng=Join-Path $env:RUNNER_TEMP 'lot05_native_demo_open_dental_window.png'
$r=[ordered]@{
  kind='LOT05_REPORTS_USER_QUERY_PERMISSION_AWARE_PROBE'
  report_route_enabled=$true
  reports_menu_attempted=$false
  reports_menu_invoked=$false
  reports_menu_cycle=-1
  reports_menu_candidate_count=0
  user_query_menu_candidate_count=0
  user_query_menu_clicked=$false
  user_query_menu_cycle=-1
  user_query_menu_hit_owned=$false
  user_query_native_window_observed=$false
  user_query_native_window_title='NOT_OBSERVED'
  user_query_native_window_owned=$false
  user_query_gui_controls=@()
  report_auth_denied_observed=$false
  report_probe_complete=$false
  report_probe_result='NOT_STARTED'
  exact_head=$env:LOT05_EXPECTED_SHA
  prereq_server_and_demo_verified=$false
  app_exe_hash_valid=$false
  app_exe_signature_valid=$false
  app_pid=-1
  session_verified=$false
  app_process_started=$false
  app_owned_window_titles=@()
  app_window_captured=$false
  app_window_title='NOT_OBSERVED'
  app_window_size=$null
  app_png_sha256=$null
  app_window_owner_pid_verified=$false
  app_window_last_cycle=-1
  file_menu_attempted=$false
  file_menu_invoked=$false
  file_menu_source='NOT_ATTEMPTED'
  file_menu_cycle=-1
  file_menu_item_candidates=0
  file_menu_known_labels=@()
  choose_database_menu_candidates=0
  choose_database_menu_item_observed=$false
  choose_database_named_element_count=0
  choose_database_menu_candidates_meta=@()
  menu_search_top_level_window_count=0
  menu_search_descendant_count=0
  menu_search_capped_count=0
  choose_database_menu_invoked=$false
  choose_database_menu_source='NOT_ATTEMPTED'
  choose_database_menu_cycle=-1
  choose_database_click_attempted=$false
  choose_database_click_owner_verified=$false
  choose_database_click_foreground_verified=$false
  choose_database_click_hit_verified=$false
  choose_database_invoke_error_type='NONE'
  choose_database_click_source='NOT_ATTEMPTED'
  post_click_owned_windows=@()
  post_click_named_controls=@()
  post_click_chooser_candidate_count=0
  observed_window_bounds=@()
  nested_chooser_window_observed=$false
  nested_chooser_candidate_count=0
  nested_chooser_bounds='NOT_OBSERVED'
  nested_chooser_hwnd_present=$false
  nested_chooser_captured_from='NONE'
  nested_chooser_password_edits_redacted=0
  nested_chooser_demo_selection_observed=$false
  nested_chooser_unauthorized_notice_observed=$false
  demo_connect_attempted=$false
  demo_connect_ok_candidates=0
  demo_connect_ok_visual_label_count=0
  demo_connect_visual_ok_guard=$false
  demo_connect_ok_click_source='NONE'
  demo_connect_button_evidence=@()
  demo_connect_demo_combo_count=0
  demo_connect_server_combo_count=0
  demo_connect_form_authorization_blocked=$false
  demo_connect_pinned_screenshot=$false
  demo_connect_ok_pid_and_geometry=$false
  demo_connect_ok_foreground_verified=$false
  demo_connect_ok_hittest_verified=$false
  demo_connect_hit_dialog_verified=$false
  demo_connect_foreground_dialog_verified=$false
  demo_connect_post_error_categories=@()
  demo_connect_post_dialog_still_present=0
  demo_connect_click_sent=$false
  demo_connect_click_cycle=-1
  demo_connect_dialog_closed_observed=$false
  demo_connect_post_checked=$false
  demo_connect_post_dialog_names=@()
  chooser_window_captured=$false
  chooser_window_title='NOT_OBSERVED'
  chooser_window_size=$null
  chooser_png_sha256=$null
  chooser_owner_pid_verified=$false
  chooser_safe_controls=@()
  chooser_edit_count=0
  chooser_combobox_count=0
  chooser_button_count=0
  observed_cycles=0
  uia_errors=0
  accessed_patient_data=$false
  modified_database=$false
  exported_csv=$false
  error_code=$null
}
$ids=New-Object 'System.Collections.Generic.HashSet[int]'
try{
  $server=Join-Path $env:RUNNER_TEMP 'lot05_server_fullchain_evidence.json'
  if(-not(Test-Path -LiteralPath $server)){throw 'SERVER_PROOF_FILE_MISSING'}
  $proof=Get-Content -LiteralPath $server -Raw | ConvertFrom-Json
  if($proof.sha -cne $env:LOT05_EXPECTED_SHA -or
     -not $proof.demo_schema_verified -or -not $proof.mariadb_service_running -or
     $proof.patient_data_accessed -or $null -ne $proof.error_code){
    throw 'EXACT_HEAD_SQL_DEMO_PROOF_REQUIRED'
  }
  if(@(Get-Service -Name 'MySQL','MariaDB' -ErrorAction SilentlyContinue |
       Where-Object {$_.Status -eq 'Running'}).Count -ne 1){throw 'MYSQL_SERVICE_NOT_RUNNING'}
  $r.prereq_server_and_demo_verified=$true
  $exe='C:\Program Files (x86)\Open Dental\OpenDental.exe'
  if(-not(Test-Path -LiteralPath $exe)){throw 'SIGNED_APP_NOT_INSTALLED'}
  $r.app_exe_hash_valid=((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ceq
                        '8e78c110e28c3052e0e83c07bf129449c2c6803a246c06aca8c75c907fe71007')
  $r.app_exe_signature_valid=((Get-AuthenticodeSignature -LiteralPath $exe).Status -eq
                                [System.Management.Automation.SignatureStatus]::Valid)
  if(-not $r.app_exe_hash_valid -or -not $r.app_exe_signature_valid){throw 'APP_BINARY_MISMATCH'}
  Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
  Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop
  Add-Type -AssemblyName System.Drawing -ErrorAction Stop
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Lot05DemoGuiWindow {
  [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left,Top,Right,Bottom; }
  [StructLayout(LayoutKind.Sequential)] public struct Point { public int X,Y; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out Rect r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h,IntPtr dc,uint flags);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
  [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(Point p);
  [DllImport("user32.dll")] public static extern bool IsChild(IntPtr hWndParent,IntPtr hWnd);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint pid);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint dx,uint dy,uint data,UIntPtr extra);
}
'@ -ErrorAction Stop
  $proc=Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe) -PassThru -ErrorAction Stop
  $r.app_process_started=$true
  $r.app_pid=[int]$proc.Id
  $null=$ids.Add([int]$proc.Id)
  $r.session_verified=($proc.SessionId -eq [System.Diagnostics.Process]::GetCurrentProcess().SessionId)
  if(-not $r.session_verified){throw 'NONINTERACTIVE_APP_SESSION'}
  for($cycle=0;$cycle -lt 115;$cycle++){
    Start-Sleep -Milliseconds 1100
    $r.observed_cycles=$cycle+1
    $all=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    for($depth=0;$depth -lt 2;$depth++){
      foreach($child in $all){if($ids.Contains([int]$child.ParentProcessId)){$null=$ids.Add([int]$child.ProcessId)}}
    }
    $windows=[System.Windows.Automation.AutomationElement]::RootElement.FindAll(
      [System.Windows.Automation.TreeScope]::Children,
      [System.Windows.Automation.Condition]::TrueCondition)
    for($i=0;$i -lt [Math]::Min($windows.Count,110);$i++){
      try{
        $w=$windows.Item($i)
        $pidHere=[int]$w.Current.ProcessId
        if(-not $ids.Contains($pidHere)){continue}
        $title=[string]$w.Current.Name
        if($title -match '(?i)(Choose Database|Open.?Dental|MySQL|Trial)' -and
           $r.app_owned_window_titles -notcontains $title -and
           $r.app_owned_window_titles.Count -lt 15){
          $r.app_owned_window_titles+=,$title.Substring(0,[Math]::Min(90,$title.Length))
        }
        # Actual evidence from the previous exact-HEAD run shows 'Open Dental',
        # NOT 'Choose Database'. Capture that real official window without clicking.
        # Also continue observing for an exact Choose Database child/dialog title.
        # Observe all signed-app-owned top-level windows after the verified
        # menu click; no input or screenshots of unknown titles.
        if($r.choose_database_menu_invoked -and $r.post_click_owned_windows.Count -lt 20){
          $windowDesc=("$title"+"|"+[string]$w.Current.ControlType.ProgrammaticName+
            "|"+[int]$w.Current.NativeWindowHandle)
          if($r.post_click_owned_windows -notcontains $windowDesc){
            $r.post_click_owned_windows+=,$windowDesc
          }
          try{
            $desc=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
              [System.Windows.Automation.Condition]::TrueCondition)
            for($z=0;$z -lt [Math]::Min($desc.Count,200);$z++){
              $el=$desc.Item($z)
              if([int]$el.Current.ProcessId -ne $pidHere){continue}
              $name=[string]$el.Current.Name
              $typ=[string]$el.Current.ControlType.ProgrammaticName
              if($name -match '(?i)(database|server|connect|mysql|demo)' -and
                 $r.post_click_named_controls.Count -lt 30){
                $entry=("$name"+"|"+$typ)
                if($r.post_click_named_controls -notcontains $entry){
                  $r.post_click_named_controls+=,$entry
                }
              }
            }
          }catch{$r.uia_errors++}
        }
        # Vendor Choose Database is an UIA Child Window inside the signed
        # top-level Open Dental main window, not an independent root window.
        # Discover only exact named child windows after a verified menu click.
        if($title -ceq 'Open Dental' -and $r.choose_database_menu_invoked -and
           -not $r.chooser_window_captured){
          try{
            $children=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
              [System.Windows.Automation.Condition]::TrueCondition)
            $nested=New-Object 'System.Collections.Generic.List[System.Windows.Automation.AutomationElement]'
            for($j=0;$j -lt [Math]::Min(500,$children.Count);$j++){
              $el=$children.Item($j)
              if([int]$el.Current.ProcessId -ne $pidHere){continue}
              $name=[string]$el.Current.Name
              $type=[string]$el.Current.ControlType.ProgrammaticName
              if($name -ceq 'Choose Database' -and $type -ceq 'ControlType.Window'){
                $nested.Add($el)
              }
              if($name -match '(?i)Not authorized for' -and
                 $name -match '(?i)Choose Database'){
                $r.nested_chooser_unauthorized_notice_observed=$true
              }
            }
            $r.nested_chooser_candidate_count=$nested.Count
            if($nested.Count -eq 1){
              $child=$nested[0]
              $b=$child.Current.BoundingRectangle
              $cw=[int]$b.Width;$ch=[int]$b.Height
              $x=[int]$b.X;$y=[int]$b.Y
              $r.nested_chooser_window_observed=$true
              $r.chooser_window_title=[string]$child.Current.Name
              $r.chooser_owner_pid_verified=([int]$child.Current.ProcessId -eq $pidHere)
              $r.nested_chooser_bounds=("$x,$y,$cw,$ch")
              $childHwnd=[IntPtr]([int]$child.Current.NativeWindowHandle)
              $r.nested_chooser_hwnd_present=($childHwnd -ne [IntPtr]::Zero)
              $winPid=[uint32]0
              $handleOwned=$false
              if($r.nested_chooser_hwnd_present){
                $null=[Lot05DemoGuiWindow]::GetWindowThreadProcessId($childHwnd,[ref]$winPid)
                $handleOwned=([int]$winPid -eq $pidHere)
              }
              if($r.chooser_owner_pid_verified -and $r.nested_chooser_hwnd_present -and
                 $handleOwned -and $cw -ge 600 -and $cw -le 900 -and
                 $ch -ge 550 -and $ch -le 850){
                # PrintWindow only for the verified owned native dialog HWND.
                # No full-screen image, never screenshots of other windows.
                $bmp=New-Object System.Drawing.Bitmap($cw,$ch)
                try{
                  $gfx=[System.Drawing.Graphics]::FromImage($bmp)
                  try{
                    $dc=$gfx.GetHdc()
                    try{$printed=[Lot05DemoGuiWindow]::PrintWindow($childHwnd,$dc,[uint32]0)}
                    finally{$gfx.ReleaseHdc($dc)}
                  }finally{$gfx.Dispose()}
                  if($printed){
                    # Redact all Edit controls, not just the password, to avoid
                    # exporting any database credentials in PNG artifacts.
                    $edits=$child.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                      [System.Windows.Automation.Condition]::TrueCondition)
                    $gfx=[System.Drawing.Graphics]::FromImage($bmp)
                    try{
                      for($e=0;$e -lt [Math]::Min(240,$edits.Count);$e++){
                        $edit=$edits.Item($e)
                        if([string]$edit.Current.ControlType.ProgrammaticName -ne 'ControlType.Edit'){continue}
                        $br=$edit.Current.BoundingRectangle
                        $xx=[Math]::Max(0,[int]($br.X-$x))
                        $yy=[Math]::Max(0,[int]($br.Y-$y))
                        $ww=[Math]::Min($cw-$xx,[int]$br.Width)
                        $hh=[Math]::Min($ch-$yy,[int]$br.Height)
                        if($ww -gt 0 -and $hh -gt 0){
                          $gfx.FillRectangle([System.Drawing.Brushes]::Black,$xx,$yy,$ww,$hh)
                          $r.nested_chooser_password_edits_redacted++
                        }
                      }
                    }finally{$gfx.Dispose()}
                    $bmp.Save($png,[System.Drawing.Imaging.ImageFormat]::Png)
                    $sz=(Get-Item -LiteralPath $png).Length
                    if($sz -gt 2200 -and $sz -le 6000000){
                      $r.chooser_window_captured=$true
                      $r.chooser_png_sha256=(Get-FileHash -LiteralPath $png -Algorithm SHA256).Hash.ToLowerInvariant()
                      $r.chooser_window_size=("$cw"+"x"+"$ch")
                      $r.nested_chooser_captured_from='OWNED_CHILD_HWND_PRINTWINDOW_WITH_EDIT_REDACTION'
                    }
                  }
                }finally{$bmp.Dispose()}
              }
              # Read only non-sensitive control names/types. Never extract
              # credentials or invoke connection/DB modification controls.
              $sub=$child.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                [System.Windows.Automation.Condition]::TrueCondition)
              for($z=0;$z -lt [Math]::Min(250,$sub.Count);$z++){
                $el=$sub.Item($z)
                if([int]$el.Current.ProcessId -ne $pidHere){continue}
                $ct=[string]$el.Current.ControlType.ProgrammaticName
                $nm=[string]$el.Current.Name
                if($ct -eq 'ControlType.Edit'){$r.chooser_edit_count++}
                if($ct -eq 'ControlType.ComboBox'){$r.chooser_combobox_count++}
                if($ct -eq 'ControlType.Button'){$r.chooser_button_count++}
                if($ct -eq 'ControlType.ComboBox' -and $nm -ceq 'demo'){
                  $r.nested_chooser_demo_selection_observed=$true
                }
                if($nm -match '^(Server|Database|MySQL User|MySQL Password|OK|Cancel|Refresh|Choose Database)$' -and
                   $r.chooser_safe_controls -notcontains $nm){
                  $r.chooser_safe_controls+=,$nm
                }
              }
              # STEP 3B: confirm the already selected local-only demo DB.
              # The native chooser was captured at an identical SHA on the
              # prior green exact-HEAD run, and demo is the only permitted DB.
              if($r.chooser_window_captured -and -not $r.demo_connect_attempted){
                $r.demo_connect_attempted=$true
                $r.demo_connect_pinned_screenshot=(
                  $r.chooser_png_sha256 -ceq '4bfb92b908e789b2ba3f27b201e3588d3f4a827bb8f16e4b9207221b8bac05f4')
                # UIA Server ComboBox exposes its descriptive label, not its
                # text value. The exact pinned PNG proves its value localhost.
                $selectDemo=0;$selectLocal=0
                $buttons=New-Object 'System.Collections.Generic.List[System.Windows.Automation.AutomationElement]'
                $okEnabledLabels=0
                for($m=0;$m -lt [Math]::Min(250,$sub.Count);$m++){
                  $ctl=$sub.Item($m)
                  if([int]$ctl.Current.ProcessId -ne $pidHere){continue}
                  $n=[string]$ctl.Current.Name
                  $t=[string]$ctl.Current.ControlType.ProgrammaticName
                  if($n -ceq 'OK' -and $ctl.Current.IsEnabled){$okEnabledLabels++}
                  if($t -eq 'ControlType.ComboBox' -and $n -ceq 'demo'){$selectDemo++}
                  if($t -eq 'ControlType.ComboBox' -and $n -match '^Server Name:'){$selectLocal++}
                  if($t -eq 'ControlType.Button'){
                    $cb=$ctl.Current.BoundingRectangle
                    if($r.demo_connect_button_evidence.Count -lt 8){
                      # Log only button metadata; never input fields/passwords.
                      $r.demo_connect_button_evidence+=,@{
                        name=$n
                        enabled=[bool]$ctl.Current.IsEnabled
                        same_owner=([int]$ctl.Current.ProcessId -eq $pidHere)
                        bounds=("$([int]$cb.X),$([int]$cb.Y),$([int]$cb.Width),$([int]$cb.Height)")
                      }
                    }
                    if($n -ceq 'OK' -and $ctl.Current.IsEnabled){$buttons.Add($ctl)}
                  }
                }
                $r.demo_connect_ok_candidates=$buttons.Count
                $r.demo_connect_ok_visual_label_count=$okEnabledLabels
                $r.demo_connect_demo_combo_count=$selectDemo
                $r.demo_connect_server_combo_count=$selectLocal
                $r.demo_connect_form_authorization_blocked=$r.nested_chooser_unauthorized_notice_observed
                # This vendor dialog renders a real native OK button visually
                # but exposes it as a non-Button UIA control. The pinned exact
                # screenshot SHA and dimensions are required before a single
                # pixel coordinate derived from that screenshot can be clicked.
                $r.demo_connect_visual_ok_guard=(
                  $r.demo_connect_pinned_screenshot -and
                  $r.nested_chooser_demo_selection_observed -and
                  $selectDemo -eq 1 -and $selectLocal -eq 1 -and
                  # The pinned native PNG proves one visibly enabled OK.
                  # UIA exposes this vendor-painted button only as a plain
                  # name (not a Button, or enabled named UIA element).
                  # Require exact visual SHA, fixed dialog geometry, no
                  # competing native Button and same signed process.
                  $buttons.Count -eq 0 -and
                  $r.chooser_owner_pid_verified -and $handleOwned -and
                  $r.nested_chooser_bounds -ceq '142,26,739,676' -and
                  $r.chooser_window_size -ceq '739x676' -and
                  $r.chooser_safe_controls -contains 'OK')
                if($r.demo_connect_pinned_screenshot -and
                   $r.nested_chooser_demo_selection_observed -and
                   $selectDemo -eq 1 -and $selectLocal -eq 1 -and
                   $r.chooser_owner_pid_verified -and $handleOwned -and
                   ($buttons.Count -eq 1 -or $r.demo_connect_visual_ok_guard)){
                  if($buttons.Count -eq 1){
                    $btn=$buttons[0]
                    $bo=$btn.Current.BoundingRectangle
                    $bx=[int][Math]::Floor($bo.X+$bo.Width/2)
                    $by=[int][Math]::Floor($bo.Y+$bo.Height/2)
                    $r.demo_connect_ok_pid_and_geometry=(
                      [int]$btn.Current.ProcessId -eq $pidHere -and
                      $bo.Width -ge 45 -and $bo.Width -le 115 -and
                      $bo.Height -ge 18 -and $bo.Height -le 42 -and
                      $bx -ge ($x+$cw-150) -and $bx -le ($x+$cw) -and
                      $by -ge ($y+$ch-90) -and $by -le ($y+$ch))
                    $r.demo_connect_ok_click_source='UNIQUE_ENABLED_UIA_BUTTON'
                  }elseif($r.demo_connect_visual_ok_guard){
                    # OK center is (681,644) RELATIVE to the 739x676
                    # pinned visual dialog; no arbitrary or reused desktop
                    # coordinates. A live WindowFromPoint owner guard follows.
                    $bx=[int]($x+681)
                    $by=[int]($y+644)
                    $r.demo_connect_ok_pid_and_geometry=(
                      $bx -ge ($x+$cw-150) -and $bx -lt ($x+$cw) -and
                      $by -ge ($y+$ch-90) -and $by -lt ($y+$ch))
                    $r.demo_connect_ok_click_source='PINNED_SHA_DIALOG_OK_PID_FOREGROUND_HITTEST'
                  }
                  if($r.demo_connect_ok_pid_and_geometry){
                    # Same signed PID also owns the main window; PID-only
                    # hit-testing cannot prove the modal dialog received OK.
                    # Focus the verified dialog HWND and click only its own
                    # window or a descendant HWND. One click, fail closed.
                    $mainHwnd=[IntPtr]([int]$w.Current.NativeWindowHandle)
                    $mainPid=[uint32]0
                    if($mainHwnd -eq [IntPtr]::Zero){throw 'NATIVE_DEMO_MAIN_HWND_MISSING'}
                    $null=[Lot05DemoGuiWindow]::GetWindowThreadProcessId($mainHwnd,[ref]$mainPid)
                    if([int]$mainPid -ne $pidHere -or -not $handleOwned -or
                       $childHwnd -eq [IntPtr]::Zero){throw 'NATIVE_DEMO_DIALOG_FOCUS_DENIED'}
                    $null=[Lot05DemoGuiWindow]::SetForegroundWindow($childHwnd)
                    Start-Sleep -Milliseconds 180
                    $foreground=[Lot05DemoGuiWindow]::GetForegroundWindow()
                    $fgPid=[uint32]0
                    if($foreground -ne [IntPtr]::Zero){
                      $null=[Lot05DemoGuiWindow]::GetWindowThreadProcessId($foreground,[ref]$fgPid)
                    }
                    $r.demo_connect_ok_foreground_verified=([int]$fgPid -eq $pidHere)
                    $r.demo_connect_foreground_dialog_verified=(
                      $foreground -eq $childHwnd -or
                      [Lot05DemoGuiWindow]::IsChild($foreground,$childHwnd) -or
                      [Lot05DemoGuiWindow]::IsChild($childHwnd,$foreground))
                    $pt=New-Object Lot05DemoGuiWindow+Point
                    $pt.X=$bx;$pt.Y=$by
                    if($r.demo_connect_ok_foreground_verified -and
                       $r.demo_connect_foreground_dialog_verified -and
                       [Lot05DemoGuiWindow]::SetCursorPos($bx,$by)){
                      Start-Sleep -Milliseconds 90
                      $hit=[Lot05DemoGuiWindow]::WindowFromPoint($pt)
                      $hitPid=[uint32]0
                      if($hit -ne [IntPtr]::Zero){
                        $null=[Lot05DemoGuiWindow]::GetWindowThreadProcessId($hit,[ref]$hitPid)
                      }
                      $r.demo_connect_ok_hittest_verified=([int]$hitPid -eq $pidHere)
                      $r.demo_connect_hit_dialog_verified=(
                        $hit -eq $childHwnd -or
                        [Lot05DemoGuiWindow]::IsChild($childHwnd,$hit))
                      if($r.demo_connect_ok_hittest_verified -and
                         $r.demo_connect_hit_dialog_verified){
                        [Lot05DemoGuiWindow]::mouse_event([uint32]2,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                        Start-Sleep -Milliseconds 90
                        [Lot05DemoGuiWindow]::mouse_event([uint32]4,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                        $r.demo_connect_click_sent=$true
                        $r.demo_connect_click_cycle=$cycle
                      }
                    }
                  }
                }
              }
            }
          }catch{$r.uia_errors++}
        }
        if($title -ceq 'Open Dental' -and $r.demo_connect_click_sent -and
           $cycle -gt $r.demo_connect_click_cycle -and
           -not $r.demo_connect_post_checked){
          try{
            $subNow=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
              [System.Windows.Automation.Condition]::TrueCondition)
            $foundChooser=0
            for($u=0;$u -lt [Math]::Min(500,$subNow.Count);$u++){
              $el=$subNow.Item($u)
              if([int]$el.Current.ProcessId -ne $pidHere){continue}
              $nm=[string]$el.Current.Name
              $ct=[string]$el.Current.ControlType.ProgrammaticName
              if($nm -ceq 'Choose Database' -and $ct -ceq 'ControlType.Window'){$foundChooser++}
              # Only fixed categories, never arbitrary UI labels (PHI risk).
              if($nm -match '(?i)not authorized|not authorised|permission denied' -and
                 $r.demo_connect_post_error_categories -notcontains 'PERMISSION_DENIED'){
                $r.demo_connect_post_error_categories+=,'PERMISSION_DENIED'
              }
              if($nm -match '(?i)unable to connect|cannot connect|connection failed|connect to database failed' -and
                 $r.demo_connect_post_error_categories -notcontains 'DB_CONNECTION_ERROR'){
                $r.demo_connect_post_error_categories+=,'DB_CONNECTION_ERROR'
              }
              if($nm -match '(?i)access denied for user|incorrect password|invalid password' -and
                 $r.demo_connect_post_error_categories -notcontains 'DB_AUTH_ERROR'){
                $r.demo_connect_post_error_categories+=,'DB_AUTH_ERROR'
              }
              if($ct -ceq 'ControlType.Window' -and
                 $r.demo_connect_post_dialog_names.Count -lt 10 -and
                 $r.demo_connect_post_dialog_names -notcontains $nm){
                $r.demo_connect_post_dialog_names+=,$nm
              }
            }
            $r.demo_connect_dialog_closed_observed=($foundChooser -eq 0)
            $r.demo_connect_post_dialog_still_present=$foundChooser
            if($r.demo_connect_dialog_closed_observed -or
               $cycle -ge $r.demo_connect_click_cycle+15){$r.demo_connect_post_checked=$true}
          }catch{$r.uia_errors++}
        }
        # PATH B: avoid File > Choose Database entirely after the
        # application's explicit "Not authorized" response. Use only the
        # independently permission-checked Reports > User Query menu. No
        # patients, credentials, SQL, database edits, or exports in this probe.
        if($r.report_route_enabled -and $r.report_route_started -and
           $title -match '^(User Query|User Query - .+)$' -and
           $ids.Contains($pidHere)){
          $r.user_query_native_window_observed=$true
          $r.user_query_native_window_title='User Query'
          $r.user_query_native_window_owned=$true
          $r.report_probe_result='AUTHORIZED_USER_QUERY_WINDOW'
          $r.report_probe_complete=$true
        }
        $isChooser=($title -ceq 'Choose Database')
        $isApp=($title -ceq 'Open Dental')
        if(-not $isChooser -and -not $isApp){continue}
        if($isChooser -and $r.chooser_window_captured){continue}
        # Continue UIA menu discovery each cycle after main window evidence.
        if($isApp -and -not $r.report_route_enabled -and
           $cycle -notin @(8,20,40,65,95,110) -and
           -not ($r.app_window_captured -and -not $r.choose_database_menu_invoked)){
          continue
        }
        if($isChooser){
          $r.chooser_window_title=$title
          $r.chooser_owner_pid_verified=$ids.Contains($pidHere)
        }else{
          $r.app_window_title=$title
          $r.app_window_owner_pid_verified=$ids.Contains($pidHere)
        }
        $hwnd=[IntPtr]([int]$w.Current.NativeWindowHandle)
        $rect=New-Object Lot05DemoGuiWindow+Rect
        if($hwnd -eq [IntPtr]::Zero -or -not [Lot05DemoGuiWindow]::GetWindowRect($hwnd,[ref]$rect)){continue}
        $width=[int]($rect.Right-$rect.Left);$height=[int]($rect.Bottom-$rect.Top)
        if($r.observed_window_bounds.Count -lt 12){$r.observed_window_bounds+=,("$title"+" "+$width+"x"+$height)}
        # Window-only vendor GUI, never desktop, screens or unrelated processes.
        if($width -lt 200 -or $width -gt 2200 -or $height -lt 120 -or $height -gt 1550){continue}
        $target=if($isChooser){$png}else{$appPng}
        $shouldPrint=($isChooser -or $cycle -in @(8,20,40,65,95,110))
        if($shouldPrint){
        $bmp=New-Object System.Drawing.Bitmap($width,$height)
        try{
          $g=[System.Drawing.Graphics]::FromImage($bmp)
          try{
            $dc=$g.GetHdc()
            try{$printed=[Lot05DemoGuiWindow]::PrintWindow($hwnd,$dc,[uint32]0)}
            finally{$g.ReleaseHdc($dc)}
          }finally{$g.Dispose()}
          if($printed){
            $bmp.Save($target,[System.Drawing.Imaging.ImageFormat]::Png)
            $size=(Get-Item -LiteralPath $target).Length
            if($size -gt 2200 -and $size -le 6000000){
              $hash=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
              if($isChooser){
                $r.chooser_window_captured=$true
                $r.chooser_png_sha256=$hash
                $r.chooser_window_size=("$width"+"x"+"$height")
              }else{
                $r.app_window_captured=$true
                $r.app_png_sha256=$hash
                $r.app_window_size=("$width"+"x"+"$height")
                $r.app_window_last_cycle=$cycle
              }
            }
          }
        }finally{$bmp.Dispose()}
        }
        if($isChooser -and $r.chooser_window_captured){
          $controls=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                                [System.Windows.Automation.Condition]::TrueCondition)
          for($k=0;$k -lt [Math]::Min($controls.Count,170);$k++){
            $el=$controls.Item($k)
            if([int]$el.Current.ProcessId -ne $pidHere){continue}
            $nm=[string]$el.Current.Name
            $typ=[string]$el.Current.ControlType.ProgrammaticName
            if($typ -eq 'ControlType.Edit'){$r.chooser_edit_count++}
            if($typ -eq 'ControlType.ComboBox'){$r.chooser_combobox_count++}
            if($typ -eq 'ControlType.Button'){$r.chooser_button_count++}
            if($nm -match '^(Server|Database|MySQL User|MySQL Password|OK|Cancel|Refresh|Choose Database)$' -and
               $r.chooser_safe_controls -notcontains $nm){
              $r.chooser_safe_controls+=,$nm
            }
          }
        }
        # Read-only report entitlement probe, not a database selection.
        if($r.report_route_enabled -and $isApp -and
           $r.app_window_captured -and
           $r.app_png_sha256 -ceq '31ef8a37ff9a3f93845e799dca610ae6a05bc4ed4b11378fac5d577af1b7bd6d' -and
           $width -eq 1040 -and $height -eq 744 -and
           $r.app_window_owner_pid_verified -and
           $cycle -ge 20 -and -not $r.reports_menu_attempted){
          $r.reports_menu_attempted=$true
          $r.reports_menu_cycle=$cycle
          $r.report_route_started=$true
          try{
            $allItems=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
              [System.Windows.Automation.Condition]::TrueCondition)
            $reportItems=New-Object 'System.Collections.Generic.List[System.Windows.Automation.AutomationElement]'
            for($j=0;$j -lt [Math]::Min(450,$allItems.Count);$j++){
              $el=$allItems.Item($j)
              if([int]$el.Current.ProcessId -ne $pidHere){continue}
              if([string]$el.Current.Name -ceq 'Reports' -and
                 [string]$el.Current.ControlType.ProgrammaticName -ceq 'ControlType.MenuItem' -and
                 $el.Current.IsEnabled){$reportItems.Add($el)}
            }
            $r.reports_menu_candidate_count=$reportItems.Count
            if($reportItems.Count -eq 1){
              $node=$reportItems[0]
              $pat=$null
              if($node.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$pat)){
                ([System.Windows.Automation.ExpandCollapsePattern]$pat).Expand()
                $r.reports_menu_invoked=$true
                $r.report_probe_result='REPORTS_MENU_EXPANDED'
              }
            }
          }catch{$r.uia_errors++}
        }
        if($r.report_route_enabled -and $isApp -and
           $r.reports_menu_invoked -and -not $r.user_query_menu_clicked -and
           $cycle -gt $r.reports_menu_cycle){
          try{
            $allItems=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
              [System.Windows.Automation.Condition]::TrueCondition)
            $items=New-Object 'System.Collections.Generic.List[System.Windows.Automation.AutomationElement]'
            for($j=0;$j -lt [Math]::Min(500,$allItems.Count);$j++){
              $el=$allItems.Item($j)
              if([int]$el.Current.ProcessId -ne $pidHere){continue}
              $nm=[string]$el.Current.Name
              $ct=[string]$el.Current.ControlType.ProgrammaticName
              if($nm -match '(?i)Not authorized for.*User.?Query|Permission denied.*User.?Query'){
                $r.report_auth_denied_observed=$true
                $r.report_probe_result='USER_QUERY_PERMISSION_DENIED'
              }
              if($nm -ceq 'User Query' -and
                 $ct -ceq 'ControlType.MenuItem' -and
                 $el.Current.IsEnabled){$items.Add($el)}
            }
            $r.user_query_menu_candidate_count=$items.Count
            if($items.Count -eq 1 -and -not $r.report_auth_denied_observed){
              $el=$items[0]
              $bo=$el.Current.BoundingRectangle
              $bx=[int][Math]::Floor($bo.X+$bo.Width/2)
              $by=[int][Math]::Floor($bo.Y+$bo.Height/2)
              if([int]$el.Current.ProcessId -eq $pidHere -and
                 $bo.Width -ge 70 -and $bo.Width -le 350 -and
                 $bo.Height -ge 16 -and $bo.Height -le 42 -and
                 $bx -ge 0 -and $by -ge 0){
                $null=[Lot05DemoGuiWindow]::SetForegroundWindow($hwnd)
                Start-Sleep -Milliseconds 140
                $fg=[Lot05DemoGuiWindow]::GetForegroundWindow()
                $fgPid=[uint32]0
                if($fg -ne [IntPtr]::Zero){
                  $null=[Lot05DemoGuiWindow]::GetWindowThreadProcessId($fg,[ref]$fgPid)
                }
                $pt=New-Object Lot05DemoGuiWindow+Point
                $pt.X=$bx;$pt.Y=$by
                if([int]$fgPid -eq $pidHere -and [Lot05DemoGuiWindow]::SetCursorPos($bx,$by)){
                  Start-Sleep -Milliseconds 70
                  $hit=[Lot05DemoGuiWindow]::WindowFromPoint($pt)
                  $hitPid=[uint32]0
                  if($hit -ne [IntPtr]::Zero){
                    $null=[Lot05DemoGuiWindow]::GetWindowThreadProcessId($hit,[ref]$hitPid)
                  }
                  $r.user_query_menu_hit_owned=([int]$hitPid -eq $pidHere)
                  if($r.user_query_menu_hit_owned){
                    [Lot05DemoGuiWindow]::mouse_event([uint32]2,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                    Start-Sleep -Milliseconds 85
                    [Lot05DemoGuiWindow]::mouse_event([uint32]4,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                    $r.user_query_menu_clicked=$true
                    $r.user_query_menu_cycle=$cycle
                    $r.report_probe_result='USER_QUERY_MENU_CLICK_SENT'
                  }
                }
              }
            }
          }catch{$r.uia_errors++}
        }
        if($r.report_route_enabled -and $isApp -and
           $r.user_query_menu_clicked -and -not $r.user_query_native_window_observed -and
           $cycle -gt $r.user_query_menu_cycle){
          try{
            $allItems=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
              [System.Windows.Automation.Condition]::TrueCondition)
            for($j=0;$j -lt [Math]::Min(500,$allItems.Count);$j++){
              $el=$allItems.Item($j)
              if([int]$el.Current.ProcessId -ne $pidHere){continue}
              $nm=[string]$el.Current.Name
              $ct=[string]$el.Current.ControlType.ProgrammaticName
              if($nm -match '(?i)Not authorized for.*User.?Query|Permission denied.*User.?Query'){
                $r.report_auth_denied_observed=$true
                $r.report_probe_result='USER_QUERY_PERMISSION_DENIED'
              }
              if($ct -ceq 'ControlType.Window' -and
                 $nm -match '^(User Query|User Query - .+)$'){
                $r.user_query_native_window_observed=$true
                $r.user_query_native_window_title='User Query'
                $r.user_query_native_window_owned=$ids.Contains([int]$el.Current.ProcessId)
                $r.report_probe_result='AUTHORIZED_USER_QUERY_WINDOW'
                $r.report_probe_complete=$true
              }
              if($nm -match '^(Submit Query|Export \.csv|Query Results|Favorites)$' -and
                 $r.user_query_gui_controls -notcontains $nm -and
                 $r.user_query_gui_controls.Count -lt 8){
                $r.user_query_gui_controls+=,$nm
              }
            }
          }catch{$r.uia_errors++}
        }
        # STEP 3A: one allowlisted native File -> Choose Database menu
        # navigation. The prior TWO exact-HEAD runs pinned this untouched main
        # window PNG, same 1040x744, signed OpenDental.exe, no selected patient.
        # No database field, password, report or patient control is touched.
        if(-not $r.report_route_enabled -and $isApp -and $r.app_window_captured -and
           $r.app_png_sha256 -ceq '31ef8a37ff9a3f93845e799dca610ae6a05bc4ed4b11378fac5d577af1b7bd6d' -and
           $width -eq 1040 -and $height -eq 744 -and
           $r.app_window_owner_pid_verified -and
           $cycle -ge 20 -and -not $r.file_menu_attempted){
          $r.file_menu_attempted=$true
          $r.file_menu_cycle=$cycle
          $candidates=New-Object 'System.Collections.Generic.List[System.Windows.Automation.AutomationElement]'
          try{
            $items=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                              [System.Windows.Automation.Condition]::TrueCondition)
            for($k=0;$k -lt [Math]::Min($items.Count,360);$k++){
              $el=$items.Item($k)
              if([int]$el.Current.ProcessId -ne $pidHere){continue}
              $name=[string]$el.Current.Name
              $type=[string]$el.Current.ControlType.ProgrammaticName
              if($name -match '^(File|Setup|Reports|Choose Database)$' -and
                 $r.file_menu_known_labels -notcontains $name -and $r.file_menu_known_labels.Count -lt 8){
                $r.file_menu_known_labels+=,$name
              }
              if($name -ceq 'File' -and $type -ceq 'ControlType.MenuItem' -and
                 $el.Current.IsEnabled){$candidates.Add($el)}
            }
          }catch{$r.uia_errors++}
          $r.file_menu_item_candidates=$candidates.Count
          if($candidates.Count -eq 1){
            $node=$candidates[0]
            try{
              $pattern=$null
              if($node.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$pattern)){
                ([System.Windows.Automation.ExpandCollapsePattern]$pattern).Expand()
                $r.file_menu_invoked=$true
                $r.file_menu_source='UIA_EXPAND_UNIQUE_ENABLED_FILE'
              }elseif($node.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)){
                ([System.Windows.Automation.InvokePattern]$pattern).Invoke()
                $r.file_menu_invoked=$true
                $r.file_menu_source='UIA_INVOKE_UNIQUE_ENABLED_FILE'
              }
            }catch{$r.uia_errors++}
          }
          if(-not $r.file_menu_invoked -and $r.file_menu_item_candidates -le 1){
            # Fallback ONE physical click at the File label centre proven by
            # the pinned 1040x744 PNG (x=93,y=46), never on an unknown window.
            $point=New-Object Lot05DemoGuiWindow+Point
            $point.X=[int]($rect.Left+93)
            $point.Y=[int]($rect.Top+46)
            $hit=[Lot05DemoGuiWindow]::WindowFromPoint($point)
            $hitPid=[uint32]0
            if($hit -ne [IntPtr]::Zero){
              $null=[Lot05DemoGuiWindow]::GetWindowThreadProcessId($hit,[ref]$hitPid)
            }
            $null=[Lot05DemoGuiWindow]::SetForegroundWindow($hwnd)
            Start-Sleep -Milliseconds 160
            if([int]$hitPid -eq $pidHere -and
               [Lot05DemoGuiWindow]::GetForegroundWindow() -eq $hwnd -and
               [Lot05DemoGuiWindow]::SetCursorPos($point.X,$point.Y)){
              Start-Sleep -Milliseconds 70
              if([Lot05DemoGuiWindow]::WindowFromPoint($point) -eq $hit){
                [Lot05DemoGuiWindow]::mouse_event([uint32]2,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                Start-Sleep -Milliseconds 80
                [Lot05DemoGuiWindow]::mouse_event([uint32]4,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                $r.file_menu_invoked=$true
                $r.file_menu_source='PINNED_PNG_PID_FOREGROUND_HITTEST_MOUSE_FILE'
              }
            }
          }
        }
        if(-not $r.report_route_enabled -and $isApp -and $r.file_menu_invoked -and $cycle -gt $r.file_menu_cycle -and
           -not $r.choose_database_menu_invoked){
          try{
            $allWindows=[System.Windows.Automation.AutomationElement]::RootElement.FindAll(
              [System.Windows.Automation.TreeScope]::Children,
              [System.Windows.Automation.Condition]::TrueCondition)
            $matches=New-Object 'System.Collections.Generic.List[System.Windows.Automation.AutomationElement]'
            $r.menu_search_top_level_window_count=$allWindows.Count
            for($j=0;$j -lt [Math]::Min($allWindows.Count,120);$j++){
              $root=$allWindows.Item($j)
              if(-not $ids.Contains([int]$root.Current.ProcessId)){continue}
              $items=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                [System.Windows.Automation.Condition]::TrueCondition)
              $r.menu_search_descendant_count=[Math]::Max($r.menu_search_descendant_count,$items.Count)
              if($items.Count -gt 500){$r.menu_search_capped_count++}
              for($k=0;$k -lt [Math]::Min($items.Count,500);$k++){
                try{
                  $el=$items.Item($k)
                  if([string]$el.Current.Name -cne 'Choose Database'){continue}
                  $ctrlType=[string]$el.Current.ControlType.ProgrammaticName
                  $owner=[int]$el.Current.ProcessId
                  $enabled=[bool]$el.Current.IsEnabled
                  $rectEl=$el.Current.BoundingRectangle
                  $r.choose_database_named_element_count++
                  if($r.choose_database_menu_candidates_meta.Count -lt 10){
                    $r.choose_database_menu_candidates_meta+=,@{
                      type=$ctrlType
                      same_owner=$ids.Contains($owner)
                      enabled=$enabled
                      bounds=("$([int]$rectEl.X),$([int]$rectEl.Y),$([int]$rectEl.Width),$([int]$rectEl.Height)")
                    }
                  }
                  if($ctrlType -ceq 'ControlType.MenuItem' -and $enabled -and
                     $ids.Contains($owner)){
                    $matches.Add($el)
                  }
                }catch{$r.uia_errors++}
              }
            }
            $r.choose_database_menu_candidates=$matches.Count
            $r.choose_database_menu_item_observed=($matches.Count -gt 0)
            if($matches.Count -eq 1){
              # Native Windows menu item: exact control name/type/enabled,
              # attached to the signed app PID, bounds from live UIA evidence.
              # Avoid InvokePattern on a modal WinForms menu: invocation may
              # stall the UIA RPC until its timeout. One physical click only
              # when foreground and WindowFromPoint are both verified.
              $node=$matches[0]
              $bounds=$node.Current.BoundingRectangle
              $ownerPid=[int]$node.Current.ProcessId
              $cx=[int][Math]::Floor($bounds.X+$bounds.Width/2)
              $cy=[int][Math]::Floor($bounds.Y+$bounds.Height/2)
              $r.choose_database_click_owner_verified=($ownerPid -eq $pidHere -and
                $ids.Contains($ownerPid) -and
                $bounds.Width -ge 100 -and $bounds.Width -le 300 -and
                $bounds.Height -ge 16 -and $bounds.Height -le 36 -and
                $cx -ge 0 -and $cy -ge 0)
              if($r.choose_database_click_owner_verified){
                $point=New-Object Lot05DemoGuiWindow+Point
                $point.X=$cx
                $point.Y=$cy
                $null=[Lot05DemoGuiWindow]::SetForegroundWindow($hwnd)
                Start-Sleep -Milliseconds 160
                $r.choose_database_click_foreground_verified=(
                  [Lot05DemoGuiWindow]::GetForegroundWindow() -eq $hwnd)
                if($r.choose_database_click_foreground_verified -and
                   [Lot05DemoGuiWindow]::SetCursorPos($cx,$cy)){
                  Start-Sleep -Milliseconds 90
                  $hit=[Lot05DemoGuiWindow]::WindowFromPoint($point)
                  $hitPid=[uint32]0
                  if($hit -ne [IntPtr]::Zero){
                    $null=[Lot05DemoGuiWindow]::GetWindowThreadProcessId($hit,[ref]$hitPid)
                  }
                  $r.choose_database_click_hit_verified=([int]$hitPid -eq $pidHere)
                  if($r.choose_database_click_hit_verified){
                    $r.choose_database_click_attempted=$true
                    [Lot05DemoGuiWindow]::mouse_event([uint32]2,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                    Start-Sleep -Milliseconds 85
                    [Lot05DemoGuiWindow]::mouse_event([uint32]4,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                    $r.choose_database_menu_invoked=$true
                    $r.choose_database_menu_source='LIVE_UIA_ITEM_PID_FOREGROUND_HITTEST_MOUSE'
                    $r.choose_database_click_source='LIVE_UIA_ITEM_PID_FOREGROUND_HITTEST_MOUSE'
                    $r.choose_database_menu_cycle=$cycle
                  }
                }
              }
            }
          }catch{
            $r.uia_errors++
            $r.choose_database_invoke_error_type=$_.Exception.GetType().Name
          }
        }
      }catch{$r.uia_errors++}
    }
    if($r.report_route_enabled){
      if($r.report_probe_complete -or
         ($r.report_auth_denied_observed -and $cycle -ge 26) -or
         ($r.reports_menu_attempted -and $cycle -ge 60)){
        $r.report_probe_complete=$true
        break
      }
    }elseif($r.demo_connect_post_checked){break}
  }
}catch{
  $r.error_code='EXACT_DEMO_APP_GUI_DISCOVERY_FAIL_CLOSED'
}finally{
  # Do not terminate the MariaDB service. Only terminate the app we just started.
  foreach($childPid in @($ids)){try{Stop-Process -Id $childPid -Force -ErrorAction SilentlyContinue}catch{}}
  [System.IO.File]::WriteAllText($outFile,($r|ConvertTo-Json -Depth 4),(New-Object System.Text.UTF8Encoding($false)))
}
Write-Host ('LOT05_REPORT_PROBE_ROUTE='+$r.report_route_enabled)
Write-Host ('LOT05_REPORT_MENU_EXPANDED='+$r.reports_menu_invoked)
Write-Host ('LOT05_USER_QUERY_MENU_CANDIDATES='+$r.user_query_menu_candidate_count)
Write-Host ('LOT05_USER_QUERY_MENU_CLICKED='+$r.user_query_menu_clicked)
Write-Host ('LOT05_USER_QUERY_WINDOW_OBSERVED='+$r.user_query_native_window_observed)
Write-Host ('LOT05_USER_QUERY_AUTH_DENIED='+$r.report_auth_denied_observed)
Write-Host ('LOT05_USER_QUERY_PROBE_RESULT='+$r.report_probe_result)
Write-Host ('LOT05_NATIVE_DEMO_APP_EXECUTED='+$r.app_process_started)
Write-Host ('LOT05_NATIVE_DEMO_CHOOSER_CAPTURED='+$r.chooser_window_captured)
Write-Host ('LOT05_NATIVE_DEMO_APP_WINDOW_CAPTURED='+$r.app_window_captured)
Write-Host ('LOT05_NATIVE_DEMO_APP_WINDOW_SIZE='+$r.app_window_size)
Write-Host ('LOT05_NATIVE_FILE_MENU_OPENED='+$r.file_menu_invoked)
Write-Host ('LOT05_NATIVE_FILE_MENU_SOURCE='+$r.file_menu_source)
Write-Host ('LOT05_NATIVE_CHOOSE_DB_MENU_INVOKED='+$r.choose_database_menu_invoked)
Write-Host ('LOT05_NATIVE_CHOOSE_DB_CLICK_HIT='+$r.choose_database_click_hit_verified)
Write-Host ('LOT05_NATIVE_CHOOSE_DB_ERROR_TYPE='+$r.choose_database_invoke_error_type)
Write-Host ('LOT05_NATIVE_CHOOSE_DB_NAMED='+$r.choose_database_named_element_count)
Write-Host ('LOT05_NATIVE_MENU_MAX_DESCENDANTS='+$r.menu_search_descendant_count)
Write-Host ('LOT05_NATIVE_POST_CLICK_WINDOWS='+($r.post_click_owned_windows -join ';'))
Write-Host ('LOT05_NATIVE_POST_CLICK_CONTROLS='+($r.post_click_named_controls -join ';'))
Write-Host ('LOT05_NATIVE_DEMO_CHOOSER_TITLE='+$r.chooser_window_title)
Write-Host ('LOT05_NATIVE_NESTED_CHOOSER_OBSERVED='+$r.nested_chooser_window_observed)
Write-Host ('LOT05_NATIVE_NESTED_CHOOSER_BOUNDS='+$r.nested_chooser_bounds)
Write-Host ('LOT05_NATIVE_NESTED_CHOOSER_HWND='+$r.nested_chooser_hwnd_present)
Write-Host ('LOT05_NATIVE_DEMO_SELECTION_SEEN='+$r.nested_chooser_demo_selection_observed)
Write-Host ('LOT05_NATIVE_CHOOSER_UNAUTHORIZED_NOTICE='+$r.nested_chooser_unauthorized_notice_observed)
Write-Host ('LOT05_NATIVE_DEMO_CHOOSER_CONTROLS='+($r.chooser_safe_controls -join ','))
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_OK_CANDIDATES='+$r.demo_connect_ok_candidates)
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_VISUAL_GUARD='+$r.demo_connect_visual_ok_guard)
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_UIA_OK_LABEL_COUNT='+$r.demo_connect_ok_visual_label_count)
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_OK_CLICK_SOURCE='+$r.demo_connect_ok_click_source)
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_COMBO_COUNTS='+$r.demo_connect_demo_combo_count+','+$r.demo_connect_server_combo_count)
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_CLICK='+$r.demo_connect_click_sent)
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_DIALOG_HIT='+$r.demo_connect_hit_dialog_verified)
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_FOREGROUND_DIALOG='+$r.demo_connect_foreground_dialog_verified)
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_POST_ERRORS='+($r.demo_connect_post_error_categories -join ';'))
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_CLOSED='+$r.demo_connect_dialog_closed_observed)
Write-Host ('LOT05_NATIVE_DEMO_CONNECT_POST_WINDOWS='+($r.demo_connect_post_dialog_names -join ';'))
Write-Host ('LOT05_NATIVE_DEMO_NO_PATIENTS_NO_CSV')
if($r.report_route_enabled){
  if(-not $r.prereq_server_and_demo_verified -or -not $r.app_exe_hash_valid -or
     -not $r.app_exe_signature_valid -or -not $r.app_process_started -or
     -not $r.reports_menu_invoked -or -not $r.user_query_menu_clicked -or
     -not $r.user_query_native_window_observed -or
     -not $r.user_query_native_window_owned -or
     $r.report_auth_denied_observed -or $null -ne $r.error_code){
    throw 'NATIVE_USER_QUERY_PERMISSION_OR_WINDOW_NOT_PROVEN'
  }
}else{
  if(-not $r.prereq_server_and_demo_verified -or -not $r.app_exe_hash_valid -or
     -not $r.app_exe_signature_valid -or -not $r.app_process_started -or
     -not $r.choose_database_menu_invoked -or -not $r.chooser_window_captured -or
     -not $r.demo_connect_click_sent -or -not $r.demo_connect_post_checked -or
     -not $r.demo_connect_dialog_closed_observed -or
     $null -ne $r.error_code){
    throw 'NATIVE_DEMO_CONNECT_CONFIRMATION_NOT_PROVEN'
  }
}
