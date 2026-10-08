# D2C Facad 3.14: supervised, reversible View options and mode smoke tests
# Preconditions: official Example Robert pretreatment editor already open; no edits.
param([Parameter(Mandatory=$true)][int]$FacadProcessId,
      [Parameter(Mandatory=$true)][long]$MainWindowHwnd,
      [Parameter(Mandatory=$true)][string]$OutDir)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class FacadD2CCMouse {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint flags,uint dx,uint dy,uint data,UIntPtr extra);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint processId);
}
'@
$root=[System.Windows.Automation.AutomationElement]::RootElement
$main=[System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$MainWindowHwnd)
if($null -eq $main -or $main.Current.ProcessId -ne $FacadProcessId){throw 'D2C Facad main HWND mismatch'}
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$log=Join-Path $dir 'd2c-status.txt'
$csv=Join-Path $dir 'd2c-coverage.csv'
'D2C_STARTED=true' | Set-Content -Encoding utf8 $log
'family,name,enabled,initial_state,after_state,restored_state,verdict,before_image,after_image,restore_image,note' | Set-Content -Encoding utf8 $csv
function Log([string]$s){Add-Content -Encoding utf8 -Path $log -Value $s}
function Record([string]$family,[string]$name,[string]$enabled,[string]$first,[string]$after,[string]$restored,[string]$verdict,[string]$beforeImage,[string]$afterImage,[string]$restoreImage,[string]$note){
 $parts=@($family,$name,$enabled,$first,$after,$restored,$verdict,$beforeImage,$afterImage,$restoreImage,$note) | ForEach-Object {'"'+($_ -replace '"','""')+'"'}
 Add-Content -Encoding utf8 -Path $csv -Value ($parts -join ',')
}
function Screen([string]$name){
 $bounds=[System.Windows.Forms.SystemInformation]::VirtualScreen
 $bmp=New-Object System.Drawing.Bitmap $bounds.Width,$bounds.Height
 $g=[System.Drawing.Graphics]::FromImage($bmp)
 try{
  $g.CopyFromScreen($bounds.Left,$bounds.Top,0,0,$bmp.Size)
  $bmp.Save((Join-Path $dir $name),[System.Drawing.Imaging.ImageFormat]::Png)
 }finally{$g.Dispose();$bmp.Dispose()}
}
function Ui([string]$file){
 $els=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
 $lines=New-Object 'System.Collections.Generic.List[string]'
 for($i=0;$i -lt $els.Count;$i++){
  $el=$els.Item($i)
  try{
   if($el.Current.ProcessId -eq $FacadProcessId){
    $lines.Add(("{0}|{1}|ID={2}|ENABLED={3}|OFFSCREEN={4}|BOUNDS={5}" -f $el.Current.ControlType.ProgrammaticName,$el.Current.Name,$el.Current.AutomationId,$el.Current.IsEnabled,$el.Current.IsOffscreen,$el.Current.BoundingRectangle))
   }
  }catch{}
 }
 $lines | Set-Content -Encoding utf8 (Join-Path $dir $file)
}
function ForegroundOwned(){
 $hwnd=[FacadD2CCMouse]::GetForegroundWindow()
 if($hwnd -eq [IntPtr]::Zero){return $false}
 [uint32]$pidSeen=0
 [void][FacadD2CCMouse]::GetWindowThreadProcessId($hwnd,[ref]$pidSeen)
 return $pidSeen -eq [uint32]$FacadProcessId
}
function Click([System.Windows.Automation.AutomationElement]$el){
 if($el.Current.ProcessId -ne $FacadProcessId -or -not $el.Current.IsEnabled -or -not (ForegroundOwned)){throw 'Refuse unsafe D2C click'}
 $r=$el.Current.BoundingRectangle
 if($r.IsEmpty -or $r.Width -lt 6 -or $r.Height -lt 8 -or $r.Left -lt 0 -or $r.Top -lt 0 -or $r.Right -gt 5000 -or $r.Bottom -gt 3000){throw 'D2C click rectangle outside screen'}
 if(-not [FacadD2CCMouse]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2))){throw 'D2C SetCursorPos failed'}
 Start-Sleep -Milliseconds 70
 [FacadD2CCMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 75
 [FacadD2CCMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
}
function NameType($parent,[string]$name,[string]$type){
 $arr=$parent.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty,$name))
 return ,@(for($i=0;$i -lt $arr.Count;$i++){
  $e=$arr.Item($i)
  if($e.Current.ControlType.ProgrammaticName -eq "ControlType.$type"){$e}
 })
}
function MenuRoot([string]$name){
 $bars=$main.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ControlTypeProperty,[System.Windows.Automation.ControlType]::MenuBar))
 $apps=@(for($i=0;$i -lt $bars.Count;$i++){if($bars.Item($i).Current.Name -eq 'Application'){$bars.Item($i)}})
 if($apps.Count -ne 1){throw 'D2C application menubar not unique'}
 $found=NameType $apps[0] $name 'MenuItem'
 if($found.Count -ne 1){throw "D2C main menu $name not unique"}
 return $found[0]
}
function OpenView{
 Click (MenuRoot 'View')
 Start-Sleep -Milliseconds 220
}
function FindPopupItem([string]$name){
 $arr=NameType $root $name 'MenuItem'
 $visible=@(foreach($e in $arr){
  try{
   $r=$e.Current.BoundingRectangle
   if($e.Current.ProcessId -eq $FacadProcessId -and -not $e.Current.IsOffscreen -and
      $r.Width -ge 45 -and $r.Left -ge 0 -and $r.Top -gt 35 -and $r.Top -lt 700){$e}
  }catch{}
 })
 if($visible.Count -ne 1){throw "D2C View > $name popup count=$($visible.Count)"}
 return $visible[0]
}
function State($item){
 try{
  $p=$item.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
  return "Toggle:$($p.Current.ToggleState)"
 }catch{}
 try{
  $p=$item.GetCurrentPattern([System.Windows.Automation.LegacyIAccessiblePattern]::Pattern)
  $state=[string]$p.Current.State
  return "Legacy:$state"
 }catch{}
 return 'UNKNOWN'
}
function CloseMenu{
 [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
 Start-Sleep -Milliseconds 150
 [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
 Start-Sleep -Milliseconds 180
}
# Exclude commands with known side effects or dialog/secondary-pane changes until isolated D2CB.
# Original/Planned positions are selection modes (not necessarily toggles);
# Predicted photo may load generated content. They are deliberately deferred
# until a separate D2CB with a proven one-way reset to original state.
# Strictly selected by D2B UIA proof: these three are genuine Toggle controls
# (initial state On). No clinical geometry, measurements, or save actions.
$candidates=@('Marker guide','Original positions','Planned positions')
Log "D2C_VIEW_CANDIDATES=$($candidates.Count)"
Log 'D2C_RESTRICTED_TO_UIA_TOGGLE=Marker guide;Original positions;Planned positions'
Screen 'd2c-baseline.png'
Ui 'd2c-baseline-ui.txt'
$unresolved=@()
$successful=0
$review=@()
for($i=0;$i -lt $candidates.Count;$i++){
 $name=$candidates[$i]
 $key=("{0:D2C}-{1}" -f $i,($name -replace '[^A-Za-z0-9]','_'))
 $before="d2c-$key-before.png"; $after="d2c-$key-after.png"; $restore="d2c-$key-restored.png"
 $start='UNKNOWN'; $finish='UNKNOWN'; $back='UNKNOWN'
 $enabled='UNKNOWN'; $changed=$false
 try{
  OpenView
  $beforeItem=FindPopupItem $name
  $enabled=[string]$beforeItem.Current.IsEnabled
  if(-not $beforeItem.Current.IsEnabled){
   Screen $before;CloseMenu
   Record 'VIEW' $name $enabled 'DISABLED' '' '' 'DISABLED' $before '' '' 'Quick Demo disabled'
   continue
  }
  $start=State $beforeItem
  Screen $before
  if($start -eq 'UNKNOWN'){
    CloseMenu
    Record 'VIEW' $name $enabled $start '' '' 'SKIPPED_NO_STATE_PROOF' $before '' '' 'No reliable toggle state; D2CB manual or UIA-specific proof required'
    continue
  }
  Click $beforeItem
  Start-Sleep -Milliseconds 310
  Screen $after
  Ui "d2c-$key-after-ui.txt"
  $changed=$true
  OpenView
  $afterItem=FindPopupItem $name
  $finish=State $afterItem
  if(-not $afterItem.Current.IsEnabled){throw "View > $name unexpectedly disabled after toggle"}
  # Re-click the SAME control to restore initial state.
  Click $afterItem
  Start-Sleep -Milliseconds 310
  Screen $restore
  OpenView
  $back=State (FindPopupItem $name)
  CloseMenu
  if($start -ne 'UNKNOWN' -and $finish -ne 'UNKNOWN' -and $start -ne $finish -and $start -eq $back){
   $successful++
   Record 'VIEW' $name $enabled $start $finish $back 'TOGGLED_AND_RESTORED' $before $after $restore 'UIA state changed and restored'
  }elseif($start -eq $back -and $start -ne 'UNKNOWN'){
   $review+= $name
   Record 'VIEW' $name $enabled $start $finish $back 'RESTORED_STATE_NO_CHANGE_PROOF' $before $after $restore 'Visual change needs review'
  }else{
   $review+= $name
   Record 'VIEW' $name $enabled $start $finish $back 'VISUAL_REVIEW_REQUIRED' $before $after $restore 'State not machine-verifiable'
  }
 }catch{
  $issue=$_.Exception.Message
  Log "VIEW_ERROR=$name : $issue"
  $unresolved+= $name
  Record 'VIEW' $name $enabled $start $finish $back 'BLOCKED_POSSIBLE_UNRESTORED' $before $after $restore $issue
  CloseMenu
  # Fail fast to avoid additional actions when restoration has not been proved.
  if($changed){break}
 }
}
Log "VIEW_VERIFIED_TOGGLE_RESTORE=$successful/$($candidates.Count)"
Log "VIEW_VISUAL_REVIEW=$($review -join ';')"
Log "VIEW_UNRESOLVED=$($unresolved -join ';')"
# Verify every candidate was toggled and restored according to a fresh
# UIA TogglePattern reading. A screenshot alone does not certify semantics.
Log "D2C_VERIFIED_TOGGLE_RESTORE=$successful/$($candidates.Count)"
Screen 'd2c-final.png'
Ui 'd2c-final-ui.txt'
if($unresolved.Count -gt 0){throw "D2C unsafe/unresolved View options: $($unresolved -join '; ')"}
if($successful -ne $candidates.Count){
 throw "D2C incomplete: verified=$successful / expected=$($candidates.Count), visual-review=$($review -join '; ')"
}
Log 'D2C_UIA_TOGGLE_AND_RESTORE_GATE=PASSED'
