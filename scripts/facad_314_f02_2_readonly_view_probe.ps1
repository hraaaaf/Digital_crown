# F02.2 : target-only read-only UIA observation. Never activate a leaf item.
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
public static class F022MenuMouse {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
}
'@
$root=[Windows.Automation.AutomationElement]::RootElement
$main=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$MainWindowHwnd)
if($null -eq $main -or $main.Current.ProcessId -ne $FacadProcessId){throw 'F02.2 main process/HWND mismatch'}
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$log=Join-Path $dir 'f02-2-observation.txt'
$csv=Join-Path $dir 'f02-2-targets.csv'
'F02_2_SCOPE=MENU_OBSERVATION_ONLY' | Set-Content -Encoding utf8 $log
'target,control_type,enabled,visible,pattern_toggle,pattern_selection,pattern_legacy,bounds,verdict' | Set-Content -Encoding utf8 $csv
function Log([string]$s){Add-Content -Encoding utf8 $log $s}
function Shot([string]$name){
 $rect=[Windows.Forms.SystemInformation]::VirtualScreen
 $bmp=[Drawing.Bitmap]::new($rect.Width,$rect.Height)
 $g=[Drawing.Graphics]::FromImage($bmp)
 try{$g.CopyFromScreen($rect.Left,$rect.Top,0,0,$bmp.Size);$bmp.Save((Join-Path $dir $name),[Drawing.Imaging.ImageFormat]::Png)}
 finally{$g.Dispose();$bmp.Dispose()}
}
function DumpUI([string]$name){
 $all=$root.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
 $rows=New-Object 'Collections.Generic.List[string]'
 for($i=0;$i -lt $all.Count;$i++){
  $e=$all.Item($i)
  try {if($e.Current.ProcessId -eq $FacadProcessId){
    $rows.Add(('{0}|{1}|ENABLED={2}|OFFSCREEN={3}|RECT={4}' -f $e.Current.ControlType.ProgrammaticName,$e.Current.Name,$e.Current.IsEnabled,$e.Current.IsOffscreen,$e.Current.BoundingRectangle))
  }}catch{}
 }
 $rows | Set-Content -Encoding utf8 (Join-Path $dir $name)
}
function OwnsForeground {
 $h=[F022MenuMouse]::GetForegroundWindow()
 [uint32]$pidSeen=0
 if($h -eq [IntPtr]::Zero){return $false}
 [void][F022MenuMouse]::GetWindowThreadProcessId($h,[ref]$pidSeen)
 return $pidSeen -eq [uint32]$FacadProcessId
}
function ClickViewRoot {
 if(-not (OwnsForeground)){throw 'F02.2 Facad not foreground'}
 $bars=$main.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::MenuBar))
 $views=@(for($i=0;$i -lt $bars.Count;$i++){
  $bar=$bars.Item($i)
  if($bar.Current.Name -eq 'Application'){
   $items=$bar.FindAll([Windows.Automation.TreeScope]::Descendants,
    [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::NameProperty,'View'))
   for($j=0;$j -lt $items.Count;$j++){
    if($items.Item($j).Current.ControlType.ProgrammaticName -eq 'ControlType.MenuItem'){$items.Item($j)}
   }
  }
 })
 if($views.Count -ne 1){throw "F02.2 expected one View root; found $($views.Count)"}
 $v=$views[0]
 $r=$v.Current.BoundingRectangle
 if($v.Current.ProcessId -ne $FacadProcessId -or -not $v.Current.IsEnabled -or
    $r.IsEmpty -or $r.Width -lt 10 -or $r.Height -lt 8 -or
    $r.Left -lt 0 -or $r.Top -lt 0 -or $r.Right -gt 5000 -or $r.Bottom -gt 3000){
  throw 'F02.2 unsafe View root'
 }
 if(-not [F022MenuMouse]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2))){throw 'F02.2 mouse move failed'}
 Start-Sleep -Milliseconds 80
 [F022MenuMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 70
 [F022MenuMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
}
function PatternState($el,$pattern){
 try{
  if($pattern -eq 'Toggle'){return [string]$el.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Current.ToggleState}
  if($pattern -eq 'Selection'){return [string]$el.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected}
  if($pattern -eq 'Legacy'){return [string]$el.GetCurrentPattern([Windows.Automation.LegacyIAccessiblePattern]::Pattern).Current.State}
 }catch{}
 return 'UNAVAILABLE'
}
$targets=@('Marker guide','Planned positions')
$failed=$false
Shot 'f02-2-before.png'
DumpUI 'f02-2-before-uia.txt'
try{
 ClickViewRoot
 Start-Sleep -Milliseconds 280
 Shot 'f02-2-view-open.png'
 DumpUI 'f02-2-view-open-uia.txt'
 foreach($name in $targets){
  $matches=$root.FindAll([Windows.Automation.TreeScope]::Descendants,
   [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::NameProperty,$name))
  $found=@(for($i=0;$i -lt $matches.Count;$i++){
   $e=$matches.Item($i)
   try {if($e.Current.ProcessId -eq $FacadProcessId -and
      $e.Current.ControlType.ProgrammaticName -eq 'ControlType.MenuItem' -and
      -not $e.Current.IsOffscreen){$e}}catch{}
  })
  if($found.Count -ne 1){Log "TARGET_AMBIGUOUS=$name count=$($found.Count)";$failed=$true;continue}
  $el=$found[0]
  $row=@($name,$el.Current.ControlType.ProgrammaticName,[string]$el.Current.IsEnabled,
   [string](-not $el.Current.IsOffscreen),(PatternState $el 'Toggle'),
   (PatternState $el 'Selection'),(PatternState $el 'Legacy'),
   [string]$el.Current.BoundingRectangle,'UIA_OBSERVED_NO_LEAF_CLICK')
  $escaped=@($row|ForEach-Object {'"'+($_ -replace '"','""')+'"'})
  Add-Content -Encoding utf8 $csv ($escaped -join ',')
  Log "TARGET_OBSERVED=$name;leaf_click=false"
 }
}finally{
 if(OwnsForeground){
  [Windows.Forms.SendKeys]::SendWait('{ESC}')
  Start-Sleep -Milliseconds 150
  [Windows.Forms.SendKeys]::SendWait('{ESC}')
  Start-Sleep -Milliseconds 180
 }
 Shot 'f02-2-after-menu-close.png'
 DumpUI 'f02-2-after-menu-close-uia.txt'
 Log 'SAVE_INVOKED=false'
 Log 'PATIENT_LOAD_INVOKED=false'
 Log 'LEAF_CLICK_INVOKED=false'
 Log 'SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
 Log 'CLINICAL_EDIT_ALLOWED=false'
 Log 'F02_2_VISUAL_BEHAVIOR_PROVEN=false'
}
if($failed){throw 'F02.2 missing/ambiguous target in real UI; observation incomplete'}
Log 'F02_2_MENU_OBSERVATION_COMPLETE=true'
