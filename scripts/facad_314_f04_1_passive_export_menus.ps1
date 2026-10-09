# FAC-04 F04.1: passively inspect File/Edit/Cephalometry/Tools roots only; never invoke a leaf, export or save.
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
public static class F041MenuMouse {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
}
'@
$root=[Windows.Automation.AutomationElement]::RootElement
$main=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$MainWindowHwnd)
if($null -eq $main -or $main.Current.ProcessId -ne $FacadProcessId){throw 'F04.1 target mismatch'}
$dir=[IO.Path]::GetFullPath($OutDir);[void][IO.Directory]::CreateDirectory($dir)
$log=Join-Path $dir 'f04-1-status.txt'
$csv=Join-Path $dir 'f04-1-menu-observations.csv'
'F04_1_SCOPE=MENU_ONLY_NO_LEAF_ACTIVATION' | Set-Content -Encoding utf8 $log
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
 $h=[F041MenuMouse]::GetForegroundWindow()
 if($h -eq [IntPtr]::Zero){return $false}
 [uint32]$observed=0
 [void][F041MenuMouse]::GetWindowThreadProcessId($h,[ref]$observed)
 return $observed -eq [uint32]$FacadProcessId
}
function OpenRoot([string]$name){
 if(-not (OwnsForeground)){throw "F04.1 ${name}: foreground not Facad"}
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
 if($found.Count -ne 1){throw "F04.1 $name ambiguous root: $($found.Count)"}
 $e=$found[0];$r=$e.Current.BoundingRectangle
 if($e.Current.ProcessId -ne $FacadProcessId -or -not $e.Current.IsEnabled -or
    $r.IsEmpty -or $r.Width -lt 10 -or $r.Height -lt 8 -or
    $r.Left -lt 0 -or $r.Top -lt 0 -or $r.Right -gt 5000 -or $r.Bottom -gt 3000){
   throw "F04.1 $name unsafe root"
 }
 if(-not [F041MenuMouse]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2))){throw 'F04.1 root mouse move failed'}
 Start-Sleep -Milliseconds 80
 [F041MenuMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 70
 [F041MenuMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
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
   if($e.Current.ProcessId -eq $FacadProcessId -and $e.Current.Name -ne 'System' -and -not $e.Current.IsOffscreen -and
     $r.Width -gt 10 -and $r.Height -gt 8 -and $r.Top -gt 35 -and $r.Top -lt 700){
     $vals=@($menu,$e.Current.Name,$e.Current.ControlType.ProgrammaticName,
       [string]$e.Current.IsEnabled,[string]$e.Current.IsOffscreen,[string]$r)
     Add-Content -Encoding utf8 $csv ((@($vals|ForEach-Object{'"'+($_ -replace '"','""')+'"'})) -join ',')
     $seen++
   }
  }catch{}
 }
 Log "VISIBLE_UIA_MENU_ITEMS_$menu=$seen"
 if($seen -eq 0){throw "F04.1 $menu popup empty"}
}
function CloseMenus {
 if(-not (OwnsForeground)){throw 'F04.1 lost Facad foreground before close'}
 [Windows.Forms.SendKeys]::SendWait('{ESC}')
 Start-Sleep -Milliseconds 150
 [Windows.Forms.SendKeys]::SendWait('{ESC}')
 Start-Sleep -Milliseconds 160
}
Shot 'f04-1-before.png'
DumpUi 'f04-1-before-uia.txt'
try{
 foreach($name in @('File','Edit','Cephalometry','Tools')){
  try{
   OpenRoot $name
   Shot "f04-1-$($name.ToLower())-menu.png"
   DumpUi "f04-1-$($name.ToLower())-uia.txt"
   Inventory $name
   Log "F04_1_ROOT_OBSERVED=$name"
  }finally{
   if(OwnsForeground){CloseMenus}
  }
 }
}finally{
 Shot 'f04-1-after.png'
 DumpUi 'f04-1-after-uia.txt'
 Log 'LEAF_CLICK_INVOKED=false'
 Log 'SAVE_INVOKED=false'
 Log 'PATIENT_LOAD_INVOKED=false'
 Log 'SHARED_APP_STORAGE_ISOLATION=UNVERIFIED'
 Log 'CLINICAL_EDIT_ALLOWED=false'
 Log 'F04_1_EXPORT_VALIDATED=false'
}
Log 'F04_1_ROOT_MENU_CENSUS_COMPLETE=true'
