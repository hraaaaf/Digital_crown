# LOT05: click exact signed Open Dental SERVER trial Install once, inspect next screen.
$ErrorActionPreference='Stop'
$wrapper=Join-Path $env:RUNNER_TEMP 'lot05_publisher_trial.exe'
$extract=Join-Path $env:RUNNER_TEMP 'lot05_publisher_archive'
$json=Join-Path $env:RUNNER_TEMP 'lot05_server_launcher_readonly.json'
$png=Join-Path $env:RUNNER_TEMP 'lot05_server_launcher_window.png'
$postPng=Join-Path $env:RUNNER_TEMP 'lot05_after_official_server_install_click_window.png'
$ids=New-Object 'System.Collections.Generic.HashSet[int]'
$r=[ordered]@{
  kind='PUBLISHER_SIGNED_SERVER_LAUNCHER_READONLY'
  head=$env:LOT05_EXPECTED_SHA
  wrapper_hash_pinned=$false
  wrapper_signature_valid=$false
  publisher_is_open_dental=$false
  embedded_launcher_hash='NOT_OBSERVED'
  embedded_launcher_signature='NOT_OBSERVED'
  embedded_launcher_started=$false
  session_verified=$false
  launcher_exited_early=$false
  vendor_window_title='NOT_OBSERVED'
  vendor_window_capture_ok=$false
  vendor_window_sha256=$null
  vendor_window_size=$null
  vendor_safe_control_names=@()
  native_checkbox_count=0
  observed_cycles=0
  uia_errors=0
  exact_all_selected_gui_sha256_verified=$false
  install_control_candidates=0
  install_button_pid_verified=$false
  install_button_geometry_verified=$false
  install_window_foreground_verified=$false
  install_hit_test_exact_button=$false
  install_click_attempted=$false
  install_click_physical_events=0
  clicked_install=$false
  post_click_window_captured=$false
  post_click_window_title='NOT_OBSERVED'
  post_click_window_sha256=$null
  post_click_window_size=$null
  entered_setup_wizard=$false
  installed_program_present=$false
  accepted_license=$false
  created_database=$false
  accessed_patient_data=$false
  exported_csv=$false
  error_code=$null
}
try{
  Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
  Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop
  Add-Type -AssemblyName System.Drawing -ErrorAction Stop
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class Lot05ServerReadWindow {
 [StructLayout(LayoutKind.Sequential)] public struct Rect {public int Left,Top,Right,Bottom;}
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd,out Rect rect);
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd,IntPtr hdc,uint flags);
 [StructLayout(LayoutKind.Sequential)] public struct Pt {public int X,Y;}
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(Pt p);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint pid);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hwnd,System.Text.StringBuilder sb,int max);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint dx,uint dy,uint data,UIntPtr extra);
}
'@ -ErrorAction Stop
  if(@(Get-Service -Name 'MariaDB','MySQL*' -ErrorAction SilentlyContinue).Count -gt 0){throw 'EXISTING_DB_FORBIDDEN'}
  [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest -Uri 'https://www.opendental.com/TrialDownload-25-3-48.exe' -OutFile $wrapper -TimeoutSec 210 -MaximumRedirection 2
  if((Get-Item -LiteralPath $wrapper).Length -ne 149781424){throw 'SIZE_CHANGED'}
  if((Get-FileHash -LiteralPath $wrapper -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'b892db0d3b2fc0947fa25fe4fc07c2e81815d70119f72e7abf1f8b9b0671bcb9'){throw 'SHA_CHANGED'}
  $r.wrapper_hash_pinned=$true
  $sig=Get-AuthenticodeSignature -LiteralPath $wrapper
  if($sig.Status -ne [System.Management.Automation.SignatureStatus]::Valid){throw 'SIGNED_WRAPPER_INVALID'}
  $r.wrapper_signature_valid=$true
  if($null -eq $sig.SignerCertificate -or $sig.SignerCertificate.Subject -notmatch '(?i)Open\s*Dental'){throw 'WRONG_PUBLISHER'}
  $r.publisher_is_open_dental=$true
  $sz='C:\Program Files\7-Zip\7z.exe'
  if(-not(Test-Path -LiteralPath $sz)){throw 'SEVENZIP_UNAVAILABLE'}
  $null=New-Item -ItemType Directory -Path $extract -Force
  $null=& $sz x $wrapper "-o$extract" '-y' 2>$null
  if($LASTEXITCODE -ne 0){throw 'SIGNED_ARCHIVE_EXTRACTION_FAILED'}
  $exe=Join-Path $extract 'Release\OpenDentalInstaller.exe'
  if(-not(Test-Path -LiteralPath $exe)){throw 'OFFICIAL_SERVER_EXE_MISSING'}
  $r.embedded_launcher_hash=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
  if($r.embedded_launcher_hash -cne 'd9fefd875d82b391d981a53fe412f6c8da7481c828e8e173aa1626c722a16e27'){
    throw 'OFFICIAL_SERVER_BINARY_HASH_CHANGED'
  }
  $innerSig=Get-AuthenticodeSignature -LiteralPath $exe
  $r.embedded_launcher_signature=[string]$innerSig.Status
  if($innerSig.Status -ne [System.Management.Automation.SignatureStatus]::Valid -or
     $null -eq $innerSig.SignerCertificate -or
     $innerSig.SignerCertificate.Subject -notmatch '(?i)Open\s*Dental'){
    throw 'SIGNED_INNER_SERVER_LAUNCHER_INVALID'
  }
  $proc=Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe) -PassThru -ErrorAction Stop
  $r.embedded_launcher_started=$true
  $null=$ids.Add([int]$proc.Id)
  $r.session_verified=($proc.SessionId -eq [System.Diagnostics.Process]::GetCurrentProcess().SessionId)
  if(-not $r.session_verified){throw 'SESSION_NOT_INTERACTIVE'}
  for($cycle=0;$cycle -lt 100;$cycle++){
    Start-Sleep -Milliseconds 1150
    $r.observed_cycles=$cycle+1
    $all=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    for($depth=0;$depth -lt 2;$depth++){
      foreach($child in $all){if($ids.Contains([int]$child.ParentProcessId)){$null=$ids.Add([int]$child.ProcessId)}}
    }
    if($null -eq (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue)){$r.launcher_exited_early=$true}
    $windows=[System.Windows.Automation.AutomationElement]::RootElement.FindAll(
      [System.Windows.Automation.TreeScope]::Children,[System.Windows.Automation.Condition]::TrueCondition)
    for($i=0;$i -lt [Math]::Min(100,$windows.Count);$i++){
      try{
        $w=$windows.Item($i)
        $owner=[int]$w.Current.ProcessId
        $title=[string]$w.Current.Name
        if(-not $ids.Contains($owner) -or $title -notmatch '(?i)(Open.?Dental|Trial|Install)'){continue}
        $r.vendor_window_title=$title.Substring(0,[Math]::Min($title.Length,100))
        if(-not $r.vendor_window_capture_ok){
          $hwnd=[IntPtr]([int]$w.Current.NativeWindowHandle)
          $rect=New-Object Lot05ServerReadWindow+Rect
          if($hwnd -ne [IntPtr]::Zero -and [Lot05ServerReadWindow]::GetWindowRect($hwnd,[ref]$rect)){
            $width=[int]($rect.Right-$rect.Left);$height=[int]($rect.Bottom-$rect.Top)
            if($width -ge 280 -and $height -ge 180 -and $width -le 1600 -and $height -le 1100){
              $bmp=New-Object System.Drawing.Bitmap($width,$height)
              try{
                $graphics=[System.Drawing.Graphics]::FromImage($bmp)
                try{
                  $dc=$graphics.GetHdc()
                  try{$ok=[Lot05ServerReadWindow]::PrintWindow($hwnd,$dc,[uint32]0)}
                  finally{$graphics.ReleaseHdc($dc)}
                }finally{$graphics.Dispose()}
                if($ok){
                  $bmp.Save($png,[System.Drawing.Imaging.ImageFormat]::Png)
                  $size=(Get-Item -LiteralPath $png).Length
                  if($size -gt 2500 -and $size -lt 6000000){
                    $r.vendor_window_capture_ok=$true
                    $r.vendor_window_sha256=(Get-FileHash -LiteralPath $png -Algorithm SHA256).Hash.ToLowerInvariant()
                    $r.vendor_window_size="$width"+"x"+"$height"
                  }
                }
              }finally{$bmp.Dispose()}
            }
          }
        }
        if($r.vendor_window_capture_ok){
          $desc=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
          for($k=0;$k -lt [Math]::Min($desc.Count,150);$k++){
            $el=$desc.Item($k)
            if([int]$el.Current.ProcessId -ne $owner){continue}
            $label=[string]$el.Current.Name
            if($label -match '(?i)^(Install|Server|Workstation|MariaDB|MySQL|Database|OpenDentImages|Browse|Cancel)$'){
              if($r.vendor_safe_control_names -notcontains $label){$r.vendor_safe_control_names+=,$label}
            }
            if([string]$el.Current.ControlType.ProgrammaticName -ceq 'ControlType.CheckBox'){
              $r.native_checkbox_count++
            }
          }
        }

        # The exact publisher screenshot proves ALL six server components checked:
        # Open Dental, MariaDB Server, grant tables, my.ini, DB (including demo)
        # and OpenDentImages, with local paths and only demo content.
        if($r.vendor_window_capture_ok -and $title -ceq 'Open Dental Installer' -and
           $r.vendor_window_sha256 -ceq 'cdf8ded003f178e01d0d068f829f9c004fce87aa70a1ed38ea1c30b986d94c72' -and
           -not $r.install_click_attempted -and -not $r.clicked_install){
          $r.exact_all_selected_gui_sha256_verified=$true
          try{
            $uniqueInstall=@($r.vendor_safe_control_names | Where-Object {$_ -ceq 'Install'})
            $r.install_control_candidates=$uniqueInstall.Count
            $topHwnd=[IntPtr]([int]$w.Current.NativeWindowHandle)
            $topRect=New-Object Lot05ServerReadWindow+Rect
            if($uniqueInstall.Count -eq 1 -and $topHwnd -ne [IntPtr]::Zero -and
               [Lot05ServerReadWindow]::GetWindowRect($topHwnd,[ref]$topRect)){
              $pw=[int]($topRect.Right-$topRect.Left)
              $ph=[int]($topRect.Bottom-$topRect.Top)
              $r.install_button_geometry_verified=($pw -eq 708 -and $ph -eq 636)
              if($r.install_button_geometry_verified){
                # This is the right-side Install in 708x636 signed PNG, NOT "New Server".
                $cx=[int]($topRect.Left+629)
                $cy=[int]($topRect.Top+553)
                $p=New-Object Lot05ServerReadWindow+Pt
                $p.X=$cx;$p.Y=$cy
                $button=[Lot05ServerReadWindow]::WindowFromPoint($p)
                if($button -ne [IntPtr]::Zero){
                  $pidButton=[uint32]0
                  $null=[Lot05ServerReadWindow]::GetWindowThreadProcessId($button,[ref]$pidButton)
                  $r.install_button_pid_verified=([int]$pidButton -eq $owner)
                  $labelBuf=New-Object System.Text.StringBuilder(100)
                  $null=[Lot05ServerReadWindow]::GetWindowText($button,$labelBuf,$labelBuf.Capacity)
                  $buttonLabel=$labelBuf.ToString().Replace([string]'&',[string]'').Trim()
                  $r.install_hit_test_exact_button=($buttonLabel -ceq 'Install')
                  if($r.install_button_pid_verified -and $r.install_hit_test_exact_button){
                    $null=[Lot05ServerReadWindow]::SetForegroundWindow($topHwnd)
                    Start-Sleep -Milliseconds 200
                    $r.install_window_foreground_verified=(
                      [Lot05ServerReadWindow]::GetForegroundWindow() -eq $topHwnd)
                    if($r.install_window_foreground_verified -and
                       [Lot05ServerReadWindow]::SetCursorPos($cx,$cy)){
                      Start-Sleep -Milliseconds 80
                      if([Lot05ServerReadWindow]::WindowFromPoint($p) -eq $button){
                        $r.install_click_attempted=$true
                        [Lot05ServerReadWindow]::mouse_event([uint32]2,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                        $r.install_click_physical_events=1
                        Start-Sleep -Milliseconds 80
                        [Lot05ServerReadWindow]::mouse_event([uint32]4,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                        $r.install_click_physical_events=2
                        $r.clicked_install=$true
                      }
                    }
                  }
                }
              }
            }
          }catch{$r.uia_errors++}
        }
        # After one publisher Install click: only read the next owned window.
        # No Next/Finish/EULA/DB dialog input until that screen is verified.
        if($r.clicked_install -and $cycle -gt 0 -and -not $r.post_click_window_captured){
          try{
            $hwnd=[IntPtr]([int]$w.Current.NativeWindowHandle)
            $rect=New-Object Lot05ServerReadWindow+Rect
            if($hwnd -ne [IntPtr]::Zero -and [Lot05ServerReadWindow]::GetWindowRect($hwnd,[ref]$rect)){
              $width=[int]($rect.Right-$rect.Left)
              $height=[int]($rect.Bottom-$rect.Top)
              if($width -ge 280 -and $width -le 1600 -and $height -ge 180 -and $height -le 1100){
                $bitmap=New-Object System.Drawing.Bitmap($width,$height)
                try{
                  $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
                  try{
                    $dc=$graphics.GetHdc()
                    try{$printed=[Lot05ServerReadWindow]::PrintWindow($hwnd,$dc,[uint32]0)}
                    finally{$graphics.ReleaseHdc($dc)}
                  }finally{$graphics.Dispose()}
                  if($printed){
                    $bitmap.Save($postPng,[System.Drawing.Imaging.ImageFormat]::Png)
                    $hash=(Get-FileHash -LiteralPath $postPng -Algorithm SHA256).Hash.ToLowerInvariant()
                    if($hash -cne $r.vendor_window_sha256 -and
                       (Get-Item -LiteralPath $postPng).Length -gt 2500){
                      $r.post_click_window_captured=$true
                      $r.post_click_window_title=$title.Substring(0,[Math]::Min($title.Length,100))
                      $r.post_click_window_sha256=$hash
                      $r.post_click_window_size="$width" + 'x' + "$height"
                      $r.entered_setup_wizard=($title -match '(?i)OpenDental.*Setup')
                    }
                  }
                }finally{$bitmap.Dispose()}
              }
            }
          }catch{$r.uia_errors++}
        }
      }catch{$r.uia_errors++}
    }
    if($r.post_click_window_captured){break}
  }
}catch{
  $r.error_code='READONLY_VENDOR_SERVER_ORCHESTRATOR_FAIL_CLOSED'
}finally{
  foreach($childProcessId in @($ids)){try{Stop-Process -Id $childProcessId -Force -ErrorAction SilentlyContinue}catch{}}
  Remove-Item -LiteralPath $wrapper -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $extract -Recurse -Force -ErrorAction SilentlyContinue
  $r.created_database=(@(Get-Service -Name 'MariaDB','MySQL*' -ErrorAction SilentlyContinue).Count -gt 0)
  $r.installed_program_present=(Test-Path -LiteralPath 'C:\Program Files (x86)\Open Dental\OpenDental.exe')
  [System.IO.File]::WriteAllText($json,($r|ConvertTo-Json -Depth 4),(New-Object System.Text.UTF8Encoding($false)))
}
Write-Host ('LOT05_SERVER_GUI_LAUNCHED='+$r.embedded_launcher_started)
Write-Host ('LOT05_SERVER_GUI_SIGNATURE='+$r.embedded_launcher_signature)
Write-Host ('LOT05_SERVER_GUI_TITLE='+$r.vendor_window_title)
Write-Host ('LOT05_SERVER_GUI_CAPTURE='+$r.vendor_window_capture_ok)
Write-Host ('LOT05_SERVER_GUI_SAFE_CONTROLS='+($r.vendor_safe_control_names -join ','))
Write-Host ('LOT05_SERVER_GUI_DEFAULT_ALL_SELECTED_SHA_PINNED='+$r.exact_all_selected_gui_sha256_verified)
Write-Host ('LOT05_SERVER_GUI_INSTALL_CANDIDATES='+$r.install_control_candidates)
Write-Host ('LOT05_SERVER_GUI_INSTALL_BUTTON_OWNER='+$r.install_button_pid_verified)
Write-Host ('LOT05_SERVER_GUI_INSTALL_HIT_TEST='+$r.install_hit_test_exact_button)
Write-Host ('LOT05_SERVER_GUI_INSTALL_CLICKED='+$r.clicked_install)
Write-Host ('LOT05_SERVER_GUI_AFTER_CLICK_CAPTURED='+$r.post_click_window_captured)
Write-Host ('LOT05_SERVER_GUI_AFTER_CLICK_TITLE='+$r.post_click_window_title)
Write-Host ('LOT05_SERVER_GUI_DATABASE_SERVICE='+$r.created_database)
Write-Host 'LOT05_SERVER_GUI_ONE_INSTALL_ONLY_NO_PATIENT_DATA'
if(-not $r.wrapper_hash_pinned -or -not $r.wrapper_signature_valid -or
   -not $r.publisher_is_open_dental -or -not $r.embedded_launcher_started -or
   $null -ne $r.error_code){throw 'SIGNED_LAUNCHER_INSPECTION_NOT_PROVEN'}
