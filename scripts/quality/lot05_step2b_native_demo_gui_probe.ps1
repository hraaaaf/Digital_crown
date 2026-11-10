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
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out Rect r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h,IntPtr dc,uint flags);
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
        if($isApp -and $cycle -notin @(8,20,40,65,95,110)){continue}
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
Write-Host ('LOT05_NATIVE_DEMO_CHOOSER_TITLE='+$r.chooser_window_title)
Write-Host ('LOT05_NATIVE_DEMO_CHOOSER_CONTROLS='+($r.chooser_safe_controls -join ','))
Write-Host ('LOT05_NATIVE_DEMO_NO_PATIENTS_NO_CSV')
if(-not $r.prereq_server_and_demo_verified -or -not $r.app_exe_hash_valid -or
   -not $r.app_exe_signature_valid -or -not $r.app_process_started -or
   (-not $r.chooser_window_captured -and -not $r.app_window_captured) -or
   $null -ne $r.error_code){
  throw 'NATIVE_DEMO_APP_WINDOW_NOT_PROVEN'
}
