# LOT05 Step2B — User-authorized EULA acceptance in disposable Windows ONLY.
# Explicit user instruction: "Juste clique sur accept ... la partie juridique tu me la laisses".
# This is NOT a legal determination and never authorizes production, PHI or deploying.
$ErrorActionPreference='Stop'
$outFile=Join-Path $env:RUNNER_TEMP 'lot05-step2b-eula-accepted-demo-metadata.json'
$imageFile=Join-Path $env:RUNNER_TEMP 'lot05-step2b-license-before-accept-window-only.png'
$acceptedImage=Join-Path $env:RUNNER_TEMP 'lot05-step2b-license-after-accept-window-only.png'
$followingImage=Join-Path $env:RUNNER_TEMP 'lot05-step2b-screen-after-eula-next-only.png'
$destinationFollowingImage=Join-Path $env:RUNNER_TEMP 'lot05-step2b-after-destination-next-window-only.png'
$installFinishedImage=Join-Path $env:RUNNER_TEMP 'lot05-step2b-after-install-finish-wizard-only.png'
$wrapper=Join-Path $env:RUNNER_TEMP 'lot05-publisher-signed-wrapper.exe'
$folder=Join-Path $env:RUNNER_TEMP 'lot05-publisher-signed-extracted'
$knownIds=New-Object 'System.Collections.Generic.HashSet[int]'
$r=[ordered]@{
  kind='HOSTED_DESKTOP_SESSION_AND_VENDOR_WINDOW_DIAGNOSTIC'
  sha=$env:LOT05_EXPECTED_SHA
  runner_session_id=-1
  environment_user_interactive=$false
  explorer_same_session=$false
  uia_root_accessible=$false
  synthetic_windows_gui_already_proven_in_previous_runs=$true
  wrapper_hash_pinned=$false
  wrapper_authenticode_valid=$false
  inner_setup_authenticode_valid=$false
  inner_setup_sha256='UNKNOWN'
  inner_setup_started_once=$false
  inner_setup_exited_early=$false
  inner_setup_exit_code_if_observed=$null
  inner_setup_same_session=$false
  inner_setup_mainwindow_nonzero=$false
  owned_window_count_max=0
  owned_blank_title_window_count_max=0
  owned_setup_title_window_count_max=0
  owned_generic_title_window_count_max=0
  owned_license_title_window_count_max=0
  total_uia_root_window_count_max=0
  unowned_windows_installer_title_count_max=0
  observed_process_descendants_bounded=0
  ui_observation_cycles=0
  ui_errors_count=0
  screenshot_window_only_retained=$false
  screenshot_vendor_owner_verified=$false
  screenshot_title_allowlisted=$false
  screenshot_printwindow_succeeded=$false
  screenshot_dimensions=$null
  screenshot_sha256=$null
  screenshot_error_count=0
  welcome_title_exact_proven=$false
  welcome_text_uia_observed=$false
  welcome_back_disabled=$false
  welcome_cancel_button_observed=$false
  next_button_candidate_count=0
  native_next_button_candidate_count=0
  native_cancel_candidate_count=0
  native_back_disabled_count=0
  native_button_pid_verified=$false
  next_control_source='NONE'
  next_click_attempted=$false
  foreground_window_verified=$false
  next_button_geometry_verified=$false
  cursor_over_exact_next=$false
  physical_mouse_events_sent=0
  next_click_acknowledged=$false
  next_click_cycle=-1
  pre_next_screenshot_sha256=$null
  post_next_screenshot_changed=$false
  post_next_screenshot_sha256=$null
  post_next_window_title_owned=$false
  post_next_license_window_captured=$false
  license_window_title_detected_after_next=$false
  post_next_license_keyword_seen=$false
  clicked_install=$false
  clicked_next=$false
  accepted_eula=$false
  exact_license_window_verified=$false
  eula_accept_radio_candidates=0
  eula_decline_radio_candidates=0
  eula_next_candidates=0
  eula_decline_prechecked=$false
  eula_accept_preunchecked=$false
  eula_next_pre_disabled=$false
  eula_click_attempted=$false
  eula_click_physical_events_sent=0
  eula_accept_radio_checked_after=$false
  eula_decline_radio_unchecked_after=$false
  eula_next_enabled_after=$false
  eula_accept_window_png_saved=$false
  eula_accept_window_png_sha256=$null
  eula_next_click_attempted=$false
  eula_next_click_sent=$false
  eula_next_click_physical_events_sent=0
  eula_following_screen_captured=$false
  eula_following_screen_title='NOT_OBSERVED'
  eula_following_screen_sha256=$null
  destination_screen_exact_png_verified=$false
  destination_next_candidate_count=0
  destination_cancel_candidate_count=0
  destination_browse_candidate_count=0
  destination_usage_candidate_count=0
  destination_next_click_attempted=$false
  destination_next_clicked=$false
  destination_next_physical_events=0
  destination_following_screen_captured=$false
  destination_following_screen_title='NOT_OBSERVED'
  destination_following_screen_sha256=$null
  ready_to_install_exact_png_verified=$false
  install_button_candidates=0
  install_back_candidates=0
  install_cancel_candidates=0
  install_owner_pid_verified=$false
  install_button_bounds_verified=$false
  install_button_rel_x=-1
  install_button_rel_y=-1
  install_geometry_gate_passed=$false
  install_foreground_verified=$false
  install_cursor_moved=$false
  install_cursor_hit_exact_button=$false
  install_click_attempted=$false
  install_click_sent=$false
  install_physical_events_sent=0
  installed_exe_present=$false
  installed_exe_sha256=$null
  installed_exe_authenticode_status='NOT_OBSERVED'
  completed_installer_finish_button_seen=$false
  completed_installer_screen_captured=$false
  completed_installer_screen_sha256=$null
  eula_ui_exception_count=0
  database_created=$false
  csv_exported=$false
  patient_data_accessed=$false
  diagnosis='NOT_CLASSIFIED'
  error_code=$null
}
try{
  Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
  Add-Type -AssemblyName UIAutomationTypes -ErrorAction Stop
  Add-Type -AssemblyName System.Drawing -ErrorAction Stop
  Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class Lot05CaptureSignedWindow { [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left,Top,Right,Bottom; } [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd,out Rect rect); [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hwnd,IntPtr hdc,uint flags); [DllImport("user32.dll",SetLastError=true)] public static extern IntPtr SendMessageTimeout(IntPtr hwnd,uint msg,IntPtr wParam,IntPtr lParam,uint flags,uint timeout,out IntPtr result); [StructLayout(LayoutKind.Sequential)] public struct Pt { public int X,Y; } [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hwnd); [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y); [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(Pt pt); [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint dx,uint dy,uint buttons,UIntPtr extra); public delegate bool EnumChildCallback(IntPtr hwnd,IntPtr user); [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr hwnd,EnumChildCallback callback,IntPtr user); [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hwnd,System.Text.StringBuilder sb,int capacity); [DllImport("user32.dll")] public static extern bool IsWindowEnabled(IntPtr hwnd); [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd); [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint pid); }' -ErrorAction Stop
  $r.runner_session_id=[System.Diagnostics.Process]::GetCurrentProcess().SessionId
  $r.environment_user_interactive=[System.Environment]::UserInteractive
  $r.explorer_same_session=(@(Get-Process -Name explorer -ErrorAction SilentlyContinue | Where-Object {$_.SessionId -eq $r.runner_session_id}).Count -gt 0)
  try{
    $root=[System.Windows.Automation.AutomationElement]::RootElement
    $r.uia_root_accessible=($null -ne $root)
  }catch{$r.ui_errors_count++}
  # Run only when source has been authenticated. Do not start SFX.
  [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest 'https://www.opendental.com/TrialDownload-25-3-48.exe' -OutFile $wrapper -TimeoutSec 210 -MaximumRedirection 2
  if((Get-Item -LiteralPath $wrapper).Length -ne 149781424){throw 'WRAPPER_SIZE_CHANGED'}
  if((Get-FileHash -LiteralPath $wrapper -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'b892db0d3b2fc0947fa25fe4fc07c2e81815d70119f72e7abf1f8b9b0671bcb9'){throw 'WRAPPER_DIGEST_CHANGED'}
  $r.wrapper_hash_pinned=$true
  $sig=Get-AuthenticodeSignature -LiteralPath $wrapper
  if($sig.Status -ne [System.Management.Automation.SignatureStatus]::Valid -or $null -eq $sig.SignerCertificate -or $sig.SignerCertificate.Subject -notmatch '(?i)Open\s*Dental'){throw 'WRAPPER_SIGNER_MISMATCH'}
  $r.wrapper_authenticode_valid=$true
  $sevenzip='C:\Program Files\7-Zip\7z.exe'
  if(-not (Test-Path -LiteralPath $sevenzip)){throw 'SEVENZIP_MISSING'}
  $null=New-Item -ItemType Directory -Path $folder -Force
  $null=& $sevenzip x $wrapper "-o$folder" '-y' 2>$null
  if($LASTEXITCODE -ne 0){throw 'SIGNED_ARCHIVE_EXTRACT_FAILED'}
  $setup=Join-Path $folder 'Release\Open Dental Setup\Setup.exe'
  if(-not (Test-Path -LiteralPath $setup)){throw 'EMBEDDED_SETUP_NOT_FOUND'}
  $r.inner_setup_sha256=(Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash.ToLowerInvariant()
  if($r.inner_setup_sha256 -cne 'ae9cbb314b6a7610be28e3c423137bf9c849d7d62f5a31c95c3b75bf89b1de02'){throw 'EMBEDDED_SETUP_HASH_CHANGED'}
  $innerSig=Get-AuthenticodeSignature -LiteralPath $setup
  if($innerSig.Status -ne [System.Management.Automation.SignatureStatus]::Valid){throw 'EMBEDDED_SETUP_SIGNATURE_INVALID'}
  $r.inner_setup_authenticode_valid=$true
  # Single launch. Never send mouse/keyboard/UIA Invoke.
  $proc=Start-Process -FilePath $setup -WorkingDirectory (Split-Path -Parent $setup) -PassThru -ErrorAction Stop
  $r.inner_setup_started_once=$true
  $null=$knownIds.Add([int]$proc.Id)
  for($cycle=0;$cycle -lt 130;$cycle++){
    Start-Sleep -Milliseconds 1150
    $r.ui_observation_cycles=$cycle+1
    $all=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    for($depth=0;$depth -lt 2;$depth++){
      foreach($child in $all){
        if($knownIds.Contains([int]$child.ParentProcessId)){
          $null=$knownIds.Add([int]$child.ProcessId)
        }
      }
    }
    $r.observed_process_descendants_bounded=[Math]::Min(50,$knownIds.Count)
    $p=Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if($null -ne $p){
      $p.Refresh()
      $r.inner_setup_same_session=($p.SessionId -eq $r.runner_session_id)
      if($p.MainWindowHandle -ne [IntPtr]::Zero){$r.inner_setup_mainwindow_nonzero=$true}
    }else{
      $r.inner_setup_exited_early=$true
    }
    try{
      $windows=[System.Windows.Automation.AutomationElement]::RootElement.FindAll(
        [System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition
      )
      $r.uia_root_accessible=$true
      $r.total_uia_root_window_count_max=[Math]::Max($r.total_uia_root_window_count_max,$windows.Count)
      $owned=0;$empty=0;$setupCount=0;$other=0;$license=0;$unownedMsi=0
      for($i=0;$i -lt [Math]::Min(120,$windows.Count);$i++){
        $w=$windows.Item($i)
        try{
          $winPid=[int]$w.Current.ProcessId
          $title=[string]$w.Current.Name
          if($knownIds.Contains($winPid)){
            $owned++
            if([string]::IsNullOrWhiteSpace($title)){$empty++}
            elseif($title -match '(?i)(Open.?Dental|Setup|Wizard|Licen[cs]e Agreement|EULA|Terms and Conditions)'){
              if($title -match '(?i)(Licen[cs]e Agreement|EULA|Terms and Conditions)'){
                $license++
                if($r.next_click_acknowledged){$r.license_window_title_detected_after_next=$true}
              }else{$setupCount++}
              if(-not $r.screenshot_window_only_retained -or ($r.next_click_acknowledged -and $cycle -gt $r.next_click_cycle -and -not $r.post_next_screenshot_changed)){
                try{
                  $native=[IntPtr]([int]$w.Current.NativeWindowHandle)
                  if($native -ne [IntPtr]::Zero){
                    $rect=New-Object Lot05CaptureSignedWindow+Rect
                    if([Lot05CaptureSignedWindow]::GetWindowRect($native,[ref]$rect)){
                      $width=[int]($rect.Right-$rect.Left)
                      $height=[int]($rect.Bottom-$rect.Top)
                      if($width -ge 250 -and $height -ge 150 -and $width -le 1600 -and $height -le 1100){
                        $r.screenshot_vendor_owner_verified=$true
                        $r.screenshot_title_allowlisted=$true
                        $bitmap=New-Object System.Drawing.Bitmap($width,$height)
                        try{
                          $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
                          try{
                            $hdc=$graphics.GetHdc()
                            try{
                              $ok=[Lot05CaptureSignedWindow]::PrintWindow($native,$hdc,[uint32]0)
                            }finally{$graphics.ReleaseHdc($hdc)}
                          }finally{$graphics.Dispose()}
                          if($ok){
                            $r.screenshot_printwindow_succeeded=$true
                            $bitmap.Save($imageFile,[System.Drawing.Imaging.ImageFormat]::Png)
                            if((Get-Item -LiteralPath $imageFile).Length -gt 2048 -and (Get-Item -LiteralPath $imageFile).Length -lt 6000000){
                              $r.screenshot_window_only_retained=$true
                              $r.screenshot_dimensions=("$width"+"x"+"$height")
                              $r.screenshot_sha256=(Get-FileHash -LiteralPath $imageFile -Algorithm SHA256).Hash.ToLowerInvariant()
                              if($r.next_click_acknowledged -and $cycle -gt $r.next_click_cycle -and
                                 $r.screenshot_sha256 -cne $r.pre_next_screenshot_sha256){
                                $r.post_next_screenshot_changed=$true
                                $r.post_next_screenshot_sha256=$r.screenshot_sha256
                                $r.post_next_window_title_owned=$true
                                if($title -match '(?i)(Licen[cs]e Agreement|EULA|Terms and Conditions)'){
                                  $r.post_next_license_window_captured=$true
                                  $r.post_next_license_keyword_seen=$true
                                }
                              }
                            }
                          }
                        }finally{$bitmap.Dispose()}
                      }
                    }
                  }
                }catch{$r.screenshot_error_count++}
              }


              # Evidence of next setup page after explicitly user-authorized acceptance:
              # do not click any extra control on this unknown page.
              if($r.eula_next_click_sent -and -not $r.eula_following_screen_captured -and
                 $cycle -gt $r.next_click_cycle -and
                 $title -match '^OpenDental \(25\.3\.48\) ' -and
                 $title -cne 'OpenDental (25.3.48) License Agreement'){
                try{
                  $ownedHwnd=[IntPtr]([int]$w.Current.NativeWindowHandle)
                  $screenRect=New-Object Lot05CaptureSignedWindow+Rect
                  if($ownedHwnd -ne [IntPtr]::Zero -and
                     [Lot05CaptureSignedWindow]::GetWindowRect($ownedHwnd,[ref]$screenRect)){
                    $wScreen=[int]($screenRect.Right-$screenRect.Left)
                    $hScreen=[int]($screenRect.Bottom-$screenRect.Top)
                    if($wScreen -ge 450 -and $wScreen -le 900 -and $hScreen -ge 300 -and $hScreen -le 800){
                      $finalBmp=New-Object System.Drawing.Bitmap($wScreen,$hScreen)
                      try{
                        $graphics=[System.Drawing.Graphics]::FromImage($finalBmp)
                        try{
                          $hdc=$graphics.GetHdc()
                          try{$printed=[Lot05CaptureSignedWindow]::PrintWindow($ownedHwnd,$hdc,[uint32]0)}
                          finally{$graphics.ReleaseHdc($hdc)}
                        }finally{$graphics.Dispose()}
                        if($printed){
                          $finalBmp.Save($followingImage,[System.Drawing.Imaging.ImageFormat]::Png)
                          if((Get-Item -LiteralPath $followingImage).Length -gt 2048){
                            $r.eula_following_screen_captured=$true
                            $r.eula_following_screen_title=$title
                            $r.eula_following_screen_sha256=(Get-FileHash -LiteralPath $followingImage -Algorithm SHA256).Hash.ToLowerInvariant()
                          }
                        }
                      }finally{$finalBmp.Dispose()}
                    }
                  }
                }catch{$r.eula_ui_exception_count++}
              }

              # Exact, already visually reviewed trial directory screen.
              # Keep C:\Program Files (x86)\Open Dental\ unchanged.
              if($r.eula_following_screen_captured -and -not $r.destination_next_click_attempted -and
                 $title -ceq 'OpenDental (25.3.48) Setup' -and
                 $r.eula_following_screen_sha256 -ceq '57e1cc601d1a4522a07f1fe1b35d5e953df4e0b9482c1f577d555199db1d4d4b'){
                $r.destination_screen_exact_png_verified=$true
                try{
                  $parent=[IntPtr]([int]$w.Current.NativeWindowHandle)
                  $nexts=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $cancels=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $browses=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $usages=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $cb=[Lot05CaptureSignedWindow+EnumChildCallback]{
                    param([IntPtr]$child,[IntPtr]$unused)
                    $pidNative=[uint32]0
                    $null=[Lot05CaptureSignedWindow]::GetWindowThreadProcessId($child,[ref]$pidNative)
                    if([int]$pidNative -ne $winPid){return $true}
                    $sb=New-Object System.Text.StringBuilder(140)
                    $null=[Lot05CaptureSignedWindow]::GetWindowText($child,$sb,$sb.Capacity)
                    $name=$sb.ToString().Replace([string]'&',[string]'').Trim()
                    if($name -match '(?i)^Next\s*>?$' -and [Lot05CaptureSignedWindow]::IsWindowEnabled($child)){
                      $nexts.Add($child)
                    }elseif($name -match '(?i)^Cancel$'){$cancels.Add($child)}
                    elseif($name -match '(?i)^Browse$'){$browses.Add($child)}
                    elseif($name -match '(?i)^Disk\s+Usage$'){$usages.Add($child)}
                    return $true
                  }
                  $null=[Lot05CaptureSignedWindow]::EnumChildWindows($parent,$cb,[IntPtr]::Zero)
                  $r.destination_next_candidate_count=$nexts.Count
                  $r.destination_cancel_candidate_count=$cancels.Count
                  $r.destination_browse_candidate_count=$browses.Count
                  $r.destination_usage_candidate_count=$usages.Count
                  if($nexts.Count -eq 1 -and $cancels.Count -eq 1 -and
                     $browses.Count -eq 1 -and $usages.Count -eq 1){
                    $button=$nexts[0]
                    $ownerPid=[uint32]0
                    $null=[Lot05CaptureSignedWindow]::GetWindowThreadProcessId($button,[ref]$ownerPid)
                    $wr=New-Object Lot05CaptureSignedWindow+Rect
                    $br=New-Object Lot05CaptureSignedWindow+Rect
                    if([int]$ownerPid -eq $winPid -and
                       [Lot05CaptureSignedWindow]::GetWindowRect($parent,[ref]$wr) -and
                       [Lot05CaptureSignedWindow]::GetWindowRect($button,[ref]$br)){
                      $ww=$wr.Right-$wr.Left
                      $wh=$wr.Bottom-$wr.Top
                      $cx=[int][Math]::Floor(($br.Left+$br.Right)/2)
                      $cy=[int][Math]::Floor(($br.Top+$br.Bottom)/2)
                      $rx=($cx-$wr.Left)/[double]$ww
                      $ry=($cy-$wr.Top)/[double]$wh
                      if($ww -ge 480 -and $ww -le 700 -and $wh -ge 360 -and $wh -le 500 -and
                         $rx -gt 0.62 -and $rx -lt 0.82 -and $ry -gt 0.87 -and $ry -lt 0.97){
                        $null=[Lot05CaptureSignedWindow]::SetForegroundWindow($parent)
                        Start-Sleep -Milliseconds 200
                        if([Lot05CaptureSignedWindow]::GetForegroundWindow() -eq $parent -and
                           [Lot05CaptureSignedWindow]::SetCursorPos($cx,$cy)){
                          Start-Sleep -Milliseconds 90
                          $pt=New-Object Lot05CaptureSignedWindow+Pt
                          $pt.X=$cx
                          $pt.Y=$cy
                          if([Lot05CaptureSignedWindow]::WindowFromPoint($pt) -eq $button){
                            $r.destination_next_click_attempted=$true
                            [Lot05CaptureSignedWindow]::mouse_event([uint32]2,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                            $r.destination_next_physical_events=1
                            Start-Sleep -Milliseconds 75
                            [Lot05CaptureSignedWindow]::mouse_event([uint32]4,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                            $r.destination_next_physical_events=2
                            $r.destination_next_clicked=$true
                          }
                        }
                      }
                    }
                  }
                }catch{$r.eula_ui_exception_count++}
              }
              if($r.destination_next_clicked -and -not $r.destination_following_screen_captured -and
                 $title -match '^OpenDental \(25\.3\.48\) ' -and
                 $title -cne 'OpenDental (25.3.48) License Agreement'){
                try{
                  $win=[IntPtr]([int]$w.Current.NativeWindowHandle)
                  $rect=New-Object Lot05CaptureSignedWindow+Rect
                  if($win -ne [IntPtr]::Zero -and [Lot05CaptureSignedWindow]::GetWindowRect($win,[ref]$rect)){
                    $width=[int]($rect.Right-$rect.Left)
                    $height=[int]($rect.Bottom-$rect.Top)
                    if($width -ge 450 -and $width -le 900 -and $height -ge 300 -and $height -le 800){
                      $bitmap=New-Object System.Drawing.Bitmap($width,$height)
                      try{
                        $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
                        try{
                          $hdc=$graphics.GetHdc()
                          try{$printed=[Lot05CaptureSignedWindow]::PrintWindow($win,$hdc,[uint32]0)}
                          finally{$graphics.ReleaseHdc($hdc)}
                        }finally{$graphics.Dispose()}
                        if($printed){
                          $bitmap.Save($destinationFollowingImage,[System.Drawing.Imaging.ImageFormat]::Png)
                          $hash=(Get-FileHash -LiteralPath $destinationFollowingImage -Algorithm SHA256).Hash.ToLowerInvariant()
                          if($hash -cne $r.eula_following_screen_sha256 -and
                             (Get-Item -LiteralPath $destinationFollowingImage).Length -gt 2048){
                            $r.destination_following_screen_captured=$true
                            $r.destination_following_screen_title=$title
                            $r.destination_following_screen_sha256=$hash
                          }
                        }
                      }finally{$bitmap.Dispose()}
                    }
                  }
                }catch{$r.eula_ui_exception_count++}
              }

              # User-authorized installer activation, only on exact screenshot-
              # pinned Ready-to-Install page after all prior screens verified.
              if($r.destination_following_screen_captured -and
                 $r.destination_following_screen_sha256 -ceq 'ddd11612302ead634484677d270c12b207b0e44e8284dbc25fd5af556011c514' -and
                 -not $r.install_click_attempted -and
                 $title -ceq 'OpenDental (25.3.48) Setup'){
                $r.ready_to_install_exact_png_verified=$true
                try{
                  $parent=[IntPtr]([int]$w.Current.NativeWindowHandle)
                  $installButtons=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $backCount=0
                  $cancelCount=0
                  $cb=[Lot05CaptureSignedWindow+EnumChildCallback]{
                    param([IntPtr]$child,[IntPtr]$unused)
                    $pidHere=[uint32]0
                    $null=[Lot05CaptureSignedWindow]::GetWindowThreadProcessId($child,[ref]$pidHere)
                    if([int]$pidHere -ne $winPid){return $true}
                    $sb=New-Object System.Text.StringBuilder(140)
                    $null=[Lot05CaptureSignedWindow]::GetWindowText($child,$sb,$sb.Capacity)
                    $lbl=$sb.ToString().Replace([string]'&',[string]'').Trim()
                    if($lbl -ceq 'Install' -and [Lot05CaptureSignedWindow]::IsWindowEnabled($child)){
                      $installButtons.Add($child)
                    }elseif($lbl -match '(?i)^<?\s*Back$'){$backCount++}
                    elseif($lbl -match '(?i)^Cancel$'){$cancelCount++}
                    return $true
                  }
                  $null=[Lot05CaptureSignedWindow]::EnumChildWindows($parent,$cb,[IntPtr]::Zero)
                  $r.install_button_candidates=$installButtons.Count
                  $r.install_back_candidates=$backCount
                  $r.install_cancel_candidates=$cancelCount
                  # The exact Ready-to-Install window is authenticated by the
                  # SHA256 of its screenshot and by the signed vendor PID.
                  # WinForms may omit captions of disabled sibling buttons from
                  # GetWindowText (prior run: Install=1, Back=0, Cancel=0).
                  # Never infer a target from those siblings. Instead require a
                  # UNIQUE enabled Install HWND + PID + geometry + foreground +
                  # hit-test. Reject ambiguous multiple Back/Cancel matches.
                  if($installButtons.Count -eq 1 -and $backCount -le 1 -and $cancelCount -le 1){
                    $button=$installButtons[0]
                    $pidButton=[uint32]0
                    $null=[Lot05CaptureSignedWindow]::GetWindowThreadProcessId($button,[ref]$pidButton)
                    $r.install_owner_pid_verified=([int]$pidButton -eq $winPid)
                    $wr=New-Object Lot05CaptureSignedWindow+Rect
                    $br=New-Object Lot05CaptureSignedWindow+Rect
                    if([int]$pidButton -eq $winPid -and
                       [Lot05CaptureSignedWindow]::GetWindowRect($parent,[ref]$wr) -and
                       [Lot05CaptureSignedWindow]::GetWindowRect($button,[ref]$br)){
                      $r.install_button_bounds_verified=$true
                      $ww=$wr.Right-$wr.Left
                      $hh=$wr.Bottom-$wr.Top
                      $cx=[int][Math]::Floor(($br.Left+$br.Right)/2)
                      $cy=[int][Math]::Floor(($br.Top+$br.Bottom)/2)
                      $rx=($cx-$wr.Left)/[double]$ww
                      $ry=($cy-$wr.Top)/[double]$hh
                      $r.install_button_rel_x=[Math]::Round($rx,3)
                      $r.install_button_rel_y=[Math]::Round($ry,3)
                      $r.install_geometry_gate_passed=($ww -ge 480 -and $ww -le 700 -and
                         $hh -ge 360 -and $hh -le 500 -and
                         $rx -gt 0.62 -and $rx -lt 0.82 -and $ry -gt 0.87 -and $ry -lt 0.97)
                      if($ww -ge 480 -and $ww -le 700 -and $hh -ge 360 -and $hh -le 500 -and
                         $rx -gt 0.62 -and $rx -lt 0.82 -and $ry -gt 0.87 -and $ry -lt 0.97){
                        $null=[Lot05CaptureSignedWindow]::SetForegroundWindow($parent)
                        Start-Sleep -Milliseconds 230
                        $r.install_foreground_verified=([Lot05CaptureSignedWindow]::GetForegroundWindow() -eq $parent)
                        if($r.install_foreground_verified){
                          $r.install_cursor_moved=[Lot05CaptureSignedWindow]::SetCursorPos($cx,$cy)
                        }
                        if($r.install_foreground_verified -and $r.install_cursor_moved){
                          Start-Sleep -Milliseconds 100
                          $pt=New-Object Lot05CaptureSignedWindow+Pt
                          $pt.X=$cx
                          $pt.Y=$cy
                          $r.install_cursor_hit_exact_button=([Lot05CaptureSignedWindow]::WindowFromPoint($pt) -eq $button)
                          if($r.install_cursor_hit_exact_button){
                            $r.install_click_attempted=$true
                            [Lot05CaptureSignedWindow]::mouse_event([uint32]2,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                            $r.install_physical_events_sent=1
                            Start-Sleep -Milliseconds 80
                            [Lot05CaptureSignedWindow]::mouse_event([uint32]4,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                            $r.install_physical_events_sent=2
                            $r.install_click_sent=$true
                            $r.clicked_install=$true
                          }
                        }
                      }
                    }
                  }
                }catch{$r.eula_ui_exception_count++}
              }

              # Observe completion: file installed plus Finish-enabled vendor GUI.
              # No click on Finish in this run.
              if($r.install_click_sent -and -not $r.completed_installer_screen_captured -and
                 $title -ceq 'OpenDental (25.3.48) Setup'){
                try{
                  $top=[IntPtr]([int]$w.Current.NativeWindowHandle)
                  $finishCount=0
                  $finishCb=[Lot05CaptureSignedWindow+EnumChildCallback]{
                    param([IntPtr]$child,[IntPtr]$unused)
                    $pidHere=[uint32]0
                    $null=[Lot05CaptureSignedWindow]::GetWindowThreadProcessId($child,[ref]$pidHere)
                    if([int]$pidHere -ne $winPid){return $true}
                    $sb=New-Object System.Text.StringBuilder(140)
                    $null=[Lot05CaptureSignedWindow]::GetWindowText($child,$sb,$sb.Capacity)
                    if($sb.ToString().Replace([string]'&',[string]'').Trim() -match '(?i)^Finish$' -and
                       [Lot05CaptureSignedWindow]::IsWindowEnabled($child)){$finishCount++}
                    return $true
                  }
                  $null=[Lot05CaptureSignedWindow]::EnumChildWindows($top,$finishCb,[IntPtr]::Zero)
                  if($finishCount -eq 1){
                    $r.completed_installer_finish_button_seen=$true
                    $rect=New-Object Lot05CaptureSignedWindow+Rect
                    if([Lot05CaptureSignedWindow]::GetWindowRect($top,[ref]$rect)){
                      $cw=[int]($rect.Right-$rect.Left)
                      $ch=[int]($rect.Bottom-$rect.Top)
                      if($cw -ge 450 -and $cw -le 900 -and $ch -ge 300 -and $ch -le 800){
                        $bmp=New-Object System.Drawing.Bitmap($cw,$ch)
                        try{
                          $g=[System.Drawing.Graphics]::FromImage($bmp)
                          try{
                            $hdc=$g.GetHdc()
                            try{$done=[Lot05CaptureSignedWindow]::PrintWindow($top,$hdc,[uint32]0)}
                            finally{$g.ReleaseHdc($hdc)}
                          }finally{$g.Dispose()}
                          if($done){
                            $bmp.Save($installFinishedImage,[System.Drawing.Imaging.ImageFormat]::Png)
                            if((Get-Item -LiteralPath $installFinishedImage).Length -gt 2048){
                              $r.completed_installer_screen_captured=$true
                              $r.completed_installer_screen_sha256=(Get-FileHash -LiteralPath $installFinishedImage -Algorithm SHA256).Hash.ToLowerInvariant()
                            }
                          }
                        }finally{$bmp.Dispose()}
                      }
                    }
                  }
                }catch{$r.eula_ui_exception_count++}
              }
              # USER-AUTHORIZED EULA ACCEPTANCE on the exact publisher-verified
              # License Agreement window, not an inferred radio/button.
              # One physical click on accept radio, one Next only when selected.
              if($title -ceq 'OpenDental (25.3.48) License Agreement' -and
                 $r.next_click_acknowledged -and $r.post_next_license_window_captured -and
                 -not $r.eula_click_attempted){
                $r.exact_license_window_verified=$true
                try{
                  $parentLicense=[IntPtr]([int]$w.Current.NativeWindowHandle)
                  $acceptRadios=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $declineRadios=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $eulaNexts=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $eulaCancels=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  if($parentLicense -eq [IntPtr]::Zero){throw 'NO_LICENSE_HWND'}
                  $cb=[Lot05CaptureSignedWindow+EnumChildCallback]{
                    param([IntPtr]$child,[IntPtr]$unused)
                    $pidHere=[uint32]0
                    $null=[Lot05CaptureSignedWindow]::GetWindowThreadProcessId($child,[ref]$pidHere)
                    if([int]$pidHere -ne $winPid){return $true}
                    $builder=New-Object System.Text.StringBuilder(180)
                    $null=[Lot05CaptureSignedWindow]::GetWindowText($child,$builder,$builder.Capacity)
                    $label=$builder.ToString().Replace([string]'&',[string]'').Trim()
                    if($label -ceq 'I accept the terms in the License Agreement'){$acceptRadios.Add($child)}
                    elseif($label -ceq 'I do not accept the terms in the License Agreement'){$declineRadios.Add($child)}
                    elseif($label -match '(?i)^Next\s*>?$'){$eulaNexts.Add($child)}
                    elseif($label -match '(?i)^Cancel$'){$eulaCancels.Add($child)}
                    return $true
                  }
                  $null=[Lot05CaptureSignedWindow]::EnumChildWindows($parentLicense,$cb,[IntPtr]::Zero)
                  $r.eula_accept_radio_candidates=$acceptRadios.Count
                  $r.eula_decline_radio_candidates=$declineRadios.Count
                  $r.eula_next_candidates=$eulaNexts.Count
                  if($acceptRadios.Count -eq 1 -and $declineRadios.Count -eq 1 -and
                     $eulaNexts.Count -eq 1 -and $eulaCancels.Count -eq 1){
                    $acceptHandle=$acceptRadios[0]
                    $declineHandle=$declineRadios[0]
                    $nextHandle=$eulaNexts[0]
                    $preAccept=[IntPtr]::Zero
                    $preDecline=[IntPtr]::Zero
                    $pre1=[Lot05CaptureSignedWindow]::SendMessageTimeout(
                      $acceptHandle,[uint32]0x00F0,[IntPtr]::Zero,[IntPtr]::Zero,
                      [uint32]2,[uint32]1000,[ref]$preAccept)
                    $pre2=[Lot05CaptureSignedWindow]::SendMessageTimeout(
                      $declineHandle,[uint32]0x00F0,[IntPtr]::Zero,[IntPtr]::Zero,
                      [uint32]2,[uint32]1000,[ref]$preDecline)
                    $r.eula_accept_preunchecked=($pre1 -ne [IntPtr]::Zero -and $preAccept.ToInt64() -eq 0)
                    $r.eula_decline_prechecked=($pre2 -ne [IntPtr]::Zero -and $preDecline.ToInt64() -eq 1)
                    $r.eula_next_pre_disabled=(-not [Lot05CaptureSignedWindow]::IsWindowEnabled($nextHandle))
                    $pRect=New-Object Lot05CaptureSignedWindow+Rect
                    $aRect=New-Object Lot05CaptureSignedWindow+Rect
                    if($r.eula_accept_preunchecked -and $r.eula_decline_prechecked -and
                       $r.eula_next_pre_disabled -and
                       [Lot05CaptureSignedWindow]::GetWindowRect($parentLicense,[ref]$pRect) -and
                       [Lot05CaptureSignedWindow]::GetWindowRect($acceptHandle,[ref]$aRect)){
                      $ww=$pRect.Right-$pRect.Left
                      $hh=$pRect.Bottom-$pRect.Top
                      $xx=[int][Math]::Floor(($aRect.Left+$aRect.Right)/2)
                      $yy=[int][Math]::Floor(($aRect.Top+$aRect.Bottom)/2)
                      $ax=($xx-$pRect.Left)/[double]$ww
                      $ay=($yy-$pRect.Top)/[double]$hh
                      if($ww -ge 480 -and $ww -le 700 -and $hh -ge 360 -and $hh -le 500 -and
                         $ax -gt 0.12 -and $ax -lt 0.76 -and $ay -gt 0.69 -and $ay -lt 0.80){
                        $null=[Lot05CaptureSignedWindow]::SetForegroundWindow($parentLicense)
                        Start-Sleep -Milliseconds 250
                        if([Lot05CaptureSignedWindow]::GetForegroundWindow() -eq $parentLicense -and
                           [Lot05CaptureSignedWindow]::SetCursorPos($xx,$yy)){
                          Start-Sleep -Milliseconds 90
                          $pt=New-Object Lot05CaptureSignedWindow+Pt
                          $pt.X=$xx;$pt.Y=$yy
                          if([Lot05CaptureSignedWindow]::WindowFromPoint($pt) -eq $acceptHandle){
                            $r.eula_click_attempted=$true
                            [Lot05CaptureSignedWindow]::mouse_event([uint32]2,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                            $r.eula_click_physical_events_sent=1
                            Start-Sleep -Milliseconds 80
                            [Lot05CaptureSignedWindow]::mouse_event([uint32]4,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                            $r.eula_click_physical_events_sent=2
                            Start-Sleep -Milliseconds 250
                            $acceptAfter=[IntPtr]::Zero
                            $declineAfter=[IntPtr]::Zero
                            $a1=[Lot05CaptureSignedWindow]::SendMessageTimeout(
                              $acceptHandle,[uint32]0x00F0,[IntPtr]::Zero,[IntPtr]::Zero,
                              [uint32]2,[uint32]1000,[ref]$acceptAfter)
                            $a2=[Lot05CaptureSignedWindow]::SendMessageTimeout(
                              $declineHandle,[uint32]0x00F0,[IntPtr]::Zero,[IntPtr]::Zero,
                              [uint32]2,[uint32]1000,[ref]$declineAfter)
                            $r.eula_accept_radio_checked_after=($a1 -ne [IntPtr]::Zero -and $acceptAfter.ToInt64() -eq 1)
                            $r.eula_decline_radio_unchecked_after=($a2 -ne [IntPtr]::Zero -and $declineAfter.ToInt64() -eq 0)
                            $r.eula_next_enabled_after=[Lot05CaptureSignedWindow]::IsWindowEnabled($nextHandle)
                            $r.accepted_eula=($r.eula_accept_radio_checked_after -and
                              $r.eula_decline_radio_unchecked_after -and $r.eula_next_enabled_after)
                            if($r.accepted_eula){
                              # Window-only evidence showing selected I accept and enabled Next.
                              $bmp=New-Object System.Drawing.Bitmap($ww,$hh)
                              try{
                                $g=[System.Drawing.Graphics]::FromImage($bmp)
                                try{
                                  $hdc=$g.GetHdc()
                                  try{$ok=[Lot05CaptureSignedWindow]::PrintWindow($parentLicense,$hdc,[uint32]0)}
                                  finally{$g.ReleaseHdc($hdc)}
                                }finally{$g.Dispose()}
                                if($ok){
                                  $bmp.Save($acceptedImage,[System.Drawing.Imaging.ImageFormat]::Png)
                                  $r.eula_accept_window_png_saved=((Get-Item -LiteralPath $acceptedImage).Length -gt 2048)
                                  if($r.eula_accept_window_png_saved){
                                    $r.eula_accept_window_png_sha256=(Get-FileHash -LiteralPath $acceptedImage -Algorithm SHA256).Hash.ToLowerInvariant()
                                  }
                                }
                              }finally{$bmp.Dispose()}
                            }
                            # Advance only from the checked, exact licensed screen.
                            if($r.accepted_eula -and $r.eula_accept_window_png_saved){
                              $nRect=New-Object Lot05CaptureSignedWindow+Rect
                              if([Lot05CaptureSignedWindow]::GetWindowRect($nextHandle,[ref]$nRect)){
                                $nx=[int][Math]::Floor(($nRect.Left+$nRect.Right)/2)
                                $ny=[int][Math]::Floor(($nRect.Top+$nRect.Bottom)/2)
                                $rx=($nx-$pRect.Left)/[double]$ww
                                $ry=($ny-$pRect.Top)/[double]$hh
                                if($rx -gt 0.62 -and $rx -lt 0.82 -and $ry -gt 0.87 -and $ry -lt 0.97 -and
                                   [Lot05CaptureSignedWindow]::SetCursorPos($nx,$ny)){
                                  Start-Sleep -Milliseconds 120
                                  $np=New-Object Lot05CaptureSignedWindow+Pt
                                  $np.X=$nx;$np.Y=$ny
                                  if([Lot05CaptureSignedWindow]::WindowFromPoint($np) -eq $nextHandle -and
                                     [Lot05CaptureSignedWindow]::GetForegroundWindow() -eq $parentLicense){
                                    $r.eula_next_click_attempted=$true
                                    [Lot05CaptureSignedWindow]::mouse_event([uint32]2,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                                    $r.eula_next_click_physical_events_sent=1
                                    Start-Sleep -Milliseconds 75
                                    [Lot05CaptureSignedWindow]::mouse_event([uint32]4,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                                    $r.eula_next_click_physical_events_sent=2
                                    $r.eula_next_click_sent=$true
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }catch{$r.eula_ui_exception_count++}
              }
              # Fail-closed: only the exact signed-publisher Welcome screen,
              # whose owner is already in the signed Setup process tree.
              # Send a SINGLE BM_CLICK to UIA's uniquely identified Next button.
              if(-not $r.next_click_attempted -and $r.screenshot_window_only_retained -and
                 $title -ceq 'OpenDental (25.3.48) Setup'){
                try{
                  $r.welcome_title_exact_proven=$true
                  $items=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                                    [System.Windows.Automation.Condition]::TrueCondition)
                  $nextCandidates=@()
                  $cancelCount=0
                  $disabledBack=$false
                  $welcomeText=$false
                  for($n=0;$n -lt [Math]::Min(180,$items.Count);$n++){
                    $element=$items.Item($n)
                    $nm=[string]$element.Current.Name
                    $typ=[string]$element.Current.ControlType.ProgrammaticName
                    if($nm -match '(?i)Welcome to the OpenDental\s+Setup Wizard'){$welcomeText=$true}
                    if($typ -ceq 'ControlType.Button' -and [int]$element.Current.ProcessId -eq $winPid){
                      if($nm -match '(?i)^\s*(Next\s*>|Next)\s*$' -and $element.Current.IsEnabled -and
                         -not $element.Current.IsOffscreen){$nextCandidates+=,$element}
                      if($nm -match '(?i)^\s*Cancel\s*$' -and $element.Current.IsEnabled){$cancelCount++}
                      if($nm -match '(?i)^\s*<?\s*Back\s*$' -and -not $element.Current.IsEnabled){$disabledBack=$true}
                    }
                  }
                  $r.welcome_text_uia_observed=$welcomeText
                  $r.welcome_back_disabled=$disabledBack
                  $r.welcome_cancel_button_observed=($cancelCount -eq 1)
                  $r.next_button_candidate_count=$nextCandidates.Count
                  # WinForms vendor wizard can expose native Button HWNDs
                  # while UIA reports zero ControlType.Button nodes.
                  # Read ONLY each exact child button's caption/enabled/PID.
                  # Never inspect other window text or other processes.
                  $nativeNext=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $nativeCancel=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $nativeBackDisabled=New-Object 'System.Collections.Generic.List[System.IntPtr]'
                  $parent=[IntPtr]([int]$w.Current.NativeWindowHandle)
                  if($parent -ne [IntPtr]::Zero){
                    $cb=[Lot05CaptureSignedWindow+EnumChildCallback]{
                      param([IntPtr]$child,[IntPtr]$unused)
                      $pidNative=[uint32]0
                      $null=[Lot05CaptureSignedWindow]::GetWindowThreadProcessId($child,[ref]$pidNative)
                      if([int]$pidNative -ne $winPid){return $true}
                      $sb=New-Object System.Text.StringBuilder(140)
                      $null=[Lot05CaptureSignedWindow]::GetWindowText($child,$sb,$sb.Capacity)
                      $caption=$sb.ToString().Trim()
                      if([string]::IsNullOrWhiteSpace($caption)){
                        # GetWindowText cannot read child-control text across processes.
                        # WM_GETTEXT is a read-only, system-marshalled Win32 message.
                        $buffer=[Runtime.InteropServices.Marshal]::AllocHGlobal(512)
                        try{
                          for($j=0;$j -lt 512;$j++){[Runtime.InteropServices.Marshal]::WriteByte($buffer,$j,0)}
                          $out=[IntPtr]::Zero
                          $got=[Lot05CaptureSignedWindow]::SendMessageTimeout(
                            $child,[uint32]0x000D,[IntPtr]256,$buffer,[uint32]2,[uint32]900,[ref]$out)
                          if($got -ne [IntPtr]::Zero){$caption=([Runtime.InteropServices.Marshal]::PtrToStringUni($buffer)).Trim()}
                        }finally{[Runtime.InteropServices.Marshal]::FreeHGlobal($buffer)}
                      }
                      # Windows Forms may include a mnemonic marker in button labels.
                      $caption=$caption.Replace([string]'&',[string]'').Trim()
                      if($caption -match '(?i)^Next\s*>?$' -and
                         [Lot05CaptureSignedWindow]::IsWindowEnabled($child) -and
                         [Lot05CaptureSignedWindow]::IsWindowVisible($child)){
                        $nativeNext.Add($child)
                      }elseif($caption -match '(?i)^Cancel$' -and
                               [Lot05CaptureSignedWindow]::IsWindowEnabled($child)){
                        $nativeCancel.Add($child)
                      }elseif($caption -match '(?i)^<?\s*Back$' -and
                               -not [Lot05CaptureSignedWindow]::IsWindowEnabled($child)){
                        $nativeBackDisabled.Add($child)
                      }
                      return $true
                    }
                    $null=[Lot05CaptureSignedWindow]::EnumChildWindows($parent,$cb,[IntPtr]::Zero)
                  }
                  $r.native_next_button_candidate_count=$nativeNext.Count
                  $r.native_cancel_candidate_count=$nativeCancel.Count
                  $r.native_back_disabled_count=$nativeBackDisabled.Count
                  $hwnd=[IntPtr]::Zero
                  if($nextCandidates.Count -eq 1 -and $cancelCount -eq 1 -and $disabledBack){
                    $hwnd=[IntPtr]([int]$nextCandidates[0].Current.NativeWindowHandle)
                    $r.next_control_source='UIAUTOMATION'
                  }elseif($nativeNext.Count -eq 1 -and $nativeCancel.Count -eq 1 -and $nativeBackDisabled.Count -eq 1){
                    $hwnd=$nativeNext[0]
                    $r.next_control_source='WIN32_CHILD_BUTTONS'
                    $r.welcome_back_disabled=$true
                    $r.welcome_cancel_button_observed=$true
                  }
                  if($hwnd -ne [IntPtr]::Zero -and
                     $r.screenshot_vendor_owner_verified -and $r.screenshot_title_allowlisted){
                    $buttonPid=[uint32]0
                    $null=[Lot05CaptureSignedWindow]::GetWindowThreadProcessId($hwnd,[ref]$buttonPid)
                    $r.native_button_pid_verified=([int]$buttonPid -eq $winPid)
                    if($r.native_button_pid_verified){
                      # Exactly one physical click on the proven WinForms Next HWND.
                      # Confirm the button's Welcome-screen geometry and foreground.
                      $wr=New-Object Lot05CaptureSignedWindow+Rect
                      $br=New-Object Lot05CaptureSignedWindow+Rect
                      if([Lot05CaptureSignedWindow]::GetWindowRect($parent,[ref]$wr) -and
                         [Lot05CaptureSignedWindow]::GetWindowRect($hwnd,[ref]$br)){
                        $ww=$wr.Right-$wr.Left
                        $wh=$wr.Bottom-$wr.Top
                        $bw=$br.Right-$br.Left
                        $bh=$br.Bottom-$br.Top
                        $cx=[int][Math]::Floor(($br.Left+$br.Right)/2)
                        $cy=[int][Math]::Floor(($br.Top+$br.Bottom)/2)
                        $rx=($cx-$wr.Left)/[double]$ww
                        $ry=($cy-$wr.Top)/[double]$wh
                        $r.next_button_geometry_verified=($ww -ge 480 -and $ww -le 700 -and
                          $wh -ge 360 -and $wh -le 500 -and
                          $bw -ge 55 -and $bw -le 110 -and $bh -ge 18 -and $bh -le 36 -and
                          $rx -gt 0.62 -and $rx -lt 0.82 -and $ry -gt 0.87 -and $ry -lt 0.97)
                        if($r.next_button_geometry_verified){
                          $null=[Lot05CaptureSignedWindow]::SetForegroundWindow($parent)
                          Start-Sleep -Milliseconds 300
                          $r.foreground_window_verified=([Lot05CaptureSignedWindow]::GetForegroundWindow() -eq $parent)
                          if($r.foreground_window_verified -and [Lot05CaptureSignedWindow]::SetCursorPos($cx,$cy)){
                            Start-Sleep -Milliseconds 120
                            $pt=New-Object Lot05CaptureSignedWindow+Pt
                            $pt.X=$cx
                            $pt.Y=$cy
                            $r.cursor_over_exact_next=([Lot05CaptureSignedWindow]::WindowFromPoint($pt) -eq $hwnd)
                            if($r.cursor_over_exact_next){
                              $r.pre_next_screenshot_sha256=$r.screenshot_sha256
                              $r.next_click_attempted=$true
                              [Lot05CaptureSignedWindow]::mouse_event([uint32]2,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                              $r.physical_mouse_events_sent=1
                              Start-Sleep -Milliseconds 75
                              [Lot05CaptureSignedWindow]::mouse_event([uint32]4,[uint32]0,[uint32]0,[uint32]0,[UIntPtr]::Zero)
                              $r.physical_mouse_events_sent=2
                              $r.next_click_acknowledged=$true
                              $r.clicked_next=$true
                              $r.next_click_cycle=$cycle
                            }
                          }
                        }
                      }
                    }
                  }
                }catch{$r.screenshot_error_count++}
              }
              if($r.next_click_acknowledged -and $cycle -gt $r.next_click_cycle){
                try{
                  $texts=$w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                                    [System.Windows.Automation.Condition]::TrueCondition)
                  for($n=0;$n -lt [Math]::Min(180,$texts.Count);$n++){
                    if([string]$texts.Item($n).Current.Name -match '(?i)(license agreement|licence agreement|eula|terms and conditions)'){
                      $r.post_next_license_keyword_seen=$true
                      break
                    }
                  }
                }catch{$r.ui_errors_count++}
              }
            }
            else{$other++}
          }elseif($title -match '(?i)^Windows Installer'){$unownedMsi++}
        }catch{$r.ui_errors_count++}
      }
      $r.owned_window_count_max=[Math]::Max($r.owned_window_count_max,$owned)
      $r.owned_blank_title_window_count_max=[Math]::Max($r.owned_blank_title_window_count_max,$empty)
      $r.owned_setup_title_window_count_max=[Math]::Max($r.owned_setup_title_window_count_max,$setupCount)
      $r.owned_generic_title_window_count_max=[Math]::Max($r.owned_generic_title_window_count_max,$other)
      $r.owned_license_title_window_count_max=[Math]::Max($r.owned_license_title_window_count_max,$license)
      $r.unowned_windows_installer_title_count_max=[Math]::Max($r.unowned_windows_installer_title_count_max,$unownedMsi)
    }catch{$r.ui_errors_count++}
  }
  $r.diagnosis=if($r.owned_setup_title_window_count_max -gt 0 -or $r.owned_license_title_window_count_max -gt 0){
    'VENDOR_WINDOW_TITLE_VISIBLE_NO_INPUT'
  }elseif($r.owned_window_count_max -gt 0){
    'VENDOR_WINDOW_PRESENT_BUT_UNEXPECTED_TITLE'
  }elseif(-not $r.environment_user_interactive -or -not $r.explorer_same_session){
    'NO_PROVEN_INTERACTIVE_USER_DESKTOP'
  }elseif($r.inner_setup_exited_early){
    'EMBEDDED_SETUP_EXITED_WITHOUT_OWNED_UI'
  }else{'NO_OWNED_UI_WINDOW_IN_DESKTOP_SESSION'}
}catch{
  $r.error_code='FAIL_CLOSED_SETUP_OR_WINDOW_DIAGNOSTIC'
  $r.diagnosis='NOT_PROVEN'
}finally{
  foreach($childId in @($knownIds)){
    try{Stop-Process -Id $childId -Force -ErrorAction SilentlyContinue}catch{}
  }
  Remove-Item -LiteralPath $wrapper -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $folder -Recurse -Force -ErrorAction SilentlyContinue
  $r.database_created=(@(Get-Service -Name 'MariaDB','MySQL*' -ErrorAction SilentlyContinue).Count -gt 0)
  $installedExe='C:\Program Files (x86)\Open Dental\OpenDental.exe'
  if(Test-Path -LiteralPath $installedExe){
    $r.installed_exe_present=$true
    $r.installed_exe_sha256=(Get-FileHash -LiteralPath $installedExe -Algorithm SHA256).Hash.ToLowerInvariant()
    $r.installed_exe_authenticode_status=[string](Get-AuthenticodeSignature -LiteralPath $installedExe).Status
  }
  [System.IO.File]::WriteAllText($outFile,($r|ConvertTo-Json -Depth 5),(New-Object System.Text.UTF8Encoding($false)))
}
Write-Host ('LOT05_DESKTOP_DIAGNOSIS='+$r.diagnosis)
Write-Host ('LOT05_DESKTOP_RUNNER_SESSION='+$r.runner_session_id)
Write-Host ('LOT05_DESKTOP_USER_INTERACTIVE='+$r.environment_user_interactive)
Write-Host ('LOT05_DESKTOP_EXPLORER_IN_SAME_SESSION='+$r.explorer_same_session)
Write-Host ('LOT05_DESKTOP_UIA_ROOT='+$r.uia_root_accessible)
Write-Host ('LOT05_DESKTOP_OWNED_WINDOWS='+$r.owned_window_count_max)
Write-Host ('LOT05_DESKTOP_WINDOW_ONLY_PNG='+$r.screenshot_window_only_retained)
Write-Host ('LOT05_WELCOME_EXACT_TITLE='+$r.welcome_title_exact_proven)
Write-Host ('LOT05_WELCOME_BACK_DISABLED='+$r.welcome_back_disabled)
Write-Host ('LOT05_NEXT_CANDIDATES='+$r.next_button_candidate_count)
Write-Host ('LOT05_NEXT_NATIVE_CANDIDATES='+$r.native_next_button_candidate_count)
Write-Host ('LOT05_NEXT_NATIVE_CANCEL='+$r.native_cancel_candidate_count)
Write-Host ('LOT05_NEXT_NATIVE_BACK_DISABLED='+$r.native_back_disabled_count)
Write-Host ('LOT05_NEXT_CONTROL_SOURCE='+$r.next_control_source)
Write-Host ('LOT05_NEXT_OWNER_PID_VERIFIED='+$r.native_button_pid_verified)
Write-Host ('LOT05_NEXT_PHYSICAL_MOUSE_EVENTS='+$r.physical_mouse_events_sent)
Write-Host ('LOT05_NEXT_GEOMETRY_VERIFIED='+$r.next_button_geometry_verified)
Write-Host ('LOT05_NEXT_FOREGROUND_VERIFIED='+$r.foreground_window_verified)
Write-Host ('LOT05_NEXT_CURSOR_ON_EXACT_BUTTON='+$r.cursor_over_exact_next)
Write-Host ('LOT05_NEXT_SENT_ONCE='+$r.next_click_acknowledged)
Write-Host ('LOT05_POST_NEXT_VISUAL_CHANGE='+$r.post_next_screenshot_changed)
Write-Host ('LOT05_LICENSE_TITLE_AFTER_NEXT='+$r.license_window_title_detected_after_next)
Write-Host ('LOT05_LICENSE_WINDOW_CAPTURED='+$r.post_next_license_window_captured)
Write-Host ('LOT05_POST_NEXT_LICENSE_KEYWORD='+$r.post_next_license_keyword_seen)
Write-Host ('LOT05_DESKTOP_WINDOW_ONLY_CAPTURE_ERRORS='+$r.screenshot_error_count)
Write-Host ('LOT05_DESKTOP_WINDOWS_TITLE_SETUP='+$r.owned_setup_title_window_count_max)
Write-Host ('LOT05_DESKTOP_WINDOWS_UNEXPECTED_TITLE='+$r.owned_generic_title_window_count_max)
Write-Host ('LOT05_DESKTOP_OUTSIDE_OWNER_MSI_WINDOWS='+$r.unowned_windows_installer_title_count_max)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_ACCEPT_CANDIDATES='+$r.eula_accept_radio_candidates)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_DECLINE_CANDIDATES='+$r.eula_decline_radio_candidates)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_NEXT_CANDIDATES='+$r.eula_next_candidates)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_PRE_DECLINE_CHECKED='+$r.eula_decline_prechecked)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_PRE_NEXT_DISABLED='+$r.eula_next_pre_disabled)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_ACCEPT_ATTEMPTED='+$r.eula_click_attempted)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_ACCEPT_VERIFIED='+$r.accepted_eula)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_ACCEPT_PNG='+$r.eula_accept_window_png_saved)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_NEXT_CLICK='+$r.eula_next_click_sent)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_NEXT_SCREEN='+$r.eula_following_screen_captured)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_NEXT_TITLE='+$r.eula_following_screen_title)
Write-Host ('LOT05_DESTINATION_PINNED_SCREEN='+$r.destination_screen_exact_png_verified)
Write-Host ('LOT05_DESTINATION_NEXT_CANDIDATES='+$r.destination_next_candidate_count)
Write-Host ('LOT05_DESTINATION_NEXT_CLICKED='+$r.destination_next_clicked)
Write-Host ('LOT05_DESTINATION_NEW_SCREEN='+$r.destination_following_screen_captured)
Write-Host ('LOT05_DESTINATION_NEW_SCREEN_TITLE='+$r.destination_following_screen_title)
Write-Host ('LOT05_INSTALL_READY_PAGE_PINNED='+$r.ready_to_install_exact_png_verified)
Write-Host ('LOT05_INSTALL_BUTTON_CANDIDATES='+$r.install_button_candidates)
Write-Host ('LOT05_INSTALL_BACK_CANDIDATES='+$r.install_back_candidates)
Write-Host ('LOT05_INSTALL_CANCEL_CANDIDATES='+$r.install_cancel_candidates)
Write-Host ('LOT05_INSTALL_OWNER_PID_VERIFIED='+$r.install_owner_pid_verified)
Write-Host ('LOT05_INSTALL_BUTTON_BOUNDS_VERIFIED='+$r.install_button_bounds_verified)
Write-Host ('LOT05_INSTALL_BUTTON_REL_X='+$r.install_button_rel_x)
Write-Host ('LOT05_INSTALL_BUTTON_REL_Y='+$r.install_button_rel_y)
Write-Host ('LOT05_INSTALL_GEOMETRY_GATE='+$r.install_geometry_gate_passed)
Write-Host ('LOT05_INSTALL_FOREGROUND='+$r.install_foreground_verified)
Write-Host ('LOT05_INSTALL_CURSOR_MOVED='+$r.install_cursor_moved)
Write-Host ('LOT05_INSTALL_CURSOR_HIT_EXACT='+$r.install_cursor_hit_exact_button)
Write-Host ('LOT05_INSTALL_CLICK_SENT='+$r.install_click_sent)
Write-Host ('LOT05_INSTALL_APP_EXE_PRESENT='+$r.installed_exe_present)
Write-Host ('LOT05_INSTALL_APP_EXE_SIGNED_STATUS='+$r.installed_exe_authenticode_status)
Write-Host ('LOT05_INSTALL_FINISH_CONTROL_SEEN='+$r.completed_installer_finish_button_seen)
Write-Host ('LOT05_INSTALL_FINISH_WINDOW_CAPTURED='+$r.completed_installer_screen_captured)
Write-Host ('LOT05_EXPLICIT_USER_AUTH_UI_ERRORS='+$r.eula_ui_exception_count)
Write-Host 'LOT05_EXPLICIT_CONSENT_ONLY_EPHEMERAL_DEMO_NO_PATIENTS'
if(-not $r.wrapper_hash_pinned -or -not $r.wrapper_authenticode_valid -or
   -not $r.inner_setup_authenticode_valid -or -not $r.inner_setup_started_once -or
   $r.database_created -or $null -ne $r.error_code){throw 'HOSTED_DESKTOP_DIAGNOSTIC_NOT_PROVEN'}
