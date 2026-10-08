# Facad Quick Demo, D1: catalog discovery and complete visible analysis-list census.
# Prerequisite: verified official Robert Example tracing opened by the workflow.
# Read-only inspection: do NOT load/select/replace an analysis or save to patient.
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
public static class FacadCatalogMouse {
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,uint x,uint y,uint d,UIntPtr e);
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
}
'@
$root=[Windows.Automation.AutomationElement]::RootElement
$main=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$MainWindowHwnd)
if($null -eq $main -or $main.Current.ProcessId -ne $FacadProcessId){throw 'D1 Facad main window mismatch'}
$dir=[IO.Path]::GetFullPath($OutDir)
[void][IO.Directory]::CreateDirectory($dir)
$log=Join-Path $dir 'd1-analysis-census-status.txt'
'D1_ANALYSIS_CENSUS=STARTED' | Set-Content -Encoding utf8 $log
function Log([string]$msg){Add-Content -Encoding utf8 $log $msg}
function Shot([string]$name){
 $r=[Windows.Forms.SystemInformation]::VirtualScreen
 $b=New-Object Drawing.Bitmap $r.Width,$r.Height
 $g=[Drawing.Graphics]::FromImage($b)
 try{$g.CopyFromScreen($r.Left,$r.Top,0,0,$b.Size);$b.Save((Join-Path $dir $name),[Drawing.Imaging.ImageFormat]::Png)}
 finally{$g.Dispose();$b.Dispose()}
}
function Snapshot([string]$filename){
 $els=$root.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
 $out=New-Object 'Collections.Generic.List[string]'
 for($i=0;$i -lt $els.Count;$i++){
  $e=$els.Item($i)
  try{if($e.Current.ProcessId -eq $FacadProcessId){
   $out.Add(("{0}|{1}|{2}|ENABLED={3}|OFFSCREEN={4}|BOUND={5}" -f
    $e.Current.ControlType.ProgrammaticName,$e.Current.Name,$e.Current.AutomationId,
    $e.Current.IsEnabled,$e.Current.IsOffscreen,$e.Current.BoundingRectangle))
  }}catch{}
 }
 $out | Set-Content -Encoding utf8 (Join-Path $dir $filename)
 return $out
}
function ForegroundOk{
 $h=[FacadCatalogMouse]::GetForegroundWindow()
 if($h -eq [IntPtr]::Zero){return $false}
 [uint32]$fpid=0
 [void][FacadCatalogMouse]::GetWindowThreadProcessId($h,[ref]$fpid)
 return $fpid -eq [uint32]$FacadProcessId
}
function Named($parent,[string]$name,[string]$type){
 $all=$parent.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::NameProperty,$name))
 return ,@(for($i=0;$i -lt $all.Count;$i++){
  $e=$all.Item($i)
  if($e.Current.ControlType.ProgrammaticName -eq "ControlType.$type"){$e}
 })
}
function Click($element){
 if($element.Current.ProcessId -ne $FacadProcessId -or -not $element.Current.IsEnabled -or -not (ForegroundOk)){throw 'D1 unsafe click'}
 $r=$element.Current.BoundingRectangle
 if($r.IsEmpty -or $r.Width -lt 9 -or $r.Height -lt 9 -or $r.Left -lt 0 -or $r.Top -lt 0 -or $r.Right -gt 5000 -or $r.Bottom -gt 3000){throw 'D1 unsafe bounds'}
 if(-not [FacadCatalogMouse]::SetCursorPos([int]($r.Left+$r.Width/2),[int]($r.Top+$r.Height/2))){throw 'D1 cursor failed'}
 Start-Sleep -Milliseconds 90
 [FacadCatalogMouse]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
 Start-Sleep -Milliseconds 70
 [FacadCatalogMouse]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
}
function AppMenu([string]$name){
 $bars=$main.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::MenuBar))
 $apps=@(for($i=0;$i -lt $bars.Count;$i++){if($bars.Item($i).Current.Name -eq 'Application'){$bars.Item($i)}})
 if($apps.Count -ne 1){throw "D1 application bar count $($apps.Count)"}
 $m=Named $apps[0] $name 'MenuItem'
 if($m.Count -ne 1){throw "D1 top-level menu $name count $($m.Count)"}
 return $m[0]
}
function Escape{[Windows.Forms.SendKeys]::SendWait('{ESC}');Start-Sleep -Milliseconds 280}
function CaptureDialog([string]$tag){
 Shot "d1-$tag.png"
 $all=Snapshot "d1-$tag-ui.txt"
 Log "CAPTURE_$tag=$($all.Count)_UI_ROWS"
}
function EnumerateList([string]$tag){
 # Only scroll a UIA List or DataGrid entirely visible in the active Facad-owned
 # dialog. Do not select entries, copy data, or click arbitrary filenames.
 $wins=$root.FindAll([Windows.Automation.TreeScope]::Descendants,
  [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Window))
 $visibleWindows=@(for($i=0;$i -lt $wins.Count;$i++){
  $w=$wins.Item($i)
  try{if($w.Current.ProcessId -eq $FacadProcessId -and -not $w.Current.IsOffscreen -and
    $w.Current.Name -notlike 'Pretreatment tracing*  Tracing' -and $w.Current.Name -notlike 'Pretreatment tracing*  Analysis' -and
    $w.Current.Name -ne 'Facad'){$w}}catch{}
 })
 Log "DIALOG_$tag_COUNT=$($visibleWindows.Count)"
 foreach($window in $visibleWindows){
  Log "DIALOG_$tag_NAME=$($window.Current.Name)"
  $candidates=$window.FindAll([Windows.Automation.TreeScope]::Descendants,
    [Windows.Automation.Condition]::TrueCondition)
  $lists=@(for($i=0;$i -lt $candidates.Count;$i++){
   $e=$candidates.Item($i)
   if($e.Current.ControlType -eq [Windows.Automation.ControlType]::List -or
      $e.Current.ControlType -eq [Windows.Automation.ControlType]::DataGrid){$e}
  })
  Log "DIALOG_$tag_LIST_CONTROLS=$($lists.Count)"
  if($lists.Count -ne 1){continue}
  $list=$lists[0]
  try{
   $sp=$list.GetCurrentPattern([Windows.Automation.ScrollPattern]::Pattern)
  }catch{
   Log "SCROLL_${tag}_PATTERN_UNAVAILABLE=$($_.Exception.GetType().Name)"
   continue
  }
  $seen=New-Object 'Collections.Generic.HashSet[string]'
  for($page=0;$page -lt 30;$page++){
   $rows=$list.FindAll([Windows.Automation.TreeScope]::Descendants,[Windows.Automation.Condition]::TrueCondition)
   $items=@(for($z=0;$z -lt $rows.Count;$z++){
    $e=$rows.Item($z)
    if($e.Current.ControlType -eq [Windows.Automation.ControlType]::ListItem -or
       $e.Current.ControlType -eq [Windows.Automation.ControlType]::DataItem){
      if($e.Current.Name){$e.Current.Name}
    }
   })
   $items=@($items | Sort-Object -Unique)
   $sig=$items -join ';'
   if(-not $seen.Add($sig)){Log "DIALOG_${tag}_REPEAT_AT_PAGE=$page";break}
   $items | Set-Content -Encoding utf8 (Join-Path $dir ("d1-$tag-list-page-{0:D2}.txt" -f $page))
   Shot ("d1-$tag-list-page-{0:D2}.png" -f $page)
   Log "DIALOG_${tag}_PAGE_$page=$($items.Count)"
   if(-not $sp.Current.VerticallyScrollable){break}
   if($sp.Current.VerticalScrollPercent -ge 99){break}
   $sp.Scroll([Windows.Automation.ScrollAmount]::NoAmount,[Windows.Automation.ScrollAmount]::LargeIncrement)
   Start-Sleep -Milliseconds 400
  }
 }
}
Log 'SOURCE=OFFICIAL_ROBERT_SAMPLE_ONLY'
$cephLoadSucceeded=$false
$editorLoadSucceeded=$false
CaptureDialog 'initial'
# D1A: read only exploration of Cephalometry > Load analysis...
try{
 Click (AppMenu 'Cephalometry')
 Start-Sleep -Milliseconds 300
 $load=Named $root 'Load analysis...' 'MenuItem'
 $visible=@($load | Where-Object {$_.Current.ProcessId -eq $FacadProcessId -and -not $_.Current.IsOffscreen})
 Log "CEPH_MENU_LOAD_COUNT=$($visible.Count)"
 if($visible.Count -ne 1){throw 'Cephalometry Load analysis menu item ambiguous'}
 Click $visible[0]
 Start-Sleep -Seconds 2
 CaptureDialog 'load-analysis'
 EnumerateList 'load-analysis'
 $cephLoadSucceeded=$true
 Log 'LOAD_ANALYSIS_DIALOG_INSPECTED=true'
}catch{
 Log "LOAD_ANALYSIS_ERROR=$($_.Exception.Message)"
}finally{
 Escape
 Escape
 CaptureDialog 'load-analysis-after-esc'
}
# D1B: inspect the edit analysis dialog and its Load... built-in preset picker.
try{
 Click (AppMenu 'File')
 Start-Sleep -Milliseconds 300
 $editor=Named $root 'New/Edit ceph analysis...' 'MenuItem'
 $visible=@($editor | Where-Object {$_.Current.ProcessId -eq $FacadProcessId -and -not $_.Current.IsOffscreen})
 if($visible.Count -ne 1){throw "Edit ceph analysis count $($visible.Count)"}
 Click $visible[0]
 Start-Sleep -Seconds 1
 CaptureDialog 'editor'
 $load=Named $root 'Load...' 'Button'
 $visible=@($load | Where-Object {$_.Current.ProcessId -eq $FacadProcessId -and -not $_.Current.IsOffscreen})
 Log "EDITOR_LOAD_BUTTON_COUNT=$($visible.Count)"
 if($visible.Count -ne 1){throw 'Editor Load button ambiguous'}
 Click $visible[0]
 Start-Sleep -Seconds 2
 CaptureDialog 'editor-load-presets'
 EnumerateList 'editor-load-presets'
 $editorLoadSucceeded=$true
 Log 'EDITOR_PRESET_DIALOG_INSPECTED=true'
}catch{
 Log "EDITOR_PRESET_ERROR=$($_.Exception.Message)"
}finally{
 Escape
 Escape
 Escape
 CaptureDialog 'editor-after-esc'
}
# Optional read-only installed preset filename inventory; no file contents copied.
foreach($folder in @('C:\Facad\Analysis','C:\Facad\Analyses','C:\Facad\Ceph','C:\Facad')){
 if(-not (Test-Path $folder)){continue}
 try{
  Get-ChildItem -Path $folder -File -Recurse -ErrorAction SilentlyContinue |
   Where-Object {$_.Name -match 'analysis|analyse|ceph|berg|tweed|steiner|ricket|mcnamara' -or $_.Extension -in @('.fca','.ana','.ceph','.fcd')} |
   Select-Object -First 300 -ExpandProperty FullName |
   Set-Content -Encoding utf8 (Join-Path $dir ("d1-installed-catalog-paths-{0}.txt" -f ($folder -replace '[^a-zA-Z0-9]','_')))
 }catch{Log "INSTALLED_LIST_ERROR=$folder : $($_.Exception.Message)"}
}
Log 'D1_DISCOVERY_FINISHED_NO_ANALYSIS_SELECTED'

if(-not $cephLoadSucceeded -or -not $editorLoadSucceeded){
 throw "D1 catalog discovery gate failed; Cephalometry load inspected=$cephLoadSucceeded, editor preset inspected=$editorLoadSucceeded"
}
