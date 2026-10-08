# Facad 3.14 Quick Demo — D2B UIA/Win32-menu structural census.
# Strictly read-only. Opens View popup and hovers known items; never
# invokes leaf commands, never changes the active Robert tracing.
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
public static class FacadD2BWin {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint dx,uint dy,uint d,UIntPtr x);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
}
'@
$root=[Windows.Automation.AutomationElement]::RootElement
$main=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$MainWindowHwnd)
if($null -eq $main -or $main.Current.ProcessId -ne $FacadProcessId){throw 'D2B Facad PID/HWND mismatch'}
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$ledger=Join-Path $dir 'd2b-view-state-ledger.csv'
$log=Join-Path $dir 'd2b-view-state-status.txt'
'control_name,enabled,offscreen,bounds,patterns,toggle_state,legacy_state,expand_state,submenu_new_items,verdict,evidence' | Set-Content -Encoding utf8 $ledger
'D2B_VIEW_STRUCTURE_STARTED' | Set-Content -Encoding utf8 $log
function Log([string]$v){Add-Content -Encoding utf8 $log $v}
function Row([string[]]$fields){
 $escaped=@($fields | ForEach-Object {'"'+($_ -replace '"','""')+'"'})
 Add-Content -Encoding utf8 $ledger ($escaped -join ',')
}
function Screen([string]$name){
 $r=[Windows.Forms.SystemInformation]::VirtualScreen
 $bmp=New-Object Drawing.Bitmap $r.Width,$r.Height
 $g=[Drawing.Graphics]::FromImage($bmp)
 try{$g.CopyFromScreen($r.Left,$r.Top,0,0,$bmp.Size);$bmp.Save((Join-Path $dir $name),[Drawing.Imaging.ImageFormat]::Png)}
 finally{$g.Dispose();$bmp.Dispose()}
}
function OwnsForeground{
 $fg=[FacadD2BWin]::GetForegroundWindow()
 if($fg -eq [IntPtr]::Zero){return $false}
 [uint32]$pidSeen=0
 [void][FacadD2BWin]::GetWindowThreadProcessId($fg,[ref]$pidSeen)
 return $pidSeen -eq [uint32]$FacadProcessId
}
function Rect([Windows.Automation.AutomationElement]$el){
 $r=$el.Current.BoundingRectangle
 if($r.IsEmpty -or $r.Width -lt 12 -or $r.Height -lt 9 -or
    $r.Left -lt 0 -or $r.Top -lt 0 -or $r.Right -gt 5000 -or $r.Bottom -gt 3000){
  throw 'D2B invalid rectangle'
 }
 return $r
}
function Named($parent,[string]$name,[string]$type){
 $all=$parent.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::NameProperty,$name))
 return ,@(for($i=0;$i -lt $all.Count;$i++){
  $e=$all.Item($i)
  if($e.Current.ControlType.ProgrammaticName -eq "ControlType.$type"){$e}
 })
}
function RootMenuItems{
 $all=$root.FindAll([Windows.Automation.TreeScope]::Descendants,
   [Windows.Automation.PropertyCondition]::new(
    [Windows.Automation.AutomationElement]::ControlTypeProperty,
    [Windows.Automation.ControlType]::MenuItem))
 return ,@(for($i=0;$i -lt $all.Count;$i++){
  $el=$all.Item($i)
  try{
   $r=$el.Current.BoundingRectangle
   if($el.Current.ProcessId -eq $FacadProcessId -and -not $el.Current.IsOffscreen -and
      $r.Width -ge 10 -and $r.Height -ge 8){$el}
  }catch{}
 })
}
function ViewTop{
 $bars=$main.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new(
   [Windows.Automation.AutomationElement]::ControlTypeProperty,
   [Windows.Automation.ControlType]::MenuBar))
 $app=@(for($i=0;$i -lt $bars.Count;$i++){
  if($bars.Item($i).Current.Name -eq 'Application'){$bars.Item($i)}
 })
 if($app.Count -ne 1){throw 'D2B application menu bar ambiguous'}
 $view=Named $app[0] 'View' 'MenuItem'
 if($view.Count -ne 1){throw 'D2B View main-menu ambiguous'}
 return $view[0]
}
function ClickMenu([Windows.Automation.AutomationElement]$el){
 if($el.Current.ProcessId -ne $FacadProcessId -or -not (OwnsForeground)){throw 'D2B unsafe menu open'}
 $r=Rect $el
 [void][FacadD2BWin]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2))
 Start-Sleep -Milliseconds 80
 [FacadD2BWin]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 70
 [FacadD2BWin]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
}
function ResetPopups{
 # Nested Win32 menus consume the first Escape while leaving the
 # View parent popup open; the second closes the parent popup.
 # This never invokes a command or modifies the tracing.
 for($ei=0;$ei -lt 2;$ei++){
  if(-not (OwnsForeground)){throw 'Cannot reset menu while Facad is not foreground'}
  [Windows.Forms.SendKeys]::SendWait('{ESC}')
  Start-Sleep -Milliseconds 190
 }
}
function PatternInfo([Windows.Automation.AutomationElement]$el){
 $available=New-Object 'Collections.Generic.List[string]'
 $toggle='';$legacy='';$expand=''
 try{
  $p=$el.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern)
  $available.Add('Toggle')
  $toggle=[string]$p.Current.ToggleState
 }catch{}
 try{
  $p=$el.GetCurrentPattern([Windows.Automation.LegacyIAccessiblePattern]::Pattern)
  $available.Add('LegacyIAccessible')
  $legacy=[string]$p.Current.State
 }catch{}
 try{
  $p=$el.GetCurrentPattern([Windows.Automation.ExpandCollapsePattern]::Pattern)
  $available.Add('ExpandCollapse')
  $expand=[string]$p.Current.ExpandCollapseState
 }catch{}
 try{
  $p=$el.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern)
  $available.Add('SelectionItem')
  $toggle+= " Select=$($p.Current.IsSelected)"
 }catch{}
 return @{patterns=($available -join '|');toggle=$toggle;legacy=$legacy;expand=$expand}
}
$targets=@(
 'Marker names','Marker guide','Markers','Hard tissue','Profile',
 'Ceph/Lines','Bindings','Original positions','Planned positions','Tracing image',
 'Profile photo','Predicted photo','Image #2','Harmony box','Status bar',
 'Analysis','Image/Tracing manager','Toolbars','Generate predicted photo'
)
Screen 'd2b-baseline.png'
$enumerated=0
$submenuCount=0
foreach($name in $targets){
 $safe=($name -replace '[^A-Za-z0-9]','_')
 try{
  $item=$null
  $items=@()
  # Win32 nested menu close can briefly invalidate UIA popup entries.
  # Three bounded retries: dismiss the full hierarchy and reopen View.
  for($attempt=1;$attempt -le 3;$attempt++){
   ResetPopups
   ClickMenu (ViewTop)
   Start-Sleep -Milliseconds 280
   $items=RootMenuItems
   $m=@($items | Where-Object {$_.Current.Name -eq $name})
   Log "D2B_TARGET_${safe}_ATTEMPT_$attempt=$($m.Count)"
   if($m.Count -eq 1){$item=$m[0];break}
   Log "D2B_TARGET_${safe}_VISIBLE_MENU_ITEMS=$(@($items | ForEach-Object {$_.Current.Name}) -join '; ')"
   Screen "d2b-retry-$safe-$attempt.png"
  }
  if($null -eq $item){throw "View entry $name missing/ambiguous after three non-destructive menu resets"}
  $r=Rect $item
  $states=PatternInfo $item
  $snap="d2b-view-$safe.png"
  Screen $snap
  $new=@()
  if($item.Current.IsEnabled -and (OwnsForeground)){
   # Only HOVER; safe even if popup command is destructive.
   [void][FacadD2BWin]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2))
   Start-Sleep -Milliseconds 350
   $new=@(RootMenuItems | ForEach-Object {$_.Current.Name} |
     Where-Object {$_ -notin @($items | ForEach-Object {$_.Current.Name})} |
     Sort-Object -Unique)
   if($new.Count -gt 0){
    $submenuCount++
    Screen "d2b-submenu-$safe.png"
    $new | Set-Content -Encoding utf8 (Join-Path $dir "d2b-submenu-$safe.txt")
   }
  }
  $meaning=if(-not $item.Current.IsEnabled){'DISABLED'}
   elseif($new.Count -gt 0){'SUBMENU_DISCOVERED_NOT_ACTIVATED'}
   elseif($states.patterns -match 'Toggle|SelectionItem'){'STATE_OBSERVED_ACTION_NOT_TESTED'}
   else{'DISCOVERED_UNCERTAIN_ACTION_SKIPPED'}
  Row @([string]$name,[string]$item.Current.IsEnabled,[string]$item.Current.IsOffscreen,
    [string]$r,[string]$states.patterns,[string]$states.toggle,[string]$states.legacy,
    [string]$states.expand,($new -join '; '),[string]$meaning,[string]$snap)
  Log "VIEW_$safe=$meaning"
  $enumerated++
 }catch{
  Log "D2B_$safe=BLOCKED $($_.Exception.Message)"
  Row @([string]$name,'','','','','','','','','BLOCKED',($_.Exception.Message))
 }finally{ResetPopups}
}
Screen 'd2b-final.png'
Log "D2B_VIEW_ENUMERATED=$enumerated/$($targets.Count)"
Log "D2B_SUBMENUS_DISCOVERED=$submenuCount"
Log 'D2B_NO_LEAF_COMMAND_EXECUTED=true'
if($enumerated -ne $targets.Count){throw "D2B census incomplete: $enumerated/$($targets.Count) View items"}
