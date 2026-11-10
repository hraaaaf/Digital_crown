# LOT05 2B — discover exact publisher app Choose Database after full server trial.
# Only disposable GitHub-hosted Windows + verified demo SQL metadata; no PHI.
$ErrorActionPreference='Stop'
$outFile=Join-Path $env:RUNNER_TEMP 'lot05_native_demo_gui_probe.json'
$png=Join-Path $env:RUNNER_TEMP 'lot05_native_demo_choose_database.png'
$appPng=Join-Path $env:RUNNER_TEMP 'lot05_native_demo_open_dental_window.png'
$r=[ordered]@{
  kind='LOT05_NATIVE_DEMO_GUI_DISCOVERY_FUE_I'
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
  choose_database_menu_invoked=$false
  choose_database_menu_source='NOT_ATTEMPTED'
  choose_database_menu_cycle=-1
  observed_window_bounds=@()
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
        $isChooser=($title -ceq 'Choose Database')
        $isApp=($title -ceq 'Open Dental')
        if(-not $isChooser -and -not $isApp){continue}
        if($isChooser -and $r.chooser_window_captured){continue}
        # Continue UIA menu discovery each cycle after main window evidence.
        if($isApp -and $cycle -notin @(8,20,40,65,95,110) -and
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
        # STEP 3A: one allowlisted native File -> Choose Database menu
        # navigation. The prior TWO exact-HEAD runs pinned this untouched main
        # window PNG, same 1040x744, signed OpenDental.exe, no selected patient.
        # No database field, password, report or patient control is touched.
        if($isApp -and $r.app_window_captured -and
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
        if($isApp -and $r.file_menu_invoked -and $cycle -gt $r.file_menu_cycle -and
           -not $r.choose_database_menu_invoked){
          try{
            $allWindows=[System.Windows.Automation.AutomationElement]::RootElement.FindAll(
              [System.Windows.Automation.TreeScope]::Children,
              [System.Windows.Automation.Condition]::TrueCondition)
            $matches=New-Object 'System.Collections.Generic.List[System.Windows.Automation.AutomationElement]'
            for($j=0;$j -lt [Math]::Min($allWindows.Count,120);$j++){
              $root=$allWindows.Item($j)
              if(-not $ids.Contains([int]$root.Current.ProcessId)){continue}
              $items=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                (New-Object System.Windows.Automation.PropertyCondition(
                  [System.Windows.Automation.AutomationElement]::NameProperty,[string]'Choose Database')))
              for($k=0;$k -lt [Math]::Min($items.Count,10);$k++){
                $el=$items.Item($k)
                if([string]$el.Current.Name -ceq 'Choose Database' -and
                   [string]$el.Current.ControlType.ProgrammaticName -ceq 'ControlType.MenuItem' -and
                   $el.Current.IsEnabled -and $ids.Contains([int]$el.Current.ProcessId)){
                  $matches.Add($el)
                }
              }
            }
            $r.choose_database_menu_candidates=$matches.Count
            $r.choose_database_menu_item_observed=($matches.Count -gt 0)
            if($matches.Count -eq 1){
              $node=$matches[0]
              $pattern=$null
              if($node.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)){
                ([System.Windows.Automation.InvokePattern]$pattern).Invoke()
                $r.choose_database_menu_invoked=$true
                $r.choose_database_menu_source='UIA_INVOKE_UNIQUE_CHOOSE_DATABASE'
                $r.choose_database_menu_cycle=$cycle
              }
            }
          }catch{$r.uia_errors++}
        }
      }catch{$r.uia_errors++}
    }
    if($r.chooser_window_captured){break}
  }
}catch{
  $r.error_code='EXACT_DEMO_APP_GUI_DISCOVERY_FAIL_CLOSED'
}finally{
  # Do not terminate the MariaDB service. Only terminate the app we just started.
  foreach($childPid in @($ids)){try{Stop-Process -Id $childPid -Force -ErrorAction SilentlyContinue}catch{}}
  [System.IO.File]::WriteAllText($outFile,($r|ConvertTo-Json -Depth 4),(New-Object System.Text.UTF8Encoding($false)))
}
Write-Host ('LOT05_NATIVE_DEMO_APP_EXECUTED='+$r.app_process_started)
Write-Host ('LOT05_NATIVE_DEMO_CHOOSER_CAPTURED='+$r.chooser_window_captured)
Write-Host ('LOT05_NATIVE_DEMO_APP_WINDOW_CAPTURED='+$r.app_window_captured)
Write-Host ('LOT05_NATIVE_DEMO_APP_WINDOW_SIZE='+$r.app_window_size)
Write-Host ('LOT05_NATIVE_FILE_MENU_OPENED='+$r.file_menu_invoked)
Write-Host ('LOT05_NATIVE_FILE_MENU_SOURCE='+$r.file_menu_source)
Write-Host ('LOT05_NATIVE_CHOOSE_DB_MENU_INVOKED='+$r.choose_database_menu_invoked)
Write-Host ('LOT05_NATIVE_DEMO_CHOOSER_TITLE='+$r.chooser_window_title)
Write-Host ('LOT05_NATIVE_DEMO_CHOOSER_CONTROLS='+($r.chooser_safe_controls -join ','))
Write-Host ('LOT05_NATIVE_DEMO_NO_PATIENTS_NO_CSV')
if(-not $r.prereq_server_and_demo_verified -or -not $r.app_exe_hash_valid -or
   -not $r.app_exe_signature_valid -or -not $r.app_process_started -or
   -not $r.choose_database_menu_invoked -or -not $r.chooser_window_captured -or
   $null -ne $r.error_code){
  throw 'NATIVE_DEMO_CHOOSE_DATABASE_DIALOG_NOT_PROVEN'
}
