# LOT05: official Open Dental trial SERVER orchestrator GUI, NO GUI INPUT.
$ErrorActionPreference='Stop'
$wrapper=Join-Path $env:RUNNER_TEMP 'lot05_publisher_trial.exe'
$extract=Join-Path $env:RUNNER_TEMP 'lot05_publisher_archive'
$json=Join-Path $env:RUNNER_TEMP 'lot05_server_launcher_readonly.json'
$png=Join-Path $env:RUNNER_TEMP 'lot05_server_launcher_window.png'
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
  clicked_install=$false
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
  $innerSig=Get-AuthenticodeSignature -LiteralPath $exe
  $r.embedded_launcher_signature=[string]$innerSig.Status
  if($innerSig.Status -notin @([System.Management.Automation.SignatureStatus]::Valid,[System.Management.Automation.SignatureStatus]::NotSigned)){throw 'INNER_SIGNATURE_NOT_TRUSTED'}
  $proc=Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe) -PassThru -ErrorAction Stop
  $r.embedded_launcher_started=$true
  $null=$ids.Add([int]$proc.Id)
  $r.session_verified=($proc.SessionId -eq [System.Diagnostics.Process]::GetCurrentProcess().SessionId)
  if(-not $r.session_verified){throw 'SESSION_NOT_INTERACTIVE'}
  for($cycle=0;$cycle -lt 65;$cycle++){
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
      }catch{$r.uia_errors++}
    }
    if($r.vendor_window_capture_ok){break}
  }
}catch{
  $r.error_code='READONLY_VENDOR_SERVER_ORCHESTRATOR_FAIL_CLOSED'
}finally{
  foreach($childProcessId in @($ids)){try{Stop-Process -Id $childProcessId -Force -ErrorAction SilentlyContinue}catch{}}
  Remove-Item -LiteralPath $wrapper -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $extract -Recurse -Force -ErrorAction SilentlyContinue
  $r.created_database=(@(Get-Service -Name 'MariaDB','MySQL*' -ErrorAction SilentlyContinue).Count -gt 0)
  [System.IO.File]::WriteAllText($json,($r|ConvertTo-Json -Depth 4),(New-Object System.Text.UTF8Encoding($false)))
}
Write-Host ('LOT05_SERVER_GUI_LAUNCHED='+$r.embedded_launcher_started)
Write-Host ('LOT05_SERVER_GUI_SIGNATURE='+$r.embedded_launcher_signature)
Write-Host ('LOT05_SERVER_GUI_TITLE='+$r.vendor_window_title)
Write-Host ('LOT05_SERVER_GUI_CAPTURE='+$r.vendor_window_capture_ok)
Write-Host ('LOT05_SERVER_GUI_SAFE_CONTROLS='+($r.vendor_safe_control_names -join ','))
Write-Host 'LOT05_SERVER_GUI_INSPECTION_NO_CLICKS_NO_PATIENTS'
if(-not $r.wrapper_hash_pinned -or -not $r.wrapper_signature_valid -or
   -not $r.publisher_is_open_dental -or -not $r.embedded_launcher_started -or
   $r.created_database -or $null -ne $r.error_code){throw 'SIGNED_LAUNCHER_INSPECTION_NOT_PROVEN'}
