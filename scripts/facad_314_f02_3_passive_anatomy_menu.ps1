# FAC-02 F02.3: passive UIA menu census only. No leaf commands, no save, no patient Load.
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
public static class F023MenuMouse {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
}
'@
$root=[Windows.Automation.AutomationElement]::RootElement
$main=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$MainWindowHwnd)
if($null -eq $main -or $main.Current.ProcessId -ne $FacadProcessId){throw 'F02.3 target mismatch'}
$dir=[IO.Path]::GetFullPath($OutDir);[void][IO.Directory]::CreateDirectory($dir)
$log=Join-Path $dir 'f02-3-status.txt'
$csv=Join-Path $dir 'f02-3-menu-observations.csv'
'F02_3_SCOPE=MENU_ONLY_NO_LEAF_ACTIVATION' | Set-Content -Encoding utf8 $log
'menu,name,control_type,enabled,offscreen,bounds' | Set-Content -Encoding utf8 $csv
function Log([string]$s){Add-Content -Encoding utf8 $log $s}
function Shot([string]$name){
 $r=[Windows.Forms.SystemInformation]::VirtualScreen
 $b=[Drawing.Bitmap]::new($r.Width,$r.Height);$g=[Drawing.Graphics]::FromImage($b)
 try{$g.CopyFromScreen($r.Left,$r.Top,0,0,$b.Size);$b.Save((Join-Path $dir $name),[Drawing.Imaging.ImageFormat]::Png)}
 finally{$g.Dispose();$b.Dispose()}
}
function DumpUi([string]$name){
 $all=$root.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
 $rows=New-Object 'Collections.Generic.List[string]'
 for($i=0;$i -lt $all.Count;$i++){
  $e=$all.Item($i)
  try{if($e.Current.ProcessId -eq $FacadProcessId){
   $rows.Add(('{0}|{1}|ENABLED={2}|OFFSCREEN={3}|RECT={4}' -f
     $e.Current.ControlType.ProgrammaticName,$e.Current.Name,$e.Current.IsEnabled,$e.Current.IsOffscreen,$e.Current.BoundingRectangle))
  }}catch{}
 }
 $rows | Set-Content -Encoding utf8 (Join-Path $dir $name)
}
function OwnsForeground {
 $h=[F023MenuMouse]::GetForegroundWindow()
 if($h -eq [IntPtr]::Zero){return $false}
 [uint32]$observed=0
 [void][F023MenuMouse]::GetWindowThreadProcessId($h,[ref]$observed)
 return $observed -eq [uint32]$FacadProcessId
}
function OpenRoot([string]$name){
 if(-not (OwnsForeground)){throw "F02.3 $name: foreground not Facad"}
 $bars=$main.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::MenuBar))
 $found=@(for($i=0;$i -lt $bars.Count;$i++){
  $bar=$bars.Item($i)
  if($bar.Current.Name -eq 'Application'){
   $items=$bar.FindAll([Windows.Automation.TreeScope]::Descendants,
    [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::NameProperty,$name))
   for($j=0;$j -lt $items.Count;$j++){
    if($items.Item($j).Current.ControlType.ProgrammaticName -eq 'ControlType.MenuItem'){$items.Item($j)}
   }
  }
 })
 if($found.Count -ne 1){throw "F02.3 $name ambiguous root: $($found.Count)"}
 $e=$found[0];$r=$e.Current.BoundingRectangle
 if($e.Current.ProcessId -ne $FacadProcessId -or -not $e.Current.IsEnabled -or
    $r.IsEmpty -or $r.Width -lt 10 -or $r.Height -lt 8 -or
    $r.Left -lt 0 -or $r.Top -lt 0 -or $r.Right -gt 5000 -or $r.Bottom -gt 3000){
   throw "F02.3 $name unsafe root"
 }
 if(-not [F023MenuMouse]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2))){throw 'F02.3 root mouse move failed'}
 Start-Sleep -Milliseconds 80
 [F023MenuMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 70
 [F023MenuMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 250
}
function Inventory([string]$menu){
 $items=$root.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::MenuItem))
 $seen=0
 for($i=0;$i -lt $items.Count;$i++){
  $e=$items.Item($i)
  try{
   $r=$e.Current.BoundingRectangle
   if($e.Current.ProcessId -eq $FacadProcessId -and -not $e.Current.IsOffscreen -and
     $r.Width -gt 10 -and $r.Height -gt 8 -and $r.Top -gt 35 -and $r.Top -lt 700){
     $vals=@($menu,$e.Current.Name,$e.Current.ControlType.ProgrammaticName,
       [string]$e.Current.IsEnabled,[string]$e.Current.IsOffscreen,[string]$r)
     Add-Content -Encoding utf8 $csv ((@($vals|ForEach-Object{'"'+($_ -replace '"','""')+'"'})) -join ',')
     $seen++
   }
  }catch{}
 }
 Log "VISIBLE_UIA_MENU_ITEMS_$menu=$seen"
 if($seen -eq 0){throw "F02.3 $menu popup empty"}
}
function CloseMenus {
 if(-not (OwnsForeground)){throw 'F02.3 lost Facad foreground before close'}
 [Windows.Forms.SendKeys]::SendWait('{ESC}')
 Start-Sleep -Milliseconds 150
 [Windows.Forms.SendKeys]::SendWait('{ESC}')
 Start-Sleep -Milliseconds 160
}
Shot 'f02-3-before.png'
DumpUi 'f02-3-before-uia.txt'
try{
 foreach($name in @('Tracing','View')){
  try{
   OpenRoot $name
   Shot "f02-3-$($name.ToLower())-menu.png"
   DumpUi "f02-3-$($name.ToLower())-uia.txt"
   Inventory $name
   Log "F02_3_ROOT_OBSERVED=$name"
  }finally{
   if(OwnsForeground){CloseMenus}
  }
 }
}finally{
 Shot 'f02-3-after.png'
 DumpUi 'f02-3-after-uia.txt'
 Log 'LEAF_CLICK_INVOKED=false'
 Log 'SAVE_INVOKED=false'
 Log 'PATIENT_LOAD_INVOKED=false'
 Log 'SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
 Log 'CLINICAL_EDIT_ALLOWED=false'
 Log 'F02_3_FULL_VISUAL_BEHAVIOR_PROVEN=false'
}
Log 'F02_3_ROOT_MENU_CENSUS_COMPLETE=true'
